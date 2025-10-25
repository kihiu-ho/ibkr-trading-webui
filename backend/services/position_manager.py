"""
Position Manager Service - Tracks positions and calculates P&L.

Manages:
1. Current positions (holdings)
2. Portfolio value calculations
3. Realized/unrealized P&L
4. Position updates from order fills
5. Portfolio snapshots
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.position import Position
from backend.models.order import Order
from backend.services.ibkr_service import IBKRService

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Manage trading positions and portfolio values.
    
    Features:
    - Real-time position tracking
    - P&L calculation (realized & unrealized)
    - Portfolio value aggregation
    - IBKR synchronization
    - Position risk metrics
    """
    
    def __init__(self, db: Session):
        """Initialize the position manager."""
        self.db = db
        self.ibkr = IBKRService()
    
    async def update_from_fill(
        self,
        order: Order
    ) -> Optional[Position]:
        """
        Update positions when an order is filled.
        
        Args:
            order: Filled order object
            
        Returns:
            Updated/created Position object
        """
        try:
            logger.info(f"Updating position from order fill: {order.id}")
            
            # Find existing position
            position = self.db.query(Position).filter(
                Position.conid == order.conid,
                Position.strategy_id == order.strategy_id
            ).first()
            
            if order.side == "BUY":
                return await self._handle_buy_fill(order, position)
            else:  # SELL
                return await self._handle_sell_fill(order, position)
                
        except Exception as e:
            logger.error(f"Error updating position from fill: {str(e)}", exc_info=True)
            return None
    
    async def _handle_buy_fill(
        self,
        order: Order,
        position: Optional[Position]
    ) -> Position:
        """Handle a buy order fill."""
        if position:
            # Add to existing position
            old_quantity = position.quantity
            old_avg_price = position.average_price
            
            new_quantity = old_quantity + order.filled_quantity
            new_avg_price = (
                (old_avg_price * old_quantity) + (order.filled_price * order.filled_quantity)
            ) / new_quantity
            
            position.quantity = new_quantity
            position.average_price = new_avg_price
            position.last_updated = datetime.now()
            
            logger.info(
                f"Updated position: {order.conid} from {old_quantity} to {new_quantity} "
                f"(avg price: {old_avg_price:.2f} -> {new_avg_price:.2f})"
            )
        else:
            # Create new position
            position = Position(
                conid=order.conid,
                strategy_id=order.strategy_id,
                quantity=order.filled_quantity,
                average_price=order.filled_price,
                last_price=order.filled_price,
                last_updated=datetime.now(),
                created_at=datetime.now()
            )
            self.db.add(position)
            logger.info(
                f"Created new position: {order.conid} quantity={order.filled_quantity} "
                f"@ {order.filled_price:.2f}"
            )
        
        self.db.commit()
        self.db.refresh(position)
        
        # Calculate P&L
        await self._update_position_pnl(position)
        
        return position
    
    async def _handle_sell_fill(
        self,
        order: Order,
        position: Optional[Position]
    ) -> Optional[Position]:
        """Handle a sell order fill."""
        if not position:
            logger.warning(f"Sell order {order.id} but no position found for {order.conid}")
            return None
        
        # Calculate realized P&L
        realized_pnl = (order.filled_price - position.average_price) * order.filled_quantity
        
        # Update position
        position.quantity -= order.filled_quantity
        position.realized_pnl = (position.realized_pnl or 0) + realized_pnl
        position.last_updated = datetime.now()
        
        logger.info(
            f"Position sold: {order.conid} qty={order.filled_quantity} "
            f"realized P&L=${realized_pnl:.2f}"
        )
        
        # Close position if quantity is zero
        if position.quantity <= 0:
            logger.info(f"Position closed: {order.conid}")
            position.is_closed = True
            position.closed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(position)
        
        # Update P&L
        await self._update_position_pnl(position)
        
        return position
    
    async def _update_position_pnl(self, position: Position) -> None:
        """Update position P&L values."""
        try:
            # Get current price from IBKR
            current_price = await self._get_current_price(position.conid)
            if current_price:
                position.last_price = current_price
                
                # Calculate unrealized P&L
                if not position.is_closed:
                    position.unrealized_pnl = (
                        (current_price - position.average_price) * position.quantity
                    )
                else:
                    position.unrealized_pnl = 0
                
                self.db.commit()
                
                logger.debug(
                    f"Updated P&L for {position.conid}: "
                    f"unrealized=${position.unrealized_pnl:.2f}, "
                    f"realized=${position.realized_pnl or 0:.2f}"
                )
        except Exception as e:
            logger.error(f"Error updating position P&L: {str(e)}")
    
    async def _get_current_price(self, conid: int) -> Optional[float]:
        """Get current market price for a contract."""
        try:
            market_data = await self.ibkr.get_market_data(conid)
            if market_data and 'last_price' in market_data:
                return float(market_data['last_price'])
            return None
        except Exception as e:
            logger.error(f"Error getting current price for {conid}: {str(e)}")
            return None
    
    async def get_all_positions(
        self,
        strategy_id: Optional[int] = None,
        include_closed: bool = False
    ) -> List[Position]:
        """
        Get all positions, optionally filtered by strategy.
        
        Args:
            strategy_id: Filter by strategy ID
            include_closed: Include closed positions
            
        Returns:
            List of Position objects
        """
        try:
            query = self.db.query(Position)
            
            if strategy_id:
                query = query.filter(Position.strategy_id == strategy_id)
            
            if not include_closed:
                query = query.filter(Position.is_closed == False)
            
            positions = query.order_by(Position.last_updated.desc()).all()
            
            logger.info(f"Retrieved {len(positions)} positions (strategy={strategy_id}, closed={include_closed})")
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []
    
    async def get_position(
        self,
        conid: int,
        strategy_id: Optional[int] = None
    ) -> Optional[Position]:
        """Get a specific position."""
        try:
            query = self.db.query(Position).filter(Position.conid == conid)
            
            if strategy_id:
                query = query.filter(Position.strategy_id == strategy_id)
            
            return query.first()
        except Exception as e:
            logger.error(f"Error getting position for {conid}: {str(e)}")
            return None
    
    async def calculate_portfolio_value(
        self,
        strategy_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate total portfolio value and P&L.
        
        Args:
            strategy_id: Calculate for specific strategy only
            
        Returns:
            Dictionary with portfolio metrics
        """
        try:
            positions = await self.get_all_positions(strategy_id, include_closed=False)
            
            # Update all positions with current prices
            for position in positions:
                await self._update_position_pnl(position)
            
            # Calculate totals
            total_value = sum(
                (pos.last_price or pos.average_price) * pos.quantity
                for pos in positions
            )
            
            total_cost = sum(
                pos.average_price * pos.quantity
                for pos in positions
            )
            
            total_unrealized_pnl = sum(
                pos.unrealized_pnl or 0
                for pos in positions
            )
            
            # Get realized P&L from closed positions
            closed_query = self.db.query(
                func.sum(Position.realized_pnl)
            ).filter(Position.is_closed == True)
            
            if strategy_id:
                closed_query = closed_query.filter(Position.strategy_id == strategy_id)
            
            total_realized_pnl = closed_query.scalar() or 0
            
            # Calculate returns
            total_pnl = total_realized_pnl + total_unrealized_pnl
            return_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            result = {
                "portfolio_value": total_value,
                "total_cost": total_cost,
                "realized_pnl": total_realized_pnl,
                "unrealized_pnl": total_unrealized_pnl,
                "total_pnl": total_pnl,
                "return_percent": return_pct,
                "position_count": len(positions),
                "calculated_at": datetime.now().isoformat()
            }
            
            logger.info(
                f"Portfolio value: ${total_value:.2f} "
                f"(P&L: ${total_pnl:.2f}, {return_pct:.2f}%)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "portfolio_value": 0,
                "total_pnl": 0
            }
    
    async def sync_with_ibkr(
        self,
        strategy_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Synchronize positions with IBKR account.
        
        Args:
            strategy_id: Sync for specific strategy only
            
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info("Syncing positions with IBKR...")
            
            # Get positions from IBKR
            ibkr_positions = await self.ibkr.get_positions()
            
            synced = 0
            created = 0
            updated = 0
            errors = []
            
            for ibkr_pos in ibkr_positions:
                try:
                    conid = ibkr_pos.get('conid')
                    if not conid:
                        continue
                    
                    # Find or create position
                    position = await self.get_position(conid, strategy_id)
                    
                    if position:
                        # Update existing
                        position.quantity = ibkr_pos.get('quantity', position.quantity)
                        position.average_price = ibkr_pos.get('avg_price', position.average_price)
                        position.last_price = ibkr_pos.get('market_price', position.last_price)
                        position.last_updated = datetime.now()
                        updated += 1
                    else:
                        # Create new (if we don't have it tracked)
                        position = Position(
                            conid=conid,
                            strategy_id=strategy_id,
                            quantity=ibkr_pos.get('quantity', 0),
                            average_price=ibkr_pos.get('avg_price', 0),
                            last_price=ibkr_pos.get('market_price', 0),
                            created_at=datetime.now(),
                            last_updated=datetime.now()
                        )
                        self.db.add(position)
                        created += 1
                    
                    synced += 1
                    
                except Exception as e:
                    errors.append(f"Error syncing {conid}: {str(e)}")
                    logger.error(f"Error syncing position {conid}: {str(e)}")
            
            self.db.commit()
            
            result = {
                "success": True,
                "synced": synced,
                "created": created,
                "updated": updated,
                "errors": errors,
                "synced_at": datetime.now().isoformat()
            }
            
            logger.info(f"IBKR sync complete: {synced} positions ({created} created, {updated} updated)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing with IBKR: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "synced": 0
            }
    
    async def get_position_risk_metrics(
        self,
        position: Position
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics for a position.
        
        Args:
            position: Position object
            
        Returns:
            Dictionary with risk metrics
        """
        try:
            await self._update_position_pnl(position)
            
            current_price = position.last_price or position.average_price
            position_value = current_price * position.quantity
            
            # Get total portfolio value
            portfolio = await self.calculate_portfolio_value(position.strategy_id)
            portfolio_value = portfolio['portfolio_value']
            
            # Calculate metrics
            position_pct = (position_value / portfolio_value * 100) if portfolio_value > 0 else 0
            pnl_pct = ((current_price - position.average_price) / position.average_price * 100) if position.average_price > 0 else 0
            
            metrics = {
                "position_value": position_value,
                "position_percent": position_pct,
                "pnl_percent": pnl_pct,
                "unrealized_pnl": position.unrealized_pnl or 0,
                "realized_pnl": position.realized_pnl or 0,
                "entry_price": position.average_price,
                "current_price": current_price,
                "quantity": position.quantity
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}


def get_position_manager(db: Session) -> PositionManager:
    """Factory function for PositionManager."""
    return PositionManager(db)

