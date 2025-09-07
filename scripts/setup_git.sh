#!/bin/bash

# Git setup script for Profit Tracker AI

echo "🚀 Setting up Git repository for Profit Tracker AI..."

# Initialize git if not already
if [ ! -d .git ]; then
    git init
    echo "✅ Initialized Git repository"
fi

# Add all files
git add .
echo "✅ Added all files to staging"

# Create initial commit
git commit -m "Initial commit: Profit Tracker AI - Receipt processing and profit tracking for trade businesses

- Complete Flask application with authentication and multi-tenancy
- AI-powered receipt processing using Anthropic Claude Vision
- SMS integration via Twilio for field workers
- Profit analytics and pattern detection
- Export functionality (CSV, PDF, ZIP)
- Production-ready with Docker and Heroku support
- Comprehensive test suite and documentation"

echo "✅ Created initial commit"

# Instructions for user
echo ""
echo "📝 Next steps:"
echo "1. Create a new repository on GitHub: https://github.com/new"
echo "   - Name: profit-tracker-ai"
echo "   - Description: AI-powered receipt processing and profit tracking for trade businesses"
echo "   - Make it public or private as desired"
echo ""
echo "2. Add the remote origin:"
echo "   git remote add origin https://github.com/WeberG619/profit-tracker-ai.git"
echo ""
echo "3. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "4. Deploy to Heroku:"
echo "   - Click the 'Deploy to Heroku' button in the README"
echo "   - Or use: heroku create your-app-name && git push heroku main"
echo ""
echo "5. Configure environment variables in your deployment"
echo ""
echo "🎉 Repository structure is complete and ready for deployment!"