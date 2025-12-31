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
        self.engine_process: Optional[subprocess.Popen] = None
        
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
            # 2. Ignite Hardware Engine (llama.cpp)
            self._ignite_hardware_engine()
            
            # 3. Start Relay Server (Only if configured for this node or locally)
            self._start_relay_server()
            
            # 4. Start Nodes
            logger.info("Starting sub-managers...")
            self.node_manager.start_all_nodes()
            
            # 5. Start Agents
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
            
            # 4. Shutdown Hardware
            self._shutdown_hardware_engine()
            
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
    def _ignite_hardware_engine(self):
        """Internal: Launch the local hardware LLM backend."""
        node_cfg = self.config_manager.get_node(self.local_node_id)
        if not node_cfg or not node_cfg.engine:
            logger.info(f"No hardware engine configured for node: {self.local_node_id}")
            return

        engine = node_cfg.engine
        model_path = os.path.join(node_cfg.model_root_path, engine.model_file)
        
        # Build command
        cmd = [
            engine.binary,
            "-m", model_path,
            "-c", str(engine.ctx),
            "-ngl", str(engine.ngl),
            "--host", node_cfg.host,
            "--port", str(node_cfg.port)
        ]
        
        if engine.fa:
            cmd.extend(["-fa", "on"])
            
        if engine.extra_flags:
            # Simple split for extra flags
            cmd.extend(engine.extra_flags.split())

        logger.info(f"Igniting Hardware Engine: {' '.join(cmd)}")
        
        try:
            # We run the engine in its own process group to avoid signal propagation issues
            self.engine_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Check if it started correctly
            time.sleep(2) # Engines take a moment to load weights
            if self.engine_process.poll() is not None:
                _, err = self.engine_process.communicate()
                logger.error(f"Hardware Engine failed to start: {err}")
                return

            logger.info(f"Hardware Engine ignited successfully (PID: {self.engine_process.pid})")
            
        except Exception as e:
            logger.error(f"Critical failure during engine ignition: {e}")

    def _shutdown_hardware_engine(self):
        """Internal: Gracefully shut down the hardware engine."""
        if self.engine_process:
            logger.info("Shutting down Hardware Engine...")
            self.engine_process.terminate()
            try:
                self.engine_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.engine_process.kill()
            self.engine_process = None
            logger.info("Hardware Engine offline.")
