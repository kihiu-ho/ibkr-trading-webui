"""
Comprehensive test script for LLM Chart Signals system.
Tests all components from chart generation to signal creation.
"""
import asyncio
import sys
from datetime import datetime

# Test imports
try:
    from backend.config.settings import settings
    from backend.services.chart_generator import ChartGenerator
    from backend.services.llm_service import LLMService
    from backend.services.signal_generator import SignalGenerator
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_configuration():
    """Test that all required configuration is present."""
    print("\n" + "=" * 60)
    print("TEST 1: Configuration")
    print("=" * 60)
    
    checks = {
        "LLM Provider": settings.LLM_VISION_PROVIDER,
        "LLM Model": settings.LLM_VISION_MODEL,
        "OpenAI API Key": "Configured" if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_key_here" else "NOT CONFIGURED",
        "MinIO Endpoint": settings.MINIO_ENDPOINT,
        "MinIO Public Endpoint": settings.MINIO_PUBLIC_ENDPOINT,
        "Chart Width": settings.CHART_WIDTH,
        "Chart Height": settings.CHART_HEIGHT,
        "Default Language": settings.LLM_DEFAULT_LANGUAGE,
        "Risk Per Trade": settings.RISK_PER_TRADE,
        "Max Position Size": settings.MAX_POSITION_SIZE,
    }
    
    for key, value in checks.items():
        print(f"  {key}: {value}")
    
    if settings.OPENAI_API_KEY == "your_key_here" or not settings.OPENAI_API_KEY:
        print("\n⚠️  WARNING: OpenAI API key not configured!")
        print("   Set OPENAI_API_KEY in your .env file to enable LLM analysis")
        return False
    
    print("\n✅ Configuration test passed")
    return True


