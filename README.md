# MCP-Gmail-API-Manager
create an desktop app in google cloud console ,get the credentials json file and enable the gmail API
paste in claude config for mcp servr usage

{
  "globalShortcut": "",
  "mcpServers": {
    "email_server": {
      "command": "uv",
      "args": [
        "--directory",
        "directory name",
        "run",
        "email_server.py"
      ]
    },
    "emai_sender_server": {
      "command": "uv",
      "args": [
        "--directory",
        "directory name",
        "run",
        "emai_sender_server.py"
      ]
    }
  }
}
