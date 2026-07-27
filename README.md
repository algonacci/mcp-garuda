# mcp-garuda

MCP server to give client the ability to search papers through Garba Rujukan Digital (GARUDA)

# Features

- Search articles and journals from GARUDA
- Return metadata such as title, authors, journal, publisher, abstract, DOI, and links
- Generate a simple citation string for each result
- Fetch a full GARUDA article detail page by article id or URL

# Search filters

`search_garuda` mirrors the filters available on GARUDA's own search form
(`https://garuda.kemdiktisaintek.go.id/documents`):

- `search_field`: restrict matching to `title`, `abstract`, `author`, or
  `doi`. Leave empty for GARUDA's default (title/abstract). Use `author`
  for exact author-name lookups — plain keyword search does not reliably
  match on author names.
- `publisher`: filter by publisher name (min. 3 characters).
- `pdf_only`: only return results with a downloadable PDF.
- `year_from` / `year_to`: restrict results to a publication year range.

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
