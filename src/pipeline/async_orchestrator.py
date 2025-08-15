"""
Async Orchestrator for OpenAI Assistants
Implements parallel execution with proper thread management
"""
import asyncio
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime
from openai import AsyncOpenAI, OpenAI
import time
from concurrent.futures import ThreadPoolExecutor

from ..agents.base_assistant import AssistantManager, BaseAssistant
from ..config import settings
from ..utils.files import run_dir_for_topic, write_text, read_text


class AsyncOrchestrator:
    """Orchestrates article creation with parallel assistant execution"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.sync_client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.manager = AssistantManager(self.sync_client)
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    async def initialize_assistants(self):
        """Create all assistants with proper tools"""
        print("🚀 Initializing assistants...")
        
        # Create vector store for knowledge base
        kb_files = list(Path(settings.KNOWLEDGE_BASE_DIR).rglob("*.md"))
        if kb_files:
            self.manager.create_vector_store("Dakota Knowledge Base", [str(f) for f in kb_files[:50]])
        
        # Define tool configurations
        web_search_tools = [{"type": "web_search"}]
        file_search_tools = [{"type": "file_search"}]
        code_tools = [{"type": "code_interpreter"}]
        
        # Create all assistants
        assistants_config = [
            ("web_researcher", "dakota-web-researcher.md", web_search_tools),
            ("kb_researcher", "dakota-kb-researcher.md", file_search_tools),
            ("research_synthesizer", "dakota-research-synthesizer.md", None),
            ("content_writer", "dakota-content-writer.md", code_tools),
            ("fact_checker", "dakota-fact-checker.md", code_tools),
            ("claim_checker", "dakota-claim-checker.md", None),
            ("seo_specialist", "dakota-seo-specialist.md", None),
            ("metrics_analyzer", "dakota-metrics-analyzer.md", code_tools),
            ("summary_writer", "dakota-summary-writer.md", None),
            ("social_promoter", "dakota-social-promoter.md", None),
            ("iteration_manager", "dakota-iteration-manager.md", code_tools),
            ("evidence_packager", "dakota-evidence-packager.md", code_tools)
        ]
        
        for name, prompt_file, tools in assistants_config:
            use_vector_store = name == "kb_researcher"
            self.manager.create_assistant_from_prompt(
                name=name,
                prompt_file=prompt_file,
                model=settings.DEFAULT_MODELS.get(name.replace("_", ""), "gpt-4-turbo-preview"),
                tools=tools,
                use_vector_store=use_vector_store
            )
        
        print("✅ All assistants initialized")
    
    async def run_assistant_async(self, assistant_name: str, prompt: str) -> Dict[str, Any]:
        """Run an assistant asynchronously"""
        assistant = self.manager.get_assistant(assistant_name)
        if not assistant:
            raise ValueError(f"Assistant {assistant_name} not found")
        
        # Create thread and add message
        assistant.create_thread()
        assistant.add_message(prompt)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            assistant.run
        )
        
        return {
            "assistant": assistant_name,
            "result": result.content[0].text.value if result else None,
            "thread_id": assistant.thread.id
        }
    
    async def phase2_parallel_research(self, topic: str) -> Dict[str, Any]:
        """Phase 2: Parallel research with web and KB"""
        print("\n🔍 Phase 2: Starting parallel research...")
        
        web_prompt = f"""Research topic: {topic}
        
Budget directives:
- Use at most {settings.MAX_WEB_CALLS} web searches
- Focus on authoritative sources from preferred domains
- Keep final brief under {settings.OUTPUT_TOKEN_CAPS['synth_max_tokens']} tokens

Deliver:
- Structured research brief with full citations
- 5-7 key findings with sources
- Focus on data from last 12 months"""

        kb_prompt = f"""Research topic: {topic}
        
Use file search on our Dakota knowledge base to find:
- Relevant investment philosophy connections
- Similar topics we've covered
- Dakota's perspective on this area

Budget: Maximum {settings.MAX_FILE_CALLS} searches
Output: Structured brief with specific file references"""

        # Run both researchers in parallel
        tasks = [
            self.run_assistant_async("web_researcher", web_prompt),
            self.run_assistant_async("kb_researcher", kb_prompt)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "web": results[0]["result"] if not isinstance(results[0], Exception) else str(results[0]),
            "kb": results[1]["result"] if not isinstance(results[1], Exception) else str(results[1])
        }
    
    async def phase25_evidence_packaging(self, research: Dict[str, Any], run_dir: str) -> str:
        """Phase 2.5: Create evidence package"""
        if not settings.ENABLE_EVIDENCE:
            return ""
        
        print("\n📦 Phase 2.5: Creating evidence package...")
        
        prompt = f"""Create a JSON evidence package with:
        
