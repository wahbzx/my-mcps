# My MCP Tools

A collection of MCP tools I use for my local model running on llama.cpp

## Available tools

- YouTube Tool - Atm only needed it to help me summarise long videos/lectures and ask questions about them before fully watching them

## Set up

From this repository create your virtual environment and download the dependencies:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
```

### llama.cpp

1. Copy `llama-mcp.json` to your llama.cpp directory as `mcp.json`.
2. In that copy, replace `/path/to/my_mcps` in both `command` and `args` with
   the **absolute path** to your clone of this repository. For example, if you
   cloned it to `/home/user/my_mcps`, use
   `/home/user/my_mcps/venv/bin/python` and
   `/home/user/my_mcps/server.py`.
3. Start `llama-server` from the llama.cpp directory with a model that supports
   tool calling and add the mcp-servers config parameter:

```bash
./build/bin/llama-server \
  -hf your/model-GGUF \
  -ngl 40 \
  -ncmoe 13 \
  --load-mode none \
  -c 32768 \
  -fa on \
  --jinja \
  --mcp-servers-config ./mcp.json \
  --host 127.0.0.1 \
  --port 8080
```



The copied config uses absolute paths, so `llama-server` can find the Python
environment and tool regardless of its working directory. You do not need to
start `server.py` separately. Your

Use a model that supports tool calling. In the Web UI at
`http://localhost:8080`, ask it to fetch a YouTube transcript. llama.cpp exposes
the tool as `youtube_tool_get_video_transcript` and starts the MCP process
itself.

Use ```--host 0.0.0.0 ``` if you want to expose it to your LAN but do this at your own risk.
It will then be accessible from your server's IP `http://YOURIP:8080`

`llama-cli` does not directly load MCP servers in this llama.cpp checkout. A
terminal chat needs a client that handles tool calls between `llama-server`
and this MCP server.

## YouTube transcript tool

The MCP tool is `get_video_transcript`. Give it a YouTube `video_url` and,
optionally, a caption `language` code (default: `en`). It returns the transcript
to the client without downloading the video or creating a file. The requested
caption language must be available on YouTube.




### Standalone script

The script also works without an MCP client. Pass the YouTube URL on the
command line:

```bash
venv/bin/python youtube_tool.py "https://www.youtube.com/watch?v=QRABrn606LE"
```

Use `--lang fr` (or another caption language code) to request a different
language. The script creates a `transcripts` folder in this repository if
needed and writes `transcripts/<video_id>.txt` there.
