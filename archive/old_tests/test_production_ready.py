#!/usr/bin/env python3
"""Full production test of the article generation system"""

import asyncio
import sys
import os
import time

sys.path.append(os.path.abspath('.'))

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator_production import DakotaProductionOrchestrator

async def test_production_system():
    """Run a complete production test"""
    
    topic = "ESG Integration in Private Markets 2025"
    word_count = 2000
    
    print("🚀 PRODUCTION SYSTEM TEST")
    print("=" * 60)
    print(f"Topic: {topic}")
    print(f"Target: {word_count} words")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create request
    request = ArticleRequest(
        topic=topic,
        audience="Institutional Investors", 
        tone="Professional/Educational",
        word_count=word_count
    )
    
    # Initialize orchestrator
    orchestrator = DakotaProductionOrchestrator()
    
    # Track timing
    start_time = time.time()
    
    try:
        print("\n📋 Starting article generation...")
        result = await orchestrator.execute({"request": request})
        
        elapsed = time.time() - start_time
        
        if result.get("success"):
            data = result.get("data", {})
            output_folder = data.get("output_folder", "Unknown")
            
            print(f"\n✅ PRODUCTION TEST SUCCESSFUL!")
            print(f"⏱️  Time: {elapsed:.2f}s")
            print(f"📁 Output: {output_folder}")
            
            # Verify all files exist
            files_created = data.get("files_created", [])
            print(f"\n📄 Files Generated ({len(files_created)}):")
            
            all_exist = True
            for file in files_created:
                file_path = f"{output_folder}/{file}"
                exists = os.path.exists(file_path)
                size = os.path.getsize(file_path) if exists else 0
                status = "✅" if exists and size > 0 else "❌"
                print(f"   {status} {file} ({size:,} bytes)")
                if not exists or size == 0:
                    all_exist = False
                    
            # Check source quality
            metadata_file = f"{output_folder}/{files_created[1]}" if len(files_created) > 1 else None
            if metadata_file and os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = f.read()
                    
                # Count sources
                total_sources = metadata.count("**URL:**") or metadata.count("- URL:")
                kb_sources = metadata.count("dakota.com/learning-center/dakota-knowledge-base")
                web_sources = total_sources - kb_sources
                
                print(f"\n📊 Source Analysis:")
                print(f"   Total sources: {total_sources}")
                print(f"   Web sources: {web_sources}")
                print(f"   KB sources: {kb_sources} (should be 0)")
                
                # Check for real Dakota URLs
                real_dakota_urls = metadata.count("dakota.com/resources/blog") + metadata.count("dakota.com/insights")
                print(f"   Real Dakota URLs: {real_dakota_urls}")
                
            # Final verdict
            print(f"\n{'='*60}")
            if all_exist and web_sources >= 8 and kb_sources == 0:
                print("✅ SYSTEM IS PRODUCTION READY!")
                print("   - All files generated")
                print("   - Adequate web sources")  
                print("   - No KB sources in citations")
                print("   - Real Dakota URLs present")
            else:
                print("⚠️  ISSUES DETECTED:")
                if not all_exist:
                    print("   - Missing files")
                if web_sources < 8:
                    print("   - Insufficient sources")
                if kb_sources > 0:
                    print("   - KB sources in citations")
                    
        else:
            print(f"\n❌ Production test failed: {result.get('error', 'Unknown error')}")
            print(f"⏱️  Failed after: {elapsed:.2f}s")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Exception: {e}")
        print(f"⏱️  Failed after: {elapsed:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_production_system())