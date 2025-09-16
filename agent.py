import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.types import Tool
from mcp.client.stdio import stdio_client
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool

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

    # Build a function for each tool
    def make_tool_func(tool_name):
        async def tool_func(**kwargs):
            result = await session.call_tool(tool_name, kwargs)
            return result
        
        tool_func.__name__ = tool_name
        return tool_func  

    functions_dict = {tool.name: make_tool_func(tool.name) for tool in tools}
    mcp_function_tool = FunctionTool(functions=list(functions_dict.values())) 

    print("\nConnected to server with tools:", [tool.name for tool in tools]) 
    return mcp_function_tool

class FoundryTaskAgent:
    def __init__(self, mcpTools: FunctionTool):
        self.tools = mcpTools
        self.project_client = None
        self.thread_id = None
        self.agent_id = None

        # Initialize the agent
        endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
        model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")

        if not endpoint or not model_deployment:
            print("Azure AI Foundry configuration missing. Set AZURE_AI_FOUNDRY_PROJECT_ENDPOINT and AZURE_AI_FOUNDRY_AGENT_ID")
            return  
        
        try:
            # Create the project client using Azure credentials
            self.project_client = AIProjectClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )

            # Create the agent
            agent = self.project_client.agents.create_agent(
                model=model_deployment,
                name="inventory-agent",
                instructions="""
                You are an inventory assistant. Here are some general guidelines:
                - Recommend restock if item inventory < 10  and weekly sales > 15
                - Recommend clearance if item inventory > 20 and weekly sales < 5
                """,
                tools=mcpTools.definitions
            )  
            self.agent_id = agent.id

            print(f"Created agent: {self.agent_id}")
            
            # Create a thread for this session
            thread = self.project_client.agents.threads.create()
            self.thread_id = thread.id
            print(f"Created thread: {self.thread_id}")
            print("Azure AI Foundry Task Agent initialized successfully")
            
        except ImportError as e:
            print(f"Azure AI Projects SDK not available. Install azure-ai-projects package: {e}")
        except Exception as e:
            print(f"Failed to initialize Azure AI Foundry agent: {e}")        
        print("tools:", self.tools)
              
            

    @classmethod
    async def create(cls, exit_stack):
        functiontool = await connect_to_server(exit_stack)
        return cls(functiontool)
