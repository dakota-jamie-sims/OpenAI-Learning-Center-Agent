"""
Chat Completions Orchestrator
High-performance parallel pipeline using OpenAI Chat Completions API
"""
import asyncio
import os
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import aiofiles
from openai import AsyncOpenAI

from ..agents.chat_agent import ChatAgentManager, ChatAgent, TOOL_DEFINITIONS
from ..config_enhanced import *
from ..utils.files import run_dir_for_topic, write_text, read_text
from ..tools.assistant_tools import AssistantTools
from ..tools.vector_store_handler import VectorStoreHandler, KnowledgeBaseSearchTool
from ..tools.fact_verification import EnhancedFactChecker
from openai import OpenAI


class ChatOrchestrator:
    """Orchestrates article creation using Chat Completions API with parallel execution"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.manager = ChatAgentManager(self.api_key)
        
        # Initialize vector store for knowledge base
        self.sync_client = OpenAI(api_key=self.api_key)
        self.vector_handler = VectorStoreHandler(self.sync_client)
        self.kb_search_tool = None
        
        # Initialize enhanced fact checker
        self.fact_checker = EnhancedFactChecker()
        
        self.tool_handlers = self._setup_tool_handlers()
        self.token_usage = {}
        
    def _setup_tool_handlers(self) -> Dict[str, Any]:
        """Setup tool handlers for function calling"""
        return {
            "web_search": self._handle_web_search,
            "write_file": self._handle_write_file,
            "read_file": self._handle_read_file,
            "verify_urls": self._handle_verify_urls,
            "validate_article": self._handle_validate_article,
            "search_knowledge_base": self._handle_kb_search
        }
    
    async def _handle_web_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Handle web search using external search API"""
        # This function is no longer needed since GPT models have built-in search
        # The web_researcher agent uses GPT's native search capabilities
        # If you need to use external search, integrate with:
        # - Google Custom Search API
        # - Bing Search API  
        # - SerpAPI
        # - Brave Search API
        raise NotImplementedError(
            "Web search is handled by GPT's built-in capabilities. "
            "For external search, please integrate a real search API."
        )
    
    async def _handle_write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Handle file writing asynchronously"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, 'w') as f:
                await f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_read_file(self, path: str) -> Dict[str, Any]:
        """Handle file reading asynchronously"""
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_verify_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Verify URLs asynchronously using real HTTP requests"""
        import aiohttp
        import asyncio
        
        async def check_url(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
            try:
                async with session.head(url, timeout=10, allow_redirects=True) as response:
                    return {
                        "url": url,
                        "status_code": response.status,
                        "accessible": 200 <= response.status < 400
                    }
            except asyncio.TimeoutError:
                return {"url": url, "status_code": 0, "accessible": False, "error": "Timeout"}
            except Exception as e:
                return {"url": url, "status_code": 0, "accessible": False, "error": str(e)}
        
        async with aiohttp.ClientSession() as session:
            tasks = [check_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
        
        return results
    
    async def _handle_validate_article(self, text: str, min_words: int = None, min_sources: int = None) -> Dict[str, Any]:
        """Validate article structure"""
        # Use instance values if not provided
        min_words = min_words or getattr(self, 'min_words', 2000)
        min_sources = min_sources or getattr(self, 'min_sources', 12)
        return AssistantTools.validate_article(text, min_words, min_sources)
    
    async def _handle_kb_search(self, query: str, max_results: int = 6) -> Dict[str, Any]:
        """Handle knowledge base search using vector store"""
        if self.kb_search_tool:
            return await self.kb_search_tool.search(query, max_results)
        else:
            return {"error": "Knowledge base not initialized"}
    
    async def initialize_agents(self):
        """Initialize all agents for the pipeline"""
        print("🚀 Initializing Chat Completion agents...")
        
        # Initialize vector store for knowledge base
        print("📚 Setting up knowledge base vector store...")
        vector_store_id = self.vector_handler.create_or_get_vector_store()
        
        # Upload knowledge base files if vector store is new
        if not os.getenv("VECTOR_STORE_ID"):
            kb_files = self.vector_handler.upload_knowledge_base(
                str(KNOWLEDGE_BASE_DIR),
                max_files=100
            )
            print(f"✅ Uploaded {len(kb_files)} files to vector store")
        
        # Create KB search tool
        self.kb_search_tool = KnowledgeBaseSearchTool(self.vector_handler)
        
        # Add KB search tool definition to our tools
        kb_tool_def = self.kb_search_tool.get_tool_definition()
        
        # Define agent configurations
        agent_configs = [
            # Research agents
            {
                "name": "web_researcher",
                "prompt_file": "dakota-web-researcher.md",
                "tools": [],  # Uses GPT's built-in web search
                "temperature": 0.7
            },
            {
                "name": "kb_researcher", 
                "prompt_file": "dakota-kb-researcher.md",
                "tools": [kb_tool_def],  # Use vector store search instead of file read
                "temperature": 0.5
            },
            {
                "name": "research_synthesizer",
                "prompt_file": "dakota-research-synthesizer.md",
                "temperature": 0.3
            },
            # Content creation
            {
                "name": "content_writer",
                "prompt_file": "dakota-content-writer.md",
                "tools": [TOOL_DEFINITIONS["write_file"]],
                "temperature": 0.8,
                "max_tokens": 4000
            },
            # Validation agents
            {
                "name": "fact_checker",
                "prompt_file": "dakota-fact-checker.md",
                "tools": [
                    TOOL_DEFINITIONS["read_file"],
                    TOOL_DEFINITIONS["verify_urls"],
                    TOOL_DEFINITIONS["validate_article"]
                ],
                "temperature": 0.1
            },
            {
                "name": "claim_checker",
                "prompt_file": "dakota-claim-checker.md",
                "tools": [TOOL_DEFINITIONS["read_file"]],
                "temperature": 0.1
            },
            # Enhancement agents
            {
                "name": "seo_specialist",
                "prompt_file": "dakota-seo-specialist.md",
                "tools": [TOOL_DEFINITIONS["write_file"]],
                "temperature": 0.5
            },
            {
                "name": "metrics_analyzer",
                "prompt_file": "dakota-metrics-analyzer.md",
                "tools": [TOOL_DEFINITIONS["read_file"]],
                "temperature": 0.3
            },
            # Distribution agents
            {
                "name": "summary_writer",
                "prompt_file": "dakota-summary-writer.md",
                "tools": [TOOL_DEFINITIONS["write_file"]],
                "temperature": 0.5
            },
            {
                "name": "social_promoter",
                "prompt_file": "dakota-social-promoter.md",
                "tools": [TOOL_DEFINITIONS["write_file"]],
                "temperature": 0.7
            },
            # Iteration
            {
                "name": "iteration_manager",
                "prompt_file": "dakota-iteration-manager.md",
                "tools": [
                    TOOL_DEFINITIONS["read_file"],
                    TOOL_DEFINITIONS["write_file"]
                ],
                "temperature": 0.3
            },
            # Evidence
            {
                "name": "evidence_packager",
                "prompt_file": "dakota-evidence-packager.md",
                "tools": [TOOL_DEFINITIONS["write_file"]],
                "temperature": 0.1
            }
        ]
        
        # Create all agents
        for config in agent_configs:
            self.manager.create_agent_from_prompt(
                name=config["name"],
                prompt_file=config["prompt_file"],
                model=DEFAULT_MODELS.get(config["name"].replace("_", ""), "gpt-4-turbo-preview"),
                temperature=config.get("temperature", 0.7),
                tools=config.get("tools", []),
                tool_handlers=self.tool_handlers
            )
        
        print("✅ All agents initialized")
    
    async def phase2_parallel_research(self, topic: str) -> Dict[str, Any]:
        """Phase 2: Parallel research"""
        print("\n🔍 Phase 2: Parallel research...")
        
        # Create prompts for parallel execution
        agent_prompts = [
            ("web_researcher", f"""Research topic: {topic}

Budget directives:
- Maximum {MAX_WEB_CALLS} web searches
- Focus on: {', '.join(CITATION_STANDARDS['preferred_domains'][:5])}
- Avoid: {', '.join(CITATION_STANDARDS['banned_domains'])}
- Sources must be less than {CITATION_STANDARDS['max_source_age_months']} months old

Deliver:
- 5-7 key findings with full citations
- Focus on institutional investor perspective
- Data-driven insights only"""),
            
            ("kb_researcher", f"""Research topic: {topic}

Search our Dakota knowledge base for:
- Investment philosophy connections
- Similar topics and precedents  
- Dakota's perspective and approach
- Relevant frameworks and methodologies

Use the search_knowledge_base function to find relevant content.
Make multiple searches with different angles if needed.
Deliver a structured brief with specific references to Dakota materials.""")
        ]
        
        # Run both researchers in parallel
        results = await self.manager.run_agents_parallel(agent_prompts)
        
        # Track token usage
        for i, (agent_name, _) in enumerate(agent_prompts):
            if "usage" in results[i]:
                self.token_usage[agent_name] = results[i]["usage"]
        
        return {
            "web": results[0]["content"] if results[0]["content"] else "No web research results",
            "kb": results[1]["content"] if results[1]["content"] else "No KB research results"
        }
    
    async def phase3_synthesis(self, research: Dict[str, Any]) -> str:
        """Phase 3: Synthesize research"""
        print("\n🔗 Phase 3: Synthesizing research...")
        
        prompt = f"""Synthesize the following research into a comprehensive brief:

