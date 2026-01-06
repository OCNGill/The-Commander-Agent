# Commander OS Storage Architecture - Corrected Structure

**Date:** January 6, 2026  
**Issue Resolved:** File organization and naming conventions

**Version:** 1.3.0

---

## Changelog

### Version 1.3
- Corrected file organization and naming conventions.
- Introduced a two-tier storage architecture for generic and agent-specific layers.
- Added Commander and Recruiter agent storage modules.

## The Problem

Initially, agent-specific storage was placed in `commander_os/agents/recruiter/storage.py` with a generic name. This was confusing because:

1. **Generic name for specific functionality** - `storage.py` should be generic, but it contained Recruiter-specific code
2. **No storage for The Commander** - The most important agent had no storage!
3. **Unclear separation** - It wasn't obvious what's generic vs. agent-specific

## The Solution

### Two-Tier Storage Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  GENERIC STORAGE LAYER                       │
│            (Used by ALL agents as foundation)                │
│                                                              │
│  commander_os/storage/                                       │
│  ├── base_storage.py      - Core functionality               │
│  └── agent_storage.py     - Simple key-value storage         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ extends/uses
                            │
┌─────────────────────────────────────────────────────────────┐
│              AGENT-SPECIFIC STORAGE LAYER                    │
│         (Custom schemas for individual agents)               │
│                                                              │
│  commander_os/agents/commander/                              │
│  └── commander_storage.py    - Orchestration, tasks,         │
│                                 agents, decisions            │
│                                                              │
│  commander_os/agents/recruiter/                              │
│  └── recruiter_storage.py    - Candidates, interviews,       │
│                                 job requisitions             │
│                                                              │
│  commander_os/agents/<your_agent>/                           │
│  └── <your_agent>_storage.py - Your custom schema           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## File Naming Convention

### ✅ CORRECT

**Generic Storage:**
- `commander_os/storage/base_storage.py`
- `commander_os/storage/agent_storage.py`

**Agent-Specific Storage:**
- `commander_os/agents/commander/commander_storage.py`
- `commander_os/agents/recruiter/recruiter_storage.py`
- `commander_os/agents/<agent_name>/<agent_name>_storage.py`

### ❌ INCORRECT (What we had before)

- `commander_os/agents/recruiter/storage.py` ❌ Too generic!
- Agent storage living in generic location ❌ Wrong layer!
- No commander storage ❌ Missing!

## Commander Storage

**Location:** `commander_os/agents/commander/commander_storage.py`

The Commander gets the most sophisticated storage because he:
- **Orchestrates** all tasks across agents
- **Tracks** agent performance and status
- **Logs** every decision with reasoning
- **Collects** system-wide metrics
- **Plans** strategic goals

**Hardware:** Optimized for high-performance (Radeon 7900 XTX, 48GB RAM)

### Commander's Schema

```sql
-- Task orchestration
tasks (id, title, priority, status, assigned_agent, complexity, ...)

-- Agent registry
agents (id, name, role, status, capabilities, performance_score, ...)

-- Decision history
decisions (id, decision_type, reasoning, confidence_score, outcome, ...)

-- System metrics
metrics (id, metric_type, metric_name, value, timestamp, ...)

-- Strategic goals
goals (id, title, goal_type, priority, progress, deadline, ...)

-- Inter-agent communications
communications (id, from_agent, to_agent, message_type, content, ...)
```

## Usage Examples

### Using Generic Storage (Simple Agents)

```python
from pathlib import Path
from commander_os.storage.agent_storage import AgentStorage

# Simple agent uses generic storage
storage = AgentStorage(
    agent_id="simple-agent",
    data_dir=Path("./data/agents/simple-agent"),
    htpc_url="http://10.0.0.42:8001"
)

storage.set('config', {'setting': 'value'})
config = storage.get('config')
```

### Using Agent-Specific Storage (Commander)

```python
from pathlib import Path
from commander_os.agents.commander.commander_storage import CommanderStorage

# The Commander uses his specialized storage
storage = CommanderStorage(
    data_dir=Path("./data/agents/commander"),
    htpc_url="http://10.0.0.42:8001"
)

# Create and assign task
task_id = await storage.create_task({
    'title': 'Analyze system performance',
    'priority': 9,
    'complexity': 7
})

# Get available agents
agents = await storage.get_available_agents(role='analyst')

# Assign task to best agent
await storage.assign_task(task_id, agents[0]['id'])

# Log the decision
await storage.log_decision({
    'decision_type': 'task_delegation',
    'reasoning': 'Agent has highest performance score for this task type',
    'confidence_score': 0.92,
    'related_task_id': task_id
})
```

