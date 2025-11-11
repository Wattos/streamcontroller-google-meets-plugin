#!/bin/bash
set -e

echo "📦 Packaging Chrome extension..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXTENSION_DIR="$PROJECT_ROOT/chrome_extension"
DIST_DIR="$EXTENSION_DIR/dist"

# Get version from manifest
VERSION=$(jq -r '.version' "$EXTENSION_DIR/manifest.json")
echo "📌 Version: $VERSION"

# Create output filename
OUTPUT_FILE="$PROJECT_ROOT/google-meet-streamcontroller-extension-${VERSION}.zip"

# Check if dist directory exists
if [ ! -d "$DIST_DIR" ]; then
    echo "❌ Error: dist directory not found. Run build-extension.sh first."
    exit 1
fi

# Remove old zip if exists
if [ -f "$OUTPUT_FILE" ]; then
    echo "🗑️  Removing old package..."
    rm "$OUTPUT_FILE"
fi

# Create zip file
echo "📦 Creating zip archive..."
cd "$DIST_DIR"
zip -r "$OUTPUT_FILE" . -x "*.DS_Store" "*.map"

# Also create a simple name for Chrome Web Store upload
cp "$OUTPUT_FILE" "$PROJECT_ROOT/chrome-extension.zip"

echo "✅ Extension packaged successfully!"
echo "📁 Output: $OUTPUT_FILE"
echo "📁 Chrome Web Store ready: $PROJECT_ROOT/chrome-extension.zip"
echo "📊 Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
