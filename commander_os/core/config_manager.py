"""
The-Commander: Configuration Manager

Handles loading, validation, and CRUD operations for all YAML configurations:
- relay.yaml (static network config)
- roles.yaml (role definitions)
- agents/*.yaml (per-agent configs, hot-reloadable)

Version: 1.1.0
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from threading import Lock
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RelayConfig:
    """Static relay server configuration."""
    host: str = "127.0.0.1"
    port: int = 5555
    protocol: str = "tcp"
    heartbeat_interval: int = 5
    connection_timeout: int = 30


@dataclass
class EngineConfig:
    """LLM Engine (llama.cpp) configuration."""
    binary: str = "go.exe"
    model_file: str = ""
    ctx: int = 4096
    ngl: int = 999
    fa: bool = True
    extra_flags: str = ""


@dataclass
class NodeConfig:
    """Node configuration from relay.yaml."""
    id: str
    name: str
    host: str
    port: int
    enabled: bool = True
    max_agents: int = 4
    tps_benchmark: int = 0  # Tokens per second performance baseline
    model_root_path: str = ""  # Authoritative path for model files on this node
    engine: Optional[EngineConfig] = None


@dataclass
class RoleConfig:
    """Role definition."""
    name: str
    description: str
    system_prompt_prefix: str
    default_context_size: int
    priority: int
    can_delegate_to: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)


@dataclass
class AgentModelConfig:
    """Agent model configuration."""
    path: str = ""
    context_size: int = 8192
    ngl: int = 40
    flash_attention: bool = True


@dataclass
class AgentLlamaParams:
    """Llama.cpp passthrough parameters."""
    threads: int = 8
    batch_size: int = 512
    ubatch_size: int = 64
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.9
    repeat_penalty: float = 1.1


@dataclass
class AgentNetworkConfig:
    """Agent network configuration."""
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass
class AgentHealthConfig:
    """Agent health monitoring configuration."""
    heartbeat_interval: int = 10
    max_missed_heartbeats: int = 3
    auto_restart: bool = True


@dataclass
class AgentConfig:
    """Complete agent configuration."""
    id: str
    name: str
    enabled: bool = True
    role: str = "coder"
    node_id: str = "node-local"
    model: AgentModelConfig = field(default_factory=AgentModelConfig)
    llama_params: AgentLlamaParams = field(default_factory=AgentLlamaParams)
    network: AgentNetworkConfig = field(default_factory=AgentNetworkConfig)
    health: AgentHealthConfig = field(default_factory=AgentHealthConfig)
    log_messages: bool = True
    max_history: int = 1000


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigManager:
    """
    Centralized configuration manager for The-Commander.
    
    Handles:
    - Loading relay.yaml (static, loaded once)
    - Loading roles.yaml (static, role definitions)
    - Loading and hot-reloading agent configs
    - Validation against schemas
    - CRUD operations for agent configs
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the ConfigManager.
        
        Args:
            config_dir: Path to config directory. Defaults to 'config/' relative to project root.
        """
        # Determine config directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default: config/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        
        # Config file paths
        self.relay_config_path = self.config_dir / "relay.yaml"
        self.roles_config_path = self.config_dir / "roles.yaml"
        self.agents_dir = self.config_dir / "agents"
        
        # Loaded configurations
        self._relay_config: Optional[RelayConfig] = None
        self._nodes: Dict[str, NodeConfig] = {}
        self._roles: Dict[str, RoleConfig] = {}
        self._agents: Dict[str, AgentConfig] = {}
        self._logging_config: Dict[str, Any] = {}
        
        # Thread safety
        self._lock = Lock()
        
        # Last load timestamps (for hot-reload detection)
        self._agent_mtimes: Dict[str, float] = {}
        
        logger.info(f"ConfigManager initialized with config_dir: {self.config_dir}")
    
    def load_all(self) -> bool:
        """
        Load all configuration files.
        
        Returns:
            True if all configs loaded successfully, False otherwise.
        """
        try:
            self.load_relay_config()
            self.load_roles_config()
            self.load_all_agent_configs()
            logger.info("All configurations loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            return False
    
    def load_relay_config(self) -> RelayConfig:
        """
        Load static relay configuration.
        
        Returns:
            RelayConfig dataclass instance.
            
        Raises:
            ConfigValidationError: If config is invalid.
            FileNotFoundError: If relay.yaml doesn't exist.
        """
        if not self.relay_config_path.exists():
            raise FileNotFoundError(f"Relay config not found: {self.relay_config_path}")
        
        with open(self.relay_config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Validate required sections
        if 'relay' not in data:
            raise ConfigValidationError("Missing 'relay' section in relay.yaml")
        
        relay_data = data['relay']
        
        with self._lock:
            self._relay_config = RelayConfig(
                host=relay_data.get('host', '127.0.0.1'),
                port=relay_data.get('port', 5555),
                protocol=relay_data.get('protocol', 'tcp'),
                heartbeat_interval=relay_data.get('heartbeat_interval', 5),
                connection_timeout=relay_data.get('connection_timeout', 30)
            )
            
            # Load nodes
            self._nodes = {}
            for node_data in data.get('nodes', []):
                engine = None
                if 'engine' in node_data:
                    e_data = node_data['engine']
                    engine = EngineConfig(
                        binary=e_data.get('binary', 'go.exe'),
                        model_file=e_data.get('model_file', ''),
                        ctx=e_data.get('ctx', 4096),
                        ngl=e_data.get('ngl', 999),
                        fa=e_data.get('fa', True),
                        extra_flags=e_data.get('extra_flags', '')
                    )

                node = NodeConfig(
                    id=node_data['id'],
                    name=node_data.get('name', node_data['id']),
                    host=node_data.get('host', '127.0.0.1'),
                    port=node_data.get('port', 5556),
                    enabled=node_data.get('enabled', True),
                    max_agents=node_data.get('max_agents', 4),
                    tps_benchmark=node_data.get('tps_benchmark', 0),
                    model_root_path=node_data.get('model_root_path', ""),
                    engine=engine
                )
                self._nodes[node.id] = node
            
            # Load logging config
            self._logging_config = data.get('logging', {})
        
        logger.info(f"Loaded relay config: {self._relay_config.host}:{self._relay_config.port}")
        logger.info(f"Loaded {len(self._nodes)} node configurations")
        
        return self._relay_config
    
    def load_roles_config(self) -> Dict[str, RoleConfig]:
        """
        Load role definitions.
        
        Returns:
            Dictionary of role_id -> RoleConfig.
            
        Raises:
            ConfigValidationError: If config is invalid.
            FileNotFoundError: If roles.yaml doesn't exist.
        """
        if not self.roles_config_path.exists():
            raise FileNotFoundError(f"Roles config not found: {self.roles_config_path}")
        
        with open(self.roles_config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'roles' not in data:
            raise ConfigValidationError("Missing 'roles' section in roles.yaml")
        
        with self._lock:
            self._roles = {}
            for role_id, role_data in data['roles'].items():
                self._roles[role_id] = RoleConfig(
                    name=role_data.get('name', role_id),
                    description=role_data.get('description', ''),
                    system_prompt_prefix=role_data.get('system_prompt_prefix', ''),
                    default_context_size=role_data.get('default_context_size', 8192),
                    priority=role_data.get('priority', 2),
                    can_delegate_to=role_data.get('can_delegate_to', []),
                    permissions=role_data.get('permissions', [])
                )
        
        logger.info(f"Loaded {len(self._roles)} role definitions")
        return self._roles
    
    def load_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """
        Load all agent configurations from agents/ directory.
        
        Returns:
            Dictionary of agent_id -> AgentConfig.
        """
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return {}
        
        with self._lock:
            self._agents = {}
            for yaml_file in self.agents_dir.glob("*.yaml"):
                try:
                    agent = self._load_agent_file(yaml_file)
                    self._agents[agent.id] = agent
                    self._agent_mtimes[agent.id] = yaml_file.stat().st_mtime
                except Exception as e:
                    logger.error(f"Failed to load agent config {yaml_file}: {e}")
        
        logger.info(f"Loaded {len(self._agents)} agent configurations")
        return self._agents
    
    def _load_agent_file(self, filepath: Path) -> AgentConfig:
        """
        Load a single agent configuration file.
        
        Args:
            filepath: Path to the agent YAML file.
            
        Returns:
            AgentConfig dataclass instance.
        """
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'agent' not in data:
            raise ConfigValidationError(f"Missing 'agent' section in {filepath}")
        
        agent_data = data['agent']
        
        # Parse model config
        model_data = agent_data.get('model', {})
        model = AgentModelConfig(
            path=model_data.get('path', ''),
            context_size=model_data.get('context_size', 8192),
            ngl=model_data.get('ngl', 40),
            flash_attention=model_data.get('flash_attention', True)
        )
        
        # Parse llama params
        llama_data = agent_data.get('llama_params', {})
        llama_params = AgentLlamaParams(
            threads=llama_data.get('threads', 8),
            batch_size=llama_data.get('batch_size', 512),
            ubatch_size=llama_data.get('ubatch_size', 64),
            temperature=llama_data.get('temperature', 0.7),
            top_k=llama_data.get('top_k', 40),
            top_p=llama_data.get('top_p', 0.9),
            repeat_penalty=llama_data.get('repeat_penalty', 1.1)
        )
        
        # Parse network config
        network_data = agent_data.get('network', {})
        network = AgentNetworkConfig(
            host=network_data.get('host', '127.0.0.1'),
            port=network_data.get('port', 8080)
        )
        
        # Parse health config
        health_data = agent_data.get('health', {})
        health = AgentHealthConfig(
            heartbeat_interval=health_data.get('heartbeat_interval', 10),
            max_missed_heartbeats=health_data.get('max_missed_heartbeats', 3),
            auto_restart=health_data.get('auto_restart', True)
        )
        
        # Parse memory config
        memory_data = agent_data.get('memory', {})
        
        return AgentConfig(
            id=agent_data.get('id', filepath.stem),
            name=agent_data.get('name', filepath.stem),
            enabled=agent_data.get('enabled', True),
            role=agent_data.get('role', 'coder'),
            node_id=agent_data.get('node_id', 'node-local'),
            model=model,
            llama_params=llama_params,
            network=network,
            health=health,
            log_messages=memory_data.get('log_messages', True),
            max_history=memory_data.get('max_history', 1000)
        )
    
    def reload_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Hot-reload a specific agent configuration.
        
        Args:
            agent_id: The agent ID to reload.
            
        Returns:
            Updated AgentConfig or None if not found.
        """
        yaml_file = self.agents_dir / f"{agent_id}.yaml"
        if not yaml_file.exists():
            logger.warning(f"Agent config file not found: {yaml_file}")
            return None
        
        try:
            with self._lock:
                agent = self._load_agent_file(yaml_file)
                self._agents[agent.id] = agent
                self._agent_mtimes[agent.id] = yaml_file.stat().st_mtime
            logger.info(f"Reloaded agent config: {agent_id}")
            return agent
        except Exception as e:
            logger.error(f"Failed to reload agent config {agent_id}: {e}")
            return None
    
    def check_agent_updates(self) -> List[str]:
        """
        Check for modified agent config files.
        
        Returns:
            List of agent IDs whose configs have been modified.
        """
        updated = []
        for yaml_file in self.agents_dir.glob("*.yaml"):
            agent_id = yaml_file.stem
            current_mtime = yaml_file.stat().st_mtime
            if agent_id in self._agent_mtimes:
                if current_mtime > self._agent_mtimes[agent_id]:
                    updated.append(agent_id)
            else:
                updated.append(agent_id)  # New config file
        return updated
    
    # ===============================
    # CRUD Operations for Agents
    # ===============================
    
    def create_agent_config(self, agent_id: str, config: Dict[str, Any]) -> AgentConfig:
        """
        Create a new agent configuration.
        
        Args:
            agent_id: Unique agent identifier.
            config: Agent configuration dictionary.
            
        Returns:
            Created AgentConfig.
            
        Raises:
            ConfigValidationError: If agent already exists or config is invalid.
        """
        yaml_file = self.agents_dir / f"{agent_id}.yaml"
        if yaml_file.exists():
            raise ConfigValidationError(f"Agent config already exists: {agent_id}")
        
        # Build complete config structure
        full_config = {
            'agent': {
                'id': agent_id,
                **config
            }
        }
        
        # Write to file
        with open(yaml_file, 'w') as f:
            yaml.dump(full_config, f, default_flow_style=False, sort_keys=False)
        
        # Reload and return
        return self.reload_agent_config(agent_id)
    
    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> Optional[AgentConfig]:
        """
        Update an existing agent configuration.
        
        Args:
            agent_id: Agent identifier.
            updates: Dictionary of fields to update.
            
        Returns:
            Updated AgentConfig or None if not found.
        """
        yaml_file = self.agents_dir / f"{agent_id}.yaml"
        if not yaml_file.exists():
            logger.warning(f"Agent config not found: {agent_id}")
            return None
        
        # Load current config
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Apply updates (shallow merge for simplicity, deep merge for nested dicts)
        def deep_update(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
            return base
        
        deep_update(data['agent'], updates)
        
        # Write back
        with open(yaml_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        # Reload and return
        return self.reload_agent_config(agent_id)
    
    def delete_agent_config(self, agent_id: str) -> bool:
        """
        Delete an agent configuration.
        
        Args:
            agent_id: Agent identifier.
            
        Returns:
            True if deleted, False if not found.
        """
        yaml_file = self.agents_dir / f"{agent_id}.yaml"
        if not yaml_file.exists():
            return False
        
        yaml_file.unlink()
        
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
            if agent_id in self._agent_mtimes:
                del self._agent_mtimes[agent_id]
        
        logger.info(f"Deleted agent config: {agent_id}")
        return True
    
    # ===============================
    # Getter Properties
    # ===============================
    
    @property
    def relay(self) -> Optional[RelayConfig]:
        """Get relay configuration."""
        return self._relay_config
    
    @property
    def nodes(self) -> Dict[str, NodeConfig]:
        """Get all node configurations."""
        return self._nodes.copy()
    
    @property
    def roles(self) -> Dict[str, RoleConfig]:
        """Get all role definitions."""
        return self._roles.copy()
    
    @property
    def agents(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations."""
        return self._agents.copy()
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._logging_config.copy()
    
    def get_node(self, node_id: str) -> Optional[NodeConfig]:
        """Get a specific node configuration."""
        return self._nodes.get(node_id)
    
    def get_role(self, role_id: str) -> Optional[RoleConfig]:
        """Get a specific role definition."""
        return self._roles.get(role_id)
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get a specific agent configuration."""
        return self._agents.get(agent_id)
    
    def get_agents_on_node(self, node_id: str) -> List[AgentConfig]:
        """Get all agents assigned to a specific node."""
        return [a for a in self._agents.values() if a.node_id == node_id]
    
    def get_agents_by_role(self, role: str) -> List[AgentConfig]:
        """Get all agents with a specific role."""
        return [a for a in self._agents.values() if a.role == role]
    
    def validate_role(self, role: str) -> bool:
        """Check if a role is valid."""
        return role in self._roles
    
    def validate_node(self, node_id: str) -> bool:
        """Check if a node is valid."""
        return node_id in self._nodes
