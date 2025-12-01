# MCP Servers Setup Guide

## Successfully Installed MCP Servers

### 1. **Filesystem Server** ✓
**Purpose**: Access and manipulate files across your workspace

**What you can do:**
- Read/write any file in `/teamspace/studios/this_studio`
- Search file contents
- Create directories
- Move/copy files
- Get file metadata

**Example usage in Claude Code:**
```
"Use the filesystem MCP to list all Python files in the ml-pipeline directory"
"Use the filesystem MCP to read the contents of requirements.txt"
"Use the filesystem MCP to create a new directory called experiments"
```

---

### 2. **Memory Server** ✓
**Purpose**: Store and retrieve context across sessions

**What you can do:**
- Create entities (projects, features, decisions)
- Add observations to entities
- Create relationships between entities
- Search your knowledge graph
- Remember context between Claude Code sessions

**Example usage:**
```
"Remember that we're using VRLA batteries with 120Ah capacity"
"What did I decide about the ML model architecture?"
"Store this design decision: Using FastAPI for the backend API"
```

---

### 3. **GitHub Server** ✓
**Purpose**: Manage GitHub repositories, issues, and pull requests

**Configuration:**
- Token: `<your-github-token>` (configured via `claude mcp add`)
- Scope: User (all projects)

**What you can do:**
- Create/update/list issues
- Create/merge/review pull requests
- Search repositories and code
- Fork repositories
- Create branches
- Push files to GitHub

**Example usage:**
```
"Use the github MCP to create an issue for Railway deployment"
"Use the github MCP to list all open pull requests"
"Use the github MCP to search for battery monitoring code in repositories"
```

---

### 4. **Sequential Thinking Server** ✓
**Purpose**: Enhanced problem-solving with step-by-step reasoning

**What you can do:**
- Break down complex problems
- Analyze multi-step workflows
- Debug complex issues with structured thinking

**Example usage:**
```
"Use sequential thinking to plan the ML pipeline deployment"
"Help me debug why the battery degradation model isn't working correctly"
```

---

## Pending Installation

### 5. **PostgreSQL Server** (Install after Railway deployment)

**Why pending:** Need DATABASE_URL from Railway

**Installation command (run when Railway is ready):**
```bash
# Get DATABASE_URL from Railway
railway variables get DATABASE_URL

# Install PostgreSQL MCP
claude mcp add --transport stdio postgres \
  --env POSTGRES_CONNECTION_STRING="<paste-database-url-here>" \
  --scope project -- npx -y @modelcontextprotocol/server-postgres
```

**What it will enable:**
- Query battery telemetry directly from database
- Inspect schema and tables
- Run SQL analytics
- Validate data without switching tools

---

## How to Use MCP Servers

### In Claude Code:

1. **Direct commands:**
   ```
   "Use the filesystem MCP to read backend/main.py"
   "Use the github MCP to create an issue"
   "Use the memory MCP to remember this decision"
   ```

2. **Implicit usage (Claude will use automatically when relevant):**
   ```
   "What files are in the ml-pipeline directory?" → Uses filesystem
   "Create a GitHub issue for this bug" → Uses github
   "What did we decide about the database schema?" → Uses memory
   ```

3. **Check available tools:**
   ```
   /mcp
   ```

### From Command Line:

```bash
# List all installed servers
claude mcp list

# Get details about a specific server
claude mcp get filesystem

# Remove a server
claude mcp remove <server-name> -s user

# Add a new server
claude mcp add --transport stdio <name> --scope user -- npx -y @modelcontextprotocol/server-<name>
```

---

## Configuration Files

### User Config (all projects)
Location: `/teamspace/studios/this_studio/.claude.json`

Currently installed servers:
- filesystem
- memory
- github
- sequential-thinking

### Project Config (this project only)
Location: `/teamspace/studios/this_studio/NT/RUL_prediction/.mcp.json`

Currently: Not used (will add PostgreSQL here when deploying to Railway)

---

## Next Steps

1. **Test the installed servers:**
   - Try: "Use the filesystem MCP to list all markdown files"
   - Try: "Use the github MCP to search for VRLA battery projects"
   - Try: "Use the memory MCP to remember our project structure"

2. **When ready for Railway deployment:**
   - Deploy backend to Railway
   - Get DATABASE_URL
   - Install PostgreSQL MCP server
   - Test database queries through Claude Code

3. **Optional additions:**
   - Brave Search MCP (if you get API key)
   - Puppeteer MCP (for web automation)
   - Custom Battery RUL MCP (we could build this!)

---

## Troubleshooting

### Server won't connect
```bash
# Check server status
claude mcp get <server-name>

# Remove and reinstall
claude mcp remove <server-name> -s user
claude mcp add --transport stdio <server-name> --scope user -- npx -y @modelcontextprotocol/server-<server-name>
```

### Missing permissions
Make sure environment variables are set correctly:
```bash
# For GitHub
echo $GITHUB_TOKEN

# For PostgreSQL (when installed)
echo $DATABASE_URL
```

### Large output truncated
Increase timeout:
```bash
MCP_TIMEOUT=30000 claude
```

---

## API Keys Reference

### Currently Configured:
- **GitHub Token**: `<configured-via-claude-mcp>`
- **Tavily API Key**: `<configured-via-claude-mcp>` (available but MCP not installed yet)

### Available for Future Use:
- **Brave Search**: Get free API key at https://brave.com/search/api/
- **Railway DATABASE_URL**: Will get this during deployment

---

## Resources

- MCP Documentation: https://modelcontextprotocol.io/
- Claude Code MCP Guide: https://code.claude.com/docs/en/mcp.md
- Official MCP Servers: https://github.com/modelcontextprotocol/servers
- Claude Code Issues: https://github.com/anthropics/claude-code/issues