[WEB RESEARCH]
{research['web']}

[KNOWLEDGE BASE RESEARCH]
{research['kb']}

Requirements:
- Combine insights cohesively
- Maintain all source attributions
- Highlight Dakota-relevant angles
- Focus on actionable insights
- Maximum {OUTPUT_TOKEN_CAPS['synth_max_tokens']} tokens"""

        result = await self.manager.run_agent("research_synthesizer", prompt)
        
        if "usage" in result:
            self.token_usage["research_synthesizer"] = result["usage"]
            
        return result["content"] or "Synthesis failed"
    
    async def phase4_content_creation(self, topic: str, synthesis: str, proof_path: str, article_path: str) -> str:
        """Phase 4: Write the article"""
        print("\n✍️  Phase 4: Writing article...")
        
        prompt = f"""Write a comprehensive Dakota Learning Center article.

Topic: {topic}
Output file: {article_path}

CRITICAL REQUIREMENTS:
- Minimum {self.min_words} words (absolutely non-negotiable)
- Minimum {self.min_sources} inline citations with exact URLs
- Follow the EXACT template structure from your instructions
- Include ALL required sections: {', '.join(REQUIRED_SECTIONS)}
- NEVER include forbidden sections: {', '.join(FORBIDDEN_SECTIONS)}
- Professional yet conversational tone
- Data-driven with actionable insights

RESEARCH SYNTHESIS:
{synthesis}

Evidence package: {proof_path if os.path.exists(proof_path) else 'Not available'}

Write the complete article now. Use the write_file function to save it."""

        result = await self.manager.run_agent("content_writer", prompt)
        
        if "usage" in result:
            self.token_usage["content_writer"] = result["usage"]
            
        return article_path
    
    async def phase5_parallel_enhancement(self, article_path: str, topic: str, run_dir: str) -> Dict[str, Any]:
        """Phase 5: Parallel enhancement"""
        print("\n📊 Phase 5: Parallel enhancement...")
        
        agent_prompts = []
        
        if ENABLE_SEO:
            agent_prompts.append(("seo_specialist", f"""Generate comprehensive SEO metadata for: {topic}

