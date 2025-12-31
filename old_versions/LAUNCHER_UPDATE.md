Update your .desktop launcher to point at the new HTPC start script

Current Exec in .desktop (old single-agent):

Exec=konsole --hold -e /home/gillsystems-htpc/AI/robot/Gillsystems-HTPC-LLM-Server-Port-8001.sh

Replace with:

Exec=/home/stephen/scripts/htpc_start.sh

Notes:
- No terminal required; the script daemonizes via nohup.
- Ensure /home/stephen/scripts/htpc_start.sh is executable (chmod +x).
- Adjust paths and usernames as needed for your environment.
