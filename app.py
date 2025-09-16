from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
from api import create_api_routes
from agent import FoundryTaskAgent
from contextlib import AsyncExitStack


class TaskManagerApp:
    """FastAPI application for task management with AI agents."""
    
    def __init__(self):

        server_url = "http://localhost:3000"
        
        self.app = FastAPI(
            title="Task Manager API",
            version="1.0.0",
            description="A simple task management API for Azure AI Foundry Agents",
            servers=[
                {"url": server_url, "description": "Task Manager API Server"}
            ]
        )
        self.foundry_agent = None
        self.exit_stack = None
        self._setup_middleware()

        @self.app.on_event("startup")
        async def startup_event():
            self.exit_stack = AsyncExitStack()
            await self.exit_stack.__aenter__()
            self.foundry_agent = await FoundryTaskAgent.create(self.exit_stack)
            self._setup_routes(self.foundry_agent)
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            if self.exit_stack:
                await self.exit_stack.__aexit__(None, None, None)

    
    def _setup_middleware(self):
        """Set up CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure as needed for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self, foundry_agent: FoundryTaskAgent):
        """Set up API routes and static file serving."""
        # API routes
        api_router = create_api_routes(foundry_agent)
        self.app.include_router(api_router, prefix="/api")
    
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app
    
    async def shutdown(self):
        """Cleanup resources."""
        print("Shutting down Task Manager app...")



# Create the application instance
app_instance = TaskManagerApp()
app = app_instance.get_app()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
