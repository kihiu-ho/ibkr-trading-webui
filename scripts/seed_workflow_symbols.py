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
                'config': {'position_size': 10}
            },
            {
                'symbol': 'NVDA',
                'name': 'NVIDIA Corporation',
                'enabled': True,
                'priority': 9,
                'workflow_type': 'trading_signal',
                'config': {'position_size': 10}
            }
        ]
        
        for data in symbols_data:
            symbol = WorkflowSymbol(**data)
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
