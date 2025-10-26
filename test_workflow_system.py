#!/usr/bin/env python3
"""
Test script to verify the IBKR workflow system is working.
This script creates a test strategy and executes the workflow.
"""
import sys
import os
sys.path.append('.')

from backend.core.database import SessionLocal
from backend.models.strategy import Strategy, Code
from backend.tasks.workflow_tasks import execute_trading_workflow
from datetime import datetime, timezone
import json

def create_test_strategy():
    """Create a test strategy for workflow execution."""
    db = SessionLocal()
    try:
        # Check if test strategy already exists
        existing_strategy = db.query(Strategy).filter(Strategy.name == "Test Workflow Strategy").first()
        if existing_strategy:
            print(f"Test strategy already exists with ID: {existing_strategy.id}")
            return existing_strategy.id
        
        # Create a test code (AAPL)
        test_code = db.query(Code).filter(Code.symbol == "AAPL").first()
        if not test_code:
            test_code = Code(
                symbol="AAPL",
                conid=265598,  # AAPL NASDAQ
                exchange="NASDAQ",
                name="Apple Inc"
            )
            db.add(test_code)
            db.commit()
            db.refresh(test_code)
        
        # Create test strategy
        strategy = Strategy(
            name="Test Workflow Strategy",
            workflow_id=None,  # Set to None to avoid foreign key constraint
            type="trend_following",
            param={
                "risk_per_trade": 0.02,
                "account_size": 100000
            },
            active=1,
            llm_enabled=1,
            llm_model="gpt-4-turbo-preview",
            llm_language="en",
            llm_timeframes=["1d", "1w"],
            llm_consolidate=1,
            llm_prompt_custom="Analyze this chart for trading signals"
        )
        
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        
        # Associate the code with the strategy
        strategy.codes.append(test_code)
        db.commit()
        
        print(f"Created test strategy with ID: {strategy.id}")
        print(f"Associated with code: {test_code.symbol} (conid: {test_code.conid})")
        
        return strategy.id
        
    except Exception as e:
        print(f"Error creating test strategy: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def test_workflow_execution(strategy_id):
    """Test the workflow execution."""
    print(f"\n=== Testing Workflow Execution for Strategy {strategy_id} ===")
    
    try:
        # Execute the workflow task
        result = execute_trading_workflow.apply(args=[strategy_id])
        
        print(f"Workflow task submitted successfully!")
        print(f"Task ID: {result.id}")
        print(f"Task State: {result.state}")
        
        if result.state == 'PENDING':
            print("Task is queued for execution...")
            print("Check Flower UI at http://localhost:5555 to monitor progress")
        elif result.state == 'SUCCESS':
            print("Task completed successfully!")
            print(f"Result: {result.result}")
        elif result.state == 'FAILURE':
            print("Task failed!")
            print(f"Error: {result.traceback}")
        
        return result
        
    except Exception as e:
        print(f"Error executing workflow: {e}")
        return None

def check_workflow_logs(strategy_id):
    """Check workflow execution logs."""
    db = SessionLocal()
    try:
        from backend.models.workflow import WorkflowExecution
        from backend.models.workflow_log import WorkflowLog
        
        # Get recent executions for this strategy
        executions = db.query(WorkflowExecution).filter(
            WorkflowExecution.strategy_id == strategy_id
        ).order_by(WorkflowExecution.started_at.desc()).limit(5).all()
        
        print(f"\n=== Recent Workflow Executions ===")
        for execution in executions:
            print(f"Execution {execution.id}: {execution.status} - {execution.started_at}")
            
            # Get logs for this execution
            logs = db.query(WorkflowLog).filter(
                WorkflowLog.workflow_execution_id == execution.id
            ).order_by(WorkflowLog.created_at).all()
            
            print(f"  Steps executed: {len(logs)}")
            for log in logs:
                status = "✓" if log.success else "✗"
                print(f"    {status} {log.step_name} ({log.step_type}) - {log.duration_ms}ms")
                if not log.success and log.error_message:
                    print(f"      Error: {log.error_message}")
        
    except Exception as e:
        print(f"Error checking workflow logs: {e}")
    finally:
        db.close()

def main():
    """Main test function."""
    print("=== IBKR Workflow System Test ===")
    
    # Step 1: Create test strategy
    strategy_id = create_test_strategy()
    if not strategy_id:
        print("Failed to create test strategy. Exiting.")
        return
    
    # Step 2: Test workflow execution
    result = test_workflow_execution(strategy_id)
    if not result:
        print("Failed to execute workflow. Exiting.")
        return
    
    # Step 3: Check workflow logs
    check_workflow_logs(strategy_id)
    
    print("\n=== Test Complete ===")
    print("The workflow system is set up and ready for execution.")
    print("Monitor progress at:")
    print("- Flower UI: http://localhost:5555")
    print("- Backend API: http://localhost:8000")
    print("- IBKR Gateway: http://localhost:5056")

if __name__ == "__main__":
    main()
