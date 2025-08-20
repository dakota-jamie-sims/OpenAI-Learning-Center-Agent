#!/usr/bin/env python3
"""
Generate article with STRICT fact verification
Ensures 100% accuracy while maintaining reliability
"""
import sys

from learning_center_agent.pipeline.strict_orchestrator import StrictOrchestrator

def main():
    """Generate a strictly fact-checked article"""
    if len(sys.argv) < 2:
        print("Usage: python generate_strict_article.py 'Your Article Topic' [word_count]")
        print("\nExample:")
        print("  python generate_strict_article.py 'Private Equity Trends in 2025'")
        print("  python generate_strict_article.py 'ESG Integration in Alternative Investments' 2000")
        sys.exit(1)
    
    topic = sys.argv[1]
    word_count = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    
    print("\n" + "="*60)
    print("🔐 STRICT FACT VERIFICATION MODE")
    print("="*60)
    print("\nThis mode implements:")
    print("✅ Real URL verification (HTTP HEAD requests)")
    print("✅ Verified facts database cross-referencing")
    print("✅ Credibility scoring for all sources")
    print("✅ Smart fallbacks to maintain reliability")
    print("\nCredibility thresholds:")
    print("  - 90%+: Article passes as-is")
    print("  - 70-89%: Passes with warnings")
    print("  - 50-69%: Regenerates problematic facts")
    print("  - <50%: Uses only pre-verified facts")
    print("\n" + "="*60 + "\n")
    
    try:
        orchestrator = StrictOrchestrator()
        result = orchestrator.generate_article(topic, word_count)
        
        if result["status"] == "success":
            print("\n" + "="*60)
            print("✅ STRICT FACT-VERIFIED ARTICLE GENERATED!")
            print("="*60)
            print(f"\nCredibility Score: {result['fact_check_results']['credibility_score']}%")
            print(f"Verification Status: {result['fact_check_results']['status']}")
            print(f"Verified Facts: {result['fact_check_results']['verified_facts']}/{result['fact_check_results']['total_facts']}")
            print(f"\nOutput directory: {result['output_dir']}")
            print("\nGenerated files:")
            print("  - article.md (main content)")
            print("  - summary.md (executive summary)")
            print("  - social.md (social media content)")
            print("  - metadata.md (comprehensive metadata)")
            print("  - fact-verification-report.md (detailed fact check report)")
            
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error occurred')}")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()