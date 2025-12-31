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
@click.option('--host', default='0.0.0.0', help='Host to bind relay server.')
@click.option('--port', default=8001, help='Port to bind relay server.')
def hub(host, port):
    """(HUB) Start the Central Intelligence Relay Server."""
    click.echo(f"Activating Intelligence Hub on {host}:{port}...")
    run_relay(host=host, port=port)

@cli.command(name="engine")
@click.option('--node', default='node-main', help='Local Node ID.')
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
        click.error("Engine failure. Check logs.")

@cli.command(name="war-room")
@click.option('--node', default='node-main', help='Local Node ID.')
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

if __name__ == "__main__":
    cli()
