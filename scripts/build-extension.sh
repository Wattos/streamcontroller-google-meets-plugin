#!/bin/bash
set -e

echo "🔨 Building Chrome extension..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXTENSION_DIR="$PROJECT_ROOT/chrome_extension"

# Navigate to extension directory
cd "$EXTENSION_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build with Vite
echo "📦 Building with Vite..."
npm run build

# Verify build output
if [ ! -d "dist" ]; then
    echo "❌ Build failed: dist directory not found"
    exit 1
fi

echo "✅ Chrome extension built successfully!"
echo "📁 Build output: $EXTENSION_DIR/dist"
