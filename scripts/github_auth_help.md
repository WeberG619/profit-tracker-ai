# GitHub Authentication Help

If you get an authentication error when pushing, follow these steps:

## Option 1: GitHub CLI (Recommended)
```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Authenticate
gh auth login

# Create and push repo
gh repo create profit-tracker-ai --public --source=. --remote=origin --push
```

## Option 2: Personal Access Token
1. Go to: https://github.com/settings/tokens/new
2. Create token with 'repo' scope
3. Use token as password when pushing:
```bash
git push -u origin main
# Username: WeberG619
# Password: [paste your token]
```

## Option 3: SSH Key
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: https://github.com/settings/ssh/new

# Change remote to SSH
git remote set-url origin git@github.com:WeberG619/profit-tracker-ai.git

# Push
git push -u origin main
```