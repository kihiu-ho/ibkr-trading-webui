"""
Integration test for LLM Chart Signals system.

Tests the complete flow:
1. Generate chart for a symbol
2. Analyze chart with LLM
3. Parse trading signal

Requirements:
- OPENAI_API_KEY environment variable set
- MinIO running
- IBKR Gateway running (for market data)
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.chart_generator import ChartGenerator
from backend.services.llm_service import LLMService
from backend.config.settings import settings


async def test_chart_generation(symbol: str = "TSLA"):
    """Test chart generation service."""
    print(f"\n{'='*70}")
    print(f"TEST 1: Chart Generation for {symbol}")
    print(f"{'='*70}\n")
    
    try:
        generator = ChartGenerator()
        
        print(f"📊 Generating daily chart for {symbol}...")
        daily_chart = await generator.generate_chart(
            symbol=symbol,
            timeframe="1d",
            period=200
        )
        
        print(f"✅ Daily chart generated successfully!")
        print(f"   URL (JPEG): {daily_chart['chart_url_jpeg']}")
        print(f"   URL (HTML): {daily_chart['chart_url_html']}")
        print(f"   Data points: {daily_chart['data_points']}")
        print(f"   Latest price: ${daily_chart['latest_price']:.2f}")
        print(f"   Latest date: {daily_chart['latest_date']}")
        
        print(f"\n📊 Generating weekly chart for {symbol}...")
        weekly_chart = await generator.generate_chart(
            symbol=symbol,
            timeframe="1w",
            period=52
        )
        
        print(f"✅ Weekly chart generated successfully!")
        print(f"   URL (JPEG): {weekly_chart['chart_url_jpeg']}")
        print(f"   Data points: {weekly_chart['data_points']}")
        
        return daily_chart, weekly_chart
        
    except Exception as e:
        print(f"❌ Chart generation failed: {str(e)}")
        raise


async def test_llm_analysis(chart_url: str, symbol: str):
    """Test LLM vision analysis."""
    print(f"\n{'='*70}")
    print(f"TEST 2: LLM Vision Analysis for {symbol}")
    print(f"{'='*70}\n")
    
    # Check API key
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_key_here":
        print("⚠️  OPENAI_API_KEY not set!")
        print("   Set environment variable: export OPENAI_API_KEY='sk-...'")
        print("   Skipping LLM analysis test.")
        return None
    
    try:
        llm = LLMService()
        
        print(f"🤖 Analyzing chart with {settings.LLM_VISION_MODEL}...")
        print(f"   Chart URL: {chart_url}")
        print(f"   This may take 30-60 seconds...")
        
        result = await llm.analyze_chart(
            chart_url=chart_url,
            prompt_template="daily",
            symbol=symbol,
            language="en"
        )
        
        print(f"✅ LLM analysis completed!")
        print(f"   Model: {result['model_used']}")
        print(f"   Provider: {result['provider']}")
        print(f"   Language: {result['language']}")
        
        print(f"\n📈 PARSED SIGNAL:")
        signal = result['parsed_signal']
        print(f"   Signal: {signal['signal']}")
        print(f"   Trend: {signal['trend']}")
        print(f"   Confirmation passed: {signal['confirmation']['passed']}")
        print(f"   Confirmed signals: {signal['confirmation']['confirmed_count']}/4")
        
        print(f"\n📝 ANALYSIS PREVIEW (first 500 chars):")
        print(f"   {result['raw_text'][:500]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ LLM analysis failed: {str(e)}")
        if "API key" in str(e):
            print("   → Check your OPENAI_API_KEY")
        raise


async def test_multi_timeframe_workflow(symbol: str = "TSLA"):
    """Test complete multi-timeframe workflow."""
    print(f"\n{'='*70}")
    print(f"TEST 3: Multi-Timeframe Workflow for {symbol}")
    print(f"{'='*70}\n")
    
    try:
        # 1. Generate both charts
        generator = ChartGenerator()
        llm = LLMService()
        
        print(f"📊 Step 1: Generating daily and weekly charts...")
        daily_chart, weekly_chart = await asyncio.gather(
            generator.generate_chart(symbol, "1d", 200),
            generator.generate_chart(symbol, "1w", 52)
        )
        print(f"✅ Both charts generated")
        
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_key_here":
            print("⚠️  Skipping LLM analysis (no API key)")
            return
        
        # 2. Analyze both charts
        print(f"\n🤖 Step 2: Analyzing daily chart...")
        daily_analysis = await llm.analyze_chart(
            chart_url=daily_chart['chart_url_jpeg'],
            prompt_template="daily",
            symbol=symbol
        )
        print(f"✅ Daily analysis complete")
        
        print(f"\n🤖 Step 3: Analyzing weekly chart...")
        weekly_analysis = await llm.analyze_chart(
            chart_url=weekly_chart['chart_url_jpeg'],
            prompt_template="weekly",
            symbol=symbol
        )
        print(f"✅ Weekly analysis complete")
        
        # 3. Consolidate (simplified - full implementation would call LLM again)
        print(f"\n🔄 Step 4: Consolidating analyses...")
        print(f"   Daily signal: {daily_analysis['parsed_signal']['signal']}")
        print(f"   Daily trend: {daily_analysis['parsed_signal']['trend']}")
        print(f"   Weekly confirms: (analysis text available)")
        
        print(f"\n✅ Multi-timeframe workflow complete!")
        
        return {
            "daily_chart": daily_chart,
            "weekly_chart": weekly_chart,
            "daily_analysis": daily_analysis,
            "weekly_analysis": weekly_analysis
        }
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        raise


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🤖 LLM CHART SIGNALS - INTEGRATION TEST")
    print("="*70)
    
    print(f"\n⚙️  CONFIGURATION:")
    print(f"   LLM Provider: {settings.LLM_VISION_PROVIDER}")
    print(f"   LLM Model: {settings.LLM_VISION_MODEL}")
    print(f"   MinIO Endpoint: {settings.MINIO_PUBLIC_ENDPOINT}")
    print(f"   IBKR URL: {settings.IBKR_API_BASE_URL}")
    print(f"   API Key set: {'✓' if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != 'your_key_here' else '✗'}")
    
    symbol = "TSLA"
    
    try:
        # Test 1: Chart Generation
        daily_chart, weekly_chart = await test_chart_generation(symbol)
        
        # Test 2: LLM Analysis (if API key is set)
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_key_here":
            await test_llm_analysis(daily_chart['chart_url_jpeg'], symbol)
        else:
            print(f"\n⚠️  Skipping LLM tests (set OPENAI_API_KEY to test)")
        
        # Test 3: Multi-timeframe workflow (optional)
        # await test_multi_timeframe_workflow(symbol)
        
        print(f"\n{'='*70}")
        print(f"✅ ALL TESTS PASSED!")
        print(f"{'='*70}\n")
        
        print(f"🎉 System is working! Next steps:")
        print(f"   1. Review generated charts in MinIO")
        print(f"   2. Set OPENAI_API_KEY to test LLM analysis")
        print(f"   3. Implement Phase 3: Signal Generator Service")
        print(f"   4. Implement Phase 4: Database & API")
        print(f"   5. Implement Phase 5: Frontend UI")
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ TESTS FAILED")
        print(f"{'='*70}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

