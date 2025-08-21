#!/usr/bin/env python3
"""
Quick article generation demo with GPT-5
"""
import os
import sys
from datetime import datetime
from openai import OpenAI

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.web_search import search_web

def generate_quick_article(topic: str):
    """Generate a quick article using GPT-5"""
    client = OpenAI()
    
    print(f"\n🚀 Generating article about: {topic}")
    print("="*60)
    
    # Step 1: Quick web search
    print("\n1️⃣ Searching for current information...")
    start = datetime.now()
    search_results = search_web(topic, max_results=3)
    print(f"   ✅ Found {len(search_results)} sources in {(datetime.now()-start).total_seconds():.1f}s")
    
    # Format findings
    findings = "\n".join([
        f"• {r['title']}: {r['snippet'][:100]}..."
        for r in search_results[:3]
    ])
    
    # Step 2: Generate article with GPT-5
    print("\n2️⃣ Generating article with GPT-5...")
    start = datetime.now()
    
    prompt = f"""Write a concise 500-word article about "{topic}" for investors.

Recent findings:
{findings}

Include: intro, 2-3 key points with data, and conclusion with actionable insights."""

    try:
        response = client.responses.create(
            model="gpt-5",
            input=prompt,
            reasoning={"effort": "minimal"},  # Fast mode
            text={"verbosity": "medium"}
        )
        
        # Extract text
        article = ""
        if hasattr(response, 'output_text'):
            article = response.output_text
        elif hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'text'):
                            article = content.text
                            break
        
        duration = (datetime.now()-start).total_seconds()
        print(f"   ✅ Generated in {duration:.1f}s")
        
        # Step 3: Display results
        print("\n3️⃣ Article Preview:")
        print("-"*60)
        print(article[:800] + "..." if len(article) > 800 else article)
        print("-"*60)
        
        # Save article
        filename = f"output/demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs("output", exist_ok=True)
        with open(filename, "w") as f:
            f.write(f"# {topic}\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n")
            f.write(article)
            f.write(f"\n\n---\n\n## Sources\n\n")
            for i, r in enumerate(search_results, 1):
                f.write(f"{i}. [{r['title']}]({r.get('url', '#')})\n")
        
        print(f"\n✅ Full article saved to: {filename}")
        print(f"📊 Stats: {len(article.split())} words, {len(search_results)} sources")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n⚠️  Note: Make sure you have access to GPT-5 through the Responses API")
        return False


if __name__ == "__main__":
    # Test topics
    topics = [
        "Portfolio Diversification Strategies for 2024",
        "AI Investment Opportunities in Q4 2024",
        "Private Equity Trends and Outlook"
    ]
    
    print("🎯 Quick Article Generation Demo with GPT-5")
    print("="*60)
    
    # Let user choose or use default
    print("\nAvailable topics:")
    for i, topic in enumerate(topics, 1):
        print(f"{i}. {topic}")
    
    choice = input("\nEnter topic number (or press Enter for #1): ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(topics):
        topic = topics[int(choice)-1]
    else:
        topic = topics[0]
    
    success = generate_quick_article(topic)
    
    if success:
        print("\n🎉 Demo completed successfully!")
    else:
        print("\n💡 Tip: Check your OpenAI API key and GPT-5 access")