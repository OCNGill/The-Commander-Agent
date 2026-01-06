"""
The-Commander: REST API Interface
FastAPI implementation exposing control over System, Nodes, Agents, and Memory.

Runs as the primary interface for external interaction (Web GUI, CLI tools).

Version: 1.1.0
"""

import logging
import os
import requests
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
    
    # Initialize SystemManager (config load happens here)
    # CRITICAL: Use Env Var to determine Identity (injected by main.py)
    node_id = os.getenv("COMMANDER_NODE_ID", "Gillsystems-Main")
    logger.info(f"Initializing System Manager as: {node_id}")
    system = SystemManager(local_node_id=node_id)
    
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
    title="Gillsystems Commander OS API",
    version="1.3.1",
    description="Control interface for Gillsystems Commander OS - AI Agent Operating System",
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

@app.get("/health")
async def health_check():
    """Tactical health check for port verification."""
    return {"status": "online", "system": "Gillsystems Commander OS"}

@app.get("/version")
async def get_version():
    """Return system version for dynamic display."""
    return {"version": "1.3.1", "system": "Gillsystems Commander OS"}

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
    binary: Optional[str] = None

# -------------------------------------------------------------------------
# System Endpoints
# -------------------------------------------------------------------------

class CommandRequest(BaseModel):
    text: str

@app.post("/command", response_model=ActionResponse)
async def submit_command(cmd: CommandRequest):
    """
    Submit a manual command to The Commander.
    Routes to highest-ranking active node based on tps_benchmark.
    """
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Log the user message
    if hasattr(system, 'memory_store'):
        system.memory_store.log_message(
            task_id="chat", 
            sender="THE_COMMANDER",
            recipient="system",
            role="user", 
            content=cmd.text
        )
    
    # Find highest-ranking active node (highest tps_benchmark)
    active_nodes = []
    for node_id, config in system.config_manager.nodes.items():
        node_state = system.state_manager.get_node(node_id)
        if node_state and node_state.status in ['ready', 'online']:
            active_nodes.append({
                'node_id': node_id,
                'config': config,
                'tps_benchmark': config.tps_benchmark
            })
    
    if not active_nodes:
        return {"success": False, "message": "No active nodes available"}
    
    # Sort by tps_benchmark descending (highest first)
    active_nodes.sort(key=lambda x: x['tps_benchmark'], reverse=True)
    target_node = active_nodes[0]
    
    logger.info(f"Routing command to highest-ranking node: {target_node['node_id']} (TPS: {target_node['tps_benchmark']})")
    
    # Call the node's LLM inference endpoint
    try:
        node_url = f"http://{target_node['config'].host}:{target_node['config'].port}/completion"
        payload = {
            "prompt": cmd.text,
            "n_predict": 512,
            "temperature": 0.7,
            "stop": ["User:", "Commander:"],
            "stream": False
        }
        
        logger.info(f"Sending inference request to {node_url}")
        response = requests.post(node_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('content', '').strip()
            
            # Log the assistant response
            if hasattr(system, 'memory_store'):
                system.memory_store.log_message(
                    task_id="chat",
                    sender=target_node['node_id'],
                    recipient="THE_COMMANDER",
                    role="assistant",
                    content=response_text
                )
            
            return {"success": True, "message": f"Response from {target_node['node_id']}", "response": response_text}
        else:
            error_msg = f"Node returned status {response.status_code}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
            
    except requests.exceptions.Timeout:
        error_msg = f"Timeout waiting for response from {target_node['node_id']}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
    except Exception as e:
        error_msg = f"Inference failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}

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
    nodes = []
    # Iterate all CONFIGURED nodes (Topology Source of Truth)
    for node_id, config in system.config_manager.nodes.items():
        # Get live state if available
        node_state = system.state_manager.get_node(node_id)
        
        if node_state:
            node_data = node_state.to_dict()
        else:
            # Fallback for offline nodes not yet registered
            node_data = {
                "node_id": node_id,
                "status": "offline",
                "address": f"{config.host}:{config.port}",
                "role": "worker",
                "registration_time": 0,
                "last_heartbeat": 0,
                "metrics": {"tps": 0.0, "load": 0.0, "memory": 0.0}
            }

        # Add static metadata from config
        node_data['name'] = config.name
        node_data['tps_benchmark'] = config.tps_benchmark
        if config.engine:
            node_data['model_file'] = config.engine.model_file
            node_data['ctx'] = config.engine.ctx
            node_data['ngl'] = config.engine.ngl
            node_data['fa'] = config.engine.fa
            node_data['binary'] = config.engine.binary
            
        # Ensure metrics exist if state was partial
        if 'metrics' not in node_data or not node_data['metrics']:
             node_data['metrics'] = {"tps": 0.0, "load": 0.0, "memory": 0.0}
                
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
    Currently only supports local node engine control.
    """
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Only allow updating the local node's engine
    if node_id != system.local_node_id:
        return {"success": False, "message": f"Can only control local node ({system.local_node_id}). Remote node control not yet implemented."}

    updates = {k: v for k, v in update.dict().items() if v is not None}
    logger.info(f"Reigniting engine for {node_id} with updates: {updates}")
    
    if system.reignite_local_engine(updates):
        return {"success": True, "message": f"Engine on {node_id} re-ignited with new tactical dials"}
    else:
        return {"success": False, "message": "Engine re-ignition failed"}

@app.get("/nodes/{node_id}/models", response_model=List[str])
async def list_node_models(node_id: str):
    """
    Scan for available .gguf models on a specific node.
    ALWAYS queries the target node's API endpoint (even if it's the local node).
    Each node scans its own model_root_path from config when it receives this request.
    """
    if not system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    config = system.config_manager.get_node(node_id)
    if not config:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Check if this request is FOR this node (not FROM this node)
    if node_id == system.local_node_id:
        # This node is being asked about its own models - scan local filesystem
        model_root = config.model_root_path
        
        if not model_root or not os.path.exists(model_root):
            logger.warning(f"Model root path not found for node {node_id}: {model_root}")
            return []
        
        try:
            models = [f for f in os.listdir(model_root) if f.endswith(".gguf")]
            logger.info(f"Found {len(models)} models in {model_root} for node {node_id}")
            return sorted(models)
        except Exception as e:
            logger.error(f"Failed to scan {model_root} for node {node_id}: {e}")
            return []
    else:
        # Forward request to the target node
        try:
            remote_url = f"http://{config.host}:{config.port}/nodes/{node_id}/models"
            logger.info(f"Forwarding model query to remote node: {remote_url}")
            
            response = requests.get(remote_url, timeout=5)
            response.raise_for_status()
            
            models = response.json()
            logger.info(f"Received {len(models)} models from remote node {node_id}")
            return models
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout querying remote node {node_id} at {config.host}:{config.port}")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection refused to remote node {node_id} at {config.host}:{config.port}")
            return []
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from remote node {node_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to query models on remote node {node_id}: {e}")
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