Requirements:
- Title tag (max 60 characters)
- Meta description (max 160 characters)
- 15 LSI keywords
- 5 related article suggestions
- Schema markup recommendations

Save to: {os.path.join(run_dir, 'seo-metadata.json')}"""))
        
        if ENABLE_METRICS:
            agent_prompts.append(("metrics_analyzer", f"""Analyze quality metrics for article at: {article_path}

Check:
- Word count (minimum {self.min_words})
- Source count (minimum {self.min_sources})
- Required sections presence
- Readability scores (Flesch-Kincaid)
- Passive voice percentage
- Average sentence length"""))
        
        if agent_prompts:
            results = await self.manager.run_agents_parallel(agent_prompts)
            
            output = {}
            for i, (agent_name, _) in enumerate(agent_prompts):
                if results[i]["content"]:
                    output[agent_name] = results[i]["content"]
                if "usage" in results[i]:
                    self.token_usage[agent_name] = results[i]["usage"]
            
            return output
        
        return {}
    
    async def phase6_validation(self, article_path: str) -> Dict[str, Any]:
        """Phase 6: Comprehensive validation with enhanced fact-checking"""
        print("\n✅ Phase 6: Comprehensive validation...")
        
        # Read article for fact verification
        article_content = read_text(article_path) if os.path.exists(article_path) else ""
        
        # Run enhanced fact verification first
        print("🔍 Running enhanced fact verification...")
        fact_verification = await self.fact_checker.verify_article(article_content)
        
        # If fact verification fails, no need to run other checks
        if not fact_verification["approved"]:
            return {
                "approved": False,
                "fact_check": f"REJECTED - Credibility score: {fact_verification['credibility_score']:.2f}",
                "claim_check": "Skipped due to fact verification failure",
                "issues": fact_verification["issues"],
                "fix_instructions": fact_verification.get("fix_instructions", []),
                "fact_verification_report": fact_verification
            }
        
        # Parallel validation
        agent_prompts = [
            ("fact_checker", f"""Perform comprehensive validation:

1. Read article at: {article_path}
2. Validate structure using validate_article function
3. Extract ALL URLs and verify using verify_urls function
4. Check:
   - Minimum {self.min_words} words
   - Minimum {self.min_sources} sources
   - All required sections present
   - No forbidden sections
   - All URLs return status 200

Return: APPROVED or REJECTED with specific issues listed.""")
        ]
        
        if ENABLE_CLAIM_CHECK:
            agent_prompts.append(("claim_checker", f"""Verify all factual claims in article at: {article_path}

Check:
- Every statistic has a source
- Claims are logically consistent
- No unsupported statements
- Data is current (within {CITATION_STANDARDS['max_source_age_months']} months)

Return: APPROVED or REJECTED with issues."""))
        
        results = await self.manager.run_agents_parallel(agent_prompts)
        
        # Process results
        fact_check = results[0]["content"] or "Fact check failed"
        claim_check = results[1]["content"] if len(results) > 1 else ""
        
        # Track usage
        for i, (agent_name, _) in enumerate(agent_prompts):
            if "usage" in results[i]:
                self.token_usage[agent_name] = results[i]["usage"]
        
        # Determine approval
        approved = ("APPROVED" in fact_check.upper() and 
                   (not claim_check or "APPROVED" in claim_check.upper()))
        
        return {
            "approved": approved,
            "fact_check": fact_check,
            "claim_check": claim_check,
            "issues": self._extract_issues(fact_check, claim_check)
        }
    
    async def phase65_iteration(self, validation: Dict[str, Any], article_path: str) -> str:
        """Phase 6.5: Fix issues"""
        print("\n🔧 Fixing issues...")
        
        prompt = f"""Fix ALL issues in the article at: {article_path}

Issues to fix:
{chr(10).join('- ' + issue for issue in validation['issues'])}

Validation reports:
[FACT CHECK]
{validation['fact_check']}

[CLAIM CHECK]
{validation.get('claim_check', '')}

