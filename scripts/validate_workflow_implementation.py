"""Validate workflow implementation without requiring database connection.

This script validates:
1. All code files exist and are syntactically valid
2. Database schema includes workflow_logs table
3. Workflow tasks include multi-code processing
4. Comprehensive logging is implemented
"""
import sys
import os
import ast
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False

def validate_python_syntax(filepath):
    """Validate Python file syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        return False

def check_function_exists(filepath, function_name):
    """Check if a function exists in a file (including async functions)."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and 
                    node.name == function_name):
                    return True
        return False
    except Exception as e:
        print(f"  ✗ Error checking function: {e}")
        return False

def check_sql_table_exists(filepath, table_name):
    """Check if SQL schema includes a table."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return f"CREATE TABLE IF NOT EXISTS {table_name}" in content or \
                   f"CREATE TABLE {table_name}" in content
    except Exception as e:
        print(f"  ✗ Error checking SQL: {e}")
        return False

def main():
    """Main validation function."""
    print("\n" + "="*80)
    print("WORKFLOW IMPLEMENTATION VALIDATION")
    print("="*80)
    
    all_valid = True
    
    # 1. Check database schema
    print("\n" + "─"*80)
    print("1. DATABASE SCHEMA VALIDATION")
    print("─"*80)
    
    schema_file = "database/init.sql"
    if validate_file_exists(schema_file, "Database schema"):
        if check_sql_table_exists(schema_file, "workflow_logs"):
            print("  ✓ workflow_logs table defined")
        else:
            print("  ✗ workflow_logs table NOT found")
            all_valid = False
        
        if check_sql_table_exists(schema_file, "codes"):
            print("  ✓ codes table defined")
        else:
            print("  ✗ codes table NOT found")
            all_valid = False
            
        if check_sql_table_exists(schema_file, "strategy_codes"):
            print("  ✓ strategy_codes association table defined")
        else:
            print("  ✗ strategy_codes table NOT found")
            all_valid = False
    else:
        all_valid = False
    
    # 2. Check workflow model
    print("\n" + "─"*80)
    print("2. WORKFLOW LOG MODEL VALIDATION")
    print("─"*80)
    
    model_file = "backend/models/workflow_log.py"
    if validate_file_exists(model_file, "WorkflowLog model"):
        if validate_python_syntax(model_file):
            print("  ✓ Python syntax valid")
            
            # Check for key fields
            with open(model_file, 'r') as f:
                content = f.read()
                required_fields = [
                    'workflow_execution_id',
                    'step_name',
                    'step_type',
                    'input_data',
                    'output_data',
                    'duration_ms',
                    'success',
                    'error_message'
                ]
                for field in required_fields:
                    if field in content:
                        print(f"  ✓ Field defined: {field}")
                    else:
                        print(f"  ✗ Field missing: {field}")
                        all_valid = False
        else:
            all_valid = False
    else:
        all_valid = False
    
    # 3. Check workflow tasks
    print("\n" + "─"*80)
    print("3. WORKFLOW TASKS VALIDATION")
    print("─"*80)
    
    tasks_file = "backend/tasks/workflow_tasks.py"
    if validate_file_exists(tasks_file, "Workflow tasks"):
        if validate_python_syntax(tasks_file):
            print("  ✓ Python syntax valid")
            
            # Check for key functions
            functions_to_check = [
                ('_log_workflow_step', 'Logging helper function'),
                ('_execute_workflow_for_multiple_codes', 'Multi-code processing'),
                ('_execute_workflow_for_code', 'Single code processing'),
                ('execute_trading_workflow', 'Main workflow task')
            ]
            
            for func_name, description in functions_to_check:
                if check_function_exists(tasks_file, func_name):
                    print(f"  ✓ Function exists: {func_name} - {description}")
                else:
                    print(f"  ✗ Function missing: {func_name} - {description}")
                    all_valid = False
            
            # Check for comprehensive logging
            with open(tasks_file, 'r') as f:
                content = f.read()
                logging_checks = [
                    ('_log_workflow_step(', 'Logging calls'),
                    ('input_data', 'Input data tracking'),
                    ('output_data', 'Output data tracking'),
                    ('duration_ms', 'Duration tracking'),
                    ('time.time()', 'Timing measurement'),
                    ('for idx, code_obj in enumerate(codes)', 'Multi-code loop'),
                    ('asyncio.sleep(60)', '60-second delay')
                ]
                for check, description in logging_checks:
                    if check in content:
                        print(f"  ✓ Found: {description}")
                    else:
                        print(f"  ✗ Missing: {description}")
                        all_valid = False
        else:
            all_valid = False
    else:
        all_valid = False
    
    # 4. Check test infrastructure
    print("\n" + "─"*80)
    print("4. TEST INFRASTRUCTURE VALIDATION")
    print("─"*80)
    
    test_files = [
        ("scripts/test_workflow_tsla_nvda.py", "Python test script"),
        ("scripts/setup_test_strategy.sql", "SQL setup script"),
        ("scripts/query_workflow_logs.sql", "SQL query script"),
        ("WORKFLOW_TEST_DOCUMENTATION.md", "Documentation"),
        ("WORKFLOW_IMPLEMENTATION_SUMMARY.md", "Implementation summary")
    ]
    
    for filepath, description in test_files:
        if validate_file_exists(filepath, description):
            if filepath.endswith('.py'):
                if validate_python_syntax(filepath):
                    print(f"  ✓ Python syntax valid")
                else:
                    all_valid = False
        else:
            all_valid = False
    
    # 5. Check strategy and code models
    print("\n" + "─"*80)
    print("5. DATA MODEL VALIDATION")
    print("─"*80)
    
    strategy_model = "backend/models/strategy.py"
    if validate_file_exists(strategy_model, "Strategy model"):
        if validate_python_syntax(strategy_model):
            print("  ✓ Python syntax valid")
            
            with open(strategy_model, 'r') as f:
                content = f.read()
                if 'class Code' in content:
                    print("  ✓ Code model defined")
                else:
                    print("  ✗ Code model NOT found")
                    all_valid = False
                
                if 'StrategyCode' in content or 'strategy_codes' in content:
                    print("  ✓ Many-to-many association defined")
                else:
                    print("  ✗ Many-to-many association NOT found")
                    all_valid = False
        else:
            all_valid = False
    else:
        all_valid = False
    
    # Summary
    print("\n" + "="*80)
    if all_valid:
        print("✓ ALL VALIDATIONS PASSED")
        print("="*80)
        print("\nThe workflow implementation is complete and ready for testing!")
        print("\nTo test with a real database:")
        print("1. Ensure PostgreSQL is running")
        print("2. Set DATABASE_URL environment variable")
        print("3. Run: python scripts/test_workflow_tsla_nvda.py")
        print("\n" + "="*80)
        return 0
    else:
        print("✗ VALIDATION FAILED")
        print("="*80)
        print("\nSome components are missing or invalid.")
        print("Please review the errors above.")
        print("\n" + "="*80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

