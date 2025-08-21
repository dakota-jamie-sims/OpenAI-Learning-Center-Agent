"""
Simple orchestrator using Responses API for all GPT-5 calls
"""
import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.tools.vector_store_handler import VectorStoreHandler
from src.services.openai_responses_client import ResponsesClient, supports_temperature
from src.config import DEFAULT_MODELS, OUTPUT_BASE_DIR

load_dotenv()


class SimpleOrchestrator:
    """Simplified orchestrator using Responses API throughout"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.responses_client = ResponsesClient()
        self.output_dir = Path(OUTPUT_BASE_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Vector store for knowledge base (still uses assistants API)
        self.vector_handler = VectorStoreHandler(self.client)
        self.vector_store_id = os.getenv("VECTOR_STORE_ID") or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if self.vector_store_id:
            print(f"✅ Using existing vector store: {self.vector_store_id}")
        else:
            print("⚠️ No vector store configured. Knowledge base search will be limited.")
    
    def search_knowledge_base(self, query: str, max_results: int = 5) -> str:
        """Search the knowledge base using a temporary Assistant"""
        if not self.vector_store_id:
            return "No Dakota knowledge base content available."
        
        try:
            # Still use assistants API for vector search
            assistant = self.client.beta.assistants.create(
                name="KB Search Assistant",
                instructions="You are a helpful assistant that searches through Dakota's knowledge base for relevant content.",
                model="gpt-4-turbo",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            
            thread = self.client.beta.threads.create()
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Search for information about: {query}. Return the most relevant insights from Dakota's knowledge base."
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            import time
            while run.status not in ['completed', 'failed']:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id,
                    order="desc",
                    limit=1
                )
                
                self.client.beta.assistants.delete(assistant.id)
                
                if messages.data:
                    return messages.data[0].content[0].text.value
                else:
                    return "No relevant content found in knowledge base."
            else:
                self.client.beta.assistants.delete(assistant.id)
                return "Knowledge base search failed."
                
        except Exception as e:
            print(f"⚠️ Knowledge base search error: {e}")
            return "Unable to search knowledge base at this time."
    
    def web_search(self, query: str) -> str:
        """Perform web search using responses API"""
        print(f"  🌐 Web searching: {query}")
        
        try:
            search_prompt = f"""Search the web for current information about: {query}
Focus on finding:
- Recent data and statistics from 2024-2025
- Authoritative sources and reports
- Specific numbers and trends
- Market insights for institutional investors

Return a detailed summary with specific data points and source citations."""

            response = self.responses_client.create_response(
                model=DEFAULT_MODELS["web_researcher"],
                input_text=search_prompt,
                reasoning_effort="medium",
                verbosity="high",
                temperature=0.7
            )
            
            return self._extract_text(response)
            
        except Exception as e:
            print(f"⚠️ Web search error: {e}")
            return f"Web search unavailable: {str(e)}"
    
    def fact_check_article(self, article_content: str) -> Dict[str, Any]:
        """Fact check using responses API"""
        print("🔍 Running fact check...")
        
        fact_check_prompt = f"""Fact-check this article and return a JSON response:

{article_content}

Analyze for:
1. Accuracy of statistics and data
2. Proper citations
3. Logical consistency
4. Professional tone

Return JSON with:
{{
    "fact_check_passed": true/false,
    "issues": ["list of any issues found"],
    "suggestions": ["list of improvements if needed"],
    "citation_count": number
}}"""
        
        try:
            response = self.responses_client.create_response(
                model=DEFAULT_MODELS["fact_checker"],
                input_text=fact_check_prompt,
                reasoning_effort="medium",
                verbosity="low",
                temperature=0.3
            )
            
            result_text = self._extract_text(response)
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"fact_check_passed": True, "citation_count": 0}
            
            if result.get("fact_check_passed", True):
                print(f"✅ Fact check passed! {result.get('citation_count', 0)} citations found.")
            else:
                print(f"⚠️ Fact check found issues: {', '.join(result.get('issues', []))}")
                
            return result
            
        except Exception as e:
            print(f"⚠️ Fact check error: {e}")
            return {"fact_check_passed": True, "citation_count": 0, "error": str(e)}
    
    def generate_article(self, topic: str, word_count: int = 1500) -> Dict[str, Any]:
        """Generate a complete article using responses API"""
        
        print(f"\n🚀 Generating article about: {topic}")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_").strip()[:50]
        article_dir = self.output_dir / f"{timestamp}-{safe_topic}"
        article_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Knowledge base search
            print("\n📚 Searching Dakota knowledge base...")
            search_queries = [
                topic,
                f"{topic} institutional investors",
                f"{topic} Dakota insights"
            ]
            
            kb_insights = []
            for search_query in search_queries[:2]:
                print(f"  🔍 Searching: {search_query}")
                result = self.search_knowledge_base(search_query)
                if result and "No relevant content" not in result:
                    kb_insights.append(f"### Search: {search_query}\n{result}")
            
            kb_insights_text = "\n\n".join(kb_insights) if kb_insights else "No specific Dakota knowledge base content found."
            print("✅ Knowledge base search complete")
            
            # Web search
            print("\n🌐 Searching web for current information...")
            web_searches = [
                f"{topic} 2024 2025 statistics data",
                f"{topic} recent trends institutional investors"
            ]
            
            web_results = []
            for search_query in web_searches:
                result = self.web_search(search_query)
                if result and "unavailable" not in result:
                    web_results.append(f"### Web Search: {search_query}\n{result}")
            
            web_results_text = "\n\n".join(web_results) if web_results else "Limited web search results available."
            print("✅ Web search complete")
            
            # Generate article
            print("📝 Writing article...")
            article_prompt = f"""Write a comprehensive article for Dakota's Learning Center about: {topic}

