# MCP (Model Context Protocol) Setup

This document records the MCP server configuration for Claude Code integration.

## Configured MCP Servers

### GitHub MCP Server

**Status:** Connected

```bash
claude mcp add github \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=<your-token> \
  -- npx -y @modelcontextprotocol/server-github
```

**Capabilities:**
- Create and manage repositories
- Create issues and pull requests
- Search code and repositories
- Manage branches and commits

**Token Source:** Retrieved from `gh auth token`

### Google Cloud MCP Server

**Status:** Not available (package not found on npm)

**Workaround:** Use `gcloud` CLI directly for GCP operations.

Attempted packages (all failed):
- `@anthropic-ai/gcloud-mcp`
- `@anthropic-ai/gcp-mcp`
- `@google-cloud/mcp-server-gcloud`

## Managing MCP Servers

```bash
# List configured servers
claude mcp list

# Add a new server
claude mcp add <name> -e KEY=value -- command args

# Remove a server
claude mcp remove <name>
```

## Configuration File

MCP configuration is stored in `~/.claude.json` (project-specific):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
      }
    }
  }
}
```

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [Claude Code MCP Docs](https://code.claude.com/docs/en/mcp)
