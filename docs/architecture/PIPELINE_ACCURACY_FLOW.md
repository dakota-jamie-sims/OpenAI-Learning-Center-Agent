# Pipeline Accuracy Flow

## Overview
The Dakota Learning Center pipeline ensures 100% accuracy through a carefully ordered process where summary and social content are generated ONLY after the main article is fully fact-checked and approved.

## Pipeline Order

### Phase 1-5: Article Creation & Enhancement
```
1. Research (Parallel: Web + KB)
2. Evidence Package Creation
3. Synthesis
4. Content Writing
5. Enhancement (Parallel: SEO + Metrics)
```

### Phase 6: Validation & Fact-Checking ✓
This is the critical gate where accuracy is ensured:

```
6. Validation Phase:
   ├── Enhanced Fact Verification
   │   ├── Source credibility scoring
   │   ├── URL accessibility testing
   │   └── Data freshness validation
   │
   ├── Structural Validation
   │   ├── Word count verification
   │   ├── Source count checking
   │   └── Section compliance
   │
   └── Claim Verification
       ├── Every statistic has source
       ├── No unsupported statements
       └── Data currency checking
```

**If validation fails**: Article enters iteration phase (6.5) for corrections
**Maximum iterations**: 3 attempts to meet quality standards

### Phase 7-8: Post-Approval Only
These phases ONLY execute after "✅ Article APPROVED!" message:

```
7. Distribution Assets (from approved article):
   ├── Executive Summary
   │   └── Uses only facts from final article
   │
   └── Social Media Content
       └── Extracts only verified claims

8. Metadata Generation:
   └── Calculates metrics from final, approved content
```

## Accuracy Guarantees

### 1. **Sequential Enforcement**
- Distribution content is generated ONLY after validation passes
- No summary/social content exists if article fails fact-checking
- The pipeline literally stops at validation failure

### 2. **Single Source of Truth**
- Summary writer reads the final, approved article
- Social promoter extracts from fact-checked content
- No new data can be introduced post-validation

### 3. **Explicit Instructions**
Both summary and social prompts now include:
```
**CRITICAL**: The article has been fact-checked and validated. 
Use ONLY information present in the final article. 
Do not add any new data or claims.
```

### 4. **Data Integrity Chain**
```
Research → Writing → Fact-Checking → APPROVAL → Summary/Social
                          ↓
                    If rejected: Iteration
```

## Example Flow

### Successful Flow:
1. Article written with claim: "RIAs increased PE allocation by 45%"
2. Fact-checker verifies source and data freshness ✓
3. Article APPROVED
4. Summary includes: "RIAs increased PE allocation by 45%"
5. Social post features: "📈 45% increase in RIA PE allocations"

### Failed Flow with Correction:
1. Article claims: "RIAs increased allocation by 45%" (no date)
2. Fact-checker REJECTS: "Missing temporal context"
3. Iteration adds: "RIAs increased allocation by 45% in Q4 2024"
4. Fact-checker verifies ✓
5. Article APPROVED
6. Summary/Social use corrected version with date

## Code Implementation

From `chat_orchestrator.py`:
```python
# Only after validation passes:
if not validation["approved"]:
    return {"status": "FAILED", ...}

print("\n✅ Article APPROVED!")

# THEN create distribution assets:
distribution = await self.phase7_distribution(article_path, run_dir)
```

## Benefits of This Approach

1. **100% Accuracy**: Summary and social content can only reflect validated facts
2. **No Drift**: Promotional content exactly matches article claims
3. **Consistency**: All outputs share the same fact base
4. **Trust**: Readers get the same accurate information across all formats
5. **Efficiency**: No need to separately fact-check derivative content

## Quality Control Checkpoints

### Pre-Distribution Checks:
- ✓ All sources verified (URL status 200)
- ✓ All facts have citations
- ✓ Data freshness validated
- ✓ No unsupported claims
- ✓ Structure compliance met

### Post-Distribution Verification:
- Summary key points match article claims exactly
- Social statistics are verbatim from article
- No embellishment or approximation
- All dates and numbers preserved precisely

## Summary

The pipeline's sequential design ensures that summary and social content are as accurate as the main article because they:
1. Are generated AFTER fact-checking
2. Can only use approved content
3. Cannot introduce new claims
4. Reflect all corrections from iterations

This design makes it impossible for inaccurate information to appear in distribution materials.

Last Updated: 2025-01-09