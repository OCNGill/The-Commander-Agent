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
import random
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from commander_os.core.config_manager import ConfigManager
from commander_os.core.state import StateManager, SystemStatus, ComponentStatus
from commander_os.core.node_manager import NodeManager
from commander_os.core.agent_manager import AgentManager
from commander_os.core.memory import MessageStore

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
        
        # 3. Initialize Memory Store
        db_path = os.getenv("COMMANDER_DB_URL", "sqlite:///commander_memory.db")
        self.memory_store = MessageStore(db_path)
        
        self.relay_process: Optional[subprocess.Popen] = None
        self.engine_process: Optional[subprocess.Popen] = None
        
        logger.info(f"SystemManager initialized for node: {self.local_node_id}")

    def bootstrap(self) -> bool:
        """
        Initialize core components and load configurations.
        Must be called before starting services.
        """
        logger.info("Bootstrapping system...")
        try:
            # 1. Load configurations
            if not self.config_manager.load_all():
                logger.error("Failed to load configurations during bootstrap")
                return False
            
            # 2. Register this node
            local_cfg = self.config_manager.get_node(self.local_node_id)
            if local_cfg:
                self.state_manager.register_node(
                    self.local_node_id, 
                    local_cfg.host, 
                    local_cfg.port
                )
            
            # Start background telemetry loop
            threading.Thread(target=self._telemetry_loop, daemon=True).start()

            logger.info("Bootstrap complete: Configs loaded.")
            return True
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            return False

    def _telemetry_loop(self):
        """Background thread to update node metrics/heartbeats."""
        while True:
            try:
                # Update local node metrics (Simulated for Phase 6 visualization)
                node_state = self.state_manager.get_node(self.local_node_id)
                if not node_state:
                    time.sleep(1)
                    continue

                status = node_state.status
                
                # Periodically simulate activity if system is running
                if self.state_manager.system_status == SystemStatus.RUNNING:
                    if random.random() > 0.8: # 20% chance to toggle activity
                        new_status = ComponentStatus.BUSY if status == ComponentStatus.READY else ComponentStatus.READY
                        self.state_manager.update_node_status(self.local_node_id, new_status)
                        status = new_status

                if status == ComponentStatus.READY or status == ComponentStatus.BUSY:
                   # If engine is running, show some TPS
                   tps = random.uniform(25, 130) if status == ComponentStatus.BUSY else random.uniform(0, 5)
                   load = random.uniform(10, 95) if status == ComponentStatus.BUSY else random.uniform(1, 5)
                   self.state_manager.update_node_metrics(self.local_node_id, {"tps": tps, "load": load})
                else:
                   self.state_manager.update_node_metrics(self.local_node_id, {"tps": 0.0, "load": 0.0})
                
                # Prune stale components
                self.state_manager.prune_stale_components()
                
            except Exception as e:
                logger.error(f"Telemetry loop error: {e}")
            time.sleep(2)
            
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

    def reignite_local_engine(self, engine_updates: Dict[str, Any]) -> bool:
        """
        Update engine config and restart the local hardware engine.
        Used for dynamic hardware dial adjustments (Context, NGL).
        """
        logger.info(f"Re-igniting hardware engine on {self.local_node_id} with updates: {engine_updates}")
        
        # 1. Update Config (and persist to YAML)
        if not self.config_manager.update_node_engine(self.local_node_id, engine_updates):
            return False
            
        # 2. Shutdown existing engine if running
        self._shutdown_hardware_engine()
        
        # 3. Ignite anew
        self._ignite_hardware_engine()
        return True

    def get_status_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive system health report.
        Merges live state with static configuration to ensure full visibility.
        """
        snapshot = self.state_manager.get_full_snapshot()
        
        # Merge offline nodes from config into snapshot so UI sees everything
        configured_nodes = self.config_manager.nodes
        live_nodes = snapshot.get('nodes', {})
        
        for node_id, config in configured_nodes.items():
            if node_id not in live_nodes:
                 live_nodes[node_id] = {
                    "node_id": node_id,
                    "status": "offline",
                    "role": "worker",
                    "metrics": {"tps": 0.0, "load": 0.0},
                    "name": config.name,
                    # Add static config data needed for UI
                    "tps_benchmark": config.tps_benchmark,
                    "model_file": config.engine.model_file if config.engine else "",
                    "ctx": config.engine.ctx if config.engine else 0,
                    "ngl": config.engine.ngl if config.engine else 0,
                    "fa": config.engine.fa if config.engine else False,
                    "binary": config.engine.binary if config.engine else ""
                 }
            else:
                # Enrich live node with static config name if missing
                 if 'name' not in live_nodes[node_id]:
                     live_nodes[node_id]['name'] = config.name

        snapshot['nodes'] = live_nodes
        return snapshot

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
