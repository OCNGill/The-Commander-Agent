# THE COMMANDER: Node Startup Issue Analysis

## Executive Summary

**PROBLEM:** Only one node comes online when the dashboard attempts to start the system. Other configured nodes (Gillsystems-HTPC, Gillsystems-Steam-Deck, Gillsystems-Laptop) remain OFFLINE.

**ROOT CAUSE:** The dashboard's `startSystem()` endpoint only starts the **local node** (identified by `local_node_id`). Remote/other nodes are **never explicitly started** - they only get registered but remain in STARTING/UNKNOWN status.

---

## Configuration Context

From `config/relay.yaml`, there are **4 configured nodes**:

1. **Gillsystems-Main** - 10.0.0.164:8000 - TPS: 130 ✅ LOCAL
2. **Gillsystems-HTPC** - 10.0.0.42:8001 - TPS: 60 ❌ BLOCKED
3. **Gillsystems-Steam-Deck** - 10.0.0.139:8003 - TPS: 30 ❌ BLOCKED
4. **Gillsystems-Laptop** - 10.0.0.93:8002 - TPS: 9 ❌ BLOCKED

**EXACT NODE IDENTIFIERS** (from config):
- `id: Gillsystems-Main` → `name: Gillsystems-Main`
- `id: Gillsystems-HTPC` → `name: Gillsystems-HTPC`
- `id: Gillsystems-Steam-Deck` → `name: Gillsystems-Steam-Deck`
- `id: Gillsystems-Laptop` → `name: Gillsystems-Laptop`

---

## Code Flow Analysis

### 1. **System Start Flow** (`main.py` → `system_manager.py`)

```python
# main.py - commander-gui-dashboard command
def commander_gui_dashboard(host, port):
    # ... REST API startup
    system = SystemManager(local_node_id=node_id)
    # Determines local_node_id via environment variable
    # CRITICAL: Only this node will be started
```

**The Problem:** 
- `SystemManager` is initialized with a specific `local_node_id` (usually "Gillsystems-Main" when running on Main)
- When `/system/start` is called, it only starts that one local node

---

### 2. **Node Manager Start Logic** (`node_manager.py`)

```python
def start_all_nodes(self) -> None:
    """
    Initialize and register all nodes defined in configuration.
    """
    logger.info("Initializing nodes from configuration...")
    
    nodes = self.config.nodes  # Gets ALL 4 nodes from relay.yaml
    for node_id, node_config in nodes.items():
        if node_config.enabled:
            self.register_node(node_config)  # Register all nodes
            
            # ⚠️ CRITICAL ISSUE: Only the local node is started!
            if node_id == self._local_node_id:
                self.start_node(node_id)  # Only this one gets READY status
    
    self._start_monitoring()
```

**The Issue:**
- Line `if node_id == self._local_node_id: self.start_node(node_id)`
- Remote nodes are **registered** (added to state) but **never started**
- They remain in **UNKNOWN** or **OFFLINE** status
- No mechanism to trigger startup of remote nodes

---

### 3. **Node Status Flow**

```
Node Registration → State Created (STARTING status)
                ↓
           start_node(node_id)?
                ↓
      YES (if local) → READY ✅
      NO (if remote) → UNKNOWN/OFFLINE ❌
```

---

### 4. **Dashboard UI Impact** (`App.jsx`)

```jsx
const nodes = await api.listNodes();  // Fetches all registered nodes
// Displays them with status badges

// In the UI, the status shows as:
// node-main: "ready" (green) ✅
// node-htpc: "offline" (gray) ❌
// node-steamdeck: "offline" (gray) ❌
// node-laptop: "offline" (gray) ❌
```

**Why?** The REST API's `GET /nodes` endpoint returns the state of all nodes, including their status from the state manager.

---

### 5. **No Individual Node Start Button**

In `commander-api.js`, there is a `toggleNode()` method:

