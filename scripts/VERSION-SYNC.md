# Version Synchronization

The version bump scripts ensure that the Chrome Extension and StreamController Plugin versions are **always kept in sync**.

## Files That Are Synchronized

When you bump the version, all three files are updated automatically:

1. `chrome_extension/manifest.json` - Chrome Extension manifest
2. `chrome_extension/package.json` - Chrome Extension package info
3. `manifest.json` - StreamController Plugin manifest (in project root)

## How It Works

### Automatic Sync During Version Bump

```bash
cd chrome_extension
npm run version:patch   # or :minor, :major
```

**Output:**
```
🔼 Bumping version (patch)...

📋 Files to update:
   - Chrome Extension manifest.json
   - Chrome Extension package.json
   - StreamController Plugin manifest.json

📌 Version: 1.0.0 → 1.0.1

✅ Updated: Chrome Extension manifest.json
✅ Updated: Chrome Extension package.json
✅ Updated: StreamController Plugin manifest.json

✅ Version bump complete!

🔍 Verifying version sync...
   ✅ Chrome Extension manifest.json: 1.0.1
   ✅ Chrome Extension package.json: 1.0.1
   ✅ StreamController Plugin manifest.json: 1.0.1

✅ All versions synchronized to v1.0.1
```

### Manual Sync Check

If you ever need to verify or manually sync versions:

```bash
npm run version:sync
# or directly:
./scripts/sync-versions.sh
```

This will:
1. Read the version from `chrome_extension/manifest.json` (source of truth)
2. Update other files to match
3. Verify all versions are synchronized

## Why This Matters

Keeping versions in sync ensures:

- **Chrome Extension** and **StreamController Plugin** always have matching versions
- Users can easily verify they have compatible versions installed
- GitHub releases contain matching version numbers for both packages
- Chrome Web Store and plugin directory show the same version

## Version Strategy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (1.X.0): New features, backwards compatible
- **PATCH** (1.0.X): Bug fixes, backwards compatible

## Troubleshooting

### Versions Out of Sync

If you manually edited a version and they're out of sync:

```bash
cd chrome_extension
npm run version:sync
```

This will use the Chrome Extension manifest as the source of truth and update all other files.

### Verification Failed

If the bump script reports a sync failure:

```
❌ Version sync failed! Not all files have matching versions.
```

1. Check if any file is locked or has permission issues
2. Manually check versions in all three files
3. Run `npm run version:sync` to force sync
4. Try the bump again

## During CI/CD

The GitHub Actions workflow automatically:
1. Detects version changes in `chrome_extension/manifest.json`
2. Uses that version for packaging both the extension and plugin
3. Creates GitHub releases with the synchronized version number

All packages released together will always have matching versions.
