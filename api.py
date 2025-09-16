from fastapi import APIRouter, HTTPException
from typing import List
from agent import FoundryTaskAgent

def create_api_routes(agent: FoundryTaskAgent) -> APIRouter:
    router = APIRouter()
    
    @router.get("/chat")
    async def chat_with_azureaiagent():
        response = await agent.session.list_tools()
        tools = response.tools
        return {"tools": [tool.name for tool in tools]}
    
    return router