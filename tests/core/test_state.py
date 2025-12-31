"""
Test Suite: StateManager
Tests for commander_os.core.state

Run with: pytest tests/core/test_state.py -v
"""

import pytest
import time
import threading
from commander_os.core.state import (
    StateManager, 
    SystemStatus, 
    ComponentStatus,
    NodeState,
    AgentState
)

class TestStateManager:
    """Tests for the StateManager class."""

    @pytest.fixture
    def state_manager(self):
        """Fixture to provide a fresh StateManager instance."""
        return StateManager()

    def test_initial_state(self, state_manager):
        """Test initial system state."""
        assert state_manager.system_status == SystemStatus.STOPPED
        assert state_manager.get_uptime() == 0.0
        assert len(state_manager.get_all_nodes()) == 0
        assert len(state_manager.get_all_agents()) == 0

    def test_system_status_transitions(self, state_manager):
        """Test transitioning system status."""
        # Start
        state_manager.set_system_status(SystemStatus.STARTING)
        assert state_manager.system_status == SystemStatus.STARTING
        
        # Verify timer started
        time.sleep(0.1)
        assert state_manager.get_uptime() > 0.0
        
        # Run
        state_manager.set_system_status(SystemStatus.RUNNING)
        assert state_manager.system_status == SystemStatus.RUNNING
        
        # Stop
        state_manager.set_system_status(SystemStatus.STOPPED)
        assert state_manager.system_status == SystemStatus.STOPPED

    def test_node_lifecycle(self, state_manager):
        """Test registering and updating nodes."""
        node_id = "node-1"
        
        # Register
        state_manager.register_node(node_id, "192.168.1.5", 5556)
        
        node = state_manager.get_node(node_id)
        assert node is not None
        assert node.node_id == node_id
        assert node.status == ComponentStatus.STARTING
        
        # Update status
        state_manager.update_node_status(node_id, ComponentStatus.READY)
        assert state_manager.get_node(node_id).status == ComponentStatus.READY
        
        # Checking unknown node
        assert state_manager.get_node("unknown") is None

    def test_agent_lifecycle(self, state_manager):
        """Test registering and updating agents."""
        agent_id = "agent-alpha"
        node_id = "node-1"
        
        # Setup node first
        state_manager.register_node(node_id, "localhost", 5556)
        
        # Register agent
        state_manager.register_agent(agent_id, node_id, "coder")
        
        agent = state_manager.get_agent(agent_id)
        assert agent is not None
        assert agent.agent_id == agent_id
        assert agent.node_id == node_id
        assert agent.role == "coder"
        assert agent.status == ComponentStatus.STARTING
        
        # Verify node link
        node = state_manager.get_node(node_id)
        assert agent_id in node.registered_agents
        
        # Update status
        state_manager.update_agent_status(agent_id, ComponentStatus.BUSY, "task-123")
        updated = state_manager.get_agent(agent_id)
        assert updated.status == ComponentStatus.BUSY
        assert updated.current_task_id == "task-123"

    def test_role_management(self, state_manager):
        """Test updating and querying by role."""
        # Create agents with different roles
        state_manager.register_agent("coder-1", "node-1", "coder")
        state_manager.register_agent("coder-2", "node-1", "coder")
        state_manager.register_agent("architect-1", "node-1", "architect")
        
        coders = state_manager.get_agents_by_role("coder")
        assert len(coders) == 2
        
        architects = state_manager.get_agents_by_role("architect")
        assert len(architects) == 1
        
        # Change role
        state_manager.update_agent_role("coder-2", "architect")
        
        assert len(state_manager.get_agents_by_role("coder")) == 1
        assert len(state_manager.get_agents_by_role("architect")) == 2

    def test_prune_stale_components(self, state_manager):
        """Test detection of offline components."""
        state_manager.register_node("node-old", "localhost", 5556)
        state_manager.register_agent("agent-old", "node-old", "coder")
        
        # Manually backdate heartbeats
        with state_manager._lock:
            state_manager._nodes["node-old"].last_heartbeat = time.time() - 100
            state_manager._agents["agent-old"].last_heartbeat = time.time() - 100
            
        # Register fresh ones
        state_manager.register_node("node-new", "localhost", 5556)
        
        # Prune with 60s timeout
        changed = state_manager.prune_stale_components(timeout_seconds=60.0)
        
        assert "node:node-old" in changed
        assert "agent:agent-old" in changed
        
        assert state_manager.get_node("node-old").status == ComponentStatus.OFFLINE
        assert state_manager.get_agent("agent-old").status == ComponentStatus.OFFLINE
        
        # New one should be safe
        assert state_manager.get_node("node-new").status != ComponentStatus.OFFLINE

    def test_snapshot(self, state_manager):
        """Test full system snapshot export."""
        state_manager.set_system_status(SystemStatus.RUNNING)
        state_manager.register_node("node-1", "localhost", 8000)
        state_manager.register_agent("agent-1", "node-1", "coder")
        
        snap = state_manager.get_full_snapshot()
        
        assert snap["system"]["status"] == "running"
        assert "node-1" in snap["nodes"]
        assert "agent-1" in snap["agents"]
        assert snap["nodes"]["node-1"]["status"] == "starting"

    def test_thread_safety(self, state_manager):
        """Simple stress test for thread safety."""
        # Define a worker that updates state repeatedly
        def worker(idx):
            name = f"agent-{idx}"
            state_manager.register_agent(name, "node-1", "coder")
            for _ in range(100):
                state_manager.update_agent_status(name, ComponentStatus.BUSY)
                state_manager.update_agent_status(name, ComponentStatus.READY)
                
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # Verify consistency
        assert len(state_manager.get_all_agents()) == 10
