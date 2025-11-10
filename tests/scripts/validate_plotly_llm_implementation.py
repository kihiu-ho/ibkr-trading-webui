"""
Validation script for Plotly chart generation and LLM prompt implementation.
This script validates the code structure without requiring dependencies.
"""
import sys
import os
import re
from pathlib import Path

# Add dags to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dags"))


def validate_chart_generator():
    """Validate chart_generator.py structure"""
    print("\n" + "="*70)
    print("VALIDATION 1: Chart Generator Structure")
    print("="*70 + "\n")
    
    chart_gen_path = Path(__file__).parent.parent.parent / "dags" / "utils" / "chart_generator.py"
    
    with open(chart_gen_path, 'r') as f:
        content = f.read()
    
    checks = {
        "Uses Plotly": "import plotly" in content or "from plotly" in content,
        "Uses stock_indicators": "from stock_indicators import" in content,
        "Has calculate_obv function": "def calculate_obv" in content,
        "Has normalize_value function": "def normalize_value" in content,
        "Has process_indicators function": "def process_indicators" in content,
        "Has create_plotly_figure function": "def create_plotly_figure" in content,
        "Exports JPEG": "format='jpeg'" in content or "format='jpeg'" in content.lower(),
        "7 subplots": "rows=7" in content or "make_subplots(rows=7" in content,
        "No matplotlib/mplfinance": "import matplotlib" not in content and "import mplfinance" not in content,
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False
    
    # Check for required indicators
    required_indicators = ["SuperTrend", "MACD", "RSI", "OBV", "ATR", "Volume"]
    print(f"\n   Checking for required indicators:")
    for indicator in required_indicators:
        found = indicator in content
        status = "✅" if found else "❌"
        print(f"   {status} {indicator}")
        if not found:
            all_passed = False
    
    return all_passed


def validate_llm_prompt():
    """Validate LLM prompt structure"""
    print("\n" + "="*70)
    print("VALIDATION 2: LLM Prompt Structure")
    print("="*70 + "\n")
    
    llm_path = Path(__file__).parent.parent.parent / "dags" / "utils" / "llm_signal_analyzer.py"
    
    with open(llm_path, 'r') as f:
        content = f.read()
    
    # Extract prompt
    prompt_match = re.search(r'ANALYSIS_PROMPT = """(.*?)"""', content, re.DOTALL)
    if not prompt_match:
        print("   ❌ ANALYSIS_PROMPT not found")
        return False
    
    prompt = prompt_match.group(1)
    
    checks = {
        "In English": not any(ord(c) > 127 and '\u4e00' <= c <= '\u9fff' for c in prompt[:1000]),
        "No Traditional Chinese": "使用通順的繁體中文" not in prompt and "繁體中文" not in prompt,
        "Has 6 sections": prompt.count("## ") >= 6,
        "Has Core Price Analysis": "## 1. Core Price Analysis" in prompt or "Core Price Analysis" in prompt,
        "Has Trend Indicator Analysis": "Trend Indicator Analysis" in prompt,
        "Has Confirmation Indicator Analysis": "Confirmation Indicator Analysis" in prompt,
        "Has Signal Confirmation System": "Signal Confirmation System" in prompt or "3/4 Rule" in prompt,
        "Has Trading Recommendations": "Trading Recommendations" in prompt,
        "Has Risk Assessment": "Risk Assessment" in prompt,
        "Has R-multiple": "R-multiple" in prompt or "r_multiple" in prompt,
        "Has target price framework": "Target Price Setting" in prompt or "target price" in prompt.lower(),
        "Medium-term focus": "30-180 days" in prompt or "medium-term" in prompt.lower(),
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False
    
    print(f"\n   Prompt length: {len(prompt)} characters")
    print(f"   Prompt sections: {prompt.count('## ')}")
    
    return all_passed


def validate_models():
    """Validate model updates"""
    print("\n" + "="*70)
    print("VALIDATION 3: Model Updates")
    print("="*70 + "\n")
    
    chart_model_path = Path(__file__).parent.parent.parent / "dags" / "models" / "chart.py"
    signal_model_path = Path(__file__).parent.parent.parent / "dags" / "models" / "signal.py"
    
    with open(chart_model_path, 'r') as f:
        chart_content = f.read()
    
    with open(signal_model_path, 'r') as f:
        signal_content = f.read()
    
    checks = {
        "ChartResult mentions JPEG": "JPEG" in chart_content or "jpeg" in chart_content.lower(),
        "TradingSignal has r_multiple": "r_multiple" in signal_content,
        "TradingSignal has position_size_percent": "position_size_percent" in signal_content,
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Run all validations"""
    print("\n" + "="*70)
    print("🔍 VALIDATING PLOTLY CHART & LLM IMPLEMENTATION")
    print("="*70)
    
    results = []
    
    # Run validations
    results.append(("Chart Generator", validate_chart_generator()))
    results.append(("LLM Prompt", validate_llm_prompt()))
    results.append(("Models", validate_models()))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70 + "\n")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED!")
        print("="*70)
        print("\n📝 Next steps:")
        print("   1. Run full test in Docker: ./tests/scripts/test_plotly_chart_llm_docker.sh")
        print("   2. Or manually: docker-compose exec airflow-webserver python3 tests/scripts/test_plotly_chart_llm.py")
        print("")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

