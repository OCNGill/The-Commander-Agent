"""
Test Suite: SystemManager
Tests for commander_os.core.system_manager

Run with: pytest tests/core/test_system_manager.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from commander_os.core.system_manager import SystemManager
from commander_os.core.state import SystemStatus

class TestSystemManager:
    """Tests for the SystemManager class."""

    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager."""
        with patch('commander_os.core.system_manager.ConfigManager') as mock:
            instance = mock.return_value
            instance.load_all.return_value = True
            # Mock config_dir.parent to return a valid path
            instance.config_dir = MagicMock()
            instance.config_dir.parent = MagicMock()
            yield instance

    @pytest.fixture
    def mock_node_manager(self):
        """Mock NodeManager."""
        with patch('commander_os.core.system_manager.NodeManager') as mock:
            yield mock.return_value

    @pytest.fixture
    def mock_agent_manager(self):
        """Mock AgentManager."""
        with patch('commander_os.core.system_manager.AgentManager') as mock:
            yield mock.return_value

    @pytest.fixture
    def system_manager(self, mock_config_manager, mock_node_manager, mock_agent_manager):
        """Create SystemManager instance with mocks and patched relay start."""
        with patch.object(SystemManager, '_start_relay_server'), patch.object(SystemManager, '_stop_relay_server'):
            yield SystemManager()

    def test_initialization(self, system_manager):
        """Test proper initialization of components."""
        assert system_manager.config_manager is not None
        assert system_manager.state_manager is not None
        assert system_manager.node_manager is not None
        assert system_manager.agent_manager is not None
        assert system_manager.state_manager.system_status == SystemStatus.STOPPED

    def test_bootstrap_success(self, system_manager):
        """Test successful bootstrap."""
        success = system_manager.bootstrap()
        assert success is True
        system_manager.config_manager.load_all.assert_called_once()

    def test_bootstrap_failure(self, system_manager, mock_config_manager):
        """Test bootstrap failure when config loading fails."""
        mock_config_manager.load_all.return_value = False
        
        success = system_manager.bootstrap()
        
        assert success is False
        assert system_manager.state_manager.system_status == SystemStatus.ERROR

    def test_start_system_success(self, system_manager, mock_node_manager, mock_agent_manager):
        """Test successful full system startup."""
        success = system_manager.start_system()
        
        assert success is True
        assert system_manager.state_manager.system_status == SystemStatus.RUNNING
        
        # Verify call order/presence
        mock_node_manager.start_all_nodes.assert_called_once()
        mock_agent_manager.start_all_agents.assert_called_once()

    def test_start_system_already_running(self, system_manager):
        """Test idempotency when already running."""
        system_manager.state_manager.set_system_status(SystemStatus.RUNNING)
        
        success = system_manager.start_system()
        
        assert success is True
        system_manager.config_manager.load_all.assert_not_called()

    def test_stop_system(self, system_manager, mock_node_manager, mock_agent_manager):
        """Test graceful shutdown."""
        system_manager.state_manager.set_system_status(SystemStatus.RUNNING)
        
        system_manager.stop_system()
        
        assert system_manager.state_manager.system_status == SystemStatus.STOPPED
        mock_agent_manager.stop_all_agents.assert_called_once()
        mock_node_manager.stop_all_nodes.assert_called_once()

    def test_exception_handling(self, system_manager, mock_node_manager):
        """Test error handling during startup."""
        mock_node_manager.start_all_nodes.side_effect = Exception("Node failure")
        
        success = system_manager.start_system()
        
        assert success is False
        assert system_manager.state_manager.system_status == SystemStatus.STOPPED
        
    def test_status_report(self, system_manager):
        """Test status report generation."""
        system_manager.state_manager.set_system_status(SystemStatus.RUNNING)
        report = system_manager.get_status_report()
        
        assert "system" in report
        assert report["system"]["status"] == "running"
