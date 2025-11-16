#!/usr/bin/env python3
"""
Quick test script to verify chart artifact enrichment
Run this after executing the IBKR trading signal workflow
"""
import requests
import json
import sys

BACKEND_URL = "http://localhost:8000"

def test_enriched_artifact():
    """Test that chart artifacts have enriched context"""
    print("🔍 Fetching chart artifacts...")
    
    # Get all chart artifacts
    response = requests.get(f"{BACKEND_URL}/api/artifacts/?type=chart&limit=5")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch artifacts: {response.status_code}")
        return False
    
    data = response.json()
    artifacts = data.get('artifacts', [])
    
    if not artifacts:
        print("⚠️  No chart artifacts found. Run the workflow first.")
        return False
    
    print(f"✅ Found {len(artifacts)} chart artifact(s)\n")
    
    # Test first artifact
    artifact = artifacts[0]
    artifact_id = artifact['id']
    
    print(f"📊 Testing artifact #{artifact_id}: {artifact['name']}")
    print(f"   Symbol: {artifact.get('symbol', 'N/A')}")
    print(f"   Chart Type: {artifact.get('chart_type', 'N/A')}")
    
    # Get detailed artifact
    detail_response = requests.get(f"{BACKEND_URL}/api/artifacts/{artifact_id}")
    
    if detail_response.status_code != 200:
        print(f"❌ Failed to fetch artifact details: {detail_response.status_code}")
        return False
    
    enriched = detail_response.json()
    
    # Check enrichment fields
    checks = {
        'prompt': enriched.get('prompt') is not None,
        'response': enriched.get('response') is not None,
        'model_name': enriched.get('model_name') is not None,
        'metadata': enriched.get('metadata') is not None,
    }
    
    metadata = enriched.get('metadata', {})
    checks['market_data_snapshot'] = metadata.get('market_data_snapshot') is not None
    checks['indicator_summary'] = metadata.get('indicator_summary') is not None
    checks['llm_analysis'] = metadata.get('llm_analysis') is not None
    
    print("\n📋 Enrichment Status:")
    for field, present in checks.items():
        status = "✅" if present else "❌"
        print(f"   {status} {field}")
    
    # Show sample data
    if checks['market_data_snapshot']:
        snapshot = metadata['market_data_snapshot']
        print(f"\n📈 Market Data Snapshot:")
        print(f"   Latest Price: ${snapshot.get('latest_price', 'N/A')}")
        print(f"   Bar Count: {snapshot.get('bar_count', 0)}")
        if snapshot.get('bars'):
            latest_bar = snapshot['bars'][-1]
            print(f"   Latest Bar: {latest_bar.get('date', 'N/A')}")
            print(f"     Open: ${latest_bar.get('open', 0):.2f}")
            print(f"     High: ${latest_bar.get('high', 0):.2f}")
            print(f"     Low: ${latest_bar.get('low', 0):.2f}")
            print(f"     Close: ${latest_bar.get('close', 0):.2f}")
    
    if checks['indicator_summary']:
        indicators = metadata['indicator_summary']
        print(f"\n📊 Indicator Summary:")
        for name, value in indicators.items():
            if value is not None:
                print(f"   {name}: {value:.2f}")
    
    if checks['llm_analysis']:
        analysis = metadata['llm_analysis']
        print(f"\n🤖 LLM Analysis:")
        print(f"   Action: {analysis.get('action', 'N/A')}")
        print(f"   Confidence: {analysis.get('confidence', 'N/A')} ({analysis.get('confidence_score', 0)}%)")
        print(f"   Actionable: {analysis.get('is_actionable', False)}")
        if analysis.get('reasoning_snippet'):
            print(f"   Reasoning: {analysis['reasoning_snippet']}")
    
    # Count successes
    success_count = sum(checks.values())
    total_count = len(checks)
    
    print(f"\n📊 Overall: {success_count}/{total_count} enrichment fields present")
    
    if success_count >= 5:  # At least basic enrichment
        print("✅ Chart artifact enrichment working!")
        return True
    else:
        print("⚠️  Partial enrichment. Some fields missing.")
        return False


if __name__ == "__main__":
    try:
        success = test_enriched_artifact()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
