from fastapi import APIRouter, HTTPException
from typing import List
from agent import FoundryTaskAgent

def create_api_routes(agent: FoundryTaskAgent) -> APIRouter:
    router = APIRouter()
    
    @router.get("/chat")
    async def chat_with_azureaiagent():
        return {"tools", agent.tools}
    
    return router