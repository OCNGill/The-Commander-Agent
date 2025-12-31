"""
Test Suite: TUI Dashboard
Tests for commander_os.interfaces.tui

Run with: pytest tests/interfaces/test_tui.py -v
"""

import pytest
from unittest.mock import MagicMock
from io import StringIO
from rich.console import Console
from commander_os.interfaces.tui import CommanderTUI
from commander_os.core.state import SystemStatus, ComponentStatus

class TestTUI:
    """Tests for the CommanderTUI class."""

    @pytest.fixture
    def mock_system_manager(self):
        """Create a SystemManager with mocked data."""
        sm = MagicMock()
        
        # Mock Config
        node_cfg = MagicMock()
        node_cfg.id = "node-main"
        node_cfg.host = "10.0.0.164"
        node_cfg.port = 8000
        node_cfg.tps_benchmark = 130
        sm.config_manager.nodes = {"node-main": node_cfg}
        
        # Mock State
        sm.state_manager.system_status = SystemStatus.RUNNING
        
        node_state = MagicMock()
        node_state.status = ComponentStatus.READY
        sm.state_manager.get_node.return_value = node_state
        
        agent_state = MagicMock()
        agent_state.id = "agent-1"
        agent_state.role = "coder"
        agent_state.node_id = "node-main"
        agent_state.status = ComponentStatus.READY
        sm.state_manager.get_all_agents.return_value = [agent_state]
        
        return sm

    def test_tui_layout_generation(self, mock_system_manager):
        """Verify that panels generate without error and contain correct text."""
        tui = CommanderTUI(mock_system_manager)
        console = Console(file=StringIO(), force_terminal=True, width=100)
        
        # 1. Header
        header = tui.generate_header()
        with console.capture() as capture:
            console.print(header)
        output = capture.get()
        assert "THE COMMANDER OS" in output
        assert "STATUS: RUNNING" in output
        
        # 2. Nodes
        nodes = tui.generate_nodes_table()
        with console.capture() as capture:
            console.print(nodes)
        output = capture.get()
        assert "node-main" in output
        assert "130 t/s" in output
        assert "READY" in output
        
        # 3. Agents
        agents = tui.generate_agents_table()
        with console.capture() as capture:
            console.print(agents)
        output = capture.get()
        assert "agent-1" in output
        assert "coder" in output
        assert "node-main" in output

        # 4. Logs
        logs = tui.generate_logs_panel()
        with console.capture() as capture:
            console.print(logs)
        output = capture.get()
        assert "Cluster Traffic" in output

    def test_tui_empty_state_handling(self):
        """Verify TUI handles uninitialized system gracefully."""
        sm = MagicMock()
        sm.config_manager.nodes = {}
        sm.state_manager.get_all_agents.return_value = []
        sm.state_manager.system_status = SystemStatus.STOPPED
        
        tui = CommanderTUI(sm)
        
        # Should not crash
        assert tui.generate_header() is not None
        assert tui.generate_nodes_table() is not None
        assert tui.generate_agents_table() is not None
