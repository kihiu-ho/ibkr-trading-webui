#!/usr/bin/env python3
"""
Seed initial workflow symbols (TSLA, NVDA)
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from backend.core.database import SessionLocal, engine
from backend.models import Base, WorkflowSymbol
from backend.models.workflow import Workflow
from backend.models.workflow_symbol import SymbolWorkflowLink


def seed_symbols():
    """Seed initial symbols."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if symbols already exist
        existing = db.query(WorkflowSymbol).count()
        if existing > 0:
            print(f"Found {existing} existing symbols, skipping seed")
            return
        
        symbols_data = [
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'enabled': True,
                'priority': 10,
                'workflow_type': 'trading_signal',
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'enabled': True,
                'priority': 9,
                'workflow_type': 'trading_signal',
            }
        ]

        workflows = db.query(Workflow).filter(Workflow.is_active.is_(True)).order_by(Workflow.id).all()
        
        for data in symbols_data:
            symbol = WorkflowSymbol(**data)
            if workflows:
                link = SymbolWorkflowLink(
                    workflow_id=workflows[0].id,
                    priority=0,
                    timezone="America/New_York",
                    is_active=True,
                )
                symbol.workflow_links.append(link)
            db.add(symbol)
            print(f"✅ Added symbol: {data['symbol']} - {data['name']}")
        
        db.commit()
        print("\n✅ Symbol seeding complete!")
        
    except Exception as e:
        print(f"❌ Error seeding symbols: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_symbols()
