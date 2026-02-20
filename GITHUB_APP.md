# GitHub App Configuration for Gh Nexus

## App Details
- **App ID**: 2908251
- **Client ID**: Iv23li10Mp8xjfdqDzDS

## Setup Instructions

### 1. Download Private Key
Go to: https://github.com/settings/apps/2908251

Click **Generate a private key** at the bottom of the page.

### 2. Save the Key
Save the downloaded `.pem` file as `gh_nexus.pem` in the project root.

### 3. Update .env
```bash
GITHUB_APP_ID=2908251
GITHUB_APP_PRIVATE_KEY_PATH=./gh_nexus.pem
```

### 4. Get Installation ID
After installing the app, visit:
https://github.com/settings/installations/

Click on the installation, copy the URL:
`https://github.com/settings/installations/XXXXXX`

The number at the end is your `INSTALLATION_ID`.

Add to .env:
```
GITHUB_INSTALLATION_ID=XXXXXX
```

## Using GitHub App Authentication

Once configured, gh_nexus will use the GitHub App instead of personal access tokens for:
- Creating issues
- Creating branches
- Creating PRs
- Commenting on issues
