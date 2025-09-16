from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_to_server(exit_stack: AsyncExitStack):

    server_params = StdioServerParameters(
        command="C:\\develop\\open-source\\azure-ai-agents-dotnet\\MiniMCPServer\\bin\\Release\\net8.0\\MiniMCPServer.exe",
        args=[],
        env=None
    )

    # Start the MCP server
    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport

    # Create an MCP client session
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()

    # List available tools
    response = await session.list_tools()
    tools = response.tools  
    print("\nConnected to server with tools:", [tool.name for tool in tools]) 
    return session

class FoundryTaskAgent:
    def __init__(self, session):
        self.session = session

    @classmethod
    async def create(cls, exit_stack):
        session = await connect_to_server(exit_stack)
        return cls(session)
