#!/bin/bash

# Force refresh StorySign application with cache clearing
echo "🧹 Force refreshing StorySign application..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Kill any existing processes
echo -e "${YELLOW}🛑 Stopping existing processes...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Clear frontend build cache
echo -e "${YELLOW}🧹 Clearing frontend cache...${NC}"
cd frontend
rm -rf build/ dist/ .cache/ coverage/
echo -e "${GREEN}✅ Frontend cache cleared${NC}"

# Reinstall dependencies to ensure fresh packages
echo -e "${YELLOW}📦 Reinstalling frontend dependencies...${NC}"
npm install
echo -e "${GREEN}✅ Dependencies reinstalled${NC}"

cd ..

echo -e "${BLUE}🚀 Starting fresh application...${NC}"
echo -e "${YELLOW}💡 After the app starts, please:${NC}"
echo -e "   1. Open browser in incognito/private mode"
echo -e "   2. Or press Ctrl+Shift+R (hard refresh) in your browser"
echo -e "   3. Or open Developer Tools > Application > Storage > Clear storage"
echo ""

# Start the application
./run_full_app.sh