"""
The-Commander: REST API Interface
FastAPI implementation exposing control over System, Nodes, Agents, and Memory.

Runs as the primary interface for external interaction (Web GUI, CLI tools).

Version: 1.1.0
"""

import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Body, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from commander_os.core.system_manager import SystemManager
from commander_os.core.state import SystemStatus, ComponentStatus

# Configure Logging
logger = logging.getLogger("commander_api")

# Global System Manager Instance
system: Optional[SystemManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app.
    Initializes the SystemManager on startup.
    """
    global system
    logger.info("Initializing REST API...")
    
    # Initialize System Manager (config load happens here)
    system = SystemManager()
    
    # Auto-bootstrap on API launch? 
    # Usually better to let user explicit start, or bootstrap immediately.
    # Let's bootstrap configs so we can show loaded state.
    if not system.bootstrap():
        logger.error("Failed to bootstrap system during API startup")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down REST API...")
    if system and system.state_manager.system_status != SystemStatus.STOPPED:
        system.stop_system()

# Initialize FastAPI
app = FastAPI(
    title="The-Commander API",
    version="1.1.0",
    description="Control interface for The-Commander AI Agent Operating System",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development; narrow this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# Data Models (Pydantic)
# -------------------------------------------------------------------------

class StatusResponse(BaseModel):
    status: str
    uptime: float
    timestamp: float

class ActionResponse(BaseModel):
    success: bool
    message: str

class AgentConfigUpdate(BaseModel):
    config: Dict[str, Any]

class RoleUpdate(BaseModel):
    role: str

# -------------------------------------------------------------------------
# System Endpoints
# -------------------------------------------------------------------------

@app.post("/system/start", response_model=ActionResponse)
async def start_system():
    """Start the entire Commander system."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    success = system.start_system()
    if success:
        return {"success": True, "message": "System started successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start system")

@app.post("/system/stop", response_model=ActionResponse)
async def stop_system():
    """Stop the entire Commander system."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    system.stop_system()
    return {"success": True, "message": "System stopped"}

@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status report."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    return system.get_status_report()

# -------------------------------------------------------------------------
# Node Endpoints
# -------------------------------------------------------------------------

@app.get("/nodes", response_model=List[Dict[str, Any]])
async def list_nodes():
    """List all registered nodes."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")

    nodes = []
    for node_state in system.state_manager.get_all_nodes():
        node_id = node_state.node_id
        config = system.config_manager.get_node(node_id)
        
        node_data = node_state.to_dict()
        if config:
            # Add static metadata for the GUI
            node_data['name'] = config.name
            node_data['tps_benchmark'] = config.tps_benchmark
            if config.engine:
                node_data['model_file'] = config.engine.model_file
                node_data['ctx'] = config.engine.ctx
                node_data['ngl'] = config.engine.ngl
                
        nodes.append(node_data)
    return nodes

@app.get("/nodes/{node_id}/status")
async def get_node_status(node_id: str):
    """Get status of a specific node."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    status = system.node_manager.get_node_status(node_id)
    if not status:
        raise HTTPException(status_code=404, detail="Node not found")
    return status

@app.post("/nodes/{node_id}/start", response_model=ActionResponse)
async def start_node(node_id: str):
    """Start a specific node."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if system.node_manager.start_node(node_id):
        return {"success": True, "message": f"Node {node_id} started"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to start node {node_id}")

@app.post("/nodes/{node_id}/stop", response_model=ActionResponse)
async def stop_node(node_id: str):
    """Stop a specific node."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if system.node_manager.stop_node(node_id):
        return {"success": True, "message": f"Node {node_id} stopped"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to stop node {node_id}")

# -------------------------------------------------------------------------
# Agent Endpoints
# -------------------------------------------------------------------------

@app.get("/agents", response_model=List[Dict[str, Any]])
async def list_agents(node_id: Optional[str] = None):
    """List all agents, optionally filtered by node_id."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return system.agent_manager.list_agents(node_id)

@app.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get status of a specific agent."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    status = system.agent_manager.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail="Agent not found")
    return status

@app.post("/agents/{agent_id}/start", response_model=ActionResponse)
async def start_agent(agent_id: str):
    """Start a specific agent."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if system.agent_manager.start_agent(agent_id):
        return {"success": True, "message": f"Agent {agent_id} started"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to start agent {agent_id}")

@app.post("/agents/{agent_id}/stop", response_model=ActionResponse)
async def stop_agent(agent_id: str):
    """Stop a specific agent."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if system.agent_manager.stop_agent(agent_id):
        return {"success": True, "message": f"Agent {agent_id} stopped"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to stop agent {agent_id}")

@app.patch("/agents/{agent_id}/config", response_model=ActionResponse)
async def update_agent_config(agent_id: str, update: AgentConfigUpdate):
    """Update an agent's configuration (triggers hot-reload)."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if system.agent_manager.config_agent(agent_id, update.config):
        return {"success": True, "message": f"Agent {agent_id} config updated"}
    else:
        raise HTTPException(status_code=400, detail="Failed to update config")

@app.patch("/agents/{agent_id}/role", response_model=ActionResponse)
async def update_agent_role(agent_id: str, update: RoleUpdate):
    """Override an agent's role."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if system.agent_manager.set_agent_role(agent_id, update.role):
        return {"success": True, "message": f"Agent {agent_id} role set to {update.role}"}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid role or agent: {update.role}")

# -------------------------------------------------------------------------
# Memory Endpoints
# -------------------------------------------------------------------------

@app.get("/memory/search")
async def search_memory(
    task_id: Optional[str] = None,
    sender: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 50
):
    """Search for messages in the memory store."""
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # We haven't exposed Query directly in SystemManager, let's fix that or access directly
    # Accessing directly via property is cleaner than adding wrapper for every function
    # Assuming SystemManager exposes a way to get memory component or we add it to SystemManaager
    # Current SystemManager doesn't utilize MemoryStore yet in constructor (it was phase 2)
    # Correcting: SystemManager should have initialized MemoryStore in Phase 2
    # But checking SystemManager code, it initializes NodeManager and AgentManager.
    # We should add MemoryStore to SystemManager for this to work elegantly.
    
    # HACK: For now, we'll instantiate a ephemeral store if not found, 
    # BUT ideally we modify SystemManager to hold it. 
    # Let's assume we will update SystemManager next.
    
    # Check if system has memory attribute (dynamic check)
    if hasattr(system, 'memory_store'):
         return system.memory_store.query_messages(task_id, sender, role, limit)
    else:
        # Fallback if SystemManager update is pending
        raise HTTPException(status_code=501, detail="Memory subsystem not yet attached to SystemManager")