Requirements:
- Read the current article
- Fix ALL identified issues
- Maintain or increase word count
- Write the corrected article back to the same file
- Ensure it will pass validation"""

        result = await self.manager.run_agent("iteration_manager", prompt)
        
        if "usage" in result:
            self.token_usage["iteration_manager"] = result["usage"]
            
        return result["content"] or "Iteration failed"
    
    async def phase7_distribution(self, article_path: str, run_dir: str) -> Dict[str, Any]:
        """Phase 7: Create distribution assets"""
        print("\n📢 Phase 7: Creating distribution assets...")
        
        agent_prompts = []
        
        if ENABLE_SUMMARY:
            agent_prompts.append(("summary_writer", 
                f"""Create executive summary for article at: {article_path}
                
Requirements:
- 250-300 words
- 3-5 bullet point key takeaways
- Clear value proposition
- Save to: {os.path.join(run_dir, 'executive-summary.md')}"""))
        
        if ENABLE_SOCIAL:
            agent_prompts.append(("social_promoter",
                f"""Create social media content for article at: {article_path}
                
Include:
- LinkedIn post (1500 characters)
- Twitter/X thread (5-7 tweets) 
- Email newsletter teaser (150 words)
- Save to: {os.path.join(run_dir, 'social-media.md')}"""))
        
        if agent_prompts:
            results = await self.manager.run_agents_parallel(agent_prompts)
            
            output = {}
            for i, (agent_name, _) in enumerate(agent_prompts):
                if results[i]["content"]:
                    output[agent_name] = os.path.join(run_dir, f"{agent_name.replace('_', '-')}.md")
                if "usage" in results[i]:
                    self.token_usage[agent_name] = results[i]["usage"]
            
            return output
        
        return {}
    
    async def run_pipeline(self, topic: str, min_words: int = None, min_sources: int = None) -> Dict[str, Any]:
        """Run the complete pipeline with configurable requirements"""
        start_time = time.time()
        
        # Use provided values or defaults
        self.min_words = min_words or MIN_WORD_COUNT
        self.min_sources = min_sources or MIN_SOURCES
        
        # Setup
        run_dir, slug = run_dir_for_topic(RUNS_DIR, topic)
        article_path = os.path.join(run_dir, f"{slug}-article.md")
        proof_path = os.path.join(run_dir, "evidence-pack.json")
        
        try:
            # Initialize agents
            if not self.manager.agents:
                await self.initialize_agents()
            
            # Reset token usage tracking
            self.token_usage = {}
            
            # Phase 2: Parallel Research
            research = await self.phase2_parallel_research(topic)
            
            # Phase 2.5: Evidence Package (optional)
            if ENABLE_EVIDENCE:
                print("\n📦 Phase 2.5: Creating evidence package...")
                evidence_prompt = f"""Create JSON evidence package from research:
                
[WEB RESEARCH]
{research['web'][:15000]}

[KB RESEARCH]
{research['kb'][:10000]}

