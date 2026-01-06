"""
Recruiter Agent Storage Implementation

Specialized storage for Gillsystems-Recruiter-Agent with:
- Candidate profiles management
- Interview records tracking
- Job requisitions
- Skills-based search capabilities
"""

import uuid
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from commander_os.storage.base_storage import BaseStorage


class RecruiterAgentStorage(BaseStorage):
    """
    Storage system for Gillsystems-Recruiter-Agent.
    
    Manages candidate data, interviews, and job requisitions with
    optimized queries for skills-based matching.
    """
    
    def __init__(
        self,
        data_dir: Path,
        htpc_url: Optional[str] = None,
        enable_htpc: bool = True
    ):
        super().__init__(
            agent_id="gillsystems-recruiter-agent",
            data_dir=data_dir,
            htpc_url=htpc_url,
            enable_htpc=enable_htpc
        )
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema for Recruiter Agent"""
        self.conn.executescript("""
            -- Candidate profiles
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                skills TEXT NOT NULL,  -- JSON array
                experience_years INTEGER DEFAULT 0,
                education TEXT,
                location TEXT,
                status TEXT DEFAULT 'active',
                source TEXT,  -- How candidate was found
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Interview records
            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL REFERENCES candidates(id),
                interviewer_agent TEXT,
                scheduled_date TIMESTAMP,
                actual_date TIMESTAMP,
                interview_type TEXT,  -- phone, technical, behavioral, etc.
                notes TEXT,
                score INTEGER,  -- 1-10 scale
                outcome TEXT,  -- passed, failed, pending
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Job requisitions
            CREATE TABLE IF NOT EXISTS job_requisitions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                department TEXT,
                required_skills TEXT NOT NULL,  -- JSON array
                preferred_skills TEXT,  -- JSON array
                experience_required INTEGER DEFAULT 0,
                location TEXT,
                status TEXT DEFAULT 'open',  -- open, filled, closed
                priority INTEGER DEFAULT 5,  -- 1-10 scale
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Agent interactions (for tracking collaboration)
            CREATE TABLE IF NOT EXISTS agent_interactions (
                id TEXT PRIMARY KEY,
                source_agent TEXT NOT NULL,
                target_agent TEXT NOT NULL,
                interaction_type TEXT NOT NULL,  -- query, recommendation, feedback
                context TEXT,  -- JSON data about interaction
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_candidates_status 
                ON candidates(status);
            CREATE INDEX IF NOT EXISTS idx_candidates_skills 
                ON candidates(skills);
            CREATE INDEX IF NOT EXISTS idx_interviews_candidate 
                ON interviews(candidate_id);
            CREATE INDEX IF NOT EXISTS idx_interviews_outcome 
                ON interviews(outcome);
            CREATE INDEX IF NOT EXISTS idx_jobs_status 
                ON job_requisitions(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_priority 
                ON job_requisitions(priority DESC);
            CREATE INDEX IF NOT EXISTS idx_agent_interactions_source 
                ON agent_interactions(source_agent);
            
            -- Triggers for updated_at
            CREATE TRIGGER IF NOT EXISTS update_candidates_timestamp
            AFTER UPDATE ON candidates
            BEGIN
                UPDATE candidates SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            
            CREATE TRIGGER IF NOT EXISTS update_interviews_timestamp
            AFTER UPDATE ON interviews
            BEGIN
                UPDATE interviews SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            
            CREATE TRIGGER IF NOT EXISTS update_jobs_timestamp
            AFTER UPDATE ON job_requisitions
            BEGIN
                UPDATE job_requisitions SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
        """)
        self.conn.commit()
    
    def _write_local(self, table: str, data: Dict[str, Any], operation: str):
        """Implement local write for Recruiter Agent tables"""
        if table == "candidates":
            self._write_candidate(data, operation)
        elif table == "interviews":
            self._write_interview(data, operation)
        elif table == "job_requisitions":
            self._write_job(data, operation)
        elif table == "agent_interactions":
            self._write_interaction(data, operation)
        else:
            raise ValueError(f"Unknown table: {table}")
    
    def _write_candidate(self, data: Dict[str, Any], operation: str):
        """Write candidate data"""
        if operation == "insert":
            candidate_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO candidates 
                (id, name, email, phone, skills, experience_years, education, 
                 location, status, source, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                candidate_id,
                data['name'],
                data.get('email'),
                data.get('phone'),
                json.dumps(data.get('skills', [])),
                data.get('experience_years', 0),
                data.get('education'),
                data.get('location'),
                data.get('status', 'active'),
                data.get('source'),
                data.get('notes')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE candidates 
                SET name=?, email=?, phone=?, skills=?, experience_years=?,
                    education=?, location=?, status=?, notes=?
                WHERE id=?
            """, (
                data['name'],
                data.get('email'),
                data.get('phone'),
                json.dumps(data.get('skills', [])),
                data.get('experience_years', 0),
                data.get('education'),
                data.get('location'),
                data.get('status', 'active'),
                data.get('notes'),
                data['id']
            ))
        elif operation == "delete":
            self.conn.execute("DELETE FROM candidates WHERE id=?", (data['id'],))
        
        self.conn.commit()
    
    def _write_interview(self, data: Dict[str, Any], operation: str):
        """Write interview data"""
        if operation == "insert":
            interview_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO interviews
                (id, candidate_id, interviewer_agent, scheduled_date, actual_date,
                 interview_type, notes, score, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interview_id,
                data['candidate_id'],
                data.get('interviewer_agent'),
                data.get('scheduled_date'),
                data.get('actual_date'),
                data.get('interview_type'),
                data.get('notes'),
                data.get('score'),
                data.get('outcome', 'pending')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE interviews
                SET scheduled_date=?, actual_date=?, interview_type=?,
                    notes=?, score=?, outcome=?
                WHERE id=?
            """, (
                data.get('scheduled_date'),
                data.get('actual_date'),
                data.get('interview_type'),
                data.get('notes'),
                data.get('score'),
                data.get('outcome'),
                data['id']
            ))
        elif operation == "delete":
            self.conn.execute("DELETE FROM interviews WHERE id=?", (data['id'],))
        
        self.conn.commit()
    
    def _write_job(self, data: Dict[str, Any], operation: str):
        """Write job requisition data"""
        if operation == "insert":
            job_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO job_requisitions
                (id, title, department, required_skills, preferred_skills,
                 experience_required, location, status, priority, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data['title'],
                data.get('department'),
                json.dumps(data.get('required_skills', [])),
                json.dumps(data.get('preferred_skills', [])),
                data.get('experience_required', 0),
                data.get('location'),
                data.get('status', 'open'),
                data.get('priority', 5),
                data.get('description')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE job_requisitions
                SET title=?, department=?, required_skills=?, preferred_skills=?,
                    experience_required=?, location=?, status=?, priority=?, description=?
                WHERE id=?
            """, (
                data['title'],
                data.get('department'),
                json.dumps(data.get('required_skills', [])),
                json.dumps(data.get('preferred_skills', [])),
                data.get('experience_required', 0),
                data.get('location'),
                data.get('status', 'open'),
                data.get('priority', 5),
                data.get('description'),
                data['id']
            ))
        elif operation == "delete":
            self.conn.execute("DELETE FROM job_requisitions WHERE id=?", (data['id'],))
        
        self.conn.commit()
    
    def _write_interaction(self, data: Dict[str, Any], operation: str):
        """Write agent interaction data"""
        if operation == "insert":
            interaction_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT INTO agent_interactions
                (id, source_agent, target_agent, interaction_type, context)
                VALUES (?, ?, ?, ?, ?)
            """, (
                interaction_id,
                data['source_agent'],
                data['target_agent'],
                data['interaction_type'],
                json.dumps(data.get('context', {}))
            ))
        elif operation == "delete":
            self.conn.execute("DELETE FROM agent_interactions WHERE id=?", (data['id'],))
        
        self.conn.commit()
    
    # High-level API methods
    
    async def add_candidate(self, candidate: Dict[str, Any]) -> str:
        """
        Add a new candidate.
        
        Args:
            candidate: Candidate data dictionary
            
        Returns:
            Candidate ID
        """
        candidate_id = candidate.get('id') or str(uuid.uuid4())
        candidate['id'] = candidate_id
        
        await self.write_data('candidates', candidate, 'insert')
        return candidate_id
    
    async def update_candidate(self, candidate_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing candidate"""
        updates['id'] = candidate_id
        return await self.write_data('candidates', updates, 'update')
    
    async def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get candidate by ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, email, phone, skills, experience_years,
                   education, location, status, source, notes, created_at
            FROM candidates WHERE id = ?
        """, (candidate_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'skills': json.loads(row[4]),
            'experience_years': row[5],
            'education': row[6],
            'location': row[7],
            'status': row[8],
            'source': row[9],
            'notes': row[10],
            'created_at': row[11]
        }
    
    async def search_candidates(
        self,
        skills: Optional[List[str]] = None,
        min_experience: Optional[int] = None,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """
        Search for candidates matching criteria.
        
        Args:
            skills: Required skills (matches any)
            min_experience: Minimum years of experience
            status: Candidate status filter
            
        Returns:
            List of matching candidates
        """
        query = """
            SELECT id, name, email, phone, skills, experience_years,
                   education, location, status, source
            FROM candidates
            WHERE status = ?
        """
        params = [status]
        
        if min_experience is not None:
            query += " AND experience_years >= ?"
            params.append(min_experience)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            candidate_skills = json.loads(row[4])
            
            # Filter by skills if provided
            if skills and not any(skill in candidate_skills for skill in skills):
                continue
            
            results.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'skills': candidate_skills,
                'experience_years': row[5],
                'education': row[6],
                'location': row[7],
                'status': row[8],
                'source': row[9]
            })
        
        return results
    
    async def add_interview(self, interview: Dict[str, Any]) -> str:
        """Add interview record"""
        interview_id = interview.get('id') or str(uuid.uuid4())
        interview['id'] = interview_id
        
        await self.write_data('interviews', interview, 'insert')
        return interview_id
    
    async def get_candidate_interviews(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Get all interviews for a candidate"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, interviewer_agent, scheduled_date, actual_date,
                   interview_type, notes, score, outcome
            FROM interviews
            WHERE candidate_id = ?
            ORDER BY created_at DESC
        """, (candidate_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'candidate_id': candidate_id,
                'interviewer_agent': row[1],
                'scheduled_date': row[2],
                'actual_date': row[3],
                'interview_type': row[4],
                'notes': row[5],
                'score': row[6],
                'outcome': row[7]
            })
        
        return results
    
    async def add_job_requisition(self, job: Dict[str, Any]) -> str:
        """Add job requisition"""
        job_id = job.get('id') or str(uuid.uuid4())
        job['id'] = job_id
        
        await self.write_data('job_requisitions', job, 'insert')
        return job_id
    
    async def get_open_jobs(self) -> List[Dict[str, Any]]:
        """Get all open job requisitions"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, department, required_skills, preferred_skills,
                   experience_required, location, priority, description
            FROM job_requisitions
            WHERE status = 'open'
            ORDER BY priority DESC, created_at DESC
        """, ())
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'department': row[2],
                'required_skills': json.loads(row[3]),
                'preferred_skills': json.loads(row[4]),
                'experience_required': row[5],
                'location': row[6],
                'priority': row[7],
                'description': row[8]
            })
        
        return results
    
    async def log_agent_interaction(
        self,
        target_agent: str,
        interaction_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Log interaction with another agent"""
        interaction = {
            'source_agent': self.agent_id,
            'target_agent': target_agent,
            'interaction_type': interaction_type,
            'context': context
        }
        
        interaction_id = str(uuid.uuid4())
        interaction['id'] = interaction_id
        
        await self.write_data('agent_interactions', interaction, 'insert')
        return interaction_id