1. Top 25 sources ranked by relevance and credibility
2. Key quotes with exact attribution
3. Atomic claims with confidence levels
4. Source quality metrics

Research data:
[WEB]
{research['web'][:20000]}

[KB]
{research['kb'][:10000]}

Output pure JSON only."""

        result = await self.run_assistant_async("evidence_packager", prompt)
        
        # Save evidence pack
        proof_path = os.path.join(run_dir, "proof_pack.json")
        if result["result"]:
            write_text(proof_path, result["result"])
        
        return proof_path
    
    async def phase3_synthesis(self, research: Dict[str, Any]) -> str:
        """Phase 3: Synthesize research"""
        print("\n🔗 Phase 3: Synthesizing research...")
        
        prompt = f"""Synthesize research into a unified brief for article writing.

[WEB RESEARCH]
{research['web']}

[KB RESEARCH]  
{research['kb']}

Requirements:
- Combine insights cohesively
- Maintain source attribution
- Highlight Dakota-relevant angles
- Stay under {settings.OUTPUT_TOKEN_CAPS['synth_max_tokens']} tokens"""

        result = await self.run_assistant_async("research_synthesizer", prompt)
        return result["result"]
    
    async def phase4_content_creation(self, topic: str, synthesis: str, proof_path: str, article_path: str) -> str:
        """Phase 4: Write the article"""
        print("\n✍️  Phase 4: Writing article...")
        
        prompt = f"""Write a comprehensive Dakota Learning Center article.

Topic: {topic}

CRITICAL REQUIREMENTS:
- Minimum {settings.MIN_WORD_COUNT} words (currently set to {settings.MIN_WORD_COUNT})
- Minimum {settings.MIN_SOURCES} inline citations with full URLs
- Follow the EXACT template in your instructions
- Include all required sections: {', '.join(REQUIRED_SECTIONS)}
- Exclude forbidden sections: {', '.join(FORBIDDEN_SECTIONS)}

Research synthesis:
{synthesis}

Evidence package location: {proof_path}

Remember: This must be publication-ready with zero compromises on quality."""

        result = await self.run_assistant_async("content_writer", prompt)
        
        if result["result"]:
            write_text(article_path, result["result"])
        
        return article_path
    
    async def phase5_parallel_enhancement(self, article_path: str, topic: str, run_dir: str) -> Dict[str, Any]:
        """Phase 5: Parallel enhancement (SEO, metrics)"""
        print("\n📊 Phase 5: Running parallel enhancement...")
        
        tasks = []
        
        if settings.ENABLE_SEO:
            seo_prompt = f"""Generate comprehensive SEO metadata for article about: {topic}
            
Include:
- Title tag (60 chars)
- Meta description (160 chars)  
- 10-15 LSI keywords
- 3-5 related article suggestions
- Schema markup recommendations"""
            tasks.append(("seo", self.run_assistant_async("seo_specialist", seo_prompt)))
        
        if settings.ENABLE_METRICS:
            metrics_prompt = f"""Analyze article quality metrics for: {article_path}
            
Check:
- Word count vs minimum ({settings.MIN_WORD_COUNT})
- Source count vs minimum ({settings.MIN_SOURCES})
- Required sections presence
- Readability scores
- Passive voice percentage"""
            tasks.append(("metrics", self.run_assistant_async("metrics_analyzer", metrics_prompt)))
        
        if tasks:
            results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            return {t[0]: r["result"] for t, r in zip(tasks, results) if not isinstance(r, Exception)}
        
        return {}
    
    async def phase6_validation(self, article_path: str, metadata_path: str) -> Dict[str, Any]:
        """Phase 6: Comprehensive validation"""
        print("\n✅ Phase 6: Running comprehensive validation...")
        
        article_content = read_text(article_path) if os.path.exists(article_path) else ""
        
        # Fact checking
        fact_check_prompt = f"""Perform comprehensive fact-checking:

1. Verify article meets ALL requirements:
   - Minimum {settings.MIN_WORD_COUNT} words
   - Minimum {settings.MIN_SOURCES} sources
   - All required sections present
   - No forbidden sections

2. Verify ALL URLs are working (status 200)

