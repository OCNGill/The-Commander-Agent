"""
The-Commander: Agent Manager
Manages the lifecycle of AI agents.

Handles:
- Agent process startup/shutdown (simulated or actual)
- Dynamic configuration updates (hot-reload)
- Role overrides
- Status monitoring

Version: 1.1.0
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any

from commander_os.core.config_manager import ConfigManager, AgentConfig
from commander_os.core.state import StateManager, ComponentStatus, AgentState

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manages AI Agent processes and configurations.
    """
    
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config = config_manager
        self.state = state_manager
        
        # Track active processes (stub for future Popen objects)
        self._processes: Dict[str, Any] = {}
        
        # Local node ID to determine which agents to start
        self._local_node_id = "node-local" 
        
        logger.info("AgentManager initialized")

    def start_all_agents(self) -> None:
        """
        Start all agents assigned to the local node.
        """
        logger.info("Starting agents for local node...")
        
        agents = self.config.get_agents_on_node(self._local_node_id)
        for agent_config in agents:
            if agent_config.enabled:
                self.start_agent(agent_config.id)

    def stop_all_agents(self) -> None:
        """
        Stop all locally running agents.
        """
        logger.info("Stopping all local agents...")
        
        # Snapshot keys to avoid modification during iteration
        active_agents = list(self._processes.keys())
        for agent_id in active_agents:
            self.stop_agent(agent_id)

    def start_agent(self, agent_id: str) -> bool:
        """
        Start a specific agent process.
        """
        # 1. Get Config
        agent_config = self.config.get_agent(agent_id)
        if not agent_config:
            logger.error(f"Cannot start agent {agent_id}: Config not found")
            return False
            
        # 2. Register in State
        self.state.register_agent(
            agent_id=agent_id,
            node_id=agent_config.node_id,
            role=agent_config.role
        )
        
        # 3. Check if local
        if agent_config.node_id != self._local_node_id:
            logger.info(f"Skipping start for remote agent {agent_id} (on {agent_config.node_id})")
            return True
        
        if agent_id in self._processes:
            logger.warning(f"Agent {agent_id} is already running")
            return True
            
        logger.info(f"Starting agent process: {agent_id} ({agent_config.role})")
        self.state.update_agent_status(agent_id, ComponentStatus.STARTING)
        
        # 4. Launch Process (Stub)
        # In reality: self._processes[agent_id] = subprocess.Popen(...)
        self._processes[agent_id] = {"pid": 1234, "start_time": time.time()} # Mock process handle
        
        # Simulate startup
        time.sleep(0.1)
        
        self.state.update_agent_status(agent_id, ComponentStatus.READY)
        logger.info(f"Agent {agent_id} is READY")
        return True

    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a specific agent process.
        """
        logger.info(f"Stopping agent: {agent_id}")
        
        if agent_id in self._processes:
            # In reality: self._processes[agent_id].terminate()
            del self._processes[agent_id]
            self.state.update_agent_status(agent_id, ComponentStatus.OFFLINE)
            logger.info(f"Agent {agent_id} stopped")
            return True
        else:
            logger.warning(f"Agent {agent_id} is not running")
            return False

    def restart_agent(self, agent_id: str) -> bool:
        """
        Restart an agent.
        """
        self.stop_agent(agent_id)
        time.sleep(0.5)
        return self.start_agent(agent_id)

    def config_agent(self, agent_id: str, params: Dict[str, Any]) -> bool:
        """
        Update agent configuration and hot-reload.
        """
        logger.info(f"Updating config for agent {agent_id}")
        
        # 1. Update YAML on disk
        updated_config = self.config.update_agent_config(agent_id, params)
        if not updated_config:
            logger.error(f"Failed to update config for {agent_id}")
            return False
            
        # 2. Check if restart required (e.g. model change)
        # For now, we assume simple param updates require restart to take effect safely
        if agent_id in self._processes:
            logger.info(f"Restarting agent {agent_id} to apply new config")
            return self.restart_agent(agent_id)
            
        return True

    def set_agent_role(self, agent_id: str, role: str) -> bool:
        """
        Override an agent's role dynamically.
        """
        if not self.config.validate_role(role):
            logger.error(f"Invalid role: {role}")
            return False
            
        # Update state immediately
        self.state.update_agent_role(agent_id, role)
        
        # Update config persistence
        self.config.update_agent_config(agent_id, {'role': role})
        
        logger.info(f"Agent {agent_id} role set to {role}")
        return True

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get runtime status of an agent.
        """
        agent = self.state.get_agent(agent_id)
        if agent:
            return agent.to_dict()
        return None

    def list_agents(self, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all agents, optionally filtered by node.
        """
        if node_id:
            agents = self.state.get_agents_on_node(node_id)
        else:
            agents = self.state.get_all_agents()
            
        return [a.to_dict() for a in agents]
