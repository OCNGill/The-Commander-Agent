"""
The-Commander: System Manager
Orchestrates the entire system lifecycle (startup, shutdown, monitoring).

Coordinating:
- Config loading
- State initialization
- Node & Agent Managers
- Relay Server

Version: 1.2.2 (Relay Integration)
"""

import logging
import time
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

from commander_os.core.config_manager import ConfigManager
from commander_os.core.state import StateManager, SystemStatus
from commander_os.core.node_manager import NodeManager
from commander_os.core.agent_manager import AgentManager

logger = logging.getLogger(__name__)

class SystemManager:
    """
    Top-level orchestrator for The-Commander Operating System.
    """

    def __init__(self, config_dir: Optional[str] = None, local_node_id: str = "node-main"):
        """
        Initialize the System Manager.
        
        Args:
            config_dir: Optional path to configuration directory.
            local_node_id: ID of the local node.
        """
        self.local_node_id = local_node_id
        
        # 1. Initialize Core Managers
        self.config_manager = ConfigManager(config_dir)
        self.state_manager = StateManager()
        
        # 2. Initialize Sub-Managers
        self.node_manager = NodeManager(
            self.config_manager, 
            self.state_manager, 
            local_node_id=self.local_node_id
        )
        self.agent_manager = AgentManager(
            self.config_manager, 
            self.state_manager, 
            local_node_id=self.local_node_id
        )
        
        self.relay_process: Optional[subprocess.Popen] = None
        
        logger.info(f"SystemManager initialized for node: {self.local_node_id}")

    def bootstrap(self) -> bool:
        """
        Phase 1: Load configurations and prepare for startup.
        """
        logger.info("Bootstrapping system...")
        
        if not self.config_manager.load_all():
            logger.critical("Failed to load configurations. Aborting bootstrap.")
            self.state_manager.set_system_status(SystemStatus.ERROR)
            return False
            
        logger.info("Bootstrap complete: Configs loaded.")
        return True

    def start_system(self) -> bool:
        """
        Start the entire system.
        """
        if self.state_manager.system_status == SystemStatus.RUNNING:
            logger.warning("System is already running")
            return True
            
        self.state_manager.set_system_status(SystemStatus.STARTING)
        
        if not self.bootstrap():
            return False
            
        try:
            # 2. Start Relay Server (Only if configured for this node or locally)
            # In Phase 4, we allow starting it for verification
            self._start_relay_server()
            
            # 3. Start Nodes
            logger.info("Starting sub-managers...")
            self.node_manager.start_all_nodes()
            
            # 4. Start Agents
            self.agent_manager.start_all_agents()
            
            # 5. Finalize
            self.state_manager.set_system_status(SystemStatus.RUNNING)
            logger.info("System successfully started")
            return True
            
        except Exception as e:
            logger.critical(f"System startup failed: {e}", exc_info=True)
            self.state_manager.set_system_status(SystemStatus.ERROR)
            self.stop_system()  # Rollback
            return False

    def stop_system(self) -> None:
        """
        Gracefully shut down the system.
        """
        logger.info("Stopping system...")
        self.state_manager.set_system_status(SystemStatus.STOPPING)
        
        try:
            # 1. Stop Agents
            self.agent_manager.stop_all_agents()
            
            # 2. Stop Nodes
            self.node_manager.stop_all_nodes()
            
            # 3. Stop Relay
            self._stop_relay_server()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.state_manager.set_system_status(SystemStatus.ERROR)
        finally:
            self.state_manager.set_system_status(SystemStatus.STOPPED)
            logger.info("System stopped")

    def get_status_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive system health report.
        """
        return self.state_manager.get_full_snapshot()

    def _start_relay_server(self):
        """Internal: Launch the relay server process."""
        # For now, we simulate starting unless explicitly on HTPC or local
        # In a real cluster, only node-htpc would run this via its launcher script
        if self.local_node_id != "node-htpc" and self.local_node_id != "node-main":
            logger.info("Skipping relay server start for worker node.")
            return

        logger.info(f"Launching Relay Server on {self.local_node_id}...")
        
        try:
            # Ensure we are in project root
            root = self.config_manager.config_dir.parent
            
            # Use subprocess to run as a module
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root)
            
            self.relay_process = subprocess.Popen(
                [sys.executable, "-m", "commander_os.network.relay"],
                cwd=str(root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a second to start
            time.sleep(1)
            if self.relay_process.poll() is not None:
                _, err = self.relay_process.communicate()
                raise Exception(f"Relay process exited immediately: {err}")
                
            logger.info("Relay Server process launched successfully.")
            
        except Exception as e:
            logger.error(f"Failed to launch Relay Server: {e}")
            # Don't raise here if we want system to continue in degraded mode, 
            # but for Phase 4 we want it to work.
            raise

    def _stop_relay_server(self):
        """Internal: Stop the relay server."""
        if self.relay_process:
            logger.info("Stopping Relay Server...")
            self.relay_process.terminate()
            try:
                self.relay_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.relay_process.kill()
            self.relay_process = None
            logger.info("Relay Server stopped.")
