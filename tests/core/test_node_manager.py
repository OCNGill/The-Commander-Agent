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
        # Authoritative benchmarks: Main (130) > HTPC (60) > SteamDeck (30) > Laptop (9)
        nodes = {
            'node-main': NodeConfig(id='node-main', name='Main', host='10.0.0.164', port=8000, tps_benchmark=130),
            'node-htpc': NodeConfig(id='node-htpc', name='HTPC', host='10.0.0.42', port=8001, tps_benchmark=60),
            'node-steamdeck': NodeConfig(id='node-steamdeck', name='SteamDeck', host='10.0.0.139', port=8003, tps_benchmark=30),
            'node-laptop': NodeConfig(id='node-laptop', name='Laptop', host='10.0.0.93', port=8002, tps_benchmark=9)
        }
        type(mock).nodes = PropertyMock(return_value=nodes)
        return mock

    @pytest.fixture
    def mock_state(self):
        """Mock StateManager."""
        mock = MagicMock()
        
        # Mock get_node to return a READY state for all nodes except laptop
        def get_node_side_effect(node_id):
            if node_id == 'node-laptop':
                node = MagicMock()
                node.status = ComponentStatus.OFFLINE
                return node
            node = MagicMock()
            node.status = ComponentStatus.READY
            return node
            
        mock.get_node.side_effect = get_node_side_effect
        return mock

    @pytest.fixture
    def node_manager(self, mock_config, mock_state):
        """Create NodeManager with mocks."""
        return NodeManager(mock_config, mock_state, local_node_id='node-main')

    def test_start_all_nodes(self, node_manager, mock_state):
        """Test starting all configured nodes."""
        node_manager.start_all_nodes()
        
        # Should register all 4
        assert mock_state.register_node.call_count == 4
        
        # Should start local node logic
        mock_state.register_node.assert_any_call(node_id='node-main', hostname='10.0.0.164', port=8000)
        
        # Local node (node-main) should transition STARTING -> READY
        mock_state.update_node_status.assert_any_call('node-main', ComponentStatus.STARTING)
        mock_state.update_node_status.assert_any_call('node-main', ComponentStatus.READY)

    def test_lifecycle_single_node(self, node_manager, mock_state):
        """Test individual node start/stop."""
        # Start
        node_manager.start_node('node-htpc')
        mock_state.update_node_status.assert_any_call('node-htpc', ComponentStatus.STARTING)
        mock_state.update_node_status.assert_any_call('node-htpc', ComponentStatus.READY)
        
        # Stop
        node_manager.stop_node('node-htpc')
        mock_state.update_node_status.assert_called_with('node-htpc', ComponentStatus.OFFLINE)

    def test_monitoring_thread(self, node_manager):
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
        node_manager._stop_event = MagicMock()
        node_manager._stop_event.is_set.side_effect = [False, True] # Run once then stop
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr(time, 'sleep', lambda x: None)
            node_manager._monitor_loop()
            
        # Verify heartbeat sent for local node
        mock_state.update_node_heartbeat.assert_called_with('node-main')
        
        # Verify pruning was called
        mock_state.prune_stale_components.assert_called()

    def test_get_best_worker_node(self, node_manager, mock_state):
        """Test load balancing logic based on benchmarks."""
        # Main (130) is READY in mock_state
        # HTPC (60) is READY in mock_state
        # SteamDeck (30) is READY in mock_state
        # Laptop (9) is OFFLINE in mock_state
        
        best_node = node_manager.get_best_worker_node()
        
        # Should pick node-main as it has highest TPS
        assert best_node == 'node-main'
        
        # Now if node-main goes offline
        def get_node_side_effect_no_main(node_id):
            if node_id in ['node-main', 'node-laptop']:
                node = MagicMock()
                node.status = ComponentStatus.OFFLINE
                return node
            node = MagicMock()
            node.status = ComponentStatus.READY
            return node
            
        mock_state.get_node.side_effect = get_node_side_effect_no_main
        
        best_node_2 = node_manager.get_best_worker_node()
        # Should pick node-htpc (60)
        assert best_node_2 == 'node-htpc'
