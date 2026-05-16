# mcp-garuda

MCP server to give client the ability to search papers through Garba Rujukan Digital (GARUDA)

# Features

- Search articles and journals from GARUDA
- Return metadata such as title, authors, journal, publisher, abstract, DOI, and links
- Generate a simple citation string for each result
- Fetch a full GARUDA article detail page by article id or URL

# Usage

For this MCP server to work, add the following configuration to your MCP config file:

```json
{
  "mcpServers": {
    "garuda": {
      "command": "uv",
      "args": [
        "--directory",
        "%USERPROFILE%/Documents/GitHub/mcp-garuda",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```
