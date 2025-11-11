#!/bin/bash
set -e

echo "🔄 Syncing versions across all manifest files..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Read version from source of truth (chrome extension manifest)
SOURCE_FILE="$PROJECT_ROOT/chrome_extension/manifest.json"
VERSION=$(jq -r '.version' "$SOURCE_FILE")

echo "📌 Source version: $VERSION (from chrome_extension/manifest.json)"
echo ""
echo "📋 Files to sync:"
echo "   - chrome_extension/package.json"
echo "   - manifest.json (StreamController Plugin)"
echo ""

# Update chrome extension package.json
PACKAGE_JSON="$PROJECT_ROOT/chrome_extension/package.json"
if [ -f "$PACKAGE_JSON" ]; then
    CURRENT=$(jq -r '.version' "$PACKAGE_JSON")
    if [ "$CURRENT" != "$VERSION" ]; then
        jq ".version = \"$VERSION\"" "$PACKAGE_JSON" > "$PACKAGE_JSON.tmp"
        mv "$PACKAGE_JSON.tmp" "$PACKAGE_JSON"
        echo "✅ Updated: chrome_extension/package.json ($CURRENT → $VERSION)"
    else
        echo "✓ Already synced: chrome_extension/package.json"
    fi
fi

# Update StreamController plugin manifest.json
PLUGIN_MANIFEST="$PROJECT_ROOT/manifest.json"
if [ -f "$PLUGIN_MANIFEST" ]; then
    CURRENT=$(jq -r '.version' "$PLUGIN_MANIFEST")
    if [ "$CURRENT" != "$VERSION" ]; then
        jq ".version = \"$VERSION\"" "$PLUGIN_MANIFEST" > "$PLUGIN_MANIFEST.tmp"
        mv "$PLUGIN_MANIFEST.tmp" "$PLUGIN_MANIFEST"
        echo "✅ Updated: manifest.json (StreamController Plugin) ($CURRENT → $VERSION)"
    else
        echo "✓ Already synced: manifest.json (StreamController Plugin)"
    fi
fi

echo ""
echo "🔍 Verifying all versions..."
echo ""

# Verify all versions match
ALL_SYNCED=true

EXT_MANIFEST_VER=$(jq -r '.version' "$PROJECT_ROOT/chrome_extension/manifest.json")
echo "   Extension manifest.json: $EXT_MANIFEST_VER"
if [ "$EXT_MANIFEST_VER" != "$VERSION" ]; then ALL_SYNCED=false; fi

PKG_VER=$(jq -r '.version' "$PROJECT_ROOT/chrome_extension/package.json")
echo "   Extension package.json:  $PKG_VER"
if [ "$PKG_VER" != "$VERSION" ]; then ALL_SYNCED=false; fi

PLUGIN_VER=$(jq -r '.version' "$PROJECT_ROOT/manifest.json")
echo "   Plugin manifest.json:    $PLUGIN_VER"
if [ "$PLUGIN_VER" != "$VERSION" ]; then ALL_SYNCED=false; fi

echo ""
if [ "$ALL_SYNCED" = true ]; then
    echo "✅ All versions synchronized to: v$VERSION"
else
    echo "❌ Version mismatch detected!"
    exit 1
fi
