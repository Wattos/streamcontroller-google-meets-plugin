#!/bin/bash
set -e

echo "📦 Packaging StreamController plugin..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Get version from manifest
VERSION=$(jq -r '.version' "$PROJECT_ROOT/manifest.json")
echo "📌 Version: $VERSION"

# Create output filename
OUTPUT_FILE="$PROJECT_ROOT/google-meet-streamcontroller-plugin-${VERSION}.zip"

# Remove old zip if exists
if [ -f "$OUTPUT_FILE" ]; then
    echo "🗑️  Removing old package..."
    rm "$OUTPUT_FILE"
fi

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PLUGIN_DIR="$TEMP_DIR/com_github_wattos_google_meet"

echo "📋 Copying plugin files..."
mkdir -p "$PLUGIN_DIR"

# Copy necessary directories and files
cp -r "$PROJECT_ROOT/actions" "$PLUGIN_DIR/"
cp -r "$PROJECT_ROOT/backend" "$PLUGIN_DIR/"
cp -r "$PROJECT_ROOT/assets" "$PLUGIN_DIR/"
cp -r "$PROJECT_ROOT/store" "$PLUGIN_DIR/"
cp -r "$PROJECT_ROOT/docs" "$PLUGIN_DIR/"

# Copy root files
cp "$PROJECT_ROOT/main.py" "$PLUGIN_DIR/"
cp "$PROJECT_ROOT/manifest.json" "$PLUGIN_DIR/"
cp "$PROJECT_ROOT/__install__.py" "$PLUGIN_DIR/"
cp "$PROJECT_ROOT/LICENSE" "$PLUGIN_DIR/"
cp "$PROJECT_ROOT/README.md" "$PLUGIN_DIR/"
cp "$PROJECT_ROOT/attribution.json" "$PLUGIN_DIR/"

# Copy Chrome extension dist (built version only)
if [ -d "$PROJECT_ROOT/chrome_extension/dist" ]; then
    echo "📦 Including built Chrome extension..."
    mkdir -p "$PLUGIN_DIR/chrome_extension"
    cp -r "$PROJECT_ROOT/chrome_extension/dist" "$PLUGIN_DIR/chrome_extension/"
    cp "$PROJECT_ROOT/chrome_extension/manifest.json" "$PLUGIN_DIR/chrome_extension/"
    cp "$PROJECT_ROOT/chrome_extension/README.md" "$PLUGIN_DIR/chrome_extension/"
    cp "$PROJECT_ROOT/chrome_extension/INSTALL.md" "$PLUGIN_DIR/chrome_extension/"
    cp -r "$PROJECT_ROOT/chrome_extension/icons" "$PLUGIN_DIR/chrome_extension/"
    cp -r "$PROJECT_ROOT/chrome_extension/popup" "$PLUGIN_DIR/chrome_extension/"
fi

# Clean up unnecessary files
echo "🧹 Cleaning up..."
find "$PLUGIN_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PLUGIN_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$PLUGIN_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$PLUGIN_DIR" -name "*.map" -delete 2>/dev/null || true

# Remove backend virtual environment and cache
rm -rf "$PLUGIN_DIR/backend/.venv" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/backend/__pycache__" 2>/dev/null || true
rm -rf "$PLUGIN_DIR/backend/pairing_data.json" 2>/dev/null || true

# Create zip file
echo "📦 Creating zip archive..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_FILE" com_github_wattos_google_meet -x "*.DS_Store" "*.pyc" "*__pycache__*"

# Cleanup temp directory
rm -rf "$TEMP_DIR"

echo "✅ Plugin packaged successfully!"
echo "📁 Output: $OUTPUT_FILE"
echo "📊 Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "📋 Package contents:"
echo "  - StreamController plugin files"
echo "  - Pre-built Chrome extension (in chrome_extension/dist/)"
echo "  - Documentation and assets"