3. Check citation quality:
   - Primary sources preferred
   - Sources less than 12 months old
   - Proper attribution

Article:
{article_content[:30000]}

Return APPROVED or REJECTED with specific issues."""

        tasks = [self.run_assistant_async("fact_checker", fact_check_prompt)]
        
        if settings.ENABLE_CLAIM_CHECK:
            claim_prompt = f"""Verify all factual claims in the article.
            Check for:
            - Unsupported statements
            - Accuracy of data
            - Logical consistency
            
Article: {article_path}"""
            tasks.append(self.run_assistant_async("claim_checker", claim_prompt))
        
        results = await asyncio.gather(*tasks)
        
        fact_result = results[0]["result"]
        claim_result = results[1]["result"] if len(results) > 1 else ""
        
        # Parse approval status
        approved = "APPROVED" in fact_result.upper() and (not claim_result or "APPROVED" in claim_result.upper())
        
        return {
            "fact_check": fact_result,
            "claim_check": claim_result,
            "approved": approved,
            "issues": self._extract_issues(fact_result, claim_result)
        }
    
    async def phase65_iteration(self, validation_report: Dict[str, Any], article_path: str, metadata_path: str) -> str:
        """Phase 6.5: Fix identified issues"""
        print("\n🔧 Phase 6.5: Fixing identified issues...")
        
        prompt = f"""Fix ALL identified issues in the article.

Issues to fix:
{chr(10).join(validation_report['issues'])}

Fact check report:
{validation_report['fact_check']}

Claim check report:
{validation_report.get('claim_check', '')}

Article path: {article_path}
Metadata path: {metadata_path}

Make all necessary corrections and ensure the article meets ALL requirements."""

        result = await self.run_assistant_async("iteration_manager", prompt)
        return result["result"]
    
    async def phase7_distribution(self, article_path: str, run_dir: str) -> Dict[str, Any]:
        """Phase 7: Create distribution assets"""
        print("\n📢 Phase 7: Creating distribution assets...")
        
        tasks = []
        
        if settings.ENABLE_SUMMARY:
            summary_prompt = f"""Create executive summary for article at: {article_path}
            
Requirements:
- 250-300 words
- 3-5 key takeaways
- Clear value proposition
- Professional tone"""
            tasks.append(("summary", self.run_assistant_async("summary_writer", summary_prompt)))
        
        if settings.ENABLE_SOCIAL:
            social_prompt = f"""Create social media content for article at: {article_path}
            
