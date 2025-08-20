"""
Specialized agents for content writing and editing
"""
from typing import Dict, Any, List, Tuple, Optional
import re
import json
from datetime import datetime

from learning_center_agent.agents.multi_agent_base import (
    AgentMessage,
    AgentStatus,
    BaseAgent,
)
from learning_center_agent.config import (
    DEFAULT_MODELS,
    MIN_WORD_COUNT,
    REQUIRE_DAKOTA_URLS,
)


class ContentWriterAgent(BaseAgent):
    """Agent specialized in article writing"""
    
    def __init__(self):
        super().__init__(
            agent_id="content_writer_001",
            agent_type="writer",
            team="writing"
        )
        self.capabilities = [
            "write_article",
            "write_section",
            "create_outline",
            "expand_content",
            "rewrite_content"
        ]
        self.model = DEFAULT_MODELS.get("writer", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate writing tasks"""
        valid_tasks = [
            "write_article", "write_section", "create_outline",
            "expand_content", "rewrite_content", "write_introduction",
            "write_conclusion"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by ContentWriterAgent"
        
        if task in ["write_article", "write_section"] and "topic" not in payload:
            return False, "Missing 'topic' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process writing request"""
        task = message.task
        payload = message.payload
        
        if task == "write_article":
            result = self._write_full_article(payload)
        elif task == "write_section":
            result = self._write_section(payload)
        elif task == "create_outline":
            result = self._create_article_outline(payload)
        elif task == "expand_content":
            result = self._expand_content(payload)
        elif task == "rewrite_content":
            result = self._rewrite_content(payload)
        elif task == "write_introduction":
            result = self._write_introduction(payload)
        else:
            result = self._write_conclusion(payload)
        
        return self._create_response(message, result)
    
    def _write_full_article(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Write a complete article"""
        topic = payload.get("topic", "")
        word_count = payload.get("word_count", MIN_WORD_COUNT)
        research = payload.get("research", {})
        sources = payload.get("sources", [])
        requirements = payload.get("requirements", {})
        
        # Create article structure
        outline = self._create_detailed_outline(topic, research, word_count)
        
        # Write article based on outline
        article_prompt = f"""Write a comprehensive article about: {topic}

Target word count: {word_count} words (±50 words tolerance)

Research synthesis:
{json.dumps(research, indent=2)}

Available sources for citation:
{json.dumps(sources[:15], indent=2)}

Article outline:
{outline}

Requirements:
- Professional tone for institutional investors
- Data-driven with specific statistics
- {len(sources)} inline citations minimum
- Clear actionable insights
- Dakota perspective where relevant
- Current data (2024-2025 focus)

Format citations as: [Source Name, Date](URL)

Write the complete article following the outline."""

        article = self.query_llm(
            article_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=6000
        )
        
        # Verify word count
        actual_word_count = len(article.split())
        
        return {
            "success": True,
            "article": article,
            "word_count": actual_word_count,
            "outline": outline,
            "topic": topic,
            "meets_requirements": abs(actual_word_count - word_count) <= 50
        }
    
    def _write_section(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Write a specific section"""
        section_title = payload.get("section_title", "")
        topic = payload.get("topic", "")
        context = payload.get("context", "")
        target_words = payload.get("target_words", 300)
        sources = payload.get("sources", [])
        
        section_prompt = f"""Write a section for an article about: {topic}

Section title: {section_title}
Target length: {target_words} words

Context:
{context}

Available sources:
{json.dumps(sources[:5], indent=2)}

Write a detailed, professional section that:
1. Focuses specifically on {section_title}
2. Includes relevant data and statistics
3. Provides actionable insights
4. Uses appropriate citations
5. Maintains institutional investor focus"""

        section_content = self.query_llm(
            section_prompt,
            reasoning_effort="medium",
            verbosity="high",
            max_tokens=1500
        )
        
        return {
            "success": True,
            "section_content": section_content,
            "section_title": section_title,
            "word_count": len(section_content.split())
        }
    
    def _create_article_outline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create article outline"""
        topic = payload.get("topic", "")
        research = payload.get("research", {})
        target_sections = payload.get("target_sections", 7)
        
        outline_prompt = f"""Create a detailed article outline for: {topic}

Research insights:
{json.dumps(research, indent=2)[:2000]}...

Create an outline with {target_sections} main sections that:
1. Follows logical flow
2. Covers all key aspects
3. Includes Dakota perspectives
4. Targets institutional investors
5. Enables data-driven content

For each section provide:
- Section title
- Key points to cover (3-5)
- Target word count
- Data/statistics to include
- Dakota angle (if applicable)"""

        outline = self.query_llm(
            outline_prompt,
            reasoning_effort="high",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "outline": outline,
            "topic": topic,
            "sections": self._parse_outline_sections(outline)
        }
    
    def _expand_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Expand existing content"""
        content = payload.get("content", "")
        target_expansion = payload.get("target_expansion", 200)  # words to add
        focus_areas = payload.get("focus_areas", [])
        sources = payload.get("sources", [])
        
        expand_prompt = f"""Expand this content by approximately {target_expansion} words:

{content}

Focus areas for expansion:
{json.dumps(focus_areas, indent=2)}

Additional sources:
{json.dumps(sources[:5], indent=2)}

Expand by:
1. Adding more detail to existing points
2. Including additional data/statistics
3. Providing more examples
4. Deepening analysis
5. Adding actionable insights

Maintain the same tone and style."""

        expanded_content = self.query_llm(
            expand_prompt,
            reasoning_effort="medium",
            verbosity="high",
            max_tokens=len(content.split()) + target_expansion + 500
        )
        
        original_words = len(content.split())
        expanded_words = len(expanded_content.split())
        
        return {
            "success": True,
            "expanded_content": expanded_content,
            "original_word_count": original_words,
            "expanded_word_count": expanded_words,
            "words_added": expanded_words - original_words
        }
    
    def _rewrite_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Rewrite content with improvements"""
        content = payload.get("content", "")
        improvements = payload.get("improvements", [])
        style_guide = payload.get("style_guide", {})
        
        rewrite_prompt = f"""Rewrite this content with improvements:

{content}

Requested improvements:
{json.dumps(improvements, indent=2)}

Style guidelines:
{json.dumps(style_guide, indent=2)}

Rewrite to:
1. Address all improvement requests
2. Enhance clarity and flow
3. Strengthen data presentation
4. Improve actionability
5. Maintain professional tone

Keep approximately the same length."""

        rewritten_content = self.query_llm(
            rewrite_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=len(content.split()) + 200
        )
        
        return {
            "success": True,
            "rewritten_content": rewritten_content,
            "improvements_applied": improvements,
            "original_length": len(content.split()),
            "rewritten_length": len(rewritten_content.split())
        }
    
    def _write_introduction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Write article introduction"""
        topic = payload.get("topic", "")
        key_points = payload.get("key_points", [])
        hook = payload.get("hook", "")
        
        intro_prompt = f"""Write a compelling introduction for an article about: {topic}

Key points to preview:
{json.dumps(key_points, indent=2)}

Hook/Opening angle: {hook}

Create an introduction that:
1. Captures attention immediately
2. Establishes relevance for institutional investors
3. Preview key insights
4. Sets professional, authoritative tone
5. Creates urgency or importance
6. Length: 150-200 words

Make it engaging yet professional."""

        introduction = self.query_llm(
            intro_prompt,
            reasoning_effort="high",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "introduction": introduction,
            "word_count": len(introduction.split()),
            "topic": topic
        }
    
    def _write_conclusion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Write article conclusion"""
        topic = payload.get("topic", "")
        key_takeaways = payload.get("key_takeaways", [])
        call_to_action = payload.get("call_to_action", "")
        article_summary = payload.get("article_summary", "")
        
        conclusion_prompt = f"""Write a strong conclusion for an article about: {topic}

Article summary:
{article_summary}

Key takeaways:
{json.dumps(key_takeaways, indent=2)}

Call to action: {call_to_action}

Create a conclusion that:
1. Synthesizes main insights
2. Reinforces key takeaways
3. Provides clear next steps
4. Includes Dakota value proposition
5. Ends with memorable statement
6. Length: 150-200 words

Make it actionable and memorable."""

        conclusion = self.query_llm(
            conclusion_prompt,
            reasoning_effort="high",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "conclusion": conclusion,
            "word_count": len(conclusion.split()),
            "topic": topic
        }
    
    def _create_detailed_outline(self, topic: str, research: Dict[str, Any], 
                               word_count: int) -> str:
        """Create detailed outline for article"""
        # Calculate section distribution
        intro_words = 150
        conclusion_words = 150
        body_words = word_count - intro_words - conclusion_words
        num_sections = 5  # Default main sections
        words_per_section = body_words // num_sections
        
        outline = f"""# {topic}

## I. Introduction ({intro_words} words)
- Hook: Current market relevance
- Problem/opportunity statement
- Preview of key insights
- Dakota perspective teaser

## II. Market Overview ({words_per_section} words)
- Current market size and growth
- Key trends and drivers
- Institutional adoption rates
- Recent developments (2024-2025)

## III. Investment Strategies ({words_per_section} words)
- Core strategy approaches
- Risk-return profiles
- Portfolio allocation recommendations
- Case studies/examples

## IV. Due Diligence Considerations ({words_per_section} words)
- Key evaluation criteria
- Red flags and risks
- Performance benchmarks
- Manager selection factors

## V. Dakota's Approach ({words_per_section} words)
- Unique value proposition
- Expertise and track record
- Client success stories
- Differentiated insights

## VI. Future Outlook ({words_per_section} words)
- Emerging opportunities
- Potential challenges
- Strategic recommendations
- Action items for investors

## VII. Conclusion ({conclusion_words} words)
- Key takeaways summary
- Call to action
- Dakota resources
- Next steps"""
        
        return outline
    
    def _parse_outline_sections(self, outline: str) -> List[Dict[str, Any]]:
        """Parse outline into structured sections"""
        sections = []
        current_section = None
        
        lines = outline.split('\n')
        for line in lines:
            line = line.strip()
            
            # Main section (##)
            if line.startswith('## ') and not line.startswith('### '):
                if current_section:
                    sections.append(current_section)
                
                # Extract section info
                section_match = re.match(r'## (?:[\d.IVX]+\s+)?(.+?)(?:\s*\((\d+)\s*words?\))?', line)
                if section_match:
                    current_section = {
                        "title": section_match.group(1),
                        "target_words": int(section_match.group(2)) if section_match.group(2) else 200,
                        "key_points": []
                    }
            
            # Bullet points under section
            elif line.startswith('- ') and current_section:
                current_section["key_points"].append(line[2:])
        
        if current_section:
            sections.append(current_section)
        
        return sections


class StyleEditorAgent(BaseAgent):
    """Agent specialized in style and tone editing"""
    
    def __init__(self):
        super().__init__(
            agent_id="style_editor_001",
            agent_type="editor",
            team="writing"
        )
        self.capabilities = [
            "edit_style",
            "check_tone",
            "improve_clarity",
            "ensure_consistency",
            "polish_content"
        ]
        self.model = DEFAULT_MODELS.get("editor", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate editing tasks"""
        valid_tasks = [
            "edit_style", "check_tone", "improve_clarity",
            "ensure_consistency", "polish_content", "check_grammar"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by StyleEditorAgent"
        
        if "content" not in payload:
            return False, "Missing 'content' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process editing request"""
        task = message.task
        payload = message.payload
        
        if task == "edit_style":
            result = self._edit_for_style(payload)
        elif task == "check_tone":
            result = self._check_and_adjust_tone(payload)
        elif task == "improve_clarity":
            result = self._improve_clarity(payload)
        elif task == "ensure_consistency":
            result = self._ensure_consistency(payload)
        elif task == "polish_content":
            result = self._polish_content(payload)
        else:
            result = self._check_grammar(payload)
        
        return self._create_response(message, result)
    
    def _edit_for_style(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Edit content for style consistency"""
        content = payload.get("content", "")
        style_guide = payload.get("style_guide", {
            "tone": "professional",
            "voice": "authoritative",
            "perspective": "third-person",
            "formality": "high"
        })
        
        edit_prompt = f"""Edit this content for style consistency:

{content}

Style guide:
{json.dumps(style_guide, indent=2)}

Ensure:
1. Consistent professional tone throughout
2. Appropriate formality for institutional investors
3. Active voice where possible
4. Clear, concise sentences
5. Smooth transitions between ideas
6. No jargon without explanation
7. Consistent terminology

Return the edited content maintaining the same structure and length."""

        edited_content = self.query_llm(
            edit_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=len(content.split()) + 100
        )
        
        changes = self._identify_changes(content, edited_content)
        
        return {
            "success": True,
            "edited_content": edited_content,
            "changes_made": len(changes),
            "change_summary": changes[:5],  # Top 5 changes
            "style_score": self._calculate_style_score(edited_content, style_guide)
        }
    
    def _check_and_adjust_tone(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check and adjust content tone"""
        content = payload.get("content", "")
        target_tone = payload.get("target_tone", "professional-authoritative")
        audience = payload.get("audience", "institutional investors")
        
        tone_prompt = f"""Analyze and adjust the tone of this content:

{content}

Target tone: {target_tone}
Target audience: {audience}

Analysis tasks:
1. Identify current tone
2. Note tone inconsistencies
3. Adjust to match target tone
4. Ensure appropriate for audience
5. Maintain factual accuracy

Provide:
- Current tone assessment
- Adjusted content
- Changes made"""

        response = self.query_llm(
            tone_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        # Parse response to extract components
        tone_analysis = self._parse_tone_analysis(response)
        
        return {
            "success": True,
            "current_tone": tone_analysis.get("current_tone", ""),
            "adjusted_content": tone_analysis.get("adjusted_content", content),
            "tone_changes": tone_analysis.get("changes", []),
            "tone_consistency_score": tone_analysis.get("consistency_score", 85)
        }
    
    def _improve_clarity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Improve content clarity"""
        content = payload.get("content", "")
        focus_areas = payload.get("focus_areas", ["complex sentences", "technical terms", "flow"])
        
        clarity_prompt = f"""Improve the clarity of this content:

{content}

Focus on:
{json.dumps(focus_areas, indent=2)}

Improvements:
1. Simplify complex sentences
2. Define technical terms on first use
3. Improve paragraph transitions
4. Use concrete examples
5. Eliminate ambiguity
6. Enhance readability

Maintain professional tone and technical accuracy."""

        clarified_content = self.query_llm(
            clarity_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=len(content.split()) + 100
        )
        
        readability_scores = self._calculate_readability(clarified_content)
        
        return {
            "success": True,
            "clarified_content": clarified_content,
            "readability_scores": readability_scores,
            "improvements": self._identify_clarity_improvements(content, clarified_content)
        }
    
    def _ensure_consistency(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure content consistency"""
        content = payload.get("content", "")
        terminology = payload.get("terminology", {})
        style_rules = payload.get("style_rules", [])
        
        consistency_prompt = f"""Ensure consistency throughout this content:

{content}

Terminology preferences:
{json.dumps(terminology, indent=2)}

Style rules:
{json.dumps(style_rules, indent=2)}

Check and fix:
1. Terminology consistency
2. Formatting consistency
3. Citation style consistency
4. Number/date formatting
5. Capitalization rules
6. Punctuation patterns

Return consistently formatted content."""

        consistent_content = self.query_llm(
            consistency_prompt,
            reasoning_effort="medium",
            verbosity="high",
            max_tokens=len(content.split()) + 100
        )
        
        consistency_report = self._generate_consistency_report(content, consistent_content)
        
        return {
            "success": True,
            "consistent_content": consistent_content,
            "consistency_report": consistency_report,
            "changes_applied": consistency_report.get("total_changes", 0)
        }
    
    def _polish_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Final polish of content"""
        content = payload.get("content", "")
        polish_priorities = payload.get("priorities", [
            "flow", "impact", "memorability", "professionalism"
        ])
        
        polish_prompt = f"""Provide final polish to this content:

{content}

Polish priorities:
{json.dumps(polish_priorities, indent=2)}

Final improvements:
1. Enhance opening and closing impact
2. Strengthen key messages
3. Improve memorable phrases
4. Perfect transitions
5. Eliminate any remaining awkwardness
6. Ensure professional excellence

This is the final edit - make it publication-ready."""

        polished_content = self.query_llm(
            polish_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=len(content.split()) + 100
        )
        
        quality_assessment = self._assess_final_quality(polished_content)
        
        return {
            "success": True,
            "polished_content": polished_content,
            "quality_assessment": quality_assessment,
            "ready_for_publication": quality_assessment.get("overall_score", 0) >= 90
        }
    
    def _check_grammar(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check grammar and mechanics"""
        content = payload.get("content", "")
        
        grammar_prompt = f"""Check grammar and mechanics in this content:

{content}

Check for:
1. Grammar errors
2. Spelling mistakes
3. Punctuation errors
4. Subject-verb agreement
5. Tense consistency
6. Proper word usage

Provide corrected content with all errors fixed."""

        corrected_content = self.query_llm(
            grammar_prompt,
            reasoning_effort="medium",
            verbosity="high",
            max_tokens=len(content.split()) + 50
        )
        
        errors_found = self._count_grammar_corrections(content, corrected_content)
        
        return {
            "success": True,
            "corrected_content": corrected_content,
            "errors_found": errors_found,
            "grammar_score": max(0, 100 - (errors_found * 5))
        }
    
    def _identify_changes(self, original: str, edited: str) -> List[Dict[str, str]]:
        """Identify changes between original and edited content"""
        # Simple implementation - in production would use diff algorithm
        changes = []
        
        original_sentences = original.split('.')
        edited_sentences = edited.split('.')
        
        for i, (orig, edit) in enumerate(zip(original_sentences, edited_sentences)):
            if orig.strip() != edit.strip():
                changes.append({
                    "type": "sentence_edit",
                    "location": f"Sentence {i+1}",
                    "original": orig.strip()[:100] + "...",
                    "edited": edit.strip()[:100] + "..."
                })
        
        return changes
    
    def _calculate_style_score(self, content: str, style_guide: Dict[str, str]) -> float:
        """Calculate style adherence score"""
        # Simplified scoring
        score = 85.0  # Base score
        
        # Check for passive voice
        passive_indicators = ["was", "were", "been", "being", "be"]
        passive_count = sum(content.lower().count(word) for word in passive_indicators)
        if passive_count < 10:
            score += 5
        
        # Check sentence length variation
        sentences = content.split('.')
        if len(sentences) > 5:
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if max(lengths) - min(lengths) > 10:
                score += 5
        
        # Professional language check
        professional_terms = ["strategic", "institutional", "analysis", "framework", "optimize"]
        prof_count = sum(content.lower().count(term) for term in professional_terms)
        if prof_count > 5:
            score += 5
        
        return min(100, score)
    
    def _parse_tone_analysis(self, response: str) -> Dict[str, Any]:
        """Parse tone analysis from response"""
        # Simple parsing - would be more sophisticated in production
        result = {
            "current_tone": "",
            "adjusted_content": "",
            "changes": [],
            "consistency_score": 85
        }
        
        lines = response.split('\n')
        mode = None
        
        for line in lines:
            if "current tone" in line.lower():
                mode = "tone"
            elif "adjusted content" in line.lower():
                mode = "content"
            elif "changes" in line.lower():
                mode = "changes"
            elif mode == "tone" and line.strip():
                result["current_tone"] += line.strip() + " "
            elif mode == "content" and line.strip():
                result["adjusted_content"] += line + "\n"
            elif mode == "changes" and line.strip().startswith('-'):
                result["changes"].append(line.strip()[1:].strip())
        
        return result
    
    def _calculate_readability(self, content: str) -> Dict[str, float]:
        """Calculate readability metrics"""
        words = content.split()
        sentences = content.split('.')
        
        # Simple readability metrics
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        # Count complex words (3+ syllables, simplified)
        complex_words = sum(1 for word in words if len(word) > 8)
        complex_word_ratio = complex_words / max(len(words), 1)
        
        # Flesch Reading Ease approximation
        flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * complex_word_ratio
        
        return {
            "flesch_reading_ease": max(0, min(100, flesch_score)),
            "average_sentence_length": avg_sentence_length,
            "complex_word_percentage": complex_word_ratio * 100,
            "readability_grade": "Professional" if flesch_score > 30 else "Complex"
        }
    
    def _identify_clarity_improvements(self, original: str, clarified: str) -> List[str]:
        """Identify clarity improvements made"""
        improvements = []
        
        # Check for reduced sentence length
        orig_sentences = original.split('.')
        clar_sentences = clarified.split('.')
        
        orig_avg_len = sum(len(s.split()) for s in orig_sentences) / max(len(orig_sentences), 1)
        clar_avg_len = sum(len(s.split()) for s in clar_sentences) / max(len(clar_sentences), 1)
        
        if clar_avg_len < orig_avg_len - 2:
            improvements.append("Shortened average sentence length")
        
        # Check for technical term definitions
        if "defined as" in clarified or "which means" in clarified:
            improvements.append("Added technical term definitions")
        
        # Check for examples
        if "for example" in clarified.lower() or "such as" in clarified.lower():
            improvements.append("Added concrete examples")
        
        # Check for transitions
        transitions = ["however", "furthermore", "additionally", "therefore", "consequently"]
        if any(trans in clarified.lower() for trans in transitions):
            improvements.append("Improved paragraph transitions")
        
        return improvements
    
    def _generate_consistency_report(self, original: str, consistent: str) -> Dict[str, Any]:
        """Generate consistency report"""
        report = {
            "total_changes": 0,
            "terminology_fixes": 0,
            "formatting_fixes": 0,
            "style_fixes": 0
        }
        
        # Count various types of changes (simplified)
        if original != consistent:
            # Estimate changes based on character differences
            char_diff = abs(len(original) - len(consistent))
            report["total_changes"] = max(1, char_diff // 10)
            
            # Distribute changes across categories
            report["terminology_fixes"] = report["total_changes"] // 3
            report["formatting_fixes"] = report["total_changes"] // 3
            report["style_fixes"] = report["total_changes"] - report["terminology_fixes"] - report["formatting_fixes"]
        
        return report
    
    def _assess_final_quality(self, content: str) -> Dict[str, Any]:
        """Assess final content quality"""
        assessment = {
            "overall_score": 90,
            "strengths": [],
            "areas_of_excellence": []
        }
        
        # Check various quality indicators
        if len(content.split()) > 100:
            assessment["strengths"].append("Comprehensive coverage")
        
        if "dakota" in content.lower():
            assessment["strengths"].append("Dakota perspective included")
        
        if re.search(r'\d+\.?\d*%', content):
            assessment["strengths"].append("Data-driven content")
        
        if content.count('[') > 5:
            assessment["strengths"].append("Well-cited")
        
        # Adjust score based on strengths
        assessment["overall_score"] = min(100, 85 + len(assessment["strengths"]) * 3)
        
        if assessment["overall_score"] >= 95:
            assessment["areas_of_excellence"] = ["Publication-ready quality"]
        
        return assessment
    
    def _count_grammar_corrections(self, original: str, corrected: str) -> int:
        """Count grammar corrections made"""
        # Simple approximation based on differences
        if original == corrected:
            return 0
        
        # Count character differences as a proxy
        char_diff = sum(1 for a, b in zip(original, corrected) if a != b)
        
        # Estimate errors (roughly 1 error per 20 character differences)
        return max(1, char_diff // 20)


class CitationAgent(BaseAgent):
    """Agent specialized in citation management"""
    
    def __init__(self):
        super().__init__(
            agent_id="citation_agent_001",
            agent_type="citation_manager",
            team="writing"
        )
        self.capabilities = [
            "add_citations",
            "verify_citations",
            "format_citations",
            "create_bibliography",
            "check_attribution"
        ]
        self.model = DEFAULT_MODELS.get("citation", "gpt-5-nano")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate citation tasks"""
        valid_tasks = [
            "add_citations", "verify_citations", "format_citations",
            "create_bibliography", "check_attribution", "update_citations"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by CitationAgent"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process citation request"""
        task = message.task
        payload = message.payload
        
        if task == "add_citations":
            result = self._add_citations(payload)
        elif task == "verify_citations":
            result = self._verify_citations(payload)
        elif task == "format_citations":
            result = self._format_citations(payload)
        elif task == "create_bibliography":
            result = self._create_bibliography(payload)
        elif task == "check_attribution":
            result = self._check_attribution(payload)
        else:
            result = self._update_citations(payload)
        
        return self._create_response(message, result)
    
    def _add_citations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Add citations to content"""
        content = payload.get("content", "")
        sources = payload.get("sources", [])
        min_citations = payload.get("min_citations", MIN_SOURCES)
        
        citation_prompt = f"""Add appropriate citations to this content:

{content}

Available sources:
{json.dumps(sources, indent=2)}

Requirements:
- Add at least {min_citations} citations
- Place citations at relevant claims/data points
- Use format: [Source Name, Date](URL)
- Ensure even distribution throughout
- Prioritize high-credibility sources
- Include Dakota sources where relevant

Return the content with citations added."""

        cited_content = self.query_llm(
            citation_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=len(content.split()) + 500
        )
        
        citation_count = cited_content.count('[')
        
        return {
            "success": True,
            "cited_content": cited_content,
            "citations_added": citation_count,
            "meets_minimum": citation_count >= min_citations,
            "citation_distribution": self._analyze_citation_distribution(cited_content)
        }
    
    def _verify_citations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verify all citations in content"""
        content = payload.get("content", "")
        
        # Extract citations
        citation_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        citations = re.findall(citation_pattern, content)
        
        verification_results = []
        for source_text, url in citations:
            result = {
                "citation": f"[{source_text}]({url})",
                "source_text": source_text,
                "url": url,
                "url_valid": self._validate_url_format(url),
                "source_format_valid": self._validate_source_format(source_text),
                "issues": []
            }
            
            if not result["url_valid"]:
                result["issues"].append("Invalid URL format")
            
            if not result["source_format_valid"]:
                result["issues"].append("Source format should include name and date")
            
            verification_results.append(result)
        
        valid_citations = sum(1 for r in verification_results if not r["issues"])
        
        return {
            "success": True,
            "total_citations": len(citations),
            "valid_citations": valid_citations,
            "invalid_citations": len(citations) - valid_citations,
            "verification_results": verification_results,
            "needs_correction": valid_citations < len(citations)
        }
    
    def _format_citations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Format citations consistently"""
        content = payload.get("content", "")
        citation_style = payload.get("style", "inline")  # inline, footnote, etc.
        
        format_prompt = f"""Format all citations consistently in this content:

{content}

Citation style: {citation_style}
Standard format: [Source Name, Year](URL)

Ensure:
1. Consistent formatting throughout
2. Proper date format (Year only)
3. Clean source names (no extra punctuation)
4. Valid URL format
5. No duplicate citations
6. Alphabetical order within text if multiple

Return content with properly formatted citations."""

        formatted_content = self.query_llm(
            format_prompt,
            reasoning_effort="medium",
            verbosity="high",
            max_tokens=len(content.split()) + 200
        )
        
        return {
            "success": True,
            "formatted_content": formatted_content,
            "citation_style": citation_style,
            "formatting_changes": self._count_format_changes(content, formatted_content)
        }
    
    def _create_bibliography(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create bibliography from citations"""
        content = payload.get("content", "")
        style = payload.get("style", "APA")
        
        # Extract all citations
        citation_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        citations = re.findall(citation_pattern, content)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation not in seen:
                seen.add(citation)
                unique_citations.append(citation)
        
        # Create bibliography
        bibliography_prompt = f"""Create a {style} style bibliography from these citations:

{json.dumps(unique_citations, indent=2)}

Format each entry properly according to {style} style.
Sort alphabetically by author/source name.
Include all necessary information.

Return formatted bibliography."""

        bibliography = self.query_llm(
            bibliography_prompt,
            reasoning_effort="medium",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "bibliography": bibliography,
            "total_sources": len(unique_citations),
            "citation_style": style,
            "sources": unique_citations
        }
    
    def _check_attribution(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check proper attribution of claims"""
        content = payload.get("content", "")
        
        attribution_prompt = f"""Check attribution in this content:

{content}

Identify:
1. Claims needing citations that lack them
2. Statistics without sources
3. Quotes without attribution
4. Expert opinions without references
5. Market data without sources

For each issue found, provide:
- The claim/statement
- Why it needs attribution
- Suggested fix

Return detailed attribution analysis."""

        attribution_analysis = self.query_llm(
            attribution_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        issues = self._parse_attribution_issues(attribution_analysis)
        
        return {
            "success": True,
            "attribution_complete": len(issues) == 0,
            "issues_found": len(issues),
            "attribution_issues": issues,
            "detailed_analysis": attribution_analysis
        }
    
    def _update_citations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update outdated citations"""
        content = payload.get("content", "")
        new_sources = payload.get("new_sources", [])
        update_criteria = payload.get("criteria", {"outdated": True, "broken": True})
        
        update_prompt = f"""Update citations in this content:

{content}

New/updated sources available:
{json.dumps(new_sources, indent=2)}

Update criteria:
{json.dumps(update_criteria, indent=2)}

Tasks:
1. Replace outdated sources (pre-2023) with newer ones
2. Update broken links if alternatives available
3. Add dates to sources missing them
4. Improve source credibility where possible

Maintain the same citation positions and relevance."""

        updated_content = self.query_llm(
            update_prompt,
            reasoning_effort="high",
            verbosity="high",
            max_tokens=len(content.split()) + 200
        )
        
        updates_made = self._count_citation_updates(content, updated_content)
        
        return {
            "success": True,
            "updated_content": updated_content,
            "updates_made": updates_made,
            "update_summary": self._summarize_updates(content, updated_content)
        }
    
    def _analyze_citation_distribution(self, content: str) -> Dict[str, Any]:
        """Analyze how citations are distributed in content"""
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        
        distribution = {
            "total_paragraphs": len(paragraphs),
            "paragraphs_with_citations": 0,
            "citations_per_paragraph": [],
            "even_distribution": False
        }
        
        for para in paragraphs:
            citation_count = para.count('[')
            if citation_count > 0:
                distribution["paragraphs_with_citations"] += 1
            distribution["citations_per_paragraph"].append(citation_count)
        
        # Check if distribution is relatively even
        if distribution["citations_per_paragraph"]:
            avg = sum(distribution["citations_per_paragraph"]) / len(distribution["citations_per_paragraph"])
            variance = sum((x - avg) ** 2 for x in distribution["citations_per_paragraph"]) / len(distribution["citations_per_paragraph"])
            distribution["even_distribution"] = variance < 2
        
        return distribution
    
    def _validate_url_format(self, url: str) -> bool:
        """Validate URL format"""
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(url_pattern, url))
    
    def _validate_source_format(self, source_text: str) -> bool:
        """Validate source text format (should include name and date)"""
        # Check for year pattern
        year_pattern = r'\b(19|20)\d{2}\b'
        has_year = bool(re.search(year_pattern, source_text))
        
        # Check minimum length
        has_substance = len(source_text) > 10
        
        return has_year and has_substance
    
    def _count_format_changes(self, original: str, formatted: str) -> int:
        """Count formatting changes made"""
        # Extract citations from both
        original_citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original)
        formatted_citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', formatted)
        
        changes = 0
        for (orig_text, orig_url), (form_text, form_url) in zip(original_citations, formatted_citations):
            if orig_text != form_text or orig_url != form_url:
                changes += 1
        
        return changes
    
    def _parse_attribution_issues(self, analysis: str) -> List[Dict[str, str]]:
        """Parse attribution issues from analysis"""
        issues = []
        lines = analysis.split('\n')
        
        current_issue = None
        for line in lines:
            # Look for numbered issues or bullet points
            if re.match(r'^[0-9]+\.|^-|^•', line):
                if current_issue:
                    issues.append(current_issue)
                
                current_issue = {
                    "statement": line.strip(),
                    "reason": "",
                    "suggestion": ""
                }
            elif current_issue:
                if "needs" in line.lower() or "requires" in line.lower():
                    current_issue["reason"] = line.strip()
                elif "suggest" in line.lower() or "add" in line.lower():
                    current_issue["suggestion"] = line.strip()
        
        if current_issue:
            issues.append(current_issue)
        
        return issues
    
    def _count_citation_updates(self, original: str, updated: str) -> int:
        """Count citation updates made"""
        original_citations = set(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original))
        updated_citations = set(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', updated))
        
        # Count changes
        removed = original_citations - updated_citations
        added = updated_citations - original_citations
        
        return len(removed) + len(added)
    
    def _summarize_updates(self, original: str, updated: str) -> List[str]:
        """Summarize citation updates made"""
        summary = []
        
        original_citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original)
        updated_citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', updated)
        
        # Check for date updates
        original_years = [re.search(r'(20\d{2})', c[0]) for c in original_citations]
        updated_years = [re.search(r'(20\d{2})', c[0]) for c in updated_citations]
        
        if any(u and (not o or u.group(1) > o.group(1)) for o, u in zip(original_years, updated_years)):
            summary.append("Updated outdated sources with newer references")
        
        # Check for URL changes
        if len(set(c[1] for c in original_citations)) != len(set(c[1] for c in updated_citations)):
            summary.append("Replaced broken or invalid URLs")
        
        # Check for new citations
        if len(updated_citations) > len(original_citations):
            summary.append(f"Added {len(updated_citations) - len(original_citations)} new citations")
        
        return summary