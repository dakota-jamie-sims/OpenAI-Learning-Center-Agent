"""
File management utilities for article output
"""
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, List
import re

from src.config import OUTPUT_BASE_DIR


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem compatibility"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with hyphens
    filename = filename.replace(' ', '-')
    # Remove multiple hyphens
    filename = re.sub(r'-+', '-', filename)
    # Convert to lowercase
    filename = filename.lower()
    # Limit length
    if len(filename) > 50:
        filename = filename[:50]
    return filename.strip('-')


def create_output_directory(topic: str) -> Path:
    """Create output directory for article"""
    # Generate directory name
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_topic = sanitize_filename(topic)
    dir_name = f"{date_str}-{safe_topic}"
    
    # Create full path
    output_dir = Path(OUTPUT_BASE_DIR) / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def save_article_files(output_dir: Path, article: str, summary: str, 
                      social: str, metadata: Dict[str, Any], 
                      quality_report: Dict[str, Any] = None) -> Dict[str, str]:
    """Save all article files to output directory"""
    files_saved = {}
    
    # Save main article
    article_path = output_dir / "article.md"
    article_path.write_text(article, encoding='utf-8')
    files_saved["article"] = str(article_path)
    
    # Save summary
    if summary:
        summary_path = output_dir / "summary.md"
        summary_path.write_text(summary, encoding='utf-8')
        files_saved["summary"] = str(summary_path)
    
    # Save social media content
    if social:
        social_path = output_dir / "social.md"
        social_path.write_text(social, encoding='utf-8')
        files_saved["social"] = str(social_path)
    
    # Save metadata
    if metadata:
        metadata_path = output_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        files_saved["metadata"] = str(metadata_path)
    
    # Save quality report
    if quality_report:
        quality_path = output_dir / "quality-report.json"
        quality_path.write_text(json.dumps(quality_report, indent=2), encoding='utf-8')
        files_saved["quality_report"] = str(quality_path)
        
        # Also save human-readable quality report
        quality_md = format_quality_report(quality_report)
        quality_md_path = output_dir / "quality-report.md"
        quality_md_path.write_text(quality_md, encoding='utf-8')
        files_saved["quality_report_md"] = str(quality_md_path)
    
    # Create index file
    index_content = create_index_file(files_saved, metadata)
    index_path = output_dir / "index.md"
    index_path.write_text(index_content, encoding='utf-8')
    files_saved["index"] = str(index_path)
    
    return files_saved


def format_quality_report(quality_report: Dict[str, Any]) -> str:
    """Format quality report as markdown"""
    report = f"""# Quality Assurance Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overall Results

- **Quality Score**: {quality_report.get('overall_quality_score', 0):.1f}/10
- **Grade**: {quality_report.get('quality_grade', 'N/A')}
- **Ready for Publication**: {quality_report.get('ready_for_publication', False)}

## Detailed Results

"""
    
    # Add detailed results
    detailed = quality_report.get('detailed_results', {})
    
    if 'fact_checking' in detailed:
        facts = detailed['fact_checking']
        report += f"""### Fact Checking
- Confidence Score: {facts.get('confidence_score', 0)}%
- Facts Verified: {facts.get('verified', 0)}
- Facts Unverified: {facts.get('unverified', 0)}

"""
    
    if 'compliance' in detailed:
        compliance = detailed['compliance']
        report += f"""### Compliance
- Status: {compliance.get('compliance_status', 'unknown')}
- Issues Found: {compliance.get('issues_found', 0)}

"""
    
    if 'readability' in detailed:
        readability = detailed['readability']
        report += f"""### Readability
- Flesch Score: {readability.get('flesch_score', 0):.1f}
- Grade: {readability.get('readability_grade', 'N/A')}
- Audience Appropriate: {readability.get('audience_appropriate', False)}

"""
    
    # Add recommendations
    recommendations = quality_report.get('recommendations', [])
    if recommendations:
        report += "## Recommendations\n\n"
        for rec in recommendations:
            report += f"- {rec}\n"
    
    return report


def create_index_file(files: Dict[str, str], metadata: Dict[str, Any]) -> str:
    """Create index file with links to all outputs"""
    topic = metadata.get('title', 'Article')
    date = metadata.get('generation_date', datetime.now().isoformat())
    
    index = f"""# {topic}

Generated: {date}

## Files

- [📄 Main Article](article.md)
- [📝 Executive Summary](summary.md)
- [📱 Social Media Content](social.md)
- [📊 Metadata](metadata.json)
- [✅ Quality Report](quality-report.md)

## Article Information

- **Word Count**: {metadata.get('word_count', 'N/A')}
- **Reading Time**: {metadata.get('reading_time', 'N/A')} minutes
- **Target Audience**: {metadata.get('target_audience', 'Institutional Investors')}
- **Content Type**: {metadata.get('content_type', 'Educational')}

## Keywords

{', '.join(metadata.get('keywords', []))}
"""
    
    return index


def list_recent_articles(limit: int = 10) -> List[Dict[str, Any]]:
    """List recent articles from output directory"""
    output_path = Path(OUTPUT_BASE_DIR)
    
    if not output_path.exists():
        return []
    
    articles = []
    
    # Get all article directories
    for article_dir in sorted(output_path.iterdir(), reverse=True):
        if not article_dir.is_dir():
            continue
        
        # Check for metadata file
        metadata_path = article_dir / "metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text())
                articles.append({
                    "directory": str(article_dir),
                    "title": metadata.get("title", article_dir.name),
                    "date": metadata.get("generation_date", ""),
                    "word_count": metadata.get("word_count", 0),
                    "quality_score": metadata.get("quality_score", 0)
                })
            except:
                # Skip invalid metadata
                continue
        
        if len(articles) >= limit:
            break
    
    return articles


def get_article_stats() -> Dict[str, Any]:
    """Get statistics about generated articles"""
    output_path = Path(OUTPUT_BASE_DIR)
    
    if not output_path.exists():
        return {
            "total_articles": 0,
            "average_word_count": 0,
            "average_quality_score": 0
        }
    
    total_articles = 0
    total_words = 0
    total_quality = 0
    quality_count = 0
    
    for article_dir in output_path.iterdir():
        if not article_dir.is_dir():
            continue
        
        metadata_path = article_dir / "metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text())
                total_articles += 1
                total_words += metadata.get("word_count", 0)
                
                quality_score = metadata.get("quality_score", 0)
                if quality_score > 0:
                    total_quality += quality_score
                    quality_count += 1
            except:
                continue
    
    return {
        "total_articles": total_articles,
        "average_word_count": total_words / total_articles if total_articles > 0 else 0,
        "average_quality_score": total_quality / quality_count if quality_count > 0 else 0,
        "output_directory": str(output_path)
    }


def clean_old_articles(days: int = 30) -> int:
    """Clean articles older than specified days"""
    output_path = Path(OUTPUT_BASE_DIR)
    
    if not output_path.exists():
        return 0
    
    cutoff_date = datetime.now().timestamp() - (days * 86400)
    removed = 0
    
    for article_dir in output_path.iterdir():
        if not article_dir.is_dir():
            continue
        
        # Check directory age
        if article_dir.stat().st_mtime < cutoff_date:
            try:
                # Remove directory and contents
                for file in article_dir.iterdir():
                    file.unlink()
                article_dir.rmdir()
                removed += 1
            except:
                # Skip if unable to remove
                continue
    
    return removed