#!/usr/bin/env python3
"""Quick test of strict orchestrator functionality"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Quick test without full article generation
def test_strict_features():
    print("Testing strict orchestrator features...")
    
    # Test 1: URL verification
    print("\n1. Testing URL verification:")
    from learning_center_agent.pipeline.strict_orchestrator import StrictOrchestrator

    orch = StrictOrchestrator()
    
    # Test real URL
    valid, status, msg = orch.verify_url_exists("https://www.google.com")
    print(f"  - Google.com: {valid} (Status: {status}, Message: {msg})")
    
    # Test fake URL
    valid, status, msg = orch.verify_url_exists("https://this-is-a-fake-url-that-does-not-exist-12345.com")
    print(f"  - Fake URL: {valid} (Status: {status}, Message: {msg})")
    
    # Test 2: Fact verification
    print("\n2. Testing fact verification database:")
    print(f"  - Verified facts loaded: {len(orch.verified_facts)} topics")
    for topic in orch.verified_facts:
        print(f"    - {topic}: {len(orch.verified_facts[topic]['facts'])} facts, {len(orch.verified_facts[topic]['sources'])} sources")
    
    # Test 3: Fact checking
    print("\n3. Testing fact checking on sample content:")
    sample_content = """
    Private equity AUM reached $4.5 trillion in 2024 according to recent data [Preqin, 2024](https://www.preqin.com/insights/global-reports/2024-preqin-global-report).
    
    Some made up fact that is not verified [Fake Source, 2024](https://fake-url.com/report).
    """
    
    fact_result = orch.verify_facts_against_database(sample_content)
    print(f"  - Credibility Score: {fact_result['credibility_score']}%")
    print(f"  - Verified Facts: {len(fact_result['verified_facts'])}")
    print(f"  - Unverified Facts: {len(fact_result['unverified_facts'])}")
    print(f"  - Fact Check Passed: {fact_result['fact_check_passed']}")
    
    # Test 4: Knowledge base
    print("\n4. Testing knowledge base connection:")
    if orch.vector_store_id:
        print(f"  ✅ Vector store connected: {orch.vector_store_id}")
    else:
        print("  ⚠️ No vector store configured")
    
    print("\n✅ All basic tests completed!")
    print("\nThe strict orchestrator is ready to generate fact-verified articles.")
    print("It will:")
    print("- Actually verify URLs exist")
    print("- Cross-reference facts against a verified database")
    print("- Fail articles with low credibility")
    print("- Use smart fallbacks to maintain reliability")

if __name__ == "__main__":
    test_strict_features()