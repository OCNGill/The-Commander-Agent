# COMMANDER: Multi-Node Startup Fixes - CORRECTED

## Executive Summary

**EXACT NODE CONFIGURATION (from config/relay.yaml):**

| Node ID | Display Name | IP Address | Port | TPS | Status |
|---------|--------------|------------|------|-----|--------|
| `node-main` | Gillsystems-Main | 10.0.0.164 | 8000 | 130 | ✅ READY |
| `node-htpc` | Gillsystems-HTPC | 10.0.0.42 | 8001 | 60 | ❌ BLOCKED |
| `node-steamdeck` | Gillsystems-Steam-Deck | 10.0.0.139 | 8003 | 30 | ❌ BLOCKED |
| `node-laptop` | Gillsystems-Laptop | 10.0.0.93 | 8002 | 9 | ❌ BLOCKED |

---

## The Problem

When you click "IGNITE ALL" on the dashboard:
- ✅ `node-main` becomes READY
- ❌ `node-htpc` stays OFFLINE
- ❌ `node-steamdeck` stays OFFLINE
- ❌ `node-laptop` stays OFFLINE

---

## Fix #1: Start ALL Enabled Nodes

**File:** `commander_os/core/node_manager.py`
**Function:** `start_all_nodes()`
**Lines:** 47-57

### Current Code (BROKEN):
```python
    def start_all_nodes(self) -> None:
        """
        Initialize and register all nodes defined in configuration.
        """
        logger.info("Initializing nodes from configuration...")
        
        nodes = self.config.nodes
        for node_id, node_config in nodes.items():
            if node_config.enabled:
                self.register_node(node_config)
                
                # 🚫 PROBLEM: Only node-main is started
                if node_id == self._local_node_id:
                    self.start_node(node_id)
        
        self._start_monitoring()
```

### Fixed Code:
```python
    def start_all_nodes(self) -> None:
        """
        Initialize and register all nodes defined in configuration.
        Starts all enabled nodes (node-main, node-htpc, node-steamdeck, node-laptop).
        """
        logger.info("Initializing nodes from configuration...")
        
        nodes = self.config.nodes
        for node_id, node_config in nodes.items():
            if node_config.enabled:
                self.register_node(node_config)
                # ✅ FIX: Start ALL enabled nodes
                self.start_node(node_id)
        
        self._start_monitoring()
```

**Change:** Remove the `if node_id == self._local_node_id:` condition.

**Result After Fix:**
- ✅ `node-main` → READY
- ✅ `node-htpc` → READY
- ✅ `node-steamdeck` → READY
- ✅ `node-laptop` → READY

---

## Fix #2: Add Handler for Individual Node Startup

**File:** `commander_os/interfaces/gui/src/App.jsx`
**Location:** After `handleStopNode` function (around line 120)

### Add This Code:
```javascript
  const handleStartNode = async () => {
    if (!selectedNode) return;
    try {
      await api.toggleNode(selectedNode.node_id, true);
      // WebSocket will update status automatically
    } catch (err) {
      alert("Failed to start node: " + err.message);
    }
  };
```

**What It Does:** Allows users to manually start individual nodes via `/nodes/{node_id}/start` API endpoint.

---

## Fix #3: Update Control Panel UI

**File:** `commander_os/interfaces/gui/src/App.jsx`
**Location:** Control panel section (around line 240-250)

### Current Code:
```jsx
                {selectedNode.status === 'online' && (
                    <button className="node-stop-btn" onClick={handleStopNode}>STOP NODE</button>
                )}
```

### Fixed Code:
```jsx
                {selectedNode.status === 'ready' && (
                    <button className="node-stop-btn" onClick={handleStopNode}>STOP NODE</button>
                )}
                {selectedNode.status === 'offline' && (
                    <button className="node-start-btn" onClick={handleStartNode}>START NODE</button>
                )}
```

**Changes:**
1. Status check: `'online'` → `'ready'` (matches actual state)
2. Added new button for OFFLINE nodes to allow manual startup

**Result:**
- When node is READY: Shows "STOP NODE" button
- When node is OFFLINE: Shows "START NODE" button

---

## Complete Applied Fixes Table

| File | Function/Component | Change | Purpose |
|------|-------------------|--------|---------|
| `node_manager.py` | `start_all_nodes()` | Remove `if node_id == self._local_node_id:` guard | Allow all 4 nodes to start |
| `App.jsx` | New function | Add `handleStartNode()` | Enable manual node startup |
| `App.jsx` | Control panel | Update button conditions | Show START/STOP buttons contextually |

---

## Node IDs Used Throughout Code

All references must use these exact identifiers:

```
Gillsystems-Main     (Gillsystems-Main, 10.0.0.164:8000, TPS 130)
Gillsystems-HTPC     (Gillsystems-HTPC, 10.0.0.42:8001, TPS 60)
Gillsystems-Steam-Deck (Gillsystems-Steam-Deck, 10.0.0.139:8003, TPS 30)
Gillsystems-Laptop   (Gillsystems-Laptop, 10.0.0.93:8002, TPS 9)
```

---

## Verification Checklist

- [ ] Edit `node_manager.py` line ~52: Remove the local node check
- [ ] Edit `App.jsx` line ~120: Add `handleStartNode()` function
- [ ] Edit `App.jsx` line ~240: Update button conditions for START/STOP
- [ ] Test: Click "IGNITE ALL" → All 4 nodes show READY ✅
- [ ] Test: Select `node-htpc` → Shows "START NODE" button (if offline)
- [ ] Test: Click "START NODE" on `node-steamdeck` → Status changes to READY
- [ ] Test: Click "STOP NODE" on `node-laptop` → Status changes to OFFLINE
- [ ] Verify node names in UI match: Gillsystems-Main, Gillsystems-HTPC, Gillsystems-Steam-Deck, Gillsystems-Laptop

---

## Implementation Order

1. **Priority 1:** Fix `node_manager.py` (core logic)
2. **Priority 2:** Fix `App.jsx` handlers and UI (user experience)

All changes maintain backward compatibility with existing codebase.