Requirements:
- Top 25 sources with title, URL, relevance score
- Key quotes with attribution
- Confidence levels for claims
- Save to: {proof_path}"""
                
                evidence_result = await self.manager.run_agent("evidence_packager", evidence_prompt)
                if "usage" in evidence_result:
                    self.token_usage["evidence_packager"] = evidence_result["usage"]
            
            # Phase 3: Synthesis
            synthesis = await self.phase3_synthesis(research)
            
            # Phase 4: Content Creation
            await self.phase4_content_creation(topic, synthesis, proof_path, article_path)
            
            # Phase 5: Parallel Enhancement
            enhancements = await self.phase5_parallel_enhancement(article_path, topic, run_dir)
            
            # Phase 6: Validation Loop
            iteration_count = 0
            validation = await self.phase6_validation(article_path)
            
            while not validation["approved"] and iteration_count < MAX_ITERATIONS:
                iteration_count += 1
                print(f"\n❌ Validation failed. Iteration {iteration_count}/{MAX_ITERATIONS}")
                print(f"Issues: {', '.join(validation['issues'][:3])}")
                
                await self.phase65_iteration(validation, article_path)
                validation = await self.phase6_validation(article_path)
            
            if not validation["approved"]:
                return {
                    "status": "FAILED",
                    "reason": "Failed validation after maximum iterations",
                    "issues": validation["issues"],
                    "run_dir": run_dir,
                    "token_usage": self.token_usage
                }
            
            print("\n✅ Article APPROVED!")
            
            # Phase 7: Distribution
            distribution = await self.phase7_distribution(article_path, run_dir)
            
            # Generate quality report
            quality_report = self._generate_quality_report(
                topic, article_path, validation, enhancements, 
                iteration_count, self.token_usage
            )
            report_path = os.path.join(run_dir, "quality-report.md")
            write_text(report_path, quality_report)
            
            # Generate fact-check report
            if validation.get("fact_verification_report"):
                fact_report = self._generate_fact_check_report(validation["fact_verification_report"])
                fact_report_path = os.path.join(run_dir, "fact-check-report.md")
                write_text(fact_report_path, fact_report)
            
            elapsed = time.time() - start_time
            
            return {
                "status": "SUCCESS",
                "topic": topic,
                "run_dir": run_dir,
                "article_path": article_path,
                "proof_path": proof_path if ENABLE_EVIDENCE else None,
                "distribution": distribution,
                "quality_report": report_path,
                "iterations": iteration_count,
                "elapsed_time": f"{elapsed:.1f} seconds",
                "token_usage": self.token_usage,
                "total_tokens": sum(u.get("total_tokens", 0) for u in self.token_usage.values())
            }
            
        except Exception as e:
            import traceback
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "run_dir": run_dir,
                "token_usage": self.token_usage
            }
    
    def _extract_issues(self, fact_check: str, claim_check: str) -> List[str]:
        """Extract specific issues from validation reports"""
        issues = []
        
        # Common issue patterns
        patterns = {
            "word count": ["below minimum", "insufficient words", "too short"],
            "sources": ["insufficient sources", "not enough citations", "missing sources"],
            "urls": ["broken url", "404", "inaccessible"],
            "sections": ["missing required section", "missing section"],
            "forbidden": ["contains forbidden section", "includes prohibited"]
        }
        
        combined_text = (fact_check + " " + claim_check).lower()
        
        for issue_type, keywords in patterns.items():
            if any(keyword in combined_text for keyword in keywords):
                if issue_type == "word count":
                    issues.append("Article does not meet minimum word count")
                elif issue_type == "sources":
                    issues.append("Insufficient number of sources")
                elif issue_type == "urls":
                    issues.append("Contains broken or inaccessible URLs")
                elif issue_type == "sections":
                    issues.append("Missing required sections")
                elif issue_type == "forbidden":
                    issues.append("Contains forbidden sections")
        
        return issues if issues else ["Unspecified validation issues"]
    
    def _generate_quality_report(self, topic: str, article_path: str, 
                                validation: Dict[str, Any], enhancements: Dict[str, Any],
                                iterations: int, token_usage: Dict[str, Any]) -> str:
        """Generate comprehensive quality report"""
        
        # Calculate token costs (GPT-4 pricing)
        total_tokens = sum(u.get("total_tokens", 0) for u in token_usage.values())
        prompt_tokens = sum(u.get("prompt_tokens", 0) for u in token_usage.values())
        completion_tokens = sum(u.get("completion_tokens", 0) for u in token_usage.values())
        
        # Approximate costs
        prompt_cost = (prompt_tokens / 1000) * 0.03  # $0.03 per 1K prompt tokens
        completion_cost = (completion_tokens / 1000) * 0.06  # $0.06 per 1K completion tokens
        total_cost = prompt_cost + completion_cost
        
        report = f"""# Quality Report: {topic}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Status**: {"✅ APPROVED" if validation['approved'] else "❌ REJECTED"}
