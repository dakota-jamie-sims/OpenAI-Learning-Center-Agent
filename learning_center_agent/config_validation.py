"""
Validation Configuration for Different Article Types
Allows flexible validation based on content type
"""
import re

# Standard validation (default)
STANDARD_VALIDATION = {
    "min_credibility": 0.8,
    "min_fact_accuracy": 0.9,
    "require_citation_for_all_facts": True,
    "max_unverified_facts": 0,
    "min_source_credibility": 7,
    "require_current_year_data": True
}

# Private market validation (for PE, VC, private companies)
PRIVATE_MARKET_VALIDATION = {
    "min_credibility": 0.7,
    "min_fact_accuracy": 0.85,
    "require_citation_for_all_facts": False,  # Only for key claims
    "max_unverified_facts": 5,  # Allow some general statements
    "min_source_credibility": 6,
    "require_current_year_data": True
}

# Location-based validation (for regional guides)
LOCATION_BASED_VALIDATION = {
    "min_credibility": 0.6,  # More lenient for regional content
    "min_fact_accuracy": 0.75,  # Allow more descriptive content
    "require_citation_for_all_facts": False,
    "max_unverified_facts": 15,  # Higher tolerance for general statements
    "min_source_credibility": 5,  # Accept more general sources
    "require_current_year_data": False  # Allow some general information
}

# Quick brief validation
QUICK_BRIEF_VALIDATION = {
    "min_credibility": 0.7,
    "min_fact_accuracy": 0.8,
    "require_citation_for_all_facts": False,
    "max_unverified_facts": 5,
    "min_source_credibility": 6,
    "require_current_year_data": False  # More flexible for briefs
}

def get_validation_config(topic: str, word_count: int = 2000) -> dict:
    """
    Determine appropriate validation config based on topic and type
    """
    topic_lower = topic.lower()
    
    # Check for location-based content first (higher priority than private market)
    location_keywords = ["top 10", "best firms in", "leading firms in", "firms in", 
                        "companies in", "investors in", "in atlanta", "in dallas", "in austin", 
                        "in nashville", "in memphis", "in charlotte", "in raleigh", "in boston",
                        "in chicago", "in denver", "in miami", "in seattle", "in portland", 
                        "in texas", "in california", "in new york", "in florida"]
    # Also check for "top" + location pattern
    if any(keyword in topic_lower for keyword in location_keywords) or \
       ("top" in topic_lower and ("in " in topic_lower or "texas" in topic_lower or "california" in topic_lower)):
        return LOCATION_BASED_VALIDATION
    
    # Check for private market content
    private_keywords = ["private equity", "pe firms", "venture capital", "vc firms", 
                       "private funds", "hedge funds", "family offices"]
    if any(keyword in topic_lower for keyword in private_keywords):
        return PRIVATE_MARKET_VALIDATION
    
    # Quick briefs
    if word_count <= 500:
        return QUICK_BRIEF_VALIDATION
    
    # Default to standard validation
    return STANDARD_VALIDATION

# Key facts that ALWAYS need citations (100% accuracy requirement)
MUST_CITE_PATTERNS = [
    r'\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|trillion))',  # Large dollar amounts
    r'(?:raised|allocated|invested|committed)\s+\$',  # Investment amounts
    r'\d+%\s+(?:increase|decrease|growth|decline)',  # Performance metrics
    r'(?:returned|generated|yielded)\s+\d+%',  # Return figures
    r'(?:AUM|assets under management)',  # AUM figures
    r'(?:IRR|internal rate of return)',  # IRR figures
]

def is_key_fact(fact_text: str) -> bool:
    """
    Determine if a fact is critical and must have citation
    """
    for pattern in MUST_CITE_PATTERNS:
        if re.search(pattern, fact_text, re.IGNORECASE):
            return True
    return False