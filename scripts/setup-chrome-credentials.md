# Setting Up Chrome Web Store Publishing Credentials

This guide walks you through obtaining the credentials needed for automated Chrome Web Store publishing.

## Prerequisites
- A Chrome Web Store developer account ($5 one-time fee)
- Your extension published (or draft) on the Chrome Web Store

## Step 1: Get Your Extension ID

1. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
2. Click on your extension
3. Copy the Extension ID from the URL or the dashboard
   - Format: `abcdefghijklmnopqrstuvwxyz123456`

## Step 2: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Chrome Web Store API:
   - Go to "APIs & Services" → "Enable APIs and Services"
   - Search for "Chrome Web Store API"
   - Click "Enable"

## Step 3: Create OAuth2 Credentials

1. In Google Cloud Console, go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: "Chrome Extension Publisher" (or similar)
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Not needed for Chrome Web Store
4. Create OAuth client:
   - Application type: "Desktop app"
   - Name: "Chrome Extension Publisher"
5. Copy the **Client ID** and **Client Secret**

## Step 4: Get Refresh Token

### Option A: Using chrome-webstore-upload (Recommended)

```bash
npm install -g chrome-webstore-upload-cli

# Run interactive setup
chrome-webstore-upload setup
```

Follow the prompts and it will:
1. Ask for your Client ID and Client Secret
2. Open a browser for you to authorize
3. Generate a refresh token

### Option B: Manual OAuth Flow

1. Create the authorization URL:
```
https://accounts.google.com/o/oauth2/auth?response_type=code&scope=https://www.googleapis.com/auth/chromewebstore&client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob
```

2. Visit the URL in a browser and authorize
3. Copy the authorization code
4. Exchange for refresh token:

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=YOUR_AUTH_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob"
```

5. Copy the `refresh_token` from the response

## Step 5: Add to GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these secrets:
   - `CHROME_EXTENSION_ID`: Your extension ID
   - `CHROME_CLIENT_ID`: Your OAuth client ID
   - `CHROME_CLIENT_SECRET`: Your OAuth client secret
   - `CHROME_REFRESH_TOKEN`: Your refresh token

## Step 6: Test Locally (Optional)

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Test the upload:
```bash
npm run build
npm run package
npm run publish:chrome
```

## Security Notes

- **Never commit** `.env` file or credentials to git
- The `.env` file is already in `.gitignore`
- GitHub Secrets are encrypted and only accessible to GitHub Actions
- Refresh tokens don't expire but can be revoked in Google Cloud Console
- Consider using different credentials for production vs testing

## Troubleshooting

### "Invalid client" error
- Double-check your Client ID and Client Secret
- Make sure Chrome Web Store API is enabled

### "Access denied" error
- Ensure you're using the correct Google account
- Check that the account has developer access to the extension

### "Extension not found" error
- Verify the Extension ID is correct
- Ensure the extension exists in the Chrome Web Store

## References

- [Chrome Web Store API Documentation](https://developer.chrome.com/docs/webstore/using_webstore_api/)
- [chrome-webstore-upload Documentation](https://github.com/fregante/chrome-webstore-upload)
- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
