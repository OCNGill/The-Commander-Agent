"""
The-Commander: Main Entry Point
Command-line interface for managing the Gillsystems Cluster.

Usage:
  python main.py relay          # Start the HTPC Relay Server
  python main.py start           # Start the full system (Headless)
  python main.py dashboard      # Launch the TUI Dashboard
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
    """The Commander OS Control Center."""
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind relay server.')
@click.option('--port', default=8001, help='Port to bind relay server.')
def relay(host, port):
    """Start the HTPC Message Relay Server."""
    click.echo(f"Starting Relay on {host}:{port}...")
    run_relay(host=host, port=port)

@cli.command()
@click.option('--node', default='node-main', help='Local Node ID.')
def start(node):
    """Start the full Commander System (Headless)."""
    click.echo(f"Starting Commander OS as {node}...")
    sm = SystemManager(local_node_id=node)
    if sm.start_system():
        click.echo("System is running. Press Ctrl+C to stop.")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            sm.stop_system()
    else:
        click.echo("Failed to start system.")

@cli.command()
@click.option('--node', default='node-main', help='Local Node ID.')
def dashboard(node):
    """Launch the Interactive TUI Dashboard."""
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
