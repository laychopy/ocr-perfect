# GitHub Repository Setup

This document records the GitHub repository setup for OCR Perfect.

## Repository Details

- **URL:** https://github.com/laychopy/ocr-perfect
- **Visibility:** Public
- **Default Branch:** main
- **Created:** 2026-01-20

## Setup Steps

### 1. Initialize Git Repository

```bash
git init
git branch -m main
```

### 2. Create .gitignore

Created comprehensive `.gitignore` for Python, Node.js, IDE files, and secrets.

### 3. Stage and Commit

```bash
git add -A
git commit -m "Initial commit: OCR Perfect pipeline foundation"
```

### 4. Create GitHub Repository

Used GitHub CLI to create and push:

```bash
gh repo create ocr-perfect \
  --public \
  --description "Production-ready OCR engine with multi-backend support and sub-pixel coordinate accuracy" \
  --source=. \
  --push
```

## MCP Integration

GitHub MCP server is configured for Claude Code integration:

```bash
claude mcp add github \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> \
  -- npx -y @modelcontextprotocol/server-github
```

## Initial Commit Contents

- Geometry system (transforms, bboxes, coordinate spaces)
- Intermediate Representation (models, ordering, provenance)
- Configuration system with presets
- Unit tests (~1,139 lines)
- Firebase/GCP infrastructure configuration
- Documentation

## Useful Commands

```bash
# Check remote
git remote -v

# Push changes
git push origin main

# Pull changes
git pull origin main

# Create feature branch
git checkout -b feature/my-feature
```
