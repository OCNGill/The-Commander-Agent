"""
Test Suite: AgentManager
Tests for commander_os.core.agent_manager

Run with: pytest tests/core/test_agent_manager.py -v
"""

import pytest
import time
from unittest.mock import MagicMock, PropertyMock

from commander_os.core.agent_manager import AgentManager
from commander_os.core.config_manager import AgentConfig
from commander_os.core.state import ComponentStatus
from commander_os.core.protocol import TaskDefinition, MessageType

class TestAgentManager:
    """Tests for the AgentManager class."""

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager."""
        mock = MagicMock()
        
        # Sample Agent Config - Aligned to node-main
        self.agent1 = AgentConfig(
            id='agent-1', name='Agent 1', enabled=True, role='coder', node_id='node-main'
        )
        self.agent_remote = AgentConfig(
            id='agent-remote', name='Remote', enabled=True, role='coder', node_id='node-remote'
        )
        
        mock.get_agent.side_effect = lambda aid: {
            'agent-1': self.agent1,
            'agent-remote': self.agent_remote
        }.get(aid)
        
        mock.get_agents_on_node.return_value = [self.agent1]
        mock.validate_role.return_value = True
        mock.update_agent_config.return_value = self.agent1
        
        return mock

    @pytest.fixture
    def mock_state(self):
        """Mock StateManager."""
        mock = MagicMock()
        # Mock get_agent to return an AgentState object
        agent_state = MagicMock()
        agent_state.status = ComponentStatus.READY
        agent_state.role = 'coder'
        mock.get_agent.return_value = agent_state
        return mock

    @pytest.fixture
    def agent_manager(self, mock_config, mock_state):
        """Create AgentManager with mocks."""
        return AgentManager(mock_config, mock_state, local_node_id="node-main")

    def test_start_all_agents(self, agent_manager, mock_state):
        """Test starting all local agents."""
        agent_manager.start_all_agents()
        
        # Should register agent-1
        mock_state.register_agent.assert_called_with(
            agent_id='agent-1', node_id='node-main', role='coder'
        )
        
        # Should update status to STARTING then READY
        mock_state.update_agent_status.assert_any_call('agent-1', ComponentStatus.STARTING)
        mock_state.update_agent_status.assert_any_call('agent-1', ComponentStatus.READY)
        
        # Should track process
        assert 'agent-1' in agent_manager._processes

    def test_start_remote_agent_skips(self, agent_manager, mock_state):
        """Test that remote agents are registered but NOT started."""
        result = agent_manager.start_agent('agent-remote')
        
        assert result is True  # Success means "handled correctly"
        
        # Should register
        mock_state.register_agent.assert_called_with(
            agent_id='agent-remote', node_id='node-remote', role='coder'
        )
        
        # But NOT update status to STARTING (because we don't control process)
        # Note: register_agent sets it to STARTING in state manager default, but update_agent_status 
        # is the explicit signal that we are launching it.
        mock_state.update_agent_status.assert_not_called()
        
        # Process not tracked
        assert 'agent-remote' not in agent_manager._processes

    def test_stop_agent(self, agent_manager, mock_state):
        """Test stopping an agent."""
        # Start first
        agent_manager.start_agent('agent-1')
        assert 'agent-1' in agent_manager._processes
        
        # Stop
        result = agent_manager.stop_agent('agent-1')
        
        assert result is True
        assert 'agent-1' not in agent_manager._processes
        mock_state.update_agent_status.assert_called_with('agent-1', ComponentStatus.OFFLINE)

    def test_config_agent_restart(self, agent_manager):
        """Test that config update triggers restart."""
        # Start first
        agent_manager.start_agent('agent-1')
        original_proc = agent_manager._processes['agent-1']
        
        # Update config
        agent_manager.config_agent('agent-1', {'context_size': 4096})
        
        # Should be running
        assert 'agent-1' in agent_manager._processes
        # Process handle should satisfy "restarted" (new object or same ID logic depending on impl)
        # In our mock impl, the object reference changes on start_agent call
        new_proc = agent_manager._processes['agent-1']
        
        assert new_proc is not original_proc

    def test_set_agent_role(self, agent_manager, mock_state, mock_config):
        """Test dynamic role change."""
        agent_manager.set_agent_role('agent-1', 'architect')
        
        mock_state.update_agent_role.assert_called_with('agent-1', 'architect')
        mock_config.update_agent_config.assert_called_with('agent-1', {'role': 'architect'})

    def test_stop_all_agents(self, agent_manager, mock_state):
        """Test stopping all agents."""
        agent_manager.start_agent('agent-1')
        
        agent_manager.stop_all_agents()
        
        assert len(agent_manager._processes) == 0
        mock_state.update_agent_status.assert_called_with('agent-1', ComponentStatus.OFFLINE)

    def test_execute_task_protocol(self, agent_manager, mock_state):
        """Test task execution returning protocol-compliant envelope."""
        agent_manager.start_agent('agent-1')
        
        task = TaskDefinition(
            title="Test Task",
            description="A test problem",
            assigned_to_role="coder"
        )
        
        response = agent_manager.execute_task('agent-1', task)
        
        assert response.msg_type == MessageType.RESPONSE
        assert response.recipient_id == "commander"
        assert response.task_id == task.id
        assert "data" in response.payload
        assert response.payload["data"]["content"] == f"Execution result for task 'Test Task' by role coder."
        assert response.payload["data"]["task_id"] == task.id
        
        # Status should have toggled to BUSY then READY
        mock_state.update_agent_status.assert_any_call('agent-1', ComponentStatus.BUSY)
        mock_state.update_agent_status.assert_any_call('agent-1', ComponentStatus.READY)
