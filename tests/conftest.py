"""
Pytest Configuration and Shared Fixtures
The-Commander Test Suite
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir():
    """Create a temporary directory that is cleaned up after the test."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_relay_config():
    """Return a sample relay configuration dictionary."""
    return {
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


@pytest.fixture
def sample_roles_config():
    """Return a sample roles configuration dictionary."""
    return {
        'roles': {
            'architect': {
                'name': 'Architect',
                'description': 'High-level system design and task decomposition',
                'system_prompt_prefix': 'You are the Architect agent...',
                'default_context_size': 16384,
                'priority': 1,
                'can_delegate_to': ['coder', 'reasoner', 'synthesizer'],
                'permissions': ['read', 'write', 'delegate', 'create_tasks']
            },
            'coder': {
                'name': 'Coder',
                'description': 'Implementation and code generation',
                'system_prompt_prefix': 'You are the Coder agent...',
                'default_context_size': 8192,
                'priority': 2,
                'can_delegate_to': ['reasoner'],
                'permissions': ['read', 'write', 'execute']
            },
            'reasoner': {
                'name': 'Reasoner',
                'description': 'Logical analysis and problem solving',
                'system_prompt_prefix': 'You are the Reasoner agent...',
                'default_context_size': 12288,
                'priority': 2,
                'can_delegate_to': [],
                'permissions': ['read', 'analyze']
            },
            'synthesizer': {
                'name': 'Synthesizer',
                'description': 'Combining outputs and summarization',
                'system_prompt_prefix': 'You are the Synthesizer agent...',
                'default_context_size': 8192,
                'priority': 3,
                'can_delegate_to': [],
                'permissions': ['read', 'summarize']
            }
        }
    }


@pytest.fixture
def sample_agent_config():
    """Return a sample agent configuration dictionary."""
    return {
        'agent': {
            'id': 'test-agent',
            'name': 'Test Agent',
            'enabled': True,
            'role': 'coder',
            'node_id': 'node-local',
            'model': {
                'path': '/models/test-model.gguf',
                'context_size': 8192,
                'ngl': 40,
                'flash_attention': True
            },
            'llama_params': {
                'threads': 8,
                'batch_size': 512,
                'ubatch_size': 64,
                'temperature': 0.7,
                'top_k': 40,
                'top_p': 0.9,
                'repeat_penalty': 1.1
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


@pytest.fixture
def complete_config_dir(temp_dir, sample_relay_config, sample_roles_config, sample_agent_config):
    """Create a complete configuration directory with all required files."""
    config_dir = temp_dir / "config"
    agents_dir = config_dir / "agents"
    agents_dir.mkdir(parents=True)
    
    # Write relay.yaml
    with open(config_dir / "relay.yaml", 'w') as f:
        yaml.dump(sample_relay_config, f)
    
    # Write roles.yaml
    with open(config_dir / "roles.yaml", 'w') as f:
        yaml.dump(sample_roles_config, f)
    
    # Write agent config
    with open(agents_dir / "test-agent.yaml", 'w') as f:
        yaml.dump(sample_agent_config, f)
    
    return config_dir
