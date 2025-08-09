import asyncio, os, re
from agents import Runner
from ..config import RUNS_DIR, OUTPUT_TOKEN_CAPS, MAX_WEB_CALLS, MAX_FILE_CALLS, ENABLE_EVIDENCE, ENABLE_CLAIM_CHECK, ENABLE_SEO, ENABLE_METRICS, ENABLE_SUMMARY, ENABLE_SOCIAL, FACT_CHECK_MANDATORY, MAX_ITERATIONS, MIN_WORD_COUNT, MIN_SOURCES
from ..utils.files import run_dir_for_topic, write_text, read_text
from ..agents import web_researcher, kb_researcher, research_synthesizer, content_writer, seo_specialist, fact_checker, summary_writer, social_promoter, iteration_manager, metrics_analyzer, evidence_packager, claim_checker
from ..tools.function_tools import write_file, read_file, list_directory, validate_article, verify_urls

URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)

class Pipeline:
    def __init__(self, topic: str):
        self.topic = topic
        self.run_dir, self.slug = run_dir_for_topic(RUNS_DIR, topic)
        self.prefix = self.slug
        self.article_path = os.path.join(self.run_dir, f"{self.prefix}-article.md")
        self.summary_path = os.path.join(self.run_dir, f"{self.prefix}-summary.md")
        self.social_path = os.path.join(self.run_dir, f"{self.prefix}-social.md")
        self.metadata_path = os.path.join(self.run_dir, f"{self.prefix}-metadata.md")
        self.proof_path = os.path.join(self.run_dir, "proof_pack.json")

    async def phase2_parallel_research(self) -> dict:
        caps = OUTPUT_TOKEN_CAPS
        w = web_researcher.create()
        k = kb_researcher.create()
        web_prompt = f"""Research topic: {self.topic}

Budget directives:
- Use at most {MAX_WEB_CALLS} web-search tool calls. De-duplicate queries and reuse results.
- Keep the final brief concise but complete (<= {caps['synth_max_tokens']} tokens).

Deliver:
- Structured research brief with citations to sources actually opened.
- 3–7 most important findings (bullets)."""
        kb_prompt = f"""Use File Search to gather our internal context for: {self.topic}.

Budget directives:
- Use at most {MAX_FILE_CALLS} file-search calls; prioritize relevant chunks.
- Keep your final brief compact (<= {caps['synth_max_tokens']} tokens).

Deliver:
- KB brief citing doc titles/filenames where possible.
- 3–5 key takeaways aligned to Dakota style."""
        t1 = Runner.run(w, web_prompt)
        t2 = Runner.run(k, kb_prompt)
        web_res, kb_res = await asyncio.gather(t1, t2)
        return {"web": str(web_res.final_output), "kb": str(kb_res.final_output)}

    async def phase25_evidence_packager(self, briefs: dict) -> str:
        if not ENABLE_EVIDENCE:
            return ""
        agent = evidence_packager.create()
        agent.tools.extend([write_file])
        prompt = f"""Create a compact JSON 'proof pack' and save to: {self.proof_path}

Rules:
- Rank up to 25 top sources with title/url/why.
- Include short verbatim quotes with url.
- Include atomic claims with url and confidence (high|med|low).
- JSON only; no prose.

Inputs:
[WEB]
{briefs['web'][:28000]}

[KB]
{briefs['kb'][:18000]}
"""
        res = await Runner.run(agent, prompt)
        out = str(res.final_output or "").strip()
        if out.startswith("{"):
            write_text(self.proof_path, out)
        return self.proof_path

    async def phase3_synthesis(self, briefs: dict) -> str:
        caps = OUTPUT_TOKEN_CAPS
        agent = research_synthesizer.create()
        prompt = f"""Synthesize the following research into a unified brief for writing.
Budget directive: keep the synthesis <= {caps['synth_max_tokens']} tokens.

[WEB RESEARCH]
{briefs['web']}

[KB RESEARCH]
{briefs['kb']}
"""
        res = await Runner.run(agent, prompt)
        return str(res.final_output)

    async def phase4_content(self, synthesis: str) -> str:
        caps = OUTPUT_TOKEN_CAPS
        agent = content_writer.create()
        agent.tools.extend([write_file])
        prompt = f"""Write a comprehensive Dakota Learning Center article following your MANDATORY template.

Topic: {self.topic}
Output file: {self.article_path}

CRITICAL REQUIREMENTS:
- Minimum 1,750 words (non-negotiable)
- Follow the exact template structure in your instructions
- Include 10+ inline citations with full URLs
- Use the synthesized research and proof pack below

[SYNTHESIZED RESEARCH]
{synthesis}

[PROOF PACK PATH]
{self.proof_path if os.path.exists(self.proof_path) else "(none)"}

Remember: The article MUST be at least 1,750 words with proper YAML frontmatter including word_count and reading_time fields."""
        res = await Runner.run(agent, prompt)
        content = str(res.final_output or "").strip()
        if content:
            write_text(self.article_path, content)
        return self.article_path

    async def phase5_parallel_analysis(self) -> dict:
        caps = OUTPUT_TOKEN_CAPS
        results = {}
        tasks = []

        if ENABLE_METRICS:
            m = metrics_analyzer.create()
            prompt_m = f"""Analyze objective quality metrics for:
{self.article_path}
Budget: <= {caps['metrics_max_tokens']} tokens. Return counts and issues only."""
            tasks.append(("metrics", Runner.run(m, prompt_m)))

        if ENABLE_SEO:
            s = seo_specialist.create()
            s.tools.extend([write_file])
            prompt_s = f"""Generate SEO metadata and related links for topic: {self.topic}.
Budget: <= {caps['seo_max_tokens']} tokens.
Use the Write tool to save to: {self.metadata_path}
Then include a short summary of what you wrote in your final answer."""
            tasks.append(("seo", Runner.run(s, prompt_s)))

        if tasks:
            done = await asyncio.gather(*[t for _, t in tasks])
            for (name, _), res in zip(tasks, done):
                results[name] = str(res.final_output)
        return results

    async def phase6_validation(self) -> dict:
        caps = OUTPUT_TOKEN_CAPS
        # Fact-Checker
        fc = fact_checker.create()
        fc.tools.extend([read_file, validate_article, verify_urls])
        article_text = read_text(self.article_path) if os.path.exists(self.article_path) else ""
        urls = list(set(URL_RE.findall(article_text)))
        meta_text = read_text(self.metadata_path) if os.path.exists(self.metadata_path) else ""

        prompt_fc = f"""You are the fact-checker. Perform two steps (<= {caps['factcheck_max_tokens']} tokens):

STEP A — TEMPLATE VALIDATION
- Call validate_article(text=...) on the article content
- Report any structural issues

STEP B — CITATION CHECKS
- Extract every outbound URL from the article and metadata, then call verify_urls(urls=[...])
- For any URL with status <200 or >=400, flag it as broken

Inputs:
[ARTICLE]
{article_text[:50000]}

[METADATA]
{meta_text[:20000]}
"""

        tasks = [Runner.run(fc, prompt_fc)]
        # Claim Checker (optional)
        if ENABLE_CLAIM_CHECK:
            cc = claim_checker.create()
            prompt_cc = f"""Run the claim checker per your prompt. JSON only.
Draft path: {self.article_path}"""
            tasks.append(Runner.run(cc, prompt_cc))

        results = await asyncio.gather(*tasks)
        fc_text = str(results[0].final_output)
        cc_text = str(results[1].final_output) if ENABLE_CLAIM_CHECK and len(results) > 1 else ""

        fc_ok = "✅ APPROVED" in fc_text or "APPROVED" in fc_text.upper()
        cc_ok = ("APPROVE" in cc_text.upper()) if cc_text else True
        
        # Extract specific issues if rejected
        issues = []
        if "❌ REJECTED" in fc_text or "REJECTED" in fc_text.upper():
            if "Issues Found:" in fc_text:
                issues_section = fc_text.split("Issues Found:")[1].split("\n\n")[0]
                issues = [line.strip() for line in issues_section.split("\n") if line.strip()]
        
        decision = "APPROVED" if (fc_ok and cc_ok) else "REJECTED"
        
        return {
            "factcheck": fc_text, 
            "claimcheck": cc_text, 
            "decision": decision,
            "issues": issues,
            "fc_approved": fc_ok,
            "cc_approved": cc_ok
        }

    async def phase65_iteration(self, report: dict) -> str:
        agent = iteration_manager.create()
        agent.tools.extend([read_file, write_file])
        prompt = f"""The QC gate requested revisions. Here are the reports:

[FACT-CHECK]
{report.get('factcheck','')}

[CLAIM-CHECK]
{report.get('claimcheck','')}

Read the current files, fix all issues, and overwrite them in place using Write tool:
- Article: {self.article_path}
- Metadata: {self.metadata_path}
Then stop.
"""
        res = await Runner.run(agent, prompt)
        return str(res.final_output)

    async def phase7_distribution(self) -> dict:
        caps = OUTPUT_TOKEN_CAPS
        results = {}
        tasks = []

        if ENABLE_SUMMARY:
            sw = summary_writer.create()
            sw.tools.extend([write_file])
            tasks.append(("summary", Runner.run(sw, f"Create a concise executive summary (<= {caps['summary_max_tokens']} tokens). Write to: {self.summary_path}")))

        if ENABLE_SOCIAL:
            sp = social_promoter.create()
            sp.tools.extend([write_file])
            tasks.append(("social", Runner.run(sp, f"Create a social post set (<= {caps['social_max_tokens']} tokens). Write to: {self.social_path}")))

        if tasks:
            done = await asyncio.gather(*[t for _, t in tasks])
            for (name, _), res in zip(tasks, done):
                results[name] = str(res.final_output)
        return results

    async def run_all(self) -> dict:
        # Phase 2: Parallel Research
        print("\n🔍 Phase 2: Starting parallel research...")
        briefs = await self.phase2_parallel_research()
        
        # Phase 2.5: Evidence Packaging
        if ENABLE_EVIDENCE:
            print("\n📦 Phase 2.5: Creating evidence package...")
            await self.phase25_evidence_packager(briefs)
        
        # Phase 3: Synthesis
        print("\n🔗 Phase 3: Synthesizing research...")
        synthesis = await self.phase3_synthesis(briefs)
        
        # Phase 4: Content Creation
        print("\n✍️  Phase 4: Writing article...")
        await self.phase4_content(synthesis)
        
        # Phase 5: Parallel Enhancement
        print("\n📊 Phase 5: Running parallel analysis...")
        _ = await self.phase5_parallel_analysis()
        
        # Phase 6: MANDATORY Fact-Checking
        print("\n✅ Phase 6: MANDATORY fact-checking...")
        qc = await self.phase6_validation()
        
        # Handle rejections with iteration
        iteration_count = 0
        while qc["decision"] == "REJECTED" and iteration_count < MAX_ITERATIONS:
            iteration_count += 1
            print(f"\n❌ Article REJECTED. Starting iteration {iteration_count}/{MAX_ITERATIONS}...")
            print(f"Issues found: {', '.join(qc['issues'][:3])}...")
            
            # Phase 6.5: Fix issues
            await self.phase65_iteration(qc)
            
            # Re-validate
            print(f"\n🔄 Re-validating after iteration {iteration_count}...")
            qc = await self.phase6_validation()
        
        # Final check - if still rejected after max iterations, stop
        if qc["decision"] == "REJECTED":
            print(f"\n❌ Article still REJECTED after {MAX_ITERATIONS} iterations. Stopping.")
            return {
                "run_dir": self.run_dir,
                "status": "FAILED",
                "reason": "Failed fact-checking after maximum iterations",
                "issues": qc["issues"],
                "validation": qc
            }
        
        print("\n✅ Article APPROVED! Proceeding to distribution...")
        
        # Phase 7: Distribution (only if approved)
        print("\n📢 Phase 7: Creating distribution content...")
        dist = await self.phase7_distribution()

        return {
            "run_dir": self.run_dir,
            "article": self.article_path,
            "summary": self.summary_path,
            "social": self.social_path,
            "metadata": self.metadata_path,
            "proof_pack": self.proof_path if os.path.exists(self.proof_path) else "",
            "qc": qc,
            "distribution": dist,
        }
