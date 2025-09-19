#!/bin/bash
# Orchid Continuum Partner Connect Setup Script

set -e

echo "🌺 Setting up Orchid Continuum Partner Connect..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if Node.js is available  
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

echo "✅ Python and Node.js found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build widgets
echo "📦 Installing Node.js dependencies..."
cd apps/widgets
npm install

echo "🔨 Building widgets..."
npm run build

# Return to root
cd ../..

# Initialize database and create partners
echo "🔑 Generating partner keys and documentation..."
cd scripts
python gen_partner_key.py --seed-defaults

# Return to root
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Next steps:"
echo "  1. Start the API server: cd services/api && python main.py"
echo "  2. Open demo page: http://localhost:8000/demo.html"  
echo "  3. Check partner docs: docs/partners/"
echo ""
echo "📚 Partner Documentation Generated:"
echo "  - gary-yong-gee: docs/partners/gary-yong-gee/"
echo "  - roger: docs/partners/roger/"
echo ""
echo "🔗 Demo includes working widgets with:"
echo "  - AI-powered search across orchid collections"
echo "  - Interactive maps with geoprivacy controls"
echo "  - Phenology charts showing flowering patterns"
echo ""