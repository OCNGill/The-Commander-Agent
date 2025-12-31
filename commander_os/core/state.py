"""
The-Commander: State Manager
In-memory, thread-safe state tracking for the entire system.

Tracks:
- System health and lifecycle status
- Registered nodes and their status
- Active agents, their roles, and status
- Metrics and resource usage (basic)

Version: 1.1.0
"""

import threading
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)

class SystemStatus(Enum):
    """Overall system lifecycle status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    ERROR = "error"

class ComponentStatus(Enum):
    """Status for individual components (Nodes/Agents)."""
    UNKNOWN = "unknown"
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class AgentState:
    """Runtime state of a single agent."""
    agent_id: str
    node_id: str
    role: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    model_loaded: bool = False
    current_task_id: Optional[str] = None
    last_heartbeat: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

@dataclass
class NodeState:
    """Runtime state of a compute node."""
    node_id: str
    hostname: str
    port: int
    status: ComponentStatus = ComponentStatus.UNKNOWN
    registered_agents: List[str] = field(default_factory=list)
    last_heartbeat: float = field(default_factory=time.time)
    registration_time: float = field(default_factory=time.time)
    resources: Dict[str, Any] = field(default_factory=dict)  # cpu, ram, gpu
    metrics: Dict[str, Any] = field(default_factory=lambda: {"tps": 0.0, "load": 0.0})

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

class StateManager:
    """
    Central in-memory state store for The-Commander.
    Thread-safe access to system, node, and agent states.
    """

    def __init__(self):
        self._lock = threading.RLock()
        
        # System-level state
        self._system_status: SystemStatus = SystemStatus.STOPPED
        self._start_time: float = 0.0
        
        # Component states
        self._nodes: Dict[str, NodeState] = {}
        self._agents: Dict[str, AgentState] = {}
        
        # Operation locks (optional, for finer granularity if needed later)
        # For now, safe global lock is sufficient for this scale
        
    # ===========================
    # System State
    # ===========================
    
    @property
    def system_status(self) -> SystemStatus:
        """Get current system status."""
        with self._lock:
            return self._system_status

    def set_system_status(self, status: SystemStatus) -> None:
        """Update system status."""
        with self._lock:
            if self._system_status != status:
                logger.info(f"System status change: {self._system_status.value} -> {status.value}")
                self._system_status = status
                if status == SystemStatus.STARTING:
                    self._start_time = time.time()

    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        with self._lock:
            if self._start_time == 0.0:
                return 0.0
            return time.time() - self._start_time

    # ===========================
    # Node Management
    # ===========================

    def register_node(self, node_id: str, hostname: str, port: int) -> None:
        """Register or update a node in the state."""
        with self._lock:
            if node_id not in self._nodes:
                self._nodes[node_id] = NodeState(
                    node_id=node_id,
                    hostname=hostname,
                    port=port,
                    status=ComponentStatus.STARTING
                )
                logger.info(f"Registered new node: {node_id}")
            else:
                # Update existing connection info if needed
                node = self._nodes[node_id]
                node.hostname = hostname
                node.port = port
                node.last_heartbeat = time.time()

    def update_node_status(self, node_id: str, status: ComponentStatus) -> None:
        """Update a node's status."""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].status = status
                self._nodes[node_id].last_heartbeat = time.time()

    def update_node_heartbeat(self, node_id: str) -> None:
        """Update node heartbeat timestamp."""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].last_heartbeat = time.time()

    def update_node_metrics(self, node_id: str, metrics: Dict[str, Any]) -> None:
        """Update a node's live metrics (TPS, load, etc)."""
        with self._lock:
            if node_id in self._nodes:
                self._nodes[node_id].metrics.update(metrics)
                self._nodes[node_id].last_heartbeat = time.time()
            
    def get_node(self, node_id: str) -> Optional[NodeState]:
        """Get state copy of a specific node."""
        with self._lock:
            if node_id in self._nodes:
                # Return a copy to prevent external mutation issues
                return self._nodes[node_id]  # Dataclasses are mutable, callers should be careful or we use deepcopy
            return None

    def get_all_nodes(self) -> List[NodeState]:
        """Get list of all nodes."""
        with self._lock:
            return list(self._nodes.values())

    # ===========================
    # Agent Management
    # ===========================

    def register_agent(self, agent_id: str, node_id: str, role: str) -> None:
        """Register or update an agent."""
        with self._lock:
            if agent_id not in self._agents:
                self._agents[agent_id] = AgentState(
                    agent_id=agent_id,
                    node_id=node_id,
                    role=role,
                    status=ComponentStatus.STARTING
                )
                logger.info(f"Registered new agent: {agent_id} on {node_id}")
                
                # Link to node
                if node_id in self._nodes:
                    if agent_id not in self._nodes[node_id].registered_agents:
                        self._nodes[node_id].registered_agents.append(agent_id)
            else:
                # Update static info
                agent = self._agents[agent_id]
                agent.node_id = node_id
                agent.role = role
                agent.last_heartbeat = time.time()

    def update_agent_status(self, agent_id: str, status: ComponentStatus, task_id: Optional[str] = None) -> None:
        """Update agent status and current task."""
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.status = status
                agent.last_heartbeat = time.time()
                if task_id is not None:
                    agent.current_task_id = task_id

    def update_agent_role(self, agent_id: str, role: str) -> None:
        """Dynamically change an agent's active role."""
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].role = role
                logger.info(f"Agent {agent_id} role changed to {role}")

    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Get state of a specific agent."""
        with self._lock:
            return self._agents.get(agent_id)

    def get_all_agents(self) -> List[AgentState]:
        """Get list of all agents."""
        with self._lock:
            return list(self._agents.values())

    def get_agents_by_role(self, role: str) -> List[AgentState]:
        """Get all agents with a specific role."""
        with self._lock:
            return [a for a in self._agents.values() if a.role == role]

    def get_agents_on_node(self, node_id: str) -> List[AgentState]:
        """Get all agents on a specific node."""
        with self._lock:
            return [a for a in self._agents.values() if a.node_id == node_id]

    # ===========================
    # Export/Snapshot
    # ===========================

    def get_full_snapshot(self) -> Dict[str, Any]:
        """Get a complete JSON-serializable snapshot of system state."""
        with self._lock:
            return {
                "system": {
                    "status": self._system_status.value,
                    "uptime": self.get_uptime(),
                    "timestamp": time.time()
                },
                "nodes": {nid: n.to_dict() for nid, n in self._nodes.items()},
                "agents": {aid: a.to_dict() for aid, a in self._agents.items()}
            }

    def prune_stale_components(self, timeout_seconds: float = 60.0) -> List[str]:
        """
        Mark nodes/agents as OFFLINE if heartbeat is too old.
        Returns list of IDs that were changed to OFFLINE.
        """
        changed = []
        now = time.time()
        with self._lock:
            # Check nodes
            for node_id, node in self._nodes.items():
                if node.status != ComponentStatus.OFFLINE:
                    if (now - node.last_heartbeat) > timeout_seconds:
                        node.status = ComponentStatus.OFFLINE
                        changed.append(f"node:{node_id}")
                        logger.warning(f"Node {node_id} marked OFFLINE (timeout)")
                        
            # Check agents
            for agent_id, agent in self._agents.items():
                if agent.status != ComponentStatus.OFFLINE:
                    if (now - agent.last_heartbeat) > timeout_seconds:
                        agent.status = ComponentStatus.OFFLINE
                        changed.append(f"agent:{agent_id}")
                        logger.warning(f"Agent {agent_id} marked OFFLINE (timeout)")
        return changed
