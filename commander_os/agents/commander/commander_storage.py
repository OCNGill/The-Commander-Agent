"""
Commander Agent Storage Implementation

Specialized storage for The Commander - the orchestrator and decision maker.
Optimized for high-performance operations with powerful hardware
(Radeon 7900 XTX, 48GB RAM).

The Commander manages:
- Task orchestration and delegation
- Agent coordination and status
- Decision history and reasoning
- System-wide metrics and insights
- Strategic planning and execution
"""

import uuid
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from commander_os.storage.base_storage import BaseStorage


class CommanderStorage(BaseStorage):
    """
    Storage system for The Commander Agent.
    
    Manages orchestration data, agent coordination, task tracking,
    and strategic decision making with high-performance queries
    optimized for powerful hardware.
    """
    
    def __init__(
        self,
        data_dir: Path,
        htpc_url: Optional[str] = None,
        enable_htpc: bool = True
    ):
        super().__init__(
            agent_id="the-commander",
            data_dir=data_dir,
            htpc_url=htpc_url,
            enable_htpc=enable_htpc
        )
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema for Commander Agent"""
        self.conn.executescript("""
            -- Task orchestration and tracking
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5,  -- 1-10 scale
                status TEXT DEFAULT 'pending',  -- pending, assigned, in_progress, completed, failed
                assigned_agent TEXT,
                created_by TEXT DEFAULT 'the-commander',
                parent_task_id TEXT REFERENCES tasks(id),
                complexity INTEGER DEFAULT 5,  -- 1-10 scale
                estimated_duration INTEGER,  -- minutes
                actual_duration INTEGER,  -- minutes
                result TEXT,  -- JSON result data
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Agent registry and status tracking
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                node_id TEXT,  -- Which node the agent is on
                status TEXT DEFAULT 'idle',  -- idle, busy, offline, error
                capabilities TEXT,  -- JSON array of capabilities
                current_task_id TEXT REFERENCES tasks(id),
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                average_task_duration REAL,  -- minutes
                last_heartbeat TIMESTAMP,
                performance_score REAL DEFAULT 5.0,  -- 1-10 scale
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Decision history and reasoning
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                decision_type TEXT NOT NULL,  -- delegation, strategy, escalation, etc.
                context TEXT,  -- JSON context data
                options_considered TEXT,  -- JSON array of options
                chosen_option TEXT,
                reasoning TEXT,  -- Why this decision was made
                confidence_score REAL,  -- 0-1 scale
                outcome TEXT,  -- success, failure, pending
                outcome_quality REAL,  -- 0-1 scale (how good was the decision)
                related_task_id TEXT REFERENCES tasks(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- System-wide metrics and insights
            CREATE TABLE IF NOT EXISTS metrics (
                id TEXT PRIMARY KEY,
                metric_type TEXT NOT NULL,  -- throughput, latency, error_rate, etc.
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                tags TEXT,  -- JSON object with tags
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Strategic goals and planning
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                goal_type TEXT DEFAULT 'operational',  -- strategic, operational, tactical
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'active',  -- active, completed, abandoned
                success_criteria TEXT,  -- JSON array of criteria
                progress REAL DEFAULT 0.0,  -- 0-1 scale
                deadline TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Inter-agent communication log
            CREATE TABLE IF NOT EXISTS communications (
                id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                message_type TEXT NOT NULL,  -- request, response, notification, etc.
                content TEXT,  -- JSON message content
                related_task_id TEXT REFERENCES tasks(id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Performance indexes for high-speed queries
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent 
                ON tasks(assigned_agent);
            CREATE INDEX IF NOT EXISTS idx_tasks_priority 
                ON tasks(priority DESC);
            CREATE INDEX IF NOT EXISTS idx_tasks_created 
                ON tasks(created_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_agents_status 
                ON agents(status);
            CREATE INDEX IF NOT EXISTS idx_agents_role 
                ON agents(role);
            CREATE INDEX IF NOT EXISTS idx_agents_performance 
                ON agents(performance_score DESC);
            
            CREATE INDEX IF NOT EXISTS idx_decisions_type 
                ON decisions(decision_type);
            CREATE INDEX IF NOT EXISTS idx_decisions_created 
                ON decisions(created_at DESC);
            
            CREATE INDEX IF NOT EXISTS idx_metrics_type 
                ON metrics(metric_type);
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp DESC);
            
            CREATE INDEX IF NOT EXISTS idx_goals_status 
                ON goals(status);
            CREATE INDEX IF NOT EXISTS idx_goals_priority 
                ON goals(priority DESC);
            
            CREATE INDEX IF NOT EXISTS idx_comms_from 
                ON communications(from_agent);
            CREATE INDEX IF NOT EXISTS idx_comms_to 
                ON communications(to_agent);
            CREATE INDEX IF NOT EXISTS idx_comms_timestamp 
                ON communications(timestamp DESC);
            
            -- Triggers for automatic timestamp updates
            CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp
            AFTER UPDATE ON tasks
            BEGIN
                UPDATE tasks SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            
            CREATE TRIGGER IF NOT EXISTS update_agents_timestamp
            AFTER UPDATE ON agents
            BEGIN
                UPDATE agents SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            
            CREATE TRIGGER IF NOT EXISTS update_goals_timestamp
            AFTER UPDATE ON goals
            BEGIN
                UPDATE goals SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
        """)
        self.conn.commit()
    
    def _write_local(self, table: str, data: Dict[str, Any], operation: str):
        """Implement local write for Commander tables"""
        if table == "tasks":
            self._write_task(data, operation)
        elif table == "agents":
            self._write_agent(data, operation)
        elif table == "decisions":
            self._write_decision(data, operation)
        elif table == "metrics":
            self._write_metric(data, operation)
        elif table == "goals":
            self._write_goal(data, operation)
        elif table == "communications":
            self._write_communication(data, operation)
        else:
            raise ValueError(f"Unknown table: {table}")
    
    def _write_task(self, data: Dict[str, Any], operation: str):
        """Write task data"""
        if operation == "insert":
            task_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, title, description, priority, status, assigned_agent, 
                 parent_task_id, complexity, estimated_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                data['title'],
                data.get('description'),
                data.get('priority', 5),
                data.get('status', 'pending'),
                data.get('assigned_agent'),
                data.get('parent_task_id'),
                data.get('complexity', 5),
                data.get('estimated_duration')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE tasks 
                SET status=?, assigned_agent=?, result=?, error=?,
                    started_at=?, completed_at=?, actual_duration=?
                WHERE id=?
            """, (
                data.get('status'),
                data.get('assigned_agent'),
                data.get('result'),
                data.get('error'),
                data.get('started_at'),
                data.get('completed_at'),
                data.get('actual_duration'),
                data['id']
            ))
        elif operation == "delete":
            self.conn.execute("DELETE FROM tasks WHERE id=?", (data['id'],))
        
        self.conn.commit()
    
    def _write_agent(self, data: Dict[str, Any], operation: str):
        """Write agent registry data"""
        if operation == "insert":
            agent_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO agents
                (id, name, role, node_id, status, capabilities, 
                 current_task_id, performance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                data['name'],
                data['role'],
                data.get('node_id'),
                data.get('status', 'idle'),
                json.dumps(data.get('capabilities', [])),
                data.get('current_task_id'),
                data.get('performance_score', 5.0)
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE agents
                SET status=?, current_task_id=?, last_heartbeat=?,
                    tasks_completed=?, tasks_failed=?, 
                    average_task_duration=?, performance_score=?
                WHERE id=?
            """, (
                data.get('status'),
                data.get('current_task_id'),
                data.get('last_heartbeat', datetime.utcnow().isoformat()),
                data.get('tasks_completed'),
                data.get('tasks_failed'),
                data.get('average_task_duration'),
                data.get('performance_score'),
                data['id']
            ))
        elif operation == "delete":
            self.conn.execute("DELETE FROM agents WHERE id=?", (data['id'],))
        
        self.conn.commit()
    
    def _write_decision(self, data: Dict[str, Any], operation: str):
        """Write decision history data"""
        if operation == "insert":
            decision_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT INTO decisions
                (id, decision_type, context, options_considered, chosen_option,
                 reasoning, confidence_score, related_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                data['decision_type'],
                json.dumps(data.get('context', {})),
                json.dumps(data.get('options_considered', [])),
                data.get('chosen_option'),
                data.get('reasoning'),
                data.get('confidence_score'),
                data.get('related_task_id')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE decisions
                SET outcome=?, outcome_quality=?
                WHERE id=?
            """, (
                data.get('outcome'),
                data.get('outcome_quality'),
                data['id']
            ))
        
        self.conn.commit()
    
    def _write_metric(self, data: Dict[str, Any], operation: str):
        """Write metric data"""
        if operation == "insert":
            metric_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT INTO metrics
                (id, metric_type, metric_name, value, unit, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric_id,
                data['metric_type'],
                data['metric_name'],
                data['value'],
                data.get('unit'),
                json.dumps(data.get('tags', {}))
            ))
        
        self.conn.commit()
    
    def _write_goal(self, data: Dict[str, Any], operation: str):
        """Write strategic goal data"""
        if operation == "insert":
            goal_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO goals
                (id, title, description, goal_type, priority, status,
                 success_criteria, progress, deadline)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal_id,
                data['title'],
                data.get('description'),
                data.get('goal_type', 'operational'),
                data.get('priority', 5),
                data.get('status', 'active'),
                json.dumps(data.get('success_criteria', [])),
                data.get('progress', 0.0),
                data.get('deadline')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE goals
                SET status=?, progress=?, completed_at=?
                WHERE id=?
            """, (
                data.get('status'),
                data.get('progress'),
                data.get('completed_at'),
                data['id']
            ))
        
        self.conn.commit()
    
    def _write_communication(self, data: Dict[str, Any], operation: str):
        """Write communication log data"""
        if operation == "insert":
            comm_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT INTO communications
                (id, from_agent, to_agent, message_type, content, related_task_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                comm_id,
                data['from_agent'],
                data['to_agent'],
                data['message_type'],
                json.dumps(data.get('content', {})),
                data.get('related_task_id')
            ))
        
        self.conn.commit()
    
    # High-level Commander API methods
    
    async def create_task(self, task: Dict[str, Any]) -> str:
        """Create a new task for orchestration"""
        task_id = task.get('id') or str(uuid.uuid4())
        task['id'] = task_id
        
        await self.write_data('tasks', task, 'insert')
        return task_id

    async def register_agent(self, agent_data: Dict[str, Any]) -> str:
        """Register or update an agent in the registry"""
        agent_id = agent_data.get('id') or agent_data.get('agent_id') or str(uuid.uuid4())
        agent_data['id'] = agent_id
        
        await self.write_data('agents', agent_data, 'insert')
        return agent_id

    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            'id': row[0],
            'name': row[1],
            'role': row[2],
            'node_id': row[3],
            'status': row[4],
            'capabilities': json.loads(row[5]) if row[5] else [],
            'current_task_id': row[6],
            'tasks_completed': row[7],
            'tasks_failed': row[8],
            'average_task_duration': row[9],
            'performance_score': row[11]
        }

    async def record_comm(self, interaction: Dict[str, Any]) -> str:
        """Record an inter-agent communication"""
        comm_id = interaction.get('id') or str(uuid.uuid4())
        interaction['id'] = comm_id
        
        await self.write_data('communications', interaction, 'insert')
        return comm_id
    
    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent"""
        now = datetime.utcnow().isoformat()
        return await self.write_data('tasks', {
            'id': task_id,
            'assigned_agent': agent_id,
            'status': 'assigned',
            'assigned_at': now
        }, 'update')
    
    async def get_available_agents(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available agents for task assignment"""
        query = "SELECT * FROM agents WHERE status IN ('idle', 'available')"
        params = []
        
        if role:
            query += " AND role = ?"
            params.append(role)
        
        query += " ORDER BY performance_score DESC"
        
        cursor = self.conn.cursor()
        cursor.execute(query, tuple(params))
        
        agents = []
        for row in cursor.fetchall():
            agents.append({
                'id': row[0],
                'name': row[1],
                'role': row[2],
                'capabilities': json.loads(row[5]) if row[5] else [],
                'performance_score': row[11]
            })
        
        return agents
    
    async def log_decision(self, decision: Dict[str, Any]) -> str:
        """Log a strategic or tactical decision"""
        decision_id = decision.get('id') or str(uuid.uuid4())
        decision['id'] = decision_id
        
        await self.write_data('decisions', decision, 'insert')
        return decision_id
    
    async def record_metric(self, metric_type: str, metric_name: str, 
                           value: float, unit: str = None, tags: Dict = None) -> str:
        """Record a system metric"""
        metric = {
            'metric_type': metric_type,
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {}
        }
        
        metric_id = str(uuid.uuid4())
        metric['id'] = metric_id
        
        await self.write_data('metrics', metric, 'insert')
        return metric_id
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, priority, status, assigned_agent, complexity
            FROM tasks
            WHERE status IN ('pending', 'assigned', 'in_progress')
            ORDER BY priority DESC, created_at ASC
        """)
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'title': row[1],
                'priority': row[2],
                'status': row[3],
                'assigned_agent': row[4],
                'complexity': row[5]
            })
        
        return tasks
    
    async def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all agents"""
        cursor = self.conn.cursor()
        
        # Total stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_agents,
                COUNT(CASE WHEN status = 'idle' THEN 1 END) as idle_count,
                COUNT(CASE WHEN status = 'busy' THEN 1 END) as busy_count,
                AVG(performance_score) as avg_performance,
                SUM(tasks_completed) as total_tasks_completed
            FROM agents
        """)
        
        row = cursor.fetchone()
        return {
            'total_agents': row[0],
            'idle_agents': row[1],
            'busy_agents': row[2],
            'average_performance': row[3],
            'total_tasks_completed': row[4]
        }