Include:
- LinkedIn post (1500 chars)
- Twitter thread (5-7 tweets)
- Email newsletter teaser (150 words)"""
            tasks.append(("social", self.run_assistant_async("social_promoter", social_prompt)))
        
        if tasks:
            results = await asyncio.gather(*[t[1] for t in tasks])
            
            # Save outputs
            outputs = {}
            for (name, _), result in zip(tasks, results):
                if result["result"]:
                    output_path = os.path.join(run_dir, f"{name}.md")
                    write_text(output_path, result["result"])
                    outputs[name] = output_path
            
            return outputs
        
        return {}
    
    async def run_pipeline(self, topic: str) -> Dict[str, Any]:
        """Run the complete pipeline"""
        start_time = time.time()
        
        # Setup
        run_dir, slug = run_dir_for_topic(settings.RUNS_DIR, topic)
        article_path = os.path.join(run_dir, f"{slug}-article.md")
        metadata_path = os.path.join(run_dir, f"{slug}-metadata.json")
        
        try:
            # Initialize assistants if not done
            if not self.manager.assistants:
                await self.initialize_assistants()
            
            # Phase 2: Parallel Research
            research = await self.phase2_parallel_research(topic)
            
            # Phase 2.5: Evidence Package
            proof_path = await self.phase25_evidence_packaging(research, run_dir)
            
            # Phase 3: Synthesis
            synthesis = await self.phase3_synthesis(research)
            
            # Phase 4: Content Creation
            await self.phase4_content_creation(topic, synthesis, proof_path, article_path)
            
            # Phase 5: Parallel Enhancement
            enhancements = await self.phase5_parallel_enhancement(article_path, topic, run_dir)
            
            # Save metadata
            if "seo" in enhancements:
                write_text(metadata_path, json.dumps({"seo": enhancements["seo"]}, indent=2))
            
            # Phase 6: Validation with iteration
            iteration_count = 0
            validation = await self.phase6_validation(article_path, metadata_path)
            
            while not validation["approved"] and iteration_count < settings.MAX_ITERATIONS:
                iteration_count += 1
                print(f"\n❌ Article rejected. Iteration {iteration_count}/{settings.MAX_ITERATIONS}")
                print(f"Issues: {', '.join(validation['issues'][:3])}")
                
                await self.phase65_iteration(validation, article_path, metadata_path)
                validation = await self.phase6_validation(article_path, metadata_path)
            
            if not validation["approved"]:
                return {
                    "status": "FAILED",
                    "reason": "Failed validation after maximum iterations",
                    "issues": validation["issues"],
                    "run_dir": run_dir
                }
            
            print("\n✅ Article APPROVED!")
            
            # Phase 7: Distribution
            distribution = await self.phase7_distribution(article_path, run_dir)
            
            # Generate quality report
            quality_report = self._generate_quality_report(
                topic, article_path, validation, enhancements, iteration_count
            )
            report_path = os.path.join(run_dir, "quality_report.md")
            write_text(report_path, quality_report)
            
            elapsed = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "topic": topic,
                "run_dir": run_dir,
                "article_path": article_path,
                "metadata_path": metadata_path,
                "proof_path": proof_path,
                "distribution": distribution,
                "quality_report": report_path,
                "iterations": iteration_count,
                "elapsed_time": f"{elapsed:.1f} seconds",
                "validation": validation
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "run_dir": run_dir
            }
        finally:
            # Cleanup assistants
            self.manager.cleanup_all()
    
    def _extract_issues(self, fact_check: str, claim_check: str) -> List[str]:
        """Extract specific issues from validation reports"""
        issues = []
        
        # Parse fact check for issues
        if "word count" in fact_check.lower() and "minimum" in fact_check.lower():
            issues.append("Article does not meet minimum word count")
        
        if "sources" in fact_check.lower() and ("insufficient" in fact_check.lower() or "not enough" in fact_check.lower()):
            issues.append("Insufficient number of sources")
        
        if "broken" in fact_check.lower() and "url" in fact_check.lower():
            issues.append("Contains broken URLs")
        
        # Add more parsing logic as needed
        
        return issues
    
    def _generate_quality_report(self, topic: str, article_path: str, validation: Dict[str, Any], 
                                enhancements: Dict[str, Any], iterations: int) -> str:
        """Generate comprehensive quality report"""
        article_content = read_text(article_path)
        word_count = len(article_content.split())
        
        report = f"""# Quality Report: {topic}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics Summary
- **Word Count**: {word_count} (minimum: {settings.MIN_WORD_COUNT})
- **Iterations Required**: {iterations}
- **Final Status**: {"✅ APPROVED" if validation['approved'] else "❌ REJECTED"}

## Validation Results

### Fact Check
{validation['fact_check'][:1000]}...

### Claim Check
{validation.get('claim_check', 'Not performed')[:1000]}...

## Enhancement Results

### SEO Analysis
{enhancements.get('seo', 'Not performed')[:500]}...

### Quality Metrics
{enhancements.get('metrics', 'Not performed')[:500]}...

## Compliance Checklist
- [{"✅" if word_count >= settings.MIN_WORD_COUNT else "❌"}] Minimum word count ({settings.MIN_WORD_COUNT})
- [{"✅" if validation['approved'] else "❌"}] All sources verified
- [{"✅" if validation['approved'] else "❌"}] Required sections present
- [{"✅" if validation['approved'] else "❌"}] No forbidden sections
- [{"✅" if iterations == 0 else "⚠️"}] First-pass approval (no iterations needed)

## File Outputs
- Article: {article_path}
- Quality Report: {article_path.replace('-article.md', '-quality_report.md')}
"""
        
        return report


async def main():
    """Example usage"""
    orchestrator = AsyncOrchestrator()
    
    topic = "The Role of Alternative Investments in Modern Portfolio Theory"
    
    print(f"🚀 Starting article generation for: {topic}\n")
    results = await orchestrator.run_pipeline(topic)
    
    print(f"\n📊 Pipeline Results:")
    print(f"Status: {results['status']}")
    if results['status'] == 'SUCCESS':
        print(f"Article: {results['article_path']}")
        print(f"Quality Report: {results['quality_report']}")
        print(f"Time: {results['elapsed_time']}")
    else:
        print(f"Error: {results.get('error', 'Unknown error')}")
        print(f"Issues: {results.get('issues', [])}")


if __name__ == "__main__":
    asyncio.run(main())