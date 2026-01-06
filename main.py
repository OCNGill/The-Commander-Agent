"""
THE COMMANDER: STRATEGIC OVERLORD (Main Entry)
Command-line interface for Managing the Gillsystems Intelligence Cluster.

Usage:
  python main.py hub           # Start the Central Intelligence Relay (HTPC)
  python main.py engine        # Start the Local Compute Engine (Local Service)
  python main.py war-room      # Launch the Strategic Dashboard (TUI)
"""

import click
import logging
import sys
import os
from commander_os.core.system_manager import SystemManager
from commander_os.network.relay import start_relay as run_relay
from commander_os.interfaces.tui import CommanderTUI

# Ensure logs dir exists
os.makedirs("logs", exist_ok=True)

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/commander_main.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """THE COMMANDER: Intelligence Cluster Control Center."""
    pass

@cli.command(name="hub")
def hub():
    """(HUB) Start the Central Intelligence Relay Server."""
    click.echo("Activating Intelligence Hub (config-driven)...")
    run_relay()

@cli.command(name="engine")
@click.option('--node', default='Gillsystems-Main', help='Local Node ID.')
def engine(node):
    """(ENGINE) Start the Local Compute Engine Service."""
    click.echo(f"Igniting Core Engine on {node}...")
    sm = SystemManager(local_node_id=node)
    if sm.start_system():
        click.echo("Engine is online. Awaiting commands. [Ctrl+C to Terminate]")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            sm.stop_system()
    else:
        click.echo("[ERROR] Engine failure. Check logs.")

@cli.command(name="war-room")
@click.option('--node', default='Gillsystems-Main', help='Local Node ID.')
def war_room(node):
    """(WAR-ROOM) Launch the Strategic Intelligence Dashboard."""
    # We remove StreamHandler to keep TUI clean
    for handler in logging.root.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            logging.root.removeHandler(handler)
            
    sm = SystemManager(local_node_id=node)
    sm.start_system()
    
    tui = CommanderTUI(sm)
    try:
        tui.run()
    except KeyboardInterrupt:
        sm.stop_system()

@cli.command(name="commander-gui-dashboard")
@click.option('--host', default='127.0.0.1', help='Host to bind API.')
@click.option('--port', default=8000, help='Port to bind API.')
def commander_gui_dashboard(host, port):
    """(COMMANDER-GUI) Start the Strategic REST API & Web Dashboard."""
    import uvicorn
    import socket
    from commander_os.core.config_manager import ConfigManager
    
    # Auto-Detect Identity based on IP/Host
    # This prevents "Gillsystems-Laptop" from acting as "Gillsystems-Main"
    click.echo("[IDENTITY] resolving local identity...")
    
    cm = ConfigManager()
    try:
        cm.load_relay_config()
        hostname = socket.gethostname()
        # Get all local IPs
        local_ips = set()
        try:
            # Basic
            local_ips.add(socket.gethostbyname(hostname))
            # Detailed
            for info in socket.getaddrinfo(hostname, None):
                local_ips.add(info[4][0])
        except:
            pass

        target_node = 'Gillsystems-Main' # Default fallback
        target_port = port # Default from CLI arg (8000)
        found = False

        # Check config against local IPs
        for n_id, n_cfg in cm.nodes.items():
            # Check Hostname match (case insensitive)
            if n_cfg.name.lower() in hostname.lower() or n_cfg.id.lower() in hostname.lower():
                target_node = n_id
                target_port = n_cfg.port
                found = True
                break
            # Check IP match
            if n_cfg.host in local_ips:
                target_node = n_id
                target_port = n_cfg.port
                found = True
                break

        if found:
            click.echo(f"[IDENTITY] DETECTED: {target_node} on Port {target_port}")
            os.environ["COMMANDER_NODE_ID"] = target_node
            # Override host/port if auto-detected?
            # User wants strict ports. We obey config if found.
            port = target_port 
            # Host binding: 0.0.0.0 is safer for valid access
            host = "0.0.0.0" 
        else:
            click.echo(f"[IDENTITY] UNKNOWN. Defaulting to {target_node}")
            os.environ["COMMANDER_NODE_ID"] = target_node

    except Exception as e:
        click.echo(f"[IDENTITY] Detection failed: {e}. Defaulting to Gillsystems-Main.")
        os.environ["COMMANDER_NODE_ID"] = "Gillsystems-Main"

    # Echo immediately before long imports/init
    click.echo(f"------------------------------------------------------------")
    click.echo(f"  IGNITING ORCHESTRATION HUB: http://{host}:{port}")
    click.echo(f"  IDENTITY: {os.environ.get('COMMANDER_NODE_ID')}")
    click.echo(f"  VERSION: v1.3.1")
    click.echo(f"------------------------------------------------------------")
    
    from commander_os.interfaces.rest_api import app
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    cli()