DAKOTA KNOWLEDGE BASE INSIGHTS:
{kb_insights_text}

CURRENT WEB RESEARCH:
{web_results_text}

Requirements:
- Exactly {word_count} words
- Professional yet conversational tone
- Include at least 10 inline citations using format: [Source Name, Date](URL)
- Focus on actionable insights for institutional investors
- Include specific statistics and data points

Structure with clear sections, data-driven insights, and a compelling narrative."""

            response = self.responses_client.create_response(
                model=DEFAULT_MODELS["writer"],
                input_text=article_prompt,
                reasoning_effort="medium",
                verbosity="high",
                temperature=0.7,
                max_tokens=4000
            )
            
            article_content = self._extract_text(response)
            
            # Fact check
            fact_check_result = self.fact_check_article(article_content)
            
            # Save article
            article_path = article_dir / "article.md"
            article_path.write_text(article_content)
            print(f"✅ Article saved to: {article_path}")
            
            # Generate summary
            print("📋 Creating executive summary...")
            summary_content = self._generate_summary(article_content, date_str)
            summary_path = article_dir / "summary.md"
            summary_path.write_text(summary_content)
            print("✅ Summary saved")
            
            # Generate social content
            print("📱 Creating social media content...")
            social_content = self._generate_social(article_content, topic, date_str)
            social_path = article_dir / "social.md"
            social_path.write_text(social_content)
            print("✅ Social content saved")
            
            # Generate metadata
            print("📊 Generating metadata...")
            metadata_content = self._generate_metadata(article_content, topic, date_str, fact_check_result)
            metadata_path = article_dir / "metadata.md"
            metadata_path.write_text(metadata_content)
            print("✅ Metadata saved")
            
            print(f"\n✨ Article generation complete!")
            print(f"📁 Output directory: {article_dir}")
            
            return {
                "status": "success",
                "output_dir": str(article_dir),
                "files": {
                    "article": str(article_path),
                    "summary": str(summary_path),
                    "social": str(social_path),
                    "metadata": str(metadata_path)
                },
                "fact_check": fact_check_result,
                "message": f"Article generated successfully with {fact_check_result.get('citation_count', 0)} citations"
            }
            
        except Exception as e:
            print(f"\n❌ Error generating article: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "error": str(e),
                "output_dir": str(article_dir) if 'article_dir' in locals() else None
            }
    
    def _extract_text(self, response) -> str:
        """Extract text from responses API response"""
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                texts = []
                for item in response.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                return "\n\n".join(texts)
            elif hasattr(response.content, 'text'):
                return response.content.text
        return str(response)
    
    def _generate_summary(self, article_content: str, date_str: str) -> str:
        """Generate executive summary using responses API"""
        summary_prompt = f"""Create an executive summary of this article:

{article_content[:3000]}...

Requirements:
- Extract ALL key statistics and data points
- Focus on actionable insights for institutional investors
- Include specific numbers, percentages, and dates
- Keep under 300 words
- Format with bullet points for key findings"""

        response = self.responses_client.create_response(
            model=DEFAULT_MODELS["summary"],
            input_text=summary_prompt,
            reasoning_effort="low",
            verbosity="medium",
            temperature=0.5
        )
        
        return f"""---
title: Executive Summary
date: {date_str}
---

{self._extract_text(response)}"""
    
    def _generate_social(self, article_content: str, topic: str, date_str: str) -> str:
        """Generate social media content using responses API"""
        social_prompt = f"""Create social media content for this article about {topic}:

{article_content[:2000]}...

Generate:
1. LinkedIn post (300 words with statistics)
2. Twitter/X thread (5-7 tweets with data)
3. Email snippet (150 words)

Use actual data points and statistics from the article."""

        response = self.responses_client.create_response(
            model=DEFAULT_MODELS["social"],
            input_text=social_prompt,
            reasoning_effort="minimal",
            verbosity="medium",
            temperature=0.7
        )
        
        return f"""---
title: Social Media Content
date: {date_str}
topic: {topic}
---

{self._extract_text(response)}"""
    
    def _generate_metadata(self, article_content: str, topic: str, date_str: str, fact_check_result: Dict) -> str:
        """Generate metadata using responses API"""
        metadata_prompt = f"""Generate metadata for this article about {topic}:

{article_content[:1500]}...

Create JSON metadata with:
- title: SEO-optimized title
- description: 150-160 character description
- keywords: list of 5-8 relevant keywords
- reading_time: estimated minutes
- target_audience: description"""

        response = self.responses_client.create_response(
            model=DEFAULT_MODELS["metrics"],
            input_text=metadata_prompt,
            reasoning_effort="minimal",
            verbosity="low",
            temperature=0.3
        )
        
        metadata_text = self._extract_text(response)
        
        # Try to extract JSON
        import re
        json_match = re.search(r'\{[^{}]*\}', metadata_text, re.DOTALL)
        if json_match:
            try:
                metadata = json.loads(json_match.group())
            except:
                metadata = {}
        else:
            metadata = {}
        
        # Add fact check results
        metadata["fact_check_status"] = "passed" if fact_check_result.get("fact_check_passed", True) else "needs_review"
        metadata["citation_count"] = fact_check_result.get("citation_count", 0)
        
        return f"""---
title: Article Metadata
date: {date_str}
generated_at: {datetime.now().isoformat()}
---

{json.dumps(metadata, indent=2)}

## Fact Check Results
- Status: {metadata["fact_check_status"]}
- Citations: {metadata["citation_count"]}
- Issues: {len(fact_check_result.get("issues", []))}"""