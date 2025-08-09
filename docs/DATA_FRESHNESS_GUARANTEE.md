# Data Freshness Guarantee System

## How We Ensure 100% Up-to-Date Data

The Dakota Learning Center system implements multiple layers of validation to ensure all data and facts are current and accurate.

## 1. **Automated Data Freshness Validation**

### DataFreshnessValidator Class
- Extracts all dates from article content
- Categorizes data by type (market, allocation, regulatory, general)
- Applies specific freshness rules:
  - **Market Data**: Must be within 30 days
  - **Allocation Data**: Must be within 90 days
  - **Regulatory Data**: Must be within 60 days
  - **General Data**: Must be within 180 days

### Key Features:
- Pattern matching for various date formats
- Contextual data type determination
- Age calculation in days
- Specific recommendations for outdated data

## 2. **Multi-Stage Enforcement**

### Stage 1: Research Phase
**Web Researcher Requirements:**
- Searches specifically for current year data (2025)
- Rejects sources without clear publication dates
- Prioritizes real-time and daily updated sources
- Focuses on current quarter (Q4 2024, Q1 2025)

### Stage 2: Content Creation
**Content Writer Requirements:**
- Must include dates with all statistics
- Uses timestamp phrases ("As of January 2025")
- Includes publication dates in all citations
- Starts articles with current context

### Stage 3: Fact Verification
**Enhanced Fact Checker:**
- Validates every date reference
- Checks age of all data points
- Enforces maximum age limits by data type
- Rejects articles without current year data

### Stage 4: Final Validation
**Dakota Fact Checker:**
- Zero tolerance for vague timeframes
- Requires specific dates for all data
- Validates source publication dates
- Final approval contingent on data freshness

## 3. **Technical Implementation**

### Validation Process:
```python
# For each article:
1. Extract all date references
2. Parse dates to datetime objects
3. Calculate age in days
4. Categorize by data type
5. Apply freshness rules
6. Generate recommendations
7. Reject if not fresh
```

### Integration Points:
- `src/tools/data_freshness_validator.py` - Core validation logic
- `src/tools/fact_verification.py` - Integrated freshness checks
- `src/config_enhanced.py` - Configurable age limits
- All agent prompts - Freshness requirements

## 4. **Configuration**

### Customizable Limits:
```python
MAX_AGE_MARKET_DATA_DAYS = 30
MAX_AGE_ALLOCATION_DATA_DAYS = 90
MAX_AGE_GENERAL_DATA_DAYS = 180
REQUIRE_CURRENT_YEAR_DATA = True
REQUIRE_DATED_CITATIONS = True
```

## 5. **Quality Reports**

Each article includes freshness metrics:
- Total dates found
- Age analysis for each data point
- Freshness category distribution
- Specific recommendations for updates

## 6. **Automatic Rejection Criteria**

Articles are automatically rejected if:
- No current year (2025) data present
- Market data older than 30 days
- Allocation data older than 90 days
- Sources lack publication dates
- Citations use vague timeframes

## 7. **Best Practices Enforced**

### For Research:
- Search queries include year/quarter
- Sources must have recent publication dates
- Multiple searches for time-sensitive data

### For Writing:
- Every statistic includes "(as of [date])"
- Citations format: "[Source, Date](URL)"
- Opening establishes temporal context
- Quarterly/annual data clearly labeled

### For Validation:
- Automated extraction of all dates
- Cross-reference with source dates
- Contextual freshness requirements
- Clear rejection reasons provided

## 8. **Continuous Improvement**

The system provides:
- Detailed freshness reports
- Specific update recommendations
- Tracking of data age patterns
- Automated alerts for stale data

## Result: 100% Current, Verified Data

This comprehensive system ensures:
- ✅ All market data is real-time or near real-time
- ✅ Allocation data reflects current quarter activity
- ✅ No outdated statistics slip through
- ✅ Clear temporal context for all information
- ✅ Readers can trust data currency
- ✅ Dakota's reputation for accuracy is maintained

The multi-layered approach catches outdated data at every stage, from initial research through final validation, guaranteeing that Dakota Learning Center articles always contain the most current information available.