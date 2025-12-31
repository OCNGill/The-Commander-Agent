"""
Gillsystems Commander OS: Node Manager
Manages the lifecycle of compute nodes.

Handles:
- Node startup/shutdown
- Dynamic registration
- Heartbeat monitoring
- Weighted routing (Load Balancing)

Version: 1.2.0 (Protocol Integrated)
"""

import logging
import time
import threading
import requests
from typing import Dict, List, Optional, Any

from commander_os.core.config_manager import ConfigManager, NodeConfig
from commander_os.core.state import StateManager, ComponentStatus

logger = logging.getLogger(__name__)

class NodeManager:
    """
    Manages compute nodes in the Commander ecosystem.
    """
    
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager, local_node_id: str = "Gillsystems-Main"):
        self.config = config_manager
        self.state = state_manager
        
        # Background monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._local_node_id = local_node_id
        
        logger.info(f"NodeManager initialized for node: {self._local_node_id}")

    def start_all_nodes(self) -> None:
        """
        Initialize and register all nodes defined in configuration.
    Starts ALL enabled nodes (Gillsystems-Main, Gillsystems-HTPC, Gillsystems-Steam-Deck, Gillsystems-Laptop).
        """
        logger.info("Initializing nodes from configuration...")
        
        nodes = self.config.nodes
        for node_id, node_config in nodes.items():
            if node_config.enabled:
                self.register_node(node_config)
                # Start all enabled nodes (not just local node)
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

    def start_node(self, node_id: str) -> bool:
        """
        Start a specific node (logically).
        """
        logger.info(f"Starting node: {node_id}")
        self.state.update_node_status(node_id, ComponentStatus.STARTING)
        
        # Simulate startup delay
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

    def get_best_worker_node(self, role_requirement: Optional[str] = None) -> str:
        """
        Determine the best node for a task based on authoritative tps_benchmarks.
        
        Logic: 
        1. Filter for READY nodes.
        2. Sort by tps_benchmark descending.
        3. Return the ID of the highest performing node.
        
    In Phase 4, we prioritize Gillsystems-Main and Gillsystems-HTPC.
        """
        nodes_config = self.config.nodes
        ready_nodes = []
        
        for node_id, config in nodes_config.items():
            state = self.state.get_node(node_id)
            if state and state.status == ComponentStatus.READY:
                ready_nodes.append(config)
        
        if not ready_nodes:
            logger.warning("No READY nodes found. Defaulting to local node.")
            return self._local_node_id
            
        # Sort by benchmark descending
    # 130 (Gillsystems-Main) > 60 (Gillsystems-HTPC) > 30 (Gillsystems-Steam-Deck) > 9 (Gillsystems-Laptop)
        sorted_nodes = sorted(ready_nodes, key=lambda n: n.tps_benchmark, reverse=True)
        
        best_node = sorted_nodes[0].id
        logger.info(f"Load Balancer selected best node: {best_node} (TPS: {sorted_nodes[0].tps_benchmark})")
        return best_node

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

    def _sync_with_relay(self) -> None:
        """
        Pull global cluster state from the Relay High Command.
        This ensures we see what the Relay sees (other nodes).
        """
        try:
            if not hasattr(self.config, 'relay') or not self.config.relay:
                return

            relay_cfg = self.config.relay
            # Skip if we ARE the relay (very basic check)
            if relay_cfg.host in ["localhost", "127.0.0.1", "0.0.0.0"]:
                 pass

            proto = getattr(relay_cfg, 'protocol', 'http')
            relay_url = f"{proto}://{relay_cfg.host}:{relay_cfg.port}"
            
            resp = requests.get(f"{relay_url}/nodes", timeout=2)
            if resp.status_code == 200:
                global_nodes = resp.json()
                for r_node in global_nodes:
                    nid = r_node.get('node_id')
                    if nid and nid != self._local_node_id:
                        self.state.register_node(
                            node_id=nid,
                            hostname=r_node.get('address', '').split(':')[0],
                            port=int(r_node.get('address', '').split(':')[1]) if ':' in r_node.get('address','') else 8000,
                            update_heartbeat=True 
                        )
                        metrics = r_node.get('metrics', {})
                        self.state.update_node_metrics(nid, metrics)
        except Exception:
            pass



    def _monitor_loop(self) -> None:
        """
        Background loop to maintain heartbeat.
        Nodes stay READY once started until explicitly stopped.
        NO automatic offline/pruning logic.
        """
        while not self._stop_event.is_set():
            try:
                # Update heartbeat for local node
                if self._local_node_id:
                    self.state.update_node_heartbeat(self._local_node_id)
                
                # Sync with Relay (Cluster Visibility)
                self._sync_with_relay()
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in node monitoring loop: {e}")
                time.sleep(5)
