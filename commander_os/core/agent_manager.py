"""
The-Commander: Agent Manager
Manages the lifecycle of AI agents.

Handles:
- Agent process startup/shutdown (simulated or actual)
- Dynamic configuration updates (hot-reload)
- Role overrides
- Status monitoring
- Task execution (Protocol Enforced)

Version: 1.2.0 (Protocol Integrated)
"""

import logging
import time
from typing import Dict, List, Optional, Any

from commander_os.core.config_manager import ConfigManager, AgentConfig
from commander_os.core.state import StateManager, ComponentStatus
from commander_os.core.protocol import CommanderProtocol, MessageEnvelope, TaskDefinition

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manages AI Agent processes and configurations.
    """
    
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager, local_node_id: str = "node-main"):
        self.config = config_manager
        self.state = state_manager
        
        # Track active processes (stub for future Popen objects)
        self._processes: Dict[str, Any] = {}
        
        # Local node ID to determine which agents to start
        self._local_node_id = local_node_id 
        
        logger.info(f"AgentManager initialized for node: {self._local_node_id}")

    def start_all_agents(self) -> None:
        """
        Start all agents assigned to the local node.
        """
        logger.info(f"Starting agents for node {self._local_node_id}...")
        
        agents = self.config.get_agents_on_node(self._local_node_id)
        for agent_config in agents:
            if agent_config.enabled:
                self.start_agent(agent_config.id)

    def stop_all_agents(self) -> None:
        """
        Stop all locally running agents.
        """
        logger.info(f"Stopping all agents on node {self._local_node_id}...")
        
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
            logger.warning(f"Agent {agent_id} is already running on this node")
            return True
            
        logger.info(f"Starting local agent process: {agent_id} ({agent_config.role})")
        self.state.update_agent_status(agent_id, ComponentStatus.STARTING)
        
        # 4. Launch Process (Stub)
        self._processes[agent_id] = {"pid": 1234, "start_time": time.time()} # Mock process handle
        
        # Simulate startup
        time.sleep(0.1)
        
        self.state.update_agent_status(agent_id, ComponentStatus.READY)
        logger.info(f"Agent {agent_id} is READY on {self._local_node_id}")
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
            logger.warning(f"Agent {agent_id} is not running locally")
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

    def execute_task(self, agent_id: str, task: TaskDefinition) -> MessageEnvelope:
        """
        Execute a task on a specific agent and return a protocol-compliant response.
        
        This is the core of the Phase 4 Protocol Integration.
        """
        logger.info(f"Agent {agent_id} executing task {task.id}: {task.title}")
        
        # 1. Check if agent is locally running and ready
        agent_state = self.state.get_agent(agent_id)
        if not agent_state or agent_state.status != ComponentStatus.READY:
            error_msg = f"Agent {agent_id} is not READY"
            logger.error(error_msg)
            # Create a mock command envelope to respond to
            dummy_cmd = CommanderProtocol.create_command("commander", agent_id, "execute_task", task_id=task.id)
            return CommanderProtocol.create_response(dummy_cmd, error_msg, status="error")

        # 2. Simulate Work
        self.state.update_agent_status(agent_id, ComponentStatus.BUSY)
        time.sleep(0.2) # Simulate inference time
        
        result_content = f"Execution result for task '{task.title}' by role {agent_state.role}."
        
        self.state.update_agent_status(agent_id, ComponentStatus.READY)
        
        # 3. Construct the response envelope
        # We simulate the incoming command envelope that triggered this
        incoming_msg = CommanderProtocol.create_command(
            sender_id="commander",
            recipient_id=agent_id,
            command="execute_task",
            task_id=task.id
        )
        
        response = CommanderProtocol.create_response(
            original_msg=incoming_msg,
            response_data={
                "task_id": task.id,
                "content": result_content,
                "node_id": self._local_node_id
            }
        )
        
        logger.info(f"Task {task.id} complete. Response {response.id} generated.")
        return response

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
