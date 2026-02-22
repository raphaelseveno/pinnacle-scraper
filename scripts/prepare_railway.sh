#!/bin/bash
# Prepare Project Acheron for Railway Deployment

set -e

echo "🚀 Preparing Project Acheron for Railway Deployment"
echo "=================================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Project Acheron"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if GitHub remote exists
if ! git remote | grep -q "origin"; then
    echo ""
    echo "⚠️  No GitHub remote found."
    echo "Please create a GitHub repository and run:"
    echo ""
    echo "    git remote add origin https://github.com/YOUR_USERNAME/pinnacle-scrapper.git"
    echo "    git branch -M main"
    echo "    git push -u origin main"
    echo ""
else
    echo "✅ GitHub remote configured"
fi

# Verify required files exist
echo ""
echo "🔍 Verifying deployment files..."

required_files=(
    "Dockerfile.railway"
    "railway.toml"
    "railway.json"
    "config.railway.yaml"
    "src/mcp_server.py"
    "requirements.txt"
)

all_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        all_present=false
    fi
done

if [ "$all_present" = true ]; then
    echo ""
    echo "✅ All deployment files present!"
else
    echo ""
    echo "❌ Some deployment files are missing. Please check the errors above."
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Ready for Railway Deployment!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Push to GitHub (if not already done):"
echo "   git push origin main"
echo ""
echo "2. Deploy to Railway:"
echo "   Visit: https://railway.app/new"
echo "   Select: 'Deploy from GitHub repo'"
echo "   Choose your repository"
echo ""
echo "3. Add Redis service:"
echo "   In Railway project → New → Database → Redis"
echo ""
echo "4. Configure environment variables:"
echo "   PINNACLE_USERNAME=your_username"
echo "   PINNACLE_PASSWORD=your_password"
echo "   PACKETSTREAM_API_KEY=your_api_key"
echo "   NTFY_TOPIC=your-unique-topic"
echo ""
echo "5. See full guide: RAILWAY_SETUP.md"
echo ""
