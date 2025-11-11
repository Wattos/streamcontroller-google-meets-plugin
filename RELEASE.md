# Release Guide

Complete guide for building and releasing the Google Meet StreamController plugin.

## Quick Reference

```bash
# Bump version and create release packages
cd chrome_extension
npm run version:patch    # or :minor, :major
npm run release

# Or do it all in one step
npm run release:patch    # Bump patch + build + package
npm run release:minor    # Bump minor + build + package
npm run release:major    # Bump major + build + package
```

## Automated Release Process

The project uses GitHub Actions for automated releases. When you merge a PR with a version bump:

### What Happens Automatically

1. **Detect Version Change**: CI checks if version changed in `chrome_extension/manifest.json`
2. **Build Extension**: Chrome extension is built using Vite
3. **Package Files**: Creates two zip files:
   - `google-meet-streamcontroller-extension-{version}.zip`
   - `google-meet-streamcontroller-plugin-{version}.zip`
4. **Publish to Chrome Web Store**: Extension is uploaded and auto-published
5. **Create GitHub Release**: Creates release with both packages attached

### Workflow Trigger

The workflow runs on:
- Push to `main` branch (after PR merge)
- Manual dispatch from GitHub Actions UI

## Manual Release Steps

### 1. Bump Version

```bash
cd chrome_extension

# Choose semantic version bump
npm run version:patch   # Bug fixes (1.0.0 → 1.0.1)
npm run version:minor   # New features (1.0.0 → 1.1.0)
npm run version:major   # Breaking changes (1.0.0 → 2.0.0)
```

This updates version in **all three files** to keep them synchronized:
- `chrome_extension/manifest.json` (Chrome Extension)
- `chrome_extension/package.json` (Chrome Extension)
- `manifest.json` (StreamController Plugin)

The script automatically verifies all versions match after updating.

### 2. Commit and Push

```bash
git add .
git commit -m "chore: bump version to v1.0.1"
git push origin your-branch
```

### 3. Create PR and Merge

- Create pull request
- Review changes
- Merge to main
- **GitHub Actions takes over automatically**

## Local Testing

Test the full release process locally before pushing:

```bash
cd chrome_extension

# Build and package everything
npm run release

# Output files appear in project root:
# - google-meet-streamcontroller-extension-{version}.zip
# - google-meet-streamcontroller-plugin-{version}.zip
# - chrome-extension.zip (for Chrome Web Store)
```

### Test the Packages

#### Test Chrome Extension
```bash
# Unzip the extension
unzip google-meet-streamcontroller-extension-1.0.1.zip -d test-extension

# Load in Chrome
# 1. Go to chrome://extensions
# 2. Enable Developer mode
# 3. Click "Load unpacked"
# 4. Select test-extension/
```

#### Test StreamController Plugin
```bash
# Extract to plugins directory
unzip google-meet-streamcontroller-plugin-1.0.1.zip -d ~/.local/share/StreamController/plugins/

# Restart StreamController
```

## Available Scripts

### Version Management

| Command | Description |
|---------|-------------|
| `npm run version:patch` | Bump patch version (1.0.0 → 1.0.1) |
| `npm run version:minor` | Bump minor version (1.0.0 → 1.1.0) |
| `npm run version:major` | Bump major version (1.0.0 → 2.0.0) |
| `npm run version:sync` | Sync versions across all manifest files |

### Build & Package

| Command | Description |
|---------|-------------|
| `npm run build` | Build Chrome extension with Vite |
| `npm run package` | Package Chrome extension as .zip |
| `npm run release` | Build + package extension and plugin |

### Combined Release

| Command | Description |
|---------|-------------|
| `npm run release:patch` | Bump patch + build + package |
| `npm run release:minor` | Bump minor + build + package |
| `npm run release:major` | Bump major + build + package |

## Scripts Directory

Individual scripts are available in `scripts/`:

| Script | Purpose |
|--------|---------|
| `build-extension.sh` | Build Chrome extension |
| `package-extension.sh` | Package Chrome extension as .zip |
| `package-plugin.sh` | Package StreamController plugin |
| `release.sh` | Full release process (build + package both) |
| `bump-version.js` | Update version in all manifest files |
| `sync-versions.sh` | Ensure versions are synced |

## GitHub Secrets Setup

For automated Chrome Web Store publishing, add these secrets to your GitHub repository:

1. Go to: **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:

| Secret | Description |
|--------|-------------|
| `CHROME_EXTENSION_ID` | Your extension ID from Chrome Web Store |
| `CHROME_CLIENT_ID` | OAuth2 client ID from Google Cloud |
| `CHROME_CLIENT_SECRET` | OAuth2 client secret from Google Cloud |
| `CHROME_REFRESH_TOKEN` | OAuth2 refresh token |

See `scripts/setup-chrome-credentials.md` for detailed instructions.

## Troubleshooting

### Version Bump Not Detected

If GitHub Actions doesn't detect your version bump:
- Ensure version changed in `chrome_extension/manifest.json`
- Check workflow logs in GitHub Actions
- Use "Run workflow" button with "force release" option

### Build Fails

```bash
# Clean and rebuild
cd chrome_extension
rm -rf node_modules dist
npm install
npm run build
```

### Package Errors

Ensure scripts are executable:
```bash
chmod +x scripts/*.sh scripts/bump-version.js
```

### Chrome Web Store Upload Fails

- Verify secrets are set correctly in GitHub
- Check token hasn't expired
- Ensure extension ID matches
- Review Chrome Web Store dashboard for issues

## Release Checklist

Before merging a release PR:

- [ ] Version bumped in all manifest files
- [ ] CHANGELOG updated (if applicable)
- [ ] Changes tested locally
- [ ] Chrome extension builds without errors
- [ ] Plugin packages without errors
- [ ] GitHub secrets configured
- [ ] Ready to publish to Chrome Web Store

## Manual Chrome Web Store Upload

If automated upload fails, manually upload:

1. Build and package:
   ```bash
   cd chrome_extension
   npm run build
   npm run package
   ```

2. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
3. Click on your extension
4. Click "Upload new package"
5. Upload `chrome-extension.zip`
6. Fill in release notes
7. Click "Publish"

## Force Release

To force a release without version bump:

1. Go to GitHub repository
2. Click "Actions" tab
3. Select "Release" workflow
4. Click "Run workflow"
5. Check "Force release" option
6. Click "Run workflow"

## Release Notes

GitHub Actions automatically generates release notes from commits. For better release notes:

- Use conventional commits: `feat:`, `fix:`, `chore:`, etc.
- Write clear commit messages
- Reference issues: `fixes #123`

## Version Strategy

Follow semantic versioning:

- **MAJOR** (X.0.0): Breaking changes, major UI overhaul
- **MINOR** (1.X.0): New features, backwards compatible
- **PATCH** (1.0.X): Bug fixes, minor improvements

## Support

For issues with the release process:
- Check [GitHub Actions logs](../../actions)
- Review `scripts/setup-chrome-credentials.md`
- Open an issue on GitHub