- **Iterations Required**: {iterations}
- **Total Tokens Used**: {total_tokens:,}
- **Estimated Cost**: ${total_cost:.2f}

## Token Usage by Agent
"""
        
        for agent, usage in token_usage.items():
            report += f"- **{agent}**: {usage.get('total_tokens', 0):,} tokens\n"
        
        report += f"""
## Validation Results

### Fact Check Summary
{validation['fact_check'][:500]}...

### Claim Check Summary  
{validation.get('claim_check', 'Not performed')[:500]}...

## Enhancement Results

### SEO Analysis
{enhancements.get('seo_specialist', 'Not performed')[:300]}...

### Quality Metrics
{enhancements.get('metrics_analyzer', 'Not performed')[:300]}...

## Performance Metrics
- **Prompt Tokens**: {prompt_tokens:,}
- **Completion Tokens**: {completion_tokens:,}
- **Prompt Cost**: ${prompt_cost:.3f}
- **Completion Cost**: ${completion_cost:.3f}
- **Total Cost**: ${total_cost:.3f}

## Files Generated
- Article: `{article_path}`
- Quality Report: `{article_path.replace('-article.md', '/quality-report.md')}`
"""
        
        return report
    
    def _generate_fact_check_report(self, fact_verification: Dict[str, Any]) -> str:
        """Generate detailed fact-check report"""
        report = f"""# Fact Verification Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Overall Credibility Score**: {fact_verification['credibility_score']:.2%}
- **Fact Accuracy Rate**: {fact_verification['fact_accuracy']:.2%}
- **Total Facts Checked**: {fact_verification['total_facts_checked']}
- **Verified Facts**: {fact_verification['verified_facts']}
- **Source Quality Score**: {fact_verification['source_quality']:.1f}/10

## Source Analysis
"""
        
        if "detailed_results" in fact_verification:
            source_analysis = fact_verification["detailed_results"]["source_analysis"]
            report += f"""
- **Total Sources**: {source_analysis['total_sources']}
- **Unique Domains**: {source_analysis['unique_domains']}
- **High-Credibility Sources**: {source_analysis['high_credibility_sources']}
- **Average Credibility**: {source_analysis['average_credibility']:.1f}/10

### Domain Distribution
"""
            for domain, count in source_analysis.get("domain_distribution", {}).items():
                report += f"- {domain}: {count} citations\n"
        
        # Add verification details
        if "detailed_results" in fact_verification:
            report += "\n## Fact Verification Details\n"
            for i, result in enumerate(fact_verification["detailed_results"]["verification_details"][:10], 1):
                fact = result["fact"]
                report += f"""
### Fact {i}
- **Claim**: {fact['claim']}
- **Type**: {fact['type']}
- **Verified**: {'✅' if result['verified'] else '❌'}
- **Confidence**: {result['confidence']:.2%}
- **Has Citation**: {'Yes' if fact['has_citation'] else 'No'}
"""
                if result["issues"]:
                    report += f"- **Issues**: {', '.join(result['issues'])}\n"
        
        # Add issues if any
        if fact_verification.get("issues"):
            report += "\n## Issues Requiring Attention\n"
            for issue in fact_verification["issues"]:
                report += f"- {issue}\n"
        
        return report


async def main():
    """Example usage"""
    orchestrator = ChatOrchestrator()
    
    topic = "The Evolution of Passive Investing and Its Impact on Market Efficiency"
    
    print(f"🚀 Starting article generation using Chat Completions API")
    print(f"📝 Topic: {topic}\n")
    
    results = await orchestrator.run_pipeline(topic)
    
    print(f"\n📊 Results:")
    print(f"Status: {results['status']}")
    if results['status'] == 'SUCCESS':
        print(f"Article: {results['article_path']}")
        print(f"Total tokens: {results['total_tokens']:,}")
        print(f"Time: {results['elapsed_time']}")
    else:
        print(f"Error: {results.get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())