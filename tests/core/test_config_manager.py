"""
Test Suite: ConfigManager
Tests for commander_os.core.config_manager

Run with: pytest tests/core/test_config_manager.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

from commander_os.core.config_manager import (
    ConfigManager,
    ConfigValidationError,
    RelayConfig,
    NodeConfig,
    RoleConfig,
    AgentConfig,
)


class TestConfigManagerSetup:
    """Test ConfigManager initialization and setup."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory with sample configs."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create sample relay.yaml
        relay_config = {
            'relay': {
                'host': '127.0.0.1',
                'port': 5555,
                'protocol': 'tcp',
                'heartbeat_interval': 5,
                'connection_timeout': 30
            },
            'nodes': [
                {
                    'id': 'node-local',
                    'name': 'Local Development Node',
                    'host': '127.0.0.1',
                    'port': 5556,
                    'enabled': True,
                    'max_agents': 4
                }
            ],
            'logging': {
                'level': 'INFO',
                'file': 'logs/commander.log'
            }
        }
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        # Create sample roles.yaml
        roles_config = {
            'roles': {
                'architect': {
                    'name': 'Architect',
                    'description': 'High-level system design',
                    'system_prompt_prefix': 'You are an architect...',
                    'default_context_size': 16384,
                    'priority': 1,
                    'can_delegate_to': ['coder', 'reasoner'],
                    'permissions': ['read', 'write', 'delegate']
                },
                'coder': {
                    'name': 'Coder',
                    'description': 'Implementation specialist',
                    'system_prompt_prefix': 'You are a coder...',
                    'default_context_size': 8192,
                    'priority': 2,
                    'can_delegate_to': ['reasoner'],
                    'permissions': ['read', 'write']
                }
            }
        }
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        # Create sample agent config
        agent_config = {
            'agent': {
                'id': 'test-agent',
                'name': 'Test Agent',
                'enabled': True,
                'role': 'coder',
                'node_id': 'node-local',
                'model': {
                    'path': '/models/test.gguf',
                    'context_size': 8192,
                    'ngl': 40,
                    'flash_attention': True
                },
                'llama_params': {
                    'threads': 8,
                    'batch_size': 512,
                    'temperature': 0.7
                },
                'network': {
                    'host': '127.0.0.1',
                    'port': 8080
                },
                'health': {
                    'heartbeat_interval': 10,
                    'max_missed_heartbeats': 3,
                    'auto_restart': True
                },
                'memory': {
                    'log_messages': True,
                    'max_history': 1000
                }
            }
        }
        with open(agents_dir / "test-agent.yaml", 'w') as f:
            yaml.dump(agent_config, f)
        
        yield config_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_init_with_default_path(self):
        """Test ConfigManager initializes with default config path."""
        cm = ConfigManager()
        assert cm.config_dir.name == "config"
        assert cm.relay_config_path.name == "relay.yaml"
        assert cm.roles_config_path.name == "roles.yaml"

    def test_init_with_custom_path(self, temp_config_dir):
        """Test ConfigManager initializes with custom config path."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        assert cm.config_dir == temp_config_dir


class TestRelayConfigLoading:
    """Test relay.yaml loading functionality."""

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager with temp config."""
        return ConfigManager(config_dir=str(temp_config_dir))

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        relay_config = {
            'relay': {
                'host': '192.168.1.100',
                'port': 6666,
                'protocol': 'tcp',
                'heartbeat_interval': 10,
                'connection_timeout': 60
            },
            'nodes': [
                {'id': 'node-1', 'name': 'Node 1', 'host': '127.0.0.1', 'port': 5556},
                {'id': 'node-2', 'name': 'Node 2', 'host': '127.0.0.1', 'port': 5557}
            ]
        }
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        roles_config = {'roles': {'coder': {'name': 'Coder', 'description': 'Test'}}}
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        yield config_dir
        shutil.rmtree(temp_dir)

    def test_load_relay_config(self, config_manager):
        """Test loading relay configuration."""
        relay = config_manager.load_relay_config()
        
        assert isinstance(relay, RelayConfig)
        assert relay.host == '192.168.1.100'
        assert relay.port == 6666
        assert relay.protocol == 'tcp'
        assert relay.heartbeat_interval == 10
        assert relay.connection_timeout == 60

    def test_load_nodes_from_relay(self, config_manager):
        """Test loading nodes from relay.yaml."""
        config_manager.load_relay_config()
        nodes = config_manager.nodes
        
        assert len(nodes) == 2
        assert 'node-1' in nodes
        assert 'node-2' in nodes
        assert nodes['node-1'].port == 5556
        assert nodes['node-2'].port == 5557

    def test_relay_config_missing_file(self):
        """Test error when relay.yaml is missing."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        cm = ConfigManager(config_dir=str(config_dir))
        
        with pytest.raises(FileNotFoundError):
            cm.load_relay_config()
        
        shutil.rmtree(temp_dir)

    def test_relay_config_missing_section(self):
        """Test error when 'relay' section is missing."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir()
        
        # Create invalid relay.yaml without 'relay' section
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump({'nodes': []}, f)
        
        cm = ConfigManager(config_dir=str(config_dir))
        
        with pytest.raises(ConfigValidationError):
            cm.load_relay_config()
        
        shutil.rmtree(temp_dir)


class TestRolesConfigLoading:
    """Test roles.yaml loading functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config with roles."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        relay_config = {'relay': {'host': '127.0.0.1', 'port': 5555}}
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        roles_config = {
            'roles': {
                'architect': {
                    'name': 'Architect',
                    'description': 'System designer',
                    'system_prompt_prefix': 'You design systems...',
                    'default_context_size': 16384,
                    'priority': 1,
                    'can_delegate_to': ['coder', 'reasoner'],
                    'permissions': ['read', 'write', 'delegate']
                },
                'coder': {
                    'name': 'Coder',
                    'description': 'Implementation',
                    'system_prompt_prefix': 'You write code...',
                    'default_context_size': 8192,
                    'priority': 2
                }
            }
        }
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        yield config_dir
        shutil.rmtree(temp_dir)

    def test_load_roles_config(self, temp_config_dir):
        """Test loading roles configuration."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        roles = cm.load_roles_config()
        
        assert len(roles) == 2
        assert 'architect' in roles
        assert 'coder' in roles

    def test_role_properties(self, temp_config_dir):
        """Test role properties are loaded correctly."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        cm.load_roles_config()
        
        architect = cm.get_role('architect')
        assert architect.name == 'Architect'
        assert architect.priority == 1
        assert 'coder' in architect.can_delegate_to
        assert 'delegate' in architect.permissions

    def test_validate_role(self, temp_config_dir):
        """Test role validation."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        cm.load_roles_config()
        
        assert cm.validate_role('architect') is True
        assert cm.validate_role('coder') is True
        assert cm.validate_role('nonexistent') is False


class TestAgentConfigLoading:
    """Test agent configuration loading."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config with agents."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        relay_config = {'relay': {'host': '127.0.0.1', 'port': 5555}, 'nodes': [{'id': 'node-local'}]}
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        roles_config = {'roles': {'coder': {'name': 'Coder'}}}
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        # Create multiple agent configs
        for i in range(3):
            agent_config = {
                'agent': {
                    'id': f'agent-{i}',
                    'name': f'Agent {i}',
                    'role': 'coder',
                    'node_id': 'node-local',
                    'model': {'path': f'/models/model{i}.gguf', 'context_size': 8192}
                }
            }
            with open(agents_dir / f"agent-{i}.yaml", 'w') as f:
                yaml.dump(agent_config, f)
        
        yield config_dir
        shutil.rmtree(temp_dir)

    def test_load_all_agent_configs(self, temp_config_dir):
        """Test loading all agent configurations."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        agents = cm.load_all_agent_configs()
        
        assert len(agents) == 3
        assert 'agent-0' in agents
        assert 'agent-1' in agents
        assert 'agent-2' in agents

    def test_agent_properties(self, temp_config_dir):
        """Test agent properties are loaded correctly."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        cm.load_all_agent_configs()
        
        agent = cm.get_agent('agent-0')
        assert agent.id == 'agent-0'
        assert agent.name == 'Agent 0'
        assert agent.role == 'coder'
        assert agent.model.path == '/models/model0.gguf'

    def test_get_agents_on_node(self, temp_config_dir):
        """Test filtering agents by node."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        cm.load_all_agent_configs()
        
        agents = cm.get_agents_on_node('node-local')
        assert len(agents) == 3

    def test_get_agents_by_role(self, temp_config_dir):
        """Test filtering agents by role."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        cm.load_all_agent_configs()
        
        agents = cm.get_agents_by_role('coder')
        assert len(agents) == 3


class TestAgentConfigCRUD:
    """Test CRUD operations for agent configurations."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config for CRUD tests."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        relay_config = {'relay': {'host': '127.0.0.1', 'port': 5555}}
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        roles_config = {'roles': {'coder': {'name': 'Coder'}}}
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        yield config_dir
        shutil.rmtree(temp_dir)

    def test_create_agent_config(self, temp_config_dir):
        """Test creating a new agent configuration."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        
        new_agent = cm.create_agent_config('new-agent', {
            'name': 'New Agent',
            'role': 'coder',
            'model': {'path': '/models/new.gguf'}
        })
        
        assert new_agent.id == 'new-agent'
        assert new_agent.name == 'New Agent'
        assert (temp_config_dir / "agents" / "new-agent.yaml").exists()

    def test_create_duplicate_agent_fails(self, temp_config_dir):
        """Test that creating duplicate agent fails."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        
        cm.create_agent_config('agent-1', {'name': 'Agent 1'})
        
        with pytest.raises(ConfigValidationError):
            cm.create_agent_config('agent-1', {'name': 'Agent 1 Duplicate'})

    def test_update_agent_config(self, temp_config_dir):
        """Test updating an existing agent configuration."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        
        cm.create_agent_config('test-agent', {'name': 'Original Name', 'role': 'coder'})
        
        updated = cm.update_agent_config('test-agent', {'name': 'Updated Name'})
        
        assert updated.name == 'Updated Name'

    def test_delete_agent_config(self, temp_config_dir):
        """Test deleting an agent configuration."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        
        cm.create_agent_config('delete-me', {'name': 'To Delete'})
        assert cm.get_agent('delete-me') is not None
        
        result = cm.delete_agent_config('delete-me')
        
        assert result is True
        assert cm.get_agent('delete-me') is None
        assert not (temp_config_dir / "agents" / "delete-me.yaml").exists()

    def test_delete_nonexistent_agent(self, temp_config_dir):
        """Test deleting a nonexistent agent returns False."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        
        result = cm.delete_agent_config('nonexistent')
        
        assert result is False


class TestHotReload:
    """Test hot-reload functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config for hot-reload tests."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        relay_config = {'relay': {'host': '127.0.0.1', 'port': 5555}}
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        roles_config = {'roles': {'coder': {'name': 'Coder'}}}
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        agent_config = {'agent': {'id': 'hot-reload-agent', 'name': 'Original'}}
        with open(agents_dir / "hot-reload-agent.yaml", 'w') as f:
            yaml.dump(agent_config, f)
        
        yield config_dir
        shutil.rmtree(temp_dir)

    def test_reload_agent_config(self, temp_config_dir):
        """Test reloading a specific agent configuration."""
        cm = ConfigManager(config_dir=str(temp_config_dir))
        cm.load_all_agent_configs()
        
        assert cm.get_agent('hot-reload-agent').name == 'Original'
        
        # Modify the file
        agent_file = temp_config_dir / "agents" / "hot-reload-agent.yaml"
        with open(agent_file, 'w') as f:
            yaml.dump({'agent': {'id': 'hot-reload-agent', 'name': 'Modified'}}, f)
        
        # Reload
        reloaded = cm.reload_agent_config('hot-reload-agent')
        
        assert reloaded.name == 'Modified'
        assert cm.get_agent('hot-reload-agent').name == 'Modified'


class TestLoadAll:
    """Test loading all configurations at once."""

    @pytest.fixture
    def complete_config_dir(self):
        """Create a complete configuration directory."""
        temp_dir = tempfile.mkdtemp()
        config_dir = Path(temp_dir) / "config"
        agents_dir = config_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        relay_config = {
            'relay': {'host': '127.0.0.1', 'port': 5555},
            'nodes': [{'id': 'node-1'}]
        }
        with open(config_dir / "relay.yaml", 'w') as f:
            yaml.dump(relay_config, f)
        
        roles_config = {'roles': {'coder': {'name': 'Coder'}}}
        with open(config_dir / "roles.yaml", 'w') as f:
            yaml.dump(roles_config, f)
        
        agent_config = {'agent': {'id': 'agent-1', 'name': 'Agent 1'}}
        with open(agents_dir / "agent-1.yaml", 'w') as f:
            yaml.dump(agent_config, f)
        
        yield config_dir
        shutil.rmtree(temp_dir)

    def test_load_all_success(self, complete_config_dir):
        """Test loading all configs successfully."""
        cm = ConfigManager(config_dir=str(complete_config_dir))
        result = cm.load_all()
        
        assert result is True
        assert cm.relay is not None
        assert len(cm.nodes) == 1
        assert len(cm.roles) == 1
        assert len(cm.agents) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
