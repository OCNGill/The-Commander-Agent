"""
Test Suite: REST API
Tests for commander_os.interfaces.rest_api

Run with: pytest tests/interfaces/test_rest_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from commander_os.interfaces.rest_api import app
from commander_os.core.state import SystemStatus, NodeState, AgentState, ComponentStatus

# Create TestClient
client = TestClient(app)

class TestRestApi:
    """Tests for FastAPI endpoints."""
    
    @pytest.fixture
    def mock_system(self):
        """Mock the global 'system' object in rest_api module."""
        with patch('commander_os.interfaces.rest_api.system') as mock:
            # Setup default mock behaviors
            mock.state_manager.system_status = SystemStatus.STOPPED
            
            # Mock lists
            mock.state_manager.get_all_nodes.return_value = [
                NodeState(node_id='node-1', hostname='localhost', port=5556, status=ComponentStatus.READY)
            ]
            # FIX: Ensure this returns dicts, not Objects
            mock.agent_manager.list_agents.return_value = [
                AgentState(agent_id='agent-1', node_id='node-1', role='coder', status=ComponentStatus.READY).to_dict()
            ]
            
            # Mock Status returns
            mock.node_manager.get_node_status.return_value = {'id': 'node-1', 'status': 'ready'}
            mock.agent_manager.get_agent_status.return_value = {'id': 'agent-1', 'status': 'ready'}
            
            # Mock Actions
            mock.start_system.return_value = True
            mock.node_manager.start_node.return_value = True
            mock.node_manager.stop_node.return_value = True
            mock.agent_manager.start_agent.return_value = True
            mock.agent_manager.stop_agent.return_value = True
            mock.agent_manager.config_agent.return_value = True
            mock.agent_manager.set_agent_role.return_value = True
            
            # Mock Memory
            mock.memory_store.query_messages.return_value = []
            
            yield mock

    def test_system_endpoints(self, mock_system):
        """Test system start/stop/status."""
        # Status
        mock_system.get_status_report.return_value = {'system': {'status': 'stopped'}}
        r = client.get("/system/status")
        assert r.status_code == 200
        assert r.json()['system']['status'] == 'stopped'
        
        # Start
        r = client.post("/system/start")
        assert r.status_code == 200
        assert r.json()['success'] is True
        mock_system.start_system.assert_called_once()
        
        # Stop
        r = client.post("/system/stop")
        assert r.status_code == 200
        mock_system.stop_system.assert_called_once()

    def test_node_endpoints(self, mock_system):
        """Test node listing and control."""
        # List
        r = client.get("/nodes")
        assert r.status_code == 200
        nodes = r.json()
        assert len(nodes) == 1
        assert nodes[0]['node_id'] == 'node-1'
        
        # Get Status
        r = client.get("/nodes/node-1/status")
        assert r.status_code == 200
        assert r.json()['id'] == 'node-1'
        
        # Start
        r = client.post("/nodes/node-1/start")
        assert r.status_code == 200
        mock_system.node_manager.start_node.assert_called_with('node-1')
        
        # Stop
        r = client.post("/nodes/node-1/stop")
        assert r.status_code == 200
        mock_system.node_manager.stop_node.assert_called_with('node-1')

    def test_agent_endpoints(self, mock_system):
        """Test agent listing and control."""
        # List
        r = client.get("/agents")
        assert r.status_code == 200
        assert len(r.json()) == 1
        
        # Start
        r = client.post("/agents/agent-1/start")
        assert r.status_code == 200
        mock_system.agent_manager.start_agent.assert_called_with('agent-1')
        
        # Stop
        r = client.post("/agents/agent-1/stop")
        assert r.status_code == 200
        mock_system.agent_manager.stop_agent.assert_called_with('agent-1')
        
        # Config
        payload = {'config': {'context_size': 4096}}
        r = client.patch("/agents/agent-1/config", json=payload)
        assert r.status_code == 200
        mock_system.agent_manager.config_agent.assert_called_with('agent-1', {'context_size': 4096})
        
        # Role
        payload = {'role': 'architect'}
        r = client.patch("/agents/agent-1/role", json=payload)
        assert r.status_code == 200
        mock_system.agent_manager.set_agent_role.assert_called_with('agent-1', 'architect')

    def test_memory_endpoint(self, mock_system):
        """Test memory search endpoint."""
        r = client.get("/memory/search?task_id=task-1")
        assert r.status_code == 200
        mock_system.memory_store.query_messages.assert_called()

    def test_uninitialized_system(self):
        """Test behavior when system is None."""
        with patch('commander_os.interfaces.rest_api.system', None):
            r = client.get("/system/status")
            assert r.status_code == 503
            assert "System not initialized" in r.json()['detail']
