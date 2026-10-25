"""Local MCP server for YouTube video captions."""

from mcp.server import MCPServer

from youtube_tool import get_youtube_captions


mcp = MCPServer("youtube_tool")


@mcp.tool()
def get_video_transcript(video_url: str, language: str = "en") -> str:
    """Get a YouTube video's title, channel, upload date, and timestamped captions.

    Returns text for analysis without downloading the video. The language is a
    YouTube caption language code, such as "en".
    """
    return get_youtube_captions(video_url, lang=language)


if __name__ == "__main__":
    mcp.run()