### Using Agent-Specific Storage (Recruiter)

```python
from pathlib import Path
from commander_os.agents.recruiter.recruiter_storage import RecruiterAgentStorage

# Recruiter uses his specialized storage
storage = RecruiterAgentStorage(
    data_dir=Path("./data/agents/recruiter"),
    htpc_url="http://10.0.0.42:8001"
)

# Add candidate
candidate_id = await storage.add_candidate({
    'name': 'Jane Developer',
    'skills': ['Python', 'React', 'AWS'],
    'experience_years': 5
})

# Search for matches
matches = await storage.search_candidates(
    skills=['Python'],
    min_experience=3
)
```

## Creating Your Own Agent Storage

When creating a new agent, ask yourself:

### Do I need custom storage?

**Use generic `AgentStorage` if:**
- ✅ Simple key-value data
- ✅ No complex queries
- ✅ No relationships between data
- ✅ Small data volume

**Create custom `<agent>_storage.py` if:**
- ✅ Complex data schema
- ✅ Need specialized queries
- ✅ Relationships between entities
- ✅ Performance-critical operations

### If you need custom storage:

1. **Create file:** `commander_os/agents/<your_agent>/<your_agent>_storage.py`
2. **Extend BaseStorage:**
   ```python
   from commander_os.storage.base_storage import BaseStorage
   
   class YourAgentStorage(BaseStorage):
       def __init__(self, data_dir, htpc_url=None, enable_htpc=True):
           super().__init__(
               agent_id="your-agent",
               data_dir=data_dir,
               htpc_url=htpc_url,
               enable_htpc=enable_htpc
           )
           self._create_schema()
   ```
3. **Define schema** in `_create_schema()`
4. **Implement `_write_local()`** for your tables
5. **Add high-level API methods** for your agent's operations

See [`Commander_OS_agent_storage_info.md`](./Commander_OS_agent_storage_info.md) for complete guide.

## Directory Structure (CORRECTED)

```
commander_os/
├── storage/                         # GENERIC - for all agents
│   ├── __init__.py
│   ├── base_storage.py             # Core functionality
│   └── agent_storage.py            # Simple key-value
│
├── agents/
│   ├── commander/                  # The Commander
│   │   ├── __init__.py
│   │   └── commander_storage.py   # ✨ NEW - Orchestration DB
│   │
│   ├── recruiter/                  # Recruiter Agent
│   │   ├── __init__.py
│   │   ├── recruiter_storage.py   # ✅ RENAMED from storage.py
│   │   └── recruiter_storage_example.py  # ✅ RENAMED
│   │
│   └── <your_agent>/               # Your future agent
│       ├── __init__.py
│       └── <your_agent>_storage.py # Follow the pattern!
│
└── network/
    └── relay.py                    # Storage sync endpoints
```

## Key Benefits of This Structure

1. **Clear Separation** - Generic vs. specific is obvious
2. **Scalable** - Easy to add new agents
3. **Consistent Naming** - `<agent>_storage.py` convention
4. **The Commander First** - Most important agent has best storage
5. **Easy to Find** - Agent's storage lives with the agent

## Migration Guide

If you have old code importing the wrong path:

### Old (WRONG)
```python
from commander_os.agents.recruiter.recruiter_storage import RecruiterAgentStorage
```

### New (CORRECT)
```python
from commander_os.agents.recruiter.recruiter_storage import RecruiterAgentStorage
```

### Old (WRONG) - Generic storage in agent folder
```python
# No such thing anymore!
```

### New (CORRECT) - Generic storage in storage folder
```python
from commander_os.storage.agent_storage import AgentStorage
```

## Summary

✅ **Generic storage** lives in `commander_os/storage/`  
✅ **Agent-specific storage** lives with the agent: `commander_os/agents/<agent>/<agent>_storage.py`  
✅ **The Commander** has his own powerful storage optimized for his hardware  
✅ **Naming convention** is clear and consistent  
✅ **Easy to extend** for new agents  

---

**Architecture Fixed:** January 6, 2026  
**Status:** Ready for production use
