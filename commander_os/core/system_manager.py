"""
The-Commander: System Manager
Orchestrates the entire system lifecycle (startup, shutdown, monitoring).

Coordinating:
- Config loading
- State initialization
- Node & Agent Managers
- Relay Server

Version: 1.1.0
"""

import logging
import time
import subprocess
import sys
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

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the System Manager.
        
        Args:
            config_dir: Optional path to configuration directory.
        """
        # 1. Initialize Core Managers
        self.config_manager = ConfigManager(config_dir)
        self.state_manager = StateManager()
        
        # 2. Initialize Sub-Managers (they depend on config/state)
        self.node_manager = NodeManager(self.config_manager, self.state_manager)
        self.agent_manager = AgentManager(self.config_manager, self.state_manager)
        
        self.relay_process: Optional[subprocess.Popen] = None
        
        logger.info("SystemManager initialized")

    def bootstrap(self) -> bool:
        """
        Phase 1: Load configurations and prepare for startup.
        """
        logger.info("Bootstrapping system...")
        
        # Load all configurations
        if not self.config_manager.load_all():
            logger.critical("Failed to load configurations. Aborting bootstrap.")
            self.state_manager.set_system_status(SystemStatus.ERROR)
            return False
            
        logger.info("Bootstrap complete: Configs loaded.")
        return True

    def start_system(self) -> bool:
        """
        Start the entire system:
        1. Bootstrap (load configs)
        2. Start Relay Server
        3. Start Node Managers (which start Agents)
        4. Set System Status -> RUNNING
        """
        if self.state_manager.system_status == SystemStatus.RUNNING:
            logger.warning("System is already running")
            return True
            
        self.state_manager.set_system_status(SystemStatus.STARTING)
        
        # 1. Bootstrap
        if not self.bootstrap():
            return False
            
        try:
            # 2. Start Relay Server (Mock/Real logic here)
            # In production, this might launch a subprocess or thread
            self._start_relay_server()
            
            # 3. Start Nodes
            logger.info("Starting sub-managers...")
            self.node_manager.start_all_nodes()
            
            # 4. Start Agents (managed by Node Manager mostly, but we trigger if centralized)
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
        # For now, we simulate this or just log it. 
        # In real impl, this would Popen 'python commander_os/network/relay.py'
        logger.info("Relay Server started (simulated)")
        # TODO: Implement actual subprocess launch
        # relay_script = Path(__file__).parent.parent / "network" / "relay_server.py"
        # self.relay_process = subprocess.Popen([sys.executable, str(relay_script)]...)

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