async def test_chart_generation():
    """Test chart generation for multiple timeframes."""
    print("\n" + "=" * 60)
    print("TEST 2: Chart Generation")
    print("=" * 60)
    
    try:
        generator = ChartGenerator()
        symbol = "TSLA"
        timeframes = ["1d", "1w"]
        
        for timeframe in timeframes:
            print(f"\n  Generating {timeframe} chart for {symbol}...")
            period = 200 if timeframe == "1d" else 52
            
            chart = await generator.generate_chart(
                symbol=symbol,
                timeframe=timeframe,
                period=period
            )
            
            print(f"    ✅ Chart generated")
            print(f"    JPEG URL: {chart['chart_url_jpeg'][:80]}...")
            print(f"    HTML URL: {chart['chart_url_html'][:80]}...")
            print(f"    Binary size: {len(chart['chart_image_binary'])} bytes")
        
        print("\n✅ Chart generation test passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Chart generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_service():
    """Test LLM service integration."""
    print("\n" + "=" * 60)
    print("TEST 3: LLM Service (Skipped if no API key)")
    print("=" * 60)
    
    if settings.OPENAI_API_KEY == "your_key_here" or not settings.OPENAI_API_KEY:
        print("  ⚠️  Skipping LLM test (no API key configured)")
        return True
    
    try:
        llm_service = LLMService()
        
        # Generate a test chart first
        chart_gen = ChartGenerator()
        chart = await chart_gen.generate_chart("TSLA", "1d", 200)
        
        print(f"\n  Analyzing chart with LLM ({settings.LLM_VISION_MODEL})...")
        
        analysis = await llm_service.analyze_chart(
            chart_url=chart["chart_url_jpeg"],
            prompt_template="daily",
            symbol="TSLA",
            language="en"
        )
        
        print(f"    ✅ Analysis received")
        print(f"    Signal: {analysis['parsed_signal'].get('signal', 'N/A')}")
        print(f"    Trend: {analysis['parsed_signal'].get('trend', 'N/A')}")
        print(f"    Text length: {len(analysis['raw_text'])} chars")
        
        print("\n✅ LLM service test passed")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM service failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_signal_generation():
    """Test complete signal generation workflow."""
    print("\n" + "=" * 60)
    print("TEST 4: Signal Generation (Skipped if no API key)")
    print("=" * 60)
    
    if settings.OPENAI_API_KEY == "your_key_here" or not settings.OPENAI_API_KEY:
        print("  ⚠️  Skipping signal generation test (no API key configured)")
        return True
    
    try:
        generator = SignalGenerator()
        symbol = "TSLA"
        
        print(f"\n  Generating complete signal for {symbol}...")
        print(f"  This will:")
        print(f"    1. Generate charts (daily + weekly)")
        print(f"    2. Analyze each with LLM")
        print(f"    3. Consolidate analyses")
        print(f"    4. Extract trading parameters")
        print(f"    5. Calculate R-multiples")
        print(f"\n  ⏳ This may take 30-60 seconds...")
        
        signal = await generator.generate_signal(
            symbol=symbol,
            timeframes=["1d", "1w"],
            language="en"
        )
        
        print(f"\n  ✅ Signal generated successfully!")
        print(f"\n  Signal Details:")
        print(f"    Symbol: {signal['symbol']}")
        print(f"    Signal Type: {signal['signal_type']}")
        print(f"    Trend: {signal['trend']}")
        print(f"    Confidence: {signal['confidence']:.1%}")
        
        if signal.get('entry_price_low'):
            print(f"\n  Trading Parameters:")
            print(f"    Entry Range: ${signal['entry_price_low']:.2f} - ${signal['entry_price_high']:.2f}")
            print(f"    Stop Loss: ${signal['stop_loss']:.2f}")
            print(f"    Conservative Target: ${signal['target_conservative']:.2f} ({signal['r_multiple_conservative']:.2f}R)")
            print(f"    Aggressive Target: ${signal['target_aggressive']:.2f} ({signal['r_multiple_aggressive']:.2f}R)")
            print(f"    Position Size: {signal['position_size_percent']:.1f}%")
        
        print(f"\n  Charts:")
        print(f"    Daily: {signal['chart_url_daily'][:60]}...")
        print(f"    Weekly: {signal['chart_url_weekly'][:60]}...")
        
        print(f"\n  Analysis Preview (first 200 chars):")
        if signal.get('analysis_consolidated'):
            print(f"    {signal['analysis_consolidated'][:200]}...")
        elif signal.get('analysis_daily'):
            print(f"    {signal['analysis_daily'][:200]}...")
        
        print("\n✅ Signal generation test passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Signal generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_generation():
    """Test batch signal generation."""
    print("\n" + "=" * 60)
    print("TEST 5: Batch Generation (Skipped if no API key)")
    print("=" * 60)
    
    if settings.OPENAI_API_KEY == "your_key_here" or not settings.OPENAI_API_KEY:
        print("  ⚠️  Skipping batch test (no API key configured)")
        return True
    
    try:
        generator = SignalGenerator()
        symbols = ["AAPL", "NVDA"]
        
        print(f"\n  Generating signals for {len(symbols)} symbols: {', '.join(symbols)}")
        print(f"  ⏳ This may take 1-2 minutes...")
        
        result = await generator.batch_generate(
            symbols=symbols,
            timeframes=["1d"],  # Only daily for speed
            language="en",
            max_concurrent=2
        )
        
        print(f"\n  ✅ Batch generation complete!")
        print(f"    Total: {result['total']}")
        print(f"    Successful: {result['successful']}")
        print(f"    Failed: {result['failed']}")
        
        if result['errors']:
            print(f"\n  Errors:")
            for error in result['errors']:
                print(f"    - {error['symbol']}: {error['error']}")
        
        print("\n✅ Batch generation test passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Batch generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  LLM CHART SIGNALS - COMPREHENSIVE TEST SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    start_time = datetime.now()
    
    results = []
    
    # Run tests sequentially
    results.append(("Configuration", await test_configuration()))
    results.append(("Chart Generation", await test_chart_generation()))
    results.append(("LLM Service", await test_llm_service()))
    results.append(("Signal Generation", await test_signal_generation()))
    # results.append(("Batch Generation", await test_batch_generation()))  # Skip for faster testing
    
    # Summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name:.<40} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print(f"  Total: {total_passed}/{total_tests} tests passed")
    print(f"  Time: {elapsed:.1f}s")
    print("=" * 60)
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run database migration: psql -U your_user -d your_db -f database/migrations/add_llm_signals.sql")
        print("  2. Start the backend: python -m backend.main")
        print("  3. Open http://localhost:8000/signals")
        print("  4. Generate your first signal!")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

