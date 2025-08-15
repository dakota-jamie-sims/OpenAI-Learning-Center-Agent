from openai import OpenAI
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.researcher_agent import ResearcherAgent
from agents.outliner_agent import OutlinerAgent
from agents.contentWriter_agent import ContentWriterAgent
from agents.reviewer_agent import ReviewerAgent
from utils.logging import get_logger

class ArticlePipeline:
    """Orchestrates the article creation pipeline using all agents"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Load environment variables
        load_dotenv()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        
        # Initialize agents
        self.researcher = ResearcherAgent(self.client)
        self.outliner = OutlinerAgent(self.client)
        self.writer = ContentWriterAgent(self.client)
        self.reviewer = ReviewerAgent(self.client)
        
        # Get vector store ID if available
        self.vector_store_id = os.getenv("VECTOR_STORE_ID")

        self.logger = get_logger(__name__)
    
    def create_article(self, topic: str, target_audience: str = "institutional investors",
                      article_type: str = "educational", max_iterations: int = 3) -> Dict[str, Any]:
        """
        Create a complete article using the full pipeline
        
        Args:
            topic: The topic to write about
            target_audience: Target audience for the article
            article_type: Type of article (educational, analysis, guide, etc.)
            max_iterations: Maximum number of revision iterations
        
        Returns:
            Dictionary containing the final article and metadata
        """
        
        pipeline_results = {
            "topic": topic,
            "target_audience": target_audience,
            "article_type": article_type,
            "stages": {}
        }
        
        try:
            # Stage 1: Research
            self.logger.info(f"Researching topic: {topic}", extra={"phase": "RESEARCH"})
            research_results = self.researcher.research(
                topic=topic,
                use_kb=True,
                use_web=True,
                vector_store_id=self.vector_store_id
            )
            pipeline_results["stages"]["research"] = research_results
            
            if research_results.get("error"):
                return {"error": f"Research failed: {research_results['error']}"}
            
            # Stage 2: Outline
            self.logger.info("Creating outline...", extra={"phase": "OUTLINE"})
            outline_results = self.outliner.create_outline(
                topic=topic,
                research_data=research_results,
                target_audience=target_audience,
                article_type=article_type
            )
            pipeline_results["stages"]["outline"] = outline_results
            
            if outline_results.get("error"):
                return {"error": f"Outline creation failed: {outline_results['error']}"}
            
            # Stage 3: Write Article
            self.logger.info("Writing article...", extra={"phase": "WRITING"})
            article_results = self.writer.write_article(
                topic=topic,
                outline=outline_results,
                research=research_results,
                min_words=1750
            )
            pipeline_results["stages"]["writing"] = article_results
            
            if article_results.get("error"):
                return {"error": f"Article writing failed: {article_results['error']}"}
            
            # Stage 4: Review and Iterate
            iteration_count = 0
            while iteration_count < max_iterations:
                self.logger.info(
                    f"Reviewing article (iteration {iteration_count + 1})...",
                    extra={"phase": "REVIEW"},
                )
                review_results = self.reviewer.review_article(article_results)
                pipeline_results["stages"][f"review_{iteration_count + 1}"] = review_results
                
                if review_results.get("approval_status"):
                    self.logger.info("Article approved!", extra={"phase": "REVIEW"})
                    break
                
                # Get improvement suggestions
                suggestions = self.reviewer.suggest_improvements(article_results, review_results)
                
                if not suggestions:
                    break
                
                # Apply improvements (simplified - in production, this would be more sophisticated)
                self.logger.info(
                    f"Applying improvements: {', '.join(suggestions[:2])}...",
                    extra={"phase": "REVISION"},
                )
                
                # For now, we'll just expand sections if the article is too short
                if any("Expand" in s for s in suggestions):
                    for section in article_results.get('sections', [])[:2]:  # Expand first 2 sections
                        article_results = self.writer.expand_section(
                            article_results, 
                            section
                        )
                
                iteration_count += 1
            
            # Final results
            final_article = article_results.get('article', '')
            
            pipeline_results["final_article"] = final_article
            pipeline_results["metadata"] = {
                "word_count": article_results.get('word_count', 0),
                "reading_time": article_results.get('reading_time', 'Unknown'),
                "sources_count": article_results.get('sources_count', 0),
                "sections": article_results.get('sections', []),
                "iterations": iteration_count + 1,
                "approved": review_results.get("approval_status", False)
            }
            
            return pipeline_results
            
        except Exception as e:
            return {"error": f"Pipeline error: {str(e)}"}
    
    def save_article(self, article_data: Dict[str, Any], output_dir: str = "output/articles") -> str:
        """Save the article to a file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from topic
        topic = article_data.get('topic', 'untitled')
        filename = topic.lower().replace(' ', '-').replace('/', '-')[:50] + '.md'
        
        filepath = output_path / filename
        
        # Write article content
        with open(filepath, 'w') as f:
            f.write(article_data.get('final_article', ''))
        
        return str(filepath)


def main():
    """Example usage of the pipeline"""
    # Initialize pipeline
    pipeline = ArticlePipeline()
    
    # Example topic
    topic = "The Benefits of Index Fund Investing for Long-Term Wealth Building"
    
    # Create article
    logger = get_logger(__name__)
    logger.info(f"Starting article creation for: {topic}", extra={"phase": "START"})
    results = pipeline.create_article(topic)
    
    if results.get("error"):
        logger.error(f"Error: {results['error']}", extra={"phase": "ERROR"})
        return
    
    # Save article
    filepath = pipeline.save_article(results)
    logger.info(f"Article saved to: {filepath}", extra={"phase": "SAVE"})
    
    # Print summary
    metadata = results.get('metadata', {})
    logger.info("Article Summary:", extra={"phase": "SUMMARY"})
    logger.info(f"Word Count: {metadata.get('word_count', 'Unknown')}", extra={"phase": "SUMMARY"})
    logger.info(f"Reading Time: {metadata.get('reading_time', 'Unknown')}", extra={"phase": "SUMMARY"})
    logger.info(f"Sources: {metadata.get('sources_count', 'Unknown')}", extra={"phase": "SUMMARY"})
    logger.info(f"Sections: {len(metadata.get('sections', []))}", extra={"phase": "SUMMARY"})
    logger.info(
        f"Approved: {'Yes' if metadata.get('approved') else 'No'}",
        extra={"phase": "SUMMARY"},
    )


if __name__ == "__main__":
    main()