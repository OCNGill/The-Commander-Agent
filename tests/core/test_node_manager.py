"""
Test Suite: NodeManager
Tests for commander_os.core.node_manager

Run with: pytest tests/core/test_node_manager.py -v
"""

import pytest
import time
from unittest.mock import MagicMock, PropertyMock

from commander_os.core.node_manager import NodeManager
from commander_os.core.config_manager import NodeConfig
from commander_os.core.state import ComponentStatus

class TestNodeManager:
    """Tests for the NodeManager class."""

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager."""
        mock = MagicMock()
        nodes = {
            'node-local': NodeConfig(id='node-local', name='Local', host='localhost', port=5556),
            'node-remote': NodeConfig(id='node-remote', name='Remote', host='192.168.1.10', port=5557)
        }
        type(mock).nodes = PropertyMock(return_value=nodes)
        return mock

    @pytest.fixture
    def mock_state(self):
        """Mock StateManager."""
        return MagicMock()

    @pytest.fixture
    def node_manager(self, mock_config, mock_state):
        """Create NodeManager with mocks."""
        return NodeManager(mock_config, mock_state)

    def test_start_all_nodes(self, node_manager, mock_state):
        """Test starting all configured nodes."""
        node_manager.start_all_nodes()
        
        # Should register both
        assert mock_state.register_node.call_count == 2
        
        # Should start local node logic
        # register_node args: node_id, hostname, port
        mock_state.register_node.assert_any_call(node_id='node-local', hostname='localhost', port=5556)
        
        # Local node should transition STARTING -> READY
        mock_state.update_node_status.assert_any_call('node-local', ComponentStatus.STARTING)
        mock_state.update_node_status.assert_any_call('node-local', ComponentStatus.READY)
        
        # Remote node should NOT be explicitly started (only registered)
        # We verify we didn't call update_node_status for remote with READY
        calls = mock_state.update_node_status.call_args_list
        remote_ready = any(c[0][0] == 'node-remote' and c[0][1] == ComponentStatus.READY for c in calls)
        assert not remote_ready

    def test_lifecycle_single_node(self, node_manager, mock_state):
        """Test individual node start/stop."""
        # Start
        node_manager.start_node('node-1')
        mock_state.update_node_status.assert_any_call('node-1', ComponentStatus.STARTING)
        mock_state.update_node_status.assert_any_call('node-1', ComponentStatus.READY)
        
        # Stop
        node_manager.stop_node('node-1')
        mock_state.update_node_status.assert_called_with('node-1', ComponentStatus.OFFLINE)

    def test_monitoring_thread(self, node_manager, mock_state):
        """Test that monitoring thread starts and stops."""
        node_manager._start_monitoring()
        
        assert node_manager._monitor_thread is not None
        assert node_manager._monitor_thread.is_alive()
        
        # Let it run a cycle
        time.sleep(0.1)
        
        node_manager._stop_monitoring()
        assert not node_manager._monitor_thread

    def test_monitor_loop_logic(self, node_manager, mock_state):
        """Test logic inside monitor loop (heartbeats)."""
        # Run one iteration of the loop logic manually to avoid timing fragility
        node_manager._stop_event = MagicMock()
        node_manager._stop_event.is_set.side_effect = [False, True] # Run once then stop
        
        # Mock sleep to avoid waiting
        with pytest.MonkeyPatch().context() as m:
            m.setattr(time, 'sleep', lambda x: None)
            node_manager._monitor_loop()
            
        # Verify heartbeat sent for local node
        mock_state.update_node_heartbeat.assert_called_with('node-local')
        
        # Verify pruning was called
        mock_state.prune_stale_components.assert_called()

    def test_stop_all_nodes(self, node_manager, mock_state):
        """Test stopping everything."""
        # Start first
        node_manager._start_monitoring()
        
        node_manager.stop_all_nodes()
        
        # Should stop monitoring
        assert node_manager._monitor_thread is None
        
        # Should stop local node
        mock_state.update_node_status.assert_called_with('node-local', ComponentStatus.OFFLINE)
