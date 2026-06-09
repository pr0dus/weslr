#!/bin/bash
# WESLR Credential Setup Script
# This script sets up secure credential storage for WESLR

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WESLR_DIR="$(dirname "$SCRIPT_DIR")"
CREDENTIALS_DIR="$WESLR_DIR/.weslr"

echo "Setting up WESLR credentials..."

# Ensure .weslr directory exists
mkdir -p "$CREDENTIALS_DIR"

# Set permissions to restrict access
chmod 700 "$CREDENTIALS_DIR"

echo "Credentials directory created at: $CREDENTIALS_DIR"
echo "Important: Edit .weslr/.env.local and set your GITHUB_TOKEN"

# Warn about sensitive files
echo ""
echo "=== SECURITY WARNING ==="
echo "Do NOT commit .env.local, .env, or credentials.json to public repositories"
echo "Add your actual GitHub token to .weslr/.env.local"
echo "========================"
