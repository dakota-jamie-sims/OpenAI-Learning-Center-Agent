# Dakota Learning Center Articles

This directory contains all generated Dakota Learning Center articles organized by date and topic.

## Directory Structure

Each article is saved in a dated subfolder with the following format:
```
YYYY-MM-DD-[topic-slug]/
├── dakota-article.md      # Main article (1,750+ words)
├── dakota-metadata.md     # SEO metadata and metrics
├── dakota-social.md       # Social media content (all platforms)
├── dakota-summary.md      # Executive summary
└── proof_pack.json        # Evidence package (if enabled)
```

## Example Structure
```
Dakota Learning Center Articles/
├── 2025-01-15-benefits-of-index-fund-investing/
│   ├── dakota-article.md
│   ├── dakota-metadata.md
│   ├── dakota-social.md
│   └── dakota-summary.md
├── 2025-01-16-emerging-markets-opportunities/
│   ├── dakota-article.md
│   ├── dakota-metadata.md
│   ├── dakota-social.md
│   └── dakota-summary.md
└── README.md
```

## Quality Standards

All articles in this directory have passed:
- ✅ Minimum 1,750 words
- ✅ 10+ verified sources with working URLs
- ✅ Mandatory fact-checking (100% URL verification)
- ✅ Template compliance validation
- ✅ No vague references or unsourced claims
- ✅ Dakota article references with verified URLs

## Usage

To generate a new article:
```bash
cd /path/to/dakota_openai_agents
python run.py "Your Article Topic Here"
```

Articles will automatically be saved in dated subfolders within this directory.

## Configuration

To change the output directory, set the environment variable:
```bash
export DAKOTA_OUTPUT_DIR="/your/custom/path"
```

Or update the `.env` file:
```
DAKOTA_OUTPUT_DIR=/your/custom/path
```