"""
The-Commander: TUI Dashboard
Real-time terminal interface for monitoring the Gillsystems Cluster.

Features:
- Live node heartbeats and performance metrics
- Agent process tracking
- Real-time message/event log

Version: 1.0.0
"""

import time
import os
from datetime import datetime
from typing import Optional, Dict, Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich import box

from commander_os.core.system_manager import SystemManager
from commander_os.core.state import SystemStatus, ComponentStatus
from commander_os.core.memory import MessageStore

class CommanderTUI:
    """
    Rich-based Dashboard for The-Commander OS.
    """
    
    def __init__(self, system_manager: SystemManager):
        self.sm = system_manager
        self.console = Console()
        self.layout = Layout()
        
        # Initialize Memory Access if available
        self.store = None
        db_path = os.getenv("COMMANDER_DB_URL", "sqlite:///commander_memory.db")
        try:
            self.store = MessageStore(db_path)
        except Exception as e:
            logger.warning(f"TUI couldn't connect to MessageStore: {e}")
        
    def make_layout(self) -> Layout:
        """Define the dashboard layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        self.layout["main"].split_row(
            Layout(name="left_pane", ratio=1),
            Layout(name="logs", ratio=1),
        )
        self.layout["left_pane"].split_column(
            Layout(name="nodes", ratio=1),
            Layout(name="agents", ratio=1),
        )
        return self.layout

    def generate_header(self) -> Panel:
        """Create the header panel."""
        status = self.sm.state_manager.system_status
        status_color = "green" if status == SystemStatus.RUNNING else "yellow"
        if status == SystemStatus.ERROR:
            status_color = "red"
            
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        grid.add_row(
            Text("THE COMMANDER OS", style="bold cyan"),
            Text(f"STATUS: {status.value.upper()}", style=f"bold {status_color}"),
            Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="bold white")
        )
        return Panel(grid, style="white on blue")

    def generate_nodes_table(self) -> Panel:
        """Create the nodes monitoring table."""
        table = Table(expand=True, box=box.SIMPLE)
        table.add_column("Node ID", style="cyan", no_wrap=True)
        table.add_column("Address", style="white")
        table.add_column("Benchmark", justify="right", style="magenta")
        table.add_column("Status", justify="center")
        
        # Get data from config and state
        nodes_config = self.sm.config_manager.nodes
        for node_id, cfg in nodes_config.items():
            state = self.sm.state_manager.get_node(node_id)
            status_str = "OFFLINE"
            style = "dim red"
            
            if state:
                status_str = state.status.value.upper()
                if state.status == ComponentStatus.READY:
                    style = "bold green"
                elif state.status == ComponentStatus.STARTING:
                    style = "yellow"
            
            table.add_row(
                node_id,
                f"{cfg.host}:{cfg.port}",
                f"{cfg.tps_benchmark} t/s",
                Text(status_str, style=style)
            )
            
        return Panel(table, title="[bold white]Cluster Nodes[/bold white]", border_style="blue")

    def generate_agents_table(self) -> Panel:
        """Create the agents tracking table."""
        table = Table(expand=True, box=box.SIMPLE)
        table.add_column("Agent ID", style="cyan")
        table.add_column("Role", style="green")
        table.add_column("Node", style="white")
        table.add_column("Status", justify="center")
        
        agents = self.sm.state_manager.get_all_agents()
        for agent in agents:
            status_str = agent.status.value.upper()
            style = "dim white"
            
            if agent.status == ComponentStatus.READY:
                style = "bold green"
            elif agent.status == ComponentStatus.BUSY:
                style = "bold orange3"
            elif agent.status == ComponentStatus.ERROR:
                style = "bold red"
                
            table.add_row(
                agent.id,
                agent.role,
                agent.node_id,
                Text(status_str, style=style)
            )
            
        return Panel(table, title="[bold white]Active Agents[/bold white]", border_style="green")

    def generate_logs_panel(self) -> Panel:
        """Create the recent messages log panel."""
        if not self.store:
            return Panel(Text("MessageStore Offline", style="dim red"), title="Recent Events")
            
        try:
            msgs = self.store.query_messages(limit=20)
            table = Table.grid(expand=True)
            table.add_column(ratio=1)
            
            for m in msgs:
                ts = datetime.fromtimestamp(m['timestamp']).strftime("%H:%M:%S")
                # Truncate content for TUI
                content = m['content'][:100] + "..." if len(m['content']) > 100 else m['content']
                content = content.replace("\n", " ")
                
                table.add_row(
                    Text.from_markup(
                        f"[dim blue]{ts}[/] [bold green]{m['sender']}[/] -> [bold cyan]{m['role']}[/]: [white]{content}[/]"
                    )
                )
            return Panel(table, title="[bold white]Cluster Traffic (Live)[/bold white]", border_style="magenta")
        except Exception as e:
            return Panel(Text(f"Error: {e}", style="red"), title="Recent Events")

    def generate_footer(self) -> Panel:
        """Create the footer with instructions."""
        return Panel(
            Text(" [Q] Quit  [S] Start Node  [R] Restart Agent  [C] Configuration", justify="center", style="dim white"),
            border_style="blue"
        )

    def run(self, refresh_rate: float = 1.0):
        """Run the live dashboard."""
        self.make_layout()
        
        with Live(self.layout, refresh_per_second=refresh_rate, screen=True):
            while True:
                # Update Layout
                self.layout["header"].update(self.generate_header())
                self.layout["nodes"].update(self.generate_nodes_table())
                self.layout["agents"].update(self.generate_agents_table())
                self.layout["logs"].update(self.generate_logs_panel())
                self.layout["footer"].update(self.generate_footer())
                
                time.sleep(1.0 / refresh_rate)
                # Note: Input handling would go here, 
                # but Rich Live is non-blocking for output. 
                # Real interactivity usually requires 'textual' or manual input threads.

if __name__ == "__main__":
    # Smoke test initialization
    sm = SystemManager()
    tui = CommanderTUI(sm)
    # tui.run() # Don't run in non-interactive environment
