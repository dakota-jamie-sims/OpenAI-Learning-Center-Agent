#!/usr/bin/env python3
"""Quick test of enhanced orchestrator"""
import asyncio

from learning_center_agent.pipeline.enhanced_orchestrator import (
    EnhancedOrchestrator,
)

async def test():
    try:
        print("Testing enhanced orchestrator...")
        orch = EnhancedOrchestrator()
        print("✅ Orchestrator created")
        
        # Test parallel research
        print("\nTesting parallel research...")
        research = await orch.parallel_research("test topic")
        print(f"✅ Research complete: KB={len(research['kb'])} chars, Web={len(research['web'])} chars")
        
        print("\n✅ Enhanced orchestrator is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    exit(0 if success else 1)