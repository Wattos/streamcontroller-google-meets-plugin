#!/bin/bash
set -e

echo "🚀 Starting release process..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Get version
VERSION=$(jq -r '.version' "$PROJECT_ROOT/chrome_extension/manifest.json")
echo "📌 Release version: $VERSION"
echo ""

# Build Chrome extension
echo "===================================="
echo "🔨 Step 1/3: Building Chrome extension"
echo "===================================="
"$SCRIPT_DIR/build-extension.sh"
echo ""

# Package Chrome extension
echo "===================================="
echo "📦 Step 2/3: Packaging Chrome extension"
echo "===================================="
"$SCRIPT_DIR/package-extension.sh"
echo ""

# Package StreamController plugin
echo "===================================="
echo "📦 Step 3/3: Packaging StreamController plugin"
echo "===================================="
"$SCRIPT_DIR/package-plugin.sh"
echo ""

echo "===================================="
echo "✅ Release build complete!"
echo "===================================="
echo ""
echo "📦 Generated files:"
echo "  - google-meet-streamcontroller-extension-${VERSION}.zip"
echo "  - google-meet-streamcontroller-plugin-${VERSION}.zip"
echo "  - chrome-extension.zip (for Chrome Web Store)"
echo ""
echo "📝 Next steps:"
echo "  1. Test the packages locally"
echo "  2. Upload chrome-extension.zip to Chrome Web Store (or use publish script)"
echo "  3. Create GitHub release with both zip files"
echo ""
echo "💡 For automated release via CI/CD:"
echo "  1. Commit and push your changes"
echo "  2. The GitHub Actions workflow will automatically:"
echo "     - Build and package"
echo "     - Publish to Chrome Web Store"
echo "     - Create GitHub Release"
