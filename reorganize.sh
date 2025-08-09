#!/bin/bash
# Script to reorganize the Dakota OpenAI Agents project structure

echo "🔧 Reorganizing Dakota OpenAI Agents project structure..."

# Create new clean structure
mkdir -p clean_structure/{src,docs,knowledge_base,templates,output,tests}

# Move source code
echo "📦 Moving source code..."
cp -r dakota_openai_agents/src/* clean_structure/src/ 2>/dev/null
cp dakota_openai_agents/run.py clean_structure/src/ 2>/dev/null
cp dakota_openai_agents/requirements.txt clean_structure/ 2>/dev/null
cp dakota_openai_agents/.env.example clean_structure/ 2>/dev/null

# Consolidate documentation
echo "📚 Consolidating documentation..."
cp README_CONSOLIDATED.md clean_structure/README.md
cp MIGRATION_GUIDE.md clean_structure/docs/
cp TROUBLESHOOTING.md clean_structure/docs/
cp -r runs/2025-08-08-benefits-of-index-fund-investing/*.md clean_structure/docs/ 2>/dev/null
cp dakota_openai_agents/*.md clean_structure/docs/ 2>/dev/null
cp dakota_openai_agents/Learnung\ Center\ Agent/CRITICAL-VALIDATION-REQUIREMENTS.md clean_structure/docs/ 2>/dev/null

# Move knowledge base
echo "🧠 Moving knowledge base..."
cp -r dakota_openai_agents/knowledge_base/* clean_structure/knowledge_base/ 2>/dev/null

# Move templates
echo "📝 Moving templates..."
cp -r dakota_openai_agents/Learnung\ Center\ Agent/templates/* clean_structure/templates/ 2>/dev/null

# Setup output directory
echo "📁 Setting up output directory..."
mkdir -p "clean_structure/output/Dakota Learning Center Articles"
cp "Dakota Learning Center Articles/README.md" "clean_structure/output/Dakota Learning Center Articles/" 2>/dev/null

# Move test files
echo "🧪 Moving test files..."
cp dakota_openai_agents/test*.py clean_structure/tests/ 2>/dev/null

# Create gitignore
echo "🚫 Creating .gitignore..."
cat > clean_structure/.gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Output
output/Dakota Learning Center Articles/*
!output/Dakota Learning Center Articles/README.md

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/
EOF

echo "✅ Reorganization complete!"
echo ""
echo "📋 New structure created in: clean_structure/"
echo ""
echo "Next steps:"
echo "1. Review the new structure: ls -la clean_structure/"
echo "2. Test it works: cd clean_structure && python src/run.py 'test topic'"
echo "3. If satisfied, rename: mv clean_structure dakota-openai-agents"
echo "4. Remove old directories: rm -rf dakota_openai_agents runs reorganized"