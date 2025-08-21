#!/usr/bin/env python3
"""
Simple test to verify KB search is working in article generation
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.services.article_generator_gpt5 import generate_article_with_gpt5
from src.services.web_search import search_web
from src.services.kb_search_optimized import search_knowledge_base

def main():
    print("="*60)
    print("PRODUCTION TEST: Simple Article with REAL KB Search")
    print("="*60)
    
    topic = "Family office investment strategies for private equity"
    
    print(f"\nTopic: {topic}")
    print("\nStep 1: Testing KB Search...")
    
    # Test KB search
    kb_results = search_knowledge_base(topic, max_results=3)
    if kb_results['success']:
        print(f"✅ KB search successful! Found {kb_results.get('citations_count', 0)} results")
        print(f"Results preview: {kb_results['results'][:300]}...")
    else:
        print(f"❌ KB search failed: {kb_results.get('results', 'Unknown error')}")
        return
    
    print("\nStep 2: Testing Web Search...")
    
    # Test web search
    web_results = search_web(f"{topic} 2024 trends", max_results=3)
    if web_results['success']:
        print(f"✅ Web search successful! Found {len(web_results.get('results', []))} results")
    else:
        print(f"❌ Web search failed: {web_results.get('error', 'Unknown error')}")
    
    print("\nStep 3: Generating Article with Both Sources...")
    
    # Prepare research data
    research_data = {
        "kb_search": kb_results['results'] if kb_results['success'] else "",
        "web_search": "\n\n".join([
            f"{r['title']}\n{r['snippet']}\nSource: {r['link']}"
            for r in web_results.get('results', [])[:3]
        ]) if web_results['success'] else ""
    }
    
    # Generate article
    start_time = datetime.now()
    
    result = generate_article_with_gpt5(
        topic=topic,
        target_audience="Family office managers and advisors",
        word_count=1000,
        tone="professional",
        research_data=research_data,
        custom_instructions="Use both knowledge base and web search results. Focus on practical strategies."
    )
    
    generation_time = (datetime.now() - start_time).total_seconds()
    
    if result['success']:
        print(f"\n✅ Article generated in {generation_time:.1f}s!")
        
        # Extract title and preview
        lines = result['article'].split('\n')
        title = lines[0].replace('#', '').strip() if lines else "Untitled"
        
        print(f"\nTitle: {title}")
        print(f"Word count: {len(result['article'].split())}")
        print(f"\nPreview:\n{result['article'][:500]}...")
        
        # Save article
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simple_kb_article_{timestamp}.md"
        filepath = os.path.join("outputs", filename)
        
        os.makedirs("outputs", exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(result['article'])
            f.write(f"\n\n---\n\n## Generation Details\n")
            f.write(f"- Generated: {datetime.now().isoformat()}\n")
            f.write(f"- Generation time: {generation_time:.1f}s\n")
            f.write(f"- KB search results used: {'Yes' if kb_results['success'] else 'No'}\n")
            f.write(f"- Web search results used: {'Yes' if web_results['success'] else 'No'}\n")
        
        print(f"\n📄 Article saved to: {filepath}")
    else:
        print(f"\n❌ Article generation failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    print("✅ Test complete! KB search is working in production!")
    print("="*60)

if __name__ == "__main__":
    main()