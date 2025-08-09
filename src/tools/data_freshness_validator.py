"""
Data Freshness Validator - Ensures 100% up-to-date information
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class DataFreshnessValidator:
    """Validates that all data and facts are current"""
    
    def __init__(self):
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month
        self.current_quarter = (self.current_month - 1) // 3 + 1
        
    def extract_dates_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract all date references from text"""
        date_patterns = [
            # Full dates
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'full_date'),
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'full_date_iso'),
            
            # Month Year
            (r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', 'month_year'),
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{4})', 'month_year_abbr'),
            
            # Quarter Year
            (r'Q(\d)\s+(\d{4})', 'quarter_year'),
            (r'(\d)Q\s+(\d{4})', 'quarter_year_alt'),
            (r'(first|second|third|fourth)\s+quarter\s+(?:of\s+)?(\d{4})', 'quarter_text'),
            
            # Year only
            (r'\b(20\d{2})\b', 'year_only'),
            
            # Relative dates
            (r'(last|previous)\s+(month|quarter|year)', 'relative_past'),
            (r'(this|current)\s+(month|quarter|year)', 'relative_current'),
            (r'year[- ]to[- ]date', 'ytd'),
            (r'trailing[- ]twelve[- ]months|TTM', 'ttm'),
        ]
        
        found_dates = []
        for pattern, date_type in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_dates.append({
                    'match': match.group(0),
                    'type': date_type,
                    'position': match.span(),
                    'groups': match.groups()
                })
        
        return found_dates
    
    def parse_date_to_datetime(self, date_info: Dict[str, Any]) -> datetime:
        """Convert extracted date to datetime object"""
        date_type = date_info['type']
        groups = date_info['groups']
        
        try:
            if date_type == 'full_date':
                month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                return datetime(year, month, day)
            
            elif date_type == 'full_date_iso':
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                return datetime(year, month, day)
            
            elif date_type in ['month_year', 'month_year_abbr']:
                month_str, year = groups[0], int(groups[1])
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
                    'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11,
                    'december': 12, 'dec': 12
                }
                month = month_map.get(month_str.lower(), 1)
                return datetime(year, month, 1)
            
            elif date_type in ['quarter_year', 'quarter_year_alt']:
                quarter = int(groups[0]) if date_type == 'quarter_year' else int(groups[0])
                year = int(groups[1])
                month = (quarter - 1) * 3 + 1
                return datetime(year, month, 1)
            
            elif date_type == 'year_only':
                year = int(groups[0])
                return datetime(year, 1, 1)
            
            elif date_type == 'relative_past':
                if 'month' in groups[1]:
                    return self.current_date - timedelta(days=30)
                elif 'quarter' in groups[1]:
                    return self.current_date - timedelta(days=90)
                elif 'year' in groups[1]:
                    return self.current_date - timedelta(days=365)
            
            elif date_type == 'relative_current':
                return self.current_date
            
            elif date_type in ['ytd', 'ttm']:
                return self.current_date
                
        except Exception as e:
            logger.warning(f"Could not parse date {date_info['match']}: {e}")
            
        return None
    
    def calculate_age_in_days(self, date: datetime) -> int:
        """Calculate how old the data is in days"""
        if date:
            age = (self.current_date - date).days
            return max(0, age)  # Ensure non-negative
        return -1  # Invalid date
    
    def categorize_data_freshness(self, age_days: int, data_type: str = 'general') -> Dict[str, Any]:
        """Categorize data freshness based on type and age"""
        freshness_rules = {
            'market_data': {
                'real_time': 1,      # 1 day
                'current': 7,        # 1 week
                'recent': 30,        # 1 month
                'acceptable': 90,    # 3 months
                'stale': 180,        # 6 months
                'outdated': float('inf')
            },
            'allocation_data': {
                'real_time': 30,     # 1 month
                'current': 90,       # 3 months
                'recent': 180,       # 6 months
                'acceptable': 365,   # 1 year
                'stale': 730,        # 2 years
                'outdated': float('inf')
            },
            'regulatory': {
                'real_time': 7,      # 1 week
                'current': 30,       # 1 month
                'recent': 90,        # 3 months
                'acceptable': 180,   # 6 months
                'stale': 365,        # 1 year
                'outdated': float('inf')
            },
            'general': {
                'real_time': 30,     # 1 month
                'current': 90,       # 3 months
                'recent': 180,       # 6 months
                'acceptable': 365,   # 1 year
                'stale': 540,        # 18 months
                'outdated': float('inf')
            }
        }
        
        rules = freshness_rules.get(data_type, freshness_rules['general'])
        
        for category, max_days in rules.items():
            if age_days <= max_days:
                return {
                    'category': category,
                    'age_days': age_days,
                    'is_acceptable': category not in ['stale', 'outdated'],
                    'recommendation': self._get_recommendation(category, data_type)
                }
        
        return {
            'category': 'outdated',
            'age_days': age_days,
            'is_acceptable': False,
            'recommendation': 'Data is too old and must be updated with current information'
        }
    
    def _get_recommendation(self, category: str, data_type: str) -> str:
        """Get recommendation based on freshness category"""
        recommendations = {
            'real_time': f"Excellent - {data_type} data is very current",
            'current': f"Good - {data_type} data is current",
            'recent': f"Acceptable - {data_type} data is recent but consider updating",
            'acceptable': f"Marginal - {data_type} data should be updated if possible",
            'stale': f"Poor - {data_type} data is stale and needs updating",
            'outdated': f"Unacceptable - {data_type} data is outdated and must be replaced"
        }
        return recommendations.get(category, "Unknown freshness category")
    
    def validate_article_freshness(self, article_text: str) -> Dict[str, Any]:
        """Validate all data freshness in an article"""
        # Extract all dates
        found_dates = self.extract_dates_from_text(article_text)
        
        # Parse and analyze each date
        date_analysis = []
        for date_info in found_dates:
            parsed_date = self.parse_date_to_datetime(date_info)
            if parsed_date:
                age_days = self.calculate_age_in_days(parsed_date)
                
                # Determine data type from context
                context = article_text[max(0, date_info['position'][0]-50):
                                     min(len(article_text), date_info['position'][1]+50)]
                data_type = self._determine_data_type(context)
                
                freshness = self.categorize_data_freshness(age_days, data_type)
                
                date_analysis.append({
                    'text': date_info['match'],
                    'position': date_info['position'],
                    'parsed_date': parsed_date,
                    'age_days': age_days,
                    'data_type': data_type,
                    'freshness': freshness,
                    'context': context.strip()
                })
        
        # Overall assessment
        all_acceptable = all(d['freshness']['is_acceptable'] for d in date_analysis)
        oldest_data = max(date_analysis, key=lambda x: x['age_days']) if date_analysis else None
        
        # Check for missing current data
        has_current_year = any(str(self.current_year) in d['text'] for d in date_analysis)
        has_recent_data = any(d['freshness']['category'] in ['real_time', 'current'] 
                             for d in date_analysis)
        
        return {
            'is_fresh': all_acceptable and has_recent_data,
            'total_dates_found': len(date_analysis),
            'date_analysis': date_analysis,
            'oldest_data': oldest_data,
            'has_current_year_data': has_current_year,
            'has_recent_data': has_recent_data,
            'recommendations': self._generate_recommendations(date_analysis, has_current_year)
        }
    
    def _determine_data_type(self, context: str) -> str:
        """Determine the type of data based on context"""
        context_lower = context.lower()
        
        market_keywords = ['price', 'trading', 'market', 'index', 'yield', 'rate', 'volatility']
        allocation_keywords = ['allocated', 'commitment', 'investment', 'billion', 'million', 'fund']
        regulatory_keywords = ['regulation', 'compliance', 'sec', 'rule', 'requirement', 'policy']
        
        if any(keyword in context_lower for keyword in market_keywords):
            return 'market_data'
        elif any(keyword in context_lower for keyword in allocation_keywords):
            return 'allocation_data'
        elif any(keyword in context_lower for keyword in regulatory_keywords):
            return 'regulatory'
        else:
            return 'general'
    
    def _generate_recommendations(self, date_analysis: List[Dict], has_current_year: bool) -> List[str]:
        """Generate specific recommendations for improving data freshness"""
        recommendations = []
        
        if not has_current_year:
            recommendations.append(f"Add current {self.current_year} data and statistics")
        
        stale_data = [d for d in date_analysis if d['freshness']['category'] in ['stale', 'outdated']]
        if stale_data:
            recommendations.append(f"Update {len(stale_data)} outdated data points with current information")
            for data in stale_data[:3]:  # Show first 3
                recommendations.append(f"  - Replace '{data['text']}' with {self.current_year} data")
        
        # Check for specific data types
        market_data = [d for d in date_analysis if d['data_type'] == 'market_data']
        if market_data and not any(d['age_days'] <= 30 for d in market_data):
            recommendations.append("Add current market data (within last 30 days)")
        
        allocation_data = [d for d in date_analysis if d['data_type'] == 'allocation_data']
        if not allocation_data:
            recommendations.append(f"Include recent allocation data from {self.current_year}")
        
        if not any(d['freshness']['category'] == 'real_time' for d in date_analysis):
            recommendations.append("Include at least one real-time/very recent data point")
        
        return recommendations
    
    def extract_source_dates(self, source_url: str, source_text: str) -> Dict[str, Any]:
        """Extract publication date from source"""
        # Look for common date patterns in URLs
        url_date_patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',  # /2024/01/15/
            r'/(\d{4})-(\d{2})-(\d{2})',   # /2024-01-15
            r'/(\d{4})(\d{2})(\d{2})',     # /20240115
        ]
        
        for pattern in url_date_patterns:
            match = re.search(pattern, source_url)
            if match:
                year, month, day = match.groups()
                return {
                    'date': datetime(int(year), int(month), int(day)),
                    'source': 'url',
                    'confidence': 'high'
                }
        
        # Look for publication dates in text
        pub_patterns = [
            r'published:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'updated:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        for pattern in pub_patterns:
            match = re.search(pattern, source_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Parse the date
                try:
                    date = datetime.strptime(date_str, '%m-%d-%Y')
                except:
                    try:
                        date = datetime.strptime(date_str, '%m/%d/%Y')
                    except:
                        continue
                
                return {
                    'date': date,
                    'source': 'text',
                    'confidence': 'medium'
                }
        
        return {
            'date': None,
            'source': 'not_found',
            'confidence': 'none'
        }


# Standalone validation function for use in pipeline
def validate_data_freshness(article_text: str, strict: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that all data in article is current
    
    Args:
        article_text: The article content to validate
        strict: If True, requires all data to be acceptable
        
    Returns:
        Tuple of (is_valid, validation_results)
    """
    validator = DataFreshnessValidator()
    results = validator.validate_article_freshness(article_text)
    
    if strict:
        is_valid = results['is_fresh'] and results['has_current_year_data']
    else:
        is_valid = results['has_recent_data']
    
    return is_valid, results