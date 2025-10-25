"""Test workflow execution for TSLA and NVDA.

This script:
1. Creates or updates the test strategy with TSLA and NVDA
2. Triggers workflow execution
3. Monitors execution progress
4. Displays all logged I/O from workflow_logs table
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.database import SessionLocal, engine, Base
from backend.models.workflow import Workflow
from backend.models.strategy import Strategy, Code, StrategyCode
from backend.models.agent import WorkflowExecution
from backend.models.workflow_log import WorkflowLog
from backend.tasks.workflow_tasks import execute_trading_workflow
from sqlalchemy import text
import time
import json
from datetime import datetime


def setup_test_data(db):
    """Set up test strategy with TSLA and NVDA."""
    print("\n" + "="*80)
    print("SETTING UP TEST DATA")
    print("="*80)
    
    # Check if workflow exists
    workflow = db.query(Workflow).filter(Workflow.name == "Two Indicator Strategy").first()
    if not workflow:
        print("\nCreating default workflow...")
        workflow = Workflow(
            name="Two Indicator Strategy",
            type="two_indicator",
            description="Trading workflow with daily and weekly chart analysis",
            steps=[
                {"step": "authenticate", "name": "Authenticate IBKR"},
                {"step": "fetch_data", "name": "Fetch Market Data"},
                {"step": "analyze_daily", "name": "Analyze Daily Chart"},
                {"step": "analyze_weekly", "name": "Analyze Weekly Chart"},
                {"step": "consolidate", "name": "Consolidate Analysis"},
                {"step": "make_decision", "name": "Generate Trading Decision"},
                {"step": "place_order", "name": "Place Order"}
            ],
            default_params={"risk_per_trade": 0.02, "account_size": 100000}
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
    print(f"✓ Workflow: {workflow.name} (ID: {workflow.id})")
    
    # Create or get TSLA code
    tsla = db.query(Code).filter(Code.conid == 76792991).first()
    if not tsla:
        print("\nCreating TSLA code record...")
        tsla = Code(
            symbol="TSLA",
            conid=76792991,
            exchange="NASDAQ",
            name="Tesla Inc"
        )
        db.add(tsla)
        db.commit()
        db.refresh(tsla)
    print(f"✓ TSLA: {tsla.symbol} (conid: {tsla.conid}, ID: {tsla.id})")
    
    # Create or get NVDA code
    nvda = db.query(Code).filter(Code.conid == 4815747).first()
    if not nvda:
        print("\nCreating NVDA code record...")
        nvda = Code(
            symbol="NVDA",
            conid=4815747,
            exchange="NASDAQ",
            name="NVIDIA Corporation"
        )
        db.add(nvda)
        db.commit()
        db.refresh(nvda)
    print(f"✓ NVDA: {nvda.symbol} (conid: {nvda.conid}, ID: {nvda.id})")
    
    # Create or update test strategy
    strategy_name = "Test Multi-Code Strategy - TSLA & NVDA"
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        print(f"\nCreating test strategy: {strategy_name}")
        strategy = Strategy(
            name=strategy_name,
            workflow_id=workflow.id,
            type="two_indicator",
            param={
                "period_1": "1y",
                "bar_1": "1d",
                "period_2": "5y",
                "bar_2": "1w",
                "risk_per_trade": 0.02,
                "account_size": 100000
            },
            active=1
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
    else:
        print(f"\n✓ Found existing strategy: {strategy_name}")
        # Update workflow_id if needed
        if strategy.workflow_id != workflow.id:
            strategy.workflow_id = workflow.id
            db.commit()
    
    print(f"✓ Strategy: {strategy.name} (ID: {strategy.id}, Workflow ID: {strategy.workflow_id})")
    
    # Associate codes with strategy (many-to-many)
    if tsla not in strategy.codes:
        print(f"\nAssociating TSLA with strategy...")
        strategy.codes.append(tsla)
    
    if nvda not in strategy.codes:
        print(f"\nAssociating NVDA with strategy...")
        strategy.codes.append(nvda)
    
    db.commit()
    
    print(f"\n✓ Strategy has {len(strategy.codes)} codes associated:")
    for code in strategy.codes:
        print(f"  - {code.symbol} (conid: {code.conid})")
    
    return strategy, workflow, [tsla, nvda]


def execute_workflow(strategy_id):
    """Execute the trading workflow."""
    print("\n" + "="*80)
    print("EXECUTING WORKFLOW")
    print("="*80)
    
    print(f"\nTriggering workflow for strategy ID: {strategy_id}")
    print("This will process TSLA and NVDA sequentially with comprehensive logging...")
    print("Note: This may take several minutes as it processes both symbols with 60s delay between them.")
    
    try:
        # Execute workflow synchronously for testing
        result = execute_trading_workflow.apply(args=[strategy_id])
        
        print("\n✓ Workflow execution completed!")
        print(f"\nExecution result:")
        print(json.dumps(result.get(), indent=2, default=str))
        
        return result.get()
        
    except Exception as e:
        print(f"\n✗ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_logs(db, execution_id=None):
    """Display comprehensive workflow logs."""
    print("\n" + "="*80)
    print("WORKFLOW LOGS")
    print("="*80)
    
    query = db.query(WorkflowLog).order_by(WorkflowLog.created_at.desc())
    
    if execution_id:
        query = query.filter(WorkflowLog.workflow_execution_id == execution_id)
        print(f"\nShowing logs for execution ID: {execution_id}")
    else:
        print("\nShowing recent workflow logs (all executions):")
    
    logs = query.limit(100).all()
    
    if not logs:
        print("\nNo logs found.")
        return
    
    print(f"\nFound {len(logs)} log entries:\n")
    
    # Group logs by code
    logs_by_code = {}
    for log in logs:
        code = log.code or "general"
        if code not in logs_by_code:
            logs_by_code[code] = []
        logs_by_code[code].append(log)
    
    for code, code_logs in logs_by_code.items():
        print(f"\n{'─'*80}")
        print(f"CODE: {code}")
        print(f"{'─'*80}")
        
        for log in reversed(code_logs):  # Show in chronological order
            status = "✓" if log.success else "✗"
            print(f"\n{status} [{log.created_at.strftime('%H:%M:%S')}] {log.step_name} ({log.step_type})")
            
            if log.duration_ms:
                print(f"   Duration: {log.duration_ms}ms ({log.duration_ms/1000:.2f}s)")
            
            if log.input_data:
                print(f"   Input: {json.dumps(log.input_data, indent=6)[:500]}...")
            
            if log.output_data:
                output_str = json.dumps(log.output_data, indent=6, default=str)
                if len(output_str) > 500:
                    print(f"   Output: {output_str[:500]}...")
                else:
                    print(f"   Output: {output_str}")
            
            if log.error_message:
                print(f"   ERROR: {log.error_message}")
    
    print(f"\n{'='*80}\n")


def display_execution_summary(db, strategy_id):
    """Display execution summary."""
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    
    # Get latest execution for this strategy
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.strategy_id == strategy_id
    ).order_by(WorkflowExecution.started_at.desc()).first()
    
    if not execution:
        print("\nNo execution found.")
        return None
    
    print(f"\nExecution ID: {execution.id}")
    print(f"Strategy ID: {execution.strategy_id}")
    print(f"Workflow ID: {execution.workflow_id}")
    print(f"Status: {execution.status}")
    print(f"Started: {execution.started_at}")
    print(f"Completed: {execution.completed_at}")
    
    if execution.result:
        print(f"\nResult:")
        print(json.dumps(execution.result, indent=2, default=str))
    
    if execution.error:
        print(f"\nError: {execution.error}")
    
    # Count logs by type
    log_counts = db.execute(text("""
        SELECT step_type, success, COUNT(*) as count
        FROM workflow_logs
        WHERE workflow_execution_id = :execution_id
        GROUP BY step_type, success
        ORDER BY step_type, success DESC
    """), {"execution_id": execution.id}).fetchall()
    
    print(f"\nLog Summary:")
    for row in log_counts:
        status = "Success" if row[1] else "Failed"
        print(f"  {row[0]}: {row[2]} ({status})")
    
    return execution


def main():
    """Main test execution."""
    print("\n" + "="*80)
    print("IBKR TRADING WORKFLOW TEST - TSLA & NVDA")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    
    db = SessionLocal()
    
    try:
        # Setup test data
        strategy, workflow, codes = setup_test_data(db)
        
        # Ask user if they want to proceed
        print("\n" + "="*80)
        response = input("\nProceed with workflow execution? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("\nExecution cancelled by user.")
            return
        
        # Execute workflow
        result = execute_workflow(strategy.id)
        
        if result:
            # Display execution summary
            execution = display_execution_summary(db, strategy.id)
            
            # Display comprehensive logs
            if execution:
                display_logs(db, execution.id)
            
            print("\n" + "="*80)
            print("TEST COMPLETED SUCCESSFULLY")
            print("="*80)
            print(f"\nAll I/O has been logged to the workflow_logs table.")
            print(f"You can query this data using:")
            print(f"  SELECT * FROM workflow_logs WHERE workflow_execution_id = {execution.id};")
            print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

