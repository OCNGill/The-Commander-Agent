"""
The-Commander: REST API Interface
FastAPI implementation exposing control over System, Nodes, Agents, and Memory.

Runs as the primary interface for external interaction (Web GUI, CLI tools).

Version: 1.1.0
"""

import logging
import os
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException, Body, Query, status, WebSocket, WebSocketDisconnect
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
    
    # Start Tactical Broadcaster
    broadcast_task = asyncio.create_task(tactical_broadcaster())
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down REST API...")
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
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
# WebSocket Connection Manager
# -------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def contract(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New Strategic GUI tactical link established. Total: {len(self.active_connections)}")

    def sever(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Tactical link severed. Active remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast intelligence packet to all active command consoles."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to tactical link: {e}")

manager = ConnectionManager()

async def tactical_broadcaster():
    """
    Background task to push real-time updates to focused command consoles.
    Monitors state changes and new memory entries.
    """
    last_msg_id = 0
    logger.info("Tactical Broadcaster online.")
    
    # Initialize last_msg_id to current max to avoid flood on restart
    if system and hasattr(system, 'memory_store'):
        try:
            recent = system.memory_store.query_messages(limit=1)
            if recent:
                last_msg_id = recent[0]['id']
        except Exception as e:
            logger.warning(f"Tactical Broadcaster failed initial memory check: {e}")

    while True:
        try:
            if not manager.active_connections:
                await asyncio.sleep(2)  # Low power mode when no one is watching
                continue

            # 1. Broadast Full System State
            if system:
                snapshot = system.get_status_report()
                await manager.broadcast({
                    "type": "state_update",
                    "data": snapshot
                })

            # 2. Broadcast New Memory entries
            if system and hasattr(system, 'memory_store'):
                recent = system.memory_store.query_messages(limit=10)
                new_msgs = [m for m in recent if m['id'] > last_msg_id]
                if new_msgs:
                    # Sort chronological for the client
                    new_msgs.sort(key=lambda x: x['id'])
                    await manager.broadcast({
                        "type": "new_messages",
                        "data": new_msgs
                    })
                    last_msg_id = new_msgs[-1]['id']

            await asyncio.sleep(0.5)  # Tactical refresh rate (500ms)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Tactical Broadcaster encountered resistance: {e}")
            await asyncio.sleep(5)

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

class EngineUpdate(BaseModel):
    ctx: Optional[int] = None
    ngl: Optional[int] = None
    fa: Optional[bool] = None
    model_file: Optional[str] = None

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

@app.post("/nodes/{node_id}/engine", response_model=ActionResponse)
async def reignite_node_engine(node_id: str, update: EngineUpdate):
    """
    Update engine config and reignite the LLM backend.
    """
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Check if this is local node or remote (Phase 6 focuses on Local Hub control)
    if node_id != system.local_node_id:
        raise HTTPException(status_code=501, detail="Remote node engine control not yet implemented in cluster-fabric")

    updates = {k: v for k, v in update.dict().items() if v is not None}
    if system.reignite_local_engine(updates):
        return {"success": True, "message": f"Engine on {node_id} re-ignited with new tactical dials"}
    else:
        raise HTTPException(status_code=500, detail="Engine re-ignition failed")

@app.get("/nodes/{node_id}/models", response_model=List[str])
async def list_node_models(node_id: str):
    """
    Scan for available .gguf models on a specific node.
    """
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Logic to scan local filesystem if node is local
    config = system.config_manager.get_node(node_id)
    if not config:
         raise HTTPException(status_code=404, detail="Node not found")
    
    model_root = config.model_root_path
    if not model_root or not os.path.exists(model_root):
        # Fallback for dev: check current dir models/
        model_root = os.path.join(os.getcwd(), "models")
        if not os.path.exists(model_root):
            return []

    try:
        models = [f for f in os.listdir(model_root) if f.endswith(".gguf")]
        return models
    except Exception as e:
        logger.error(f"Failed to scan models at {model_root}: {e}")
        return []

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

# -------------------------------------------------------------------------
# Strategic WebSocket Endpoint
# -------------------------------------------------------------------------

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    Persistent tactical link for real-time cluster intelligence.
    Streams logs, status updates, and agent events.
    """
    await manager.contract(websocket)
    try:
        while True:
            # Keep the connection alive and listen for any incoming client commands
            data = await websocket.receive_text()
            # For now, we just echo or log, as control is primary via REST
            logger.debug(f"Received from GUI client: {data}")
    except WebSocketDisconnect:
        manager.sever(websocket)
    except Exception as e:
        logger.error(f"Tactical link error: {e}")
        manager.sever(websocket)

