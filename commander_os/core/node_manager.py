"""
The-Commander: Node Manager
Manages the lifecycle of compute nodes.

Handles:
- Node startup/shutdown
- Dynamic registration
- Heartbeat monitoring
- Resource tracking (stubbed for now)

Version: 1.1.0
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any

from commander_os.core.config_manager import ConfigManager, NodeConfig
from commander_os.core.state import StateManager, ComponentStatus

logger = logging.getLogger(__name__)

class NodeManager:
    """
    Manages compute nodes in the Commander ecosystem.
    """
    
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config = config_manager
        self.state = state_manager
        
        # Background monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._local_node_id = "node-local"  # TODO: Determine from env/config real local ID
        
        logger.info("NodeManager initialized")

    def start_all_nodes(self) -> None:
        """
        Initialize and register all nodes defined in configuration.
        """
        logger.info("Initializing nodes from configuration...")
        
        nodes = self.config.nodes
        for node_id, node_config in nodes.items():
            if node_config.enabled:
                self.register_node(node_config)
                
                # If this is the local node, mark it as READY
                # In a real distributed setup, we'd check hostname/IP
                if node_id == self._local_node_id:
                    self.start_node(node_id)
        
        self._start_monitoring()

    def stop_all_nodes(self) -> None:
        """
        Stop all nodes and monitoring.
        """
        logger.info("Stopping all nodes...")
        self._stop_monitoring()
        
        # Mark local node as OFFLINE
        if self._local_node_id:
            self.stop_node(self._local_node_id)

    def register_node(self, config: NodeConfig) -> None:
        """
        Register a node in the state manager.
        """
        self.state.register_node(
            node_id=config.id,
            hostname=config.host,
            port=config.port
        )
        # Initialize basic resources stub
        # self.state.update_node_resources(...)

    def start_node(self, node_id: str) -> bool:
        """
        Start a specific node (logically).
        """
        logger.info(f"Starting node: {node_id}")
        self.state.update_node_status(node_id, ComponentStatus.STARTING)
        
        # Simulate startup delay/checks
        # In reality: checking ports, disk space, Docker connectivity, etc.
        time.sleep(0.1)
        
        self.state.update_node_status(node_id, ComponentStatus.READY)
        logger.info(f"Node {node_id} is READY")
        return True

    def stop_node(self, node_id: str) -> bool:
        """
        Stop a specific node.
        """
        logger.info(f"Stopping node: {node_id}")
        self.state.update_node_status(node_id, ComponentStatus.OFFLINE)
        return True

    def get_node_status(self, node_id: str) -> Dict[str, Any]:
        """
        Get status of a specific node.
        """
        node = self.state.get_node(node_id)
        if node:
            return node.to_dict()
        return {}

    def _start_monitoring(self) -> None:
        """Start background heartbeat monitor."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            name="NodeMonitor",
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Node monitoring started")

    def _stop_monitoring(self) -> None:
        """Stop background heartbeat monitor."""
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None
            logger.info("Node monitoring stopped")

    def _monitor_loop(self) -> None:
        """
        Background loop to:
        1. Send heartbeat for local node
        2. Prune stale remote nodes
        """
        while not self._stop_event.is_set():
            try:
                # 1. Heartbeat local node
                if self._local_node_id:
                    self.state.update_node_heartbeat(self._local_node_id)
                
                # 2. Prune remote nodes (assuming 30s timeout)
                # This ensures if a remote node crashes, we know
                self.state.prune_stale_components(timeout_seconds=30.0)
                
                # Sleep interval
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in node monitoring loop: {e}")
                time.sleep(5)
