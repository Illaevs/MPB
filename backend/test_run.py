#!/usr/bin/env python3
"""
Test script to verify the CRM system setup
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports
    from app.core.config import settings
    print("✓ Configuration loaded successfully")

    from app.database.session import engine_sync as engine
    print("✓ Database engine created successfully")

    from app.database.base import Base
    print("✓ Base model imported successfully")

    # Import models
    from app.models import (
        Company, Deal, Stage, StageDependency,
        FinancialPlan, TreasuryTransaction, TransactionAllocation,
        CBRate, WorkResult
    )
    print("✓ All models imported successfully")

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

    print("\n🎉 CRM system is ready to run!")
    print("Run 'python run.py' to start the server")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