```javascript
async toggleNode(nodeId, start = true) {
    const action = start ? 'start' : 'stop';
    const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/${action}`, {
        method: 'POST',
    });
    return response.json();
}
```

**BUT:** This method is **never called from the UI** (`App.jsx`). 
- There's a `handleStopNode()` but no `handleStartNode()`
- Only `IGNITE ALL` (entire system) is available, not per-node start

---

## Root Cause Chain

1. **Architecture Decision:** `SystemManager` is initialized with a specific `local_node_id`
2. **start_all_nodes() Logic:** Only starts the local node, registers others as OFFLINE
3. **No UI Control:** Dashboard has no button to start individual nodes
4. **No Relay Coordination:** Remote nodes aren't contacted to start themselves
5. **State Isolation:** Each dashboard instance only manages its own local node

---

## Why This Matters

- **Single Node Operation:** The cluster acts as a single machine with one "active" node
- **No Load Distribution:** Even though node-htpc, node-steamdeck, node-laptop are configured, they're never activated
- **Dashboard Limitation:** Users can't bring other nodes online from the UI
- **Relay Server Idle:** Even if relay is running, it's not coordinating multi-node startup

---

## The Fix Requires

### Option 1: **Multi-Node Startup Logic** (Recommended)
Modify `node_manager.py` to:
- Start ALL enabled nodes, not just the local one
- Send HTTP/WebSocket startup commands to remote nodes
- Wait for remote nodes to acknowledge READY status

### Option 2: **Add UI Control for Individual Nodes**
- Create `handleStartNode()` in `App.jsx`
- Add "START NODE" button to the control panel
- Call `api.toggleNode(nodeId, true)` 

### Option 3: **Relay-Coordinated Startup**
- Dashboard contacts Relay Server instead of SystemManager
- Relay broadcasts startup commands to all nodes
- Nodes self-register with Relay once online

---

## Current Behavior vs. Expected Behavior

| Scenario | Current | Expected |
|----------|---------|----------|
| Click "IGNITE ALL" | node-main → READY, node-htpc/node-steamdeck/node-laptop → OFFLINE | All → READY |
| Dashboard runs on different node | That node → READY, others → OFFLINE | All enabled nodes → READY |
| Click button to start node-htpc | No button exists | node-htpc → READY |
| Click button to start node-steamdeck | No button exists | node-steamdeck → READY |
| Click button to start node-laptop | No button exists | node-laptop → READY |
| Remote nodes come online | Never | Automatically or via UI |

---

## Critical Code Locations

1. **Problem Location 1:** `commander_os/core/node_manager.py`, line ~47-57
   ```python
   for node_id, node_config in nodes.items():
       if node_config.enabled:
           self.register_node(node_config)
           if node_id == self._local_node_id:  # ⚠️ ONLY LOCAL NODE
               self.start_node(node_id)
   ```

2. **Problem Location 2:** `commander_os/interfaces/gui/src/App.jsx` - NO `handleStartNode()` method

3. **Problem Location 3:** `commander_os/interfaces/rest_api.py`, POST `/nodes/{node_id}/start` - endpoint exists but unreachable from UI

---

## Recommended Next Steps

1. **Immediate:** Add UI button to start individual nodes (`handleStartNode()` in App.jsx)
2. **Short-term:** Modify `node_manager.start_all_nodes()` to start ALL enabled nodes
3. **Medium-term:** Implement remote node initialization protocol (HTTP POST to node's REST API)
4. **Long-term:** Implement Relay-based orchestration for multi-machine deployment

---

## References

- `config/relay.yaml` - Node definitions
- `commander_os/core/node_manager.py` - Node lifecycle (start_all_nodes is the problem)
- `commander_os/core/system_manager.py` - System orchestration
- `commander_os/interfaces/rest_api.py` - API endpoints (includes start_node but unreachable)
- `commander_os/interfaces/gui/src/App.jsx` - Dashboard UI (missing start node handler)

