"""
Unit tests for Commander OS Storage System

Tests BaseStorage, AgentStorage, and RecruiterAgentStorage implementations.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from commander_os.storage.base_storage import BaseStorage
from commander_os.storage.agent_storage import AgentStorage
from commander_os.agents.recruiter.recruiter_storage import RecruiterAgentStorage
from commander_os.agents.commander.commander_storage import CommanderStorage


class TestBaseStorage:
    """Test BaseStorage class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create BaseStorage instance with mocked _write_local"""
        class TestStorage(BaseStorage):
            def _write_local(self, table, data, operation):
                # Mock implementation for testing
                self.conn.execute(
                    f"INSERT OR REPLACE INTO test_table (id, data) VALUES (?, ?)",
                    (data.get('id', 'test'), str(data))
                )
                self.conn.commit()
        
        # Create test table
        storage = TestStorage(
            agent_id="test-agent",
            data_dir=temp_dir,
            htpc_url=None,
            enable_htpc=False
        )
        storage.conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id TEXT PRIMARY KEY,
                data TEXT
            )
        """)
        storage.conn.commit()
        
        yield storage
        storage.conn.close()
    
    def test_initialization(self, temp_dir):
        """Test storage initialization"""
        storage = AgentStorage(
            agent_id="test-agent",
            data_dir=temp_dir,
            enable_htpc=False
        )
        
        assert storage.agent_id == "test-agent"
        assert storage.conn is not None
        assert storage.db_path.exists()
        
        storage.conn.close()
    
    def test_wal_mode_enabled(self, temp_dir):
        """Test that WAL mode is properly enabled"""
        storage = AgentStorage(
            agent_id="test-agent",
            data_dir=temp_dir,
            enable_htpc=False
        )
        
        cursor = storage.conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        
        assert result[0].lower() == 'wal'
        
        storage.conn.close()
    
    def test_sync_queue_creation(self, storage):
        """Test that sync queue table is created"""
        cursor = storage.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sync_queue'
        """)
        
        assert cursor.fetchone() is not None
    
    def test_queue_for_sync(self, storage):
        """Test queueing data for sync"""
        test_data = {'id': '123', 'value': 'test'}
        storage._queue_for_sync('test_table', test_data, 'insert')
        
        queue_size = storage.get_sync_queue_size()
        assert queue_size == 1
    
    def test_health_check(self, storage):
        """Test health check functionality"""
        health = storage.health_check()
        
        assert health['agent_id'] == 'test-agent'
        assert health['local_db'] is True
        assert health['htpc_enabled'] is False
        assert 'sync_queue_size' in health


class TestAgentStorage:
    """Test AgentStorage class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create AgentStorage instance"""
        storage = AgentStorage(
            agent_id="test-agent",
            data_dir=temp_dir,
            enable_htpc=False
        )
        yield storage
        storage.conn.close()
    
    def test_set_and_get(self, storage):
        """Test basic set/get operations"""
        storage.set('test_key', {'name': 'test', 'value': 123})
        result = storage.get('test_key')
        
        assert result is not None
        assert result['name'] == 'test'
        assert result['value'] == 123
    
    def test_delete(self, storage):
        """Test delete operation"""
        storage.set('test_key', {'name': 'test'})
        assert storage.get('test_key') is not None
        
        storage.delete('test_key')
        assert storage.get('test_key') is None
    
    def test_list_all(self, storage):
        """Test listing all data"""
        storage.set('key1', {'value': 1})
        storage.set('key2', {'value': 2})
        storage.set('key3', {'value': 3})
        
        all_data = storage.list_all()
        assert len(all_data) == 3
        assert 'key1' in all_data
        assert all_data['key2']['value'] == 2


class TestRecruiterAgentStorage:
    """Test RecruiterAgentStorage class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create RecruiterAgentStorage instance"""
        storage = RecruiterAgentStorage(
            data_dir=temp_dir,
            enable_htpc=False
        )
        yield storage
        storage.conn.close()
    
    @pytest.mark.asyncio
    async def test_add_candidate(self, storage):
        """Test adding a candidate"""
        candidate = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'skills': ['Python', 'SQL', 'Machine Learning'],
            'experience_years': 5,
            'location': 'Seattle'
        }
        
        candidate_id = await storage.add_candidate(candidate)
        assert candidate_id is not None
        
        # Retrieve candidate
        retrieved = await storage.get_candidate(candidate_id)
        assert retrieved is not None
        assert retrieved['name'] == 'John Doe'
        assert 'Python' in retrieved['skills']
    
    @pytest.mark.asyncio
    async def test_search_candidates_by_skills(self, storage):
        """Test searching candidates by skills"""
        # Add multiple candidates
        await storage.add_candidate({
            'name': 'Alice',
            'email': 'alice@example.com',
            'skills': ['Python', 'Django'],
            'experience_years': 3
        })
        
        await storage.add_candidate({
            'name': 'Bob',
            'email': 'bob@example.com',
            'skills': ['Java', 'Spring'],
            'experience_years': 5
        })
        
        await storage.add_candidate({
            'name': 'Charlie',
            'email': 'charlie@example.com',
            'skills': ['Python', 'Flask'],
            'experience_years': 7
        })
        
        # Search for Python developers
        results = await storage.search_candidates(skills=['Python'])
        assert len(results) == 2
        assert all('Python' in r['skills'] for r in results)
    
    @pytest.mark.asyncio
    async def test_search_candidates_by_experience(self, storage):
        """Test searching candidates by experience"""
        await storage.add_candidate({
            'name': 'Junior Dev',
            'email': 'junior@example.com',
            'skills': ['Python'],
            'experience_years': 1
        })
        
        await storage.add_candidate({
            'name': 'Senior Dev',
            'email': 'senior@example.com',
            'skills': ['Python'],
            'experience_years': 10
        })
        
        # Search for senior developers (5+ years)
        results = await storage.search_candidates(min_experience=5)
        assert len(results) == 1
        assert results[0]['name'] == 'Senior Dev'
    
    @pytest.mark.asyncio
    async def test_add_interview(self, storage):
        """Test adding an interview record"""
        # First add a candidate
        candidate_id = await storage.add_candidate({
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'skills': ['Python'],
            'experience_years': 3
        })
        
        # Add interview
        interview = {
            'candidate_id': candidate_id,
            'interviewer_agent': 'technical-interviewer',
            'interview_type': 'technical',
            'outcome': 'pending'
        }
        
        interview_id = await storage.add_interview(interview)
        assert interview_id is not None
        
        # Retrieve interviews
        interviews = await storage.get_candidate_interviews(candidate_id)
        assert len(interviews) == 1
        assert interviews[0]['interview_type'] == 'technical'
    
    @pytest.mark.asyncio
    async def test_add_job_requisition(self, storage):
        """Test adding a job requisition"""
        job = {
            'title': 'Senior Python Developer',
            'department': 'Engineering',
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
            'experience_required': 5,
            'priority': 8
        }
        
        job_id = await storage.add_job_requisition(job)
        assert job_id is not None
        
        # Retrieve open jobs
        open_jobs = await storage.get_open_jobs()
        assert len(open_jobs) == 1
        assert open_jobs[0]['title'] == 'Senior Python Developer'
        assert 'Python' in open_jobs[0]['required_skills']
    
    @pytest.mark.asyncio
    async def test_log_agent_interaction(self, storage):
        """Test logging agent interactions"""
        interaction_id = await storage.log_agent_interaction(
            target_agent='technical-interviewer',
            interaction_type='recommendation',
            context={'candidate_id': '123', 'reason': 'skill match'}
        )
        
        assert interaction_id is not None


class TestCommanderStorage:
    """Test CommanderStorage class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create CommanderStorage instance"""
        storage = CommanderStorage(
            data_dir=temp_dir,
            enable_htpc=False
        )
        yield storage
        storage.conn.close()
    
    @pytest.mark.asyncio
    async def test_register_agent(self, storage):
        """Test agent registration"""
        agent_data = {
            'agent_id': 'recruiter-1',
            'name': 'Recruiter Alpha',
            'role': 'recruiter',
            'capabilities': ['search', 'email'],
            'endpoint': 'http://10.0.0.50:8000'
        }
        
        await storage.register_agent(agent_data)
        
        # Verify registration
        agent = await storage.get_agent_info('recruiter-1')
        assert agent is not None
        assert agent['name'] == 'Recruiter Alpha'
        assert agent['role'] == 'recruiter'
        assert 'search' in agent['capabilities']
    
    @pytest.mark.asyncio
    async def test_track_task(self, storage):
        """Test task tracking"""
        task_id = await storage.create_task({
            'title': 'Hiring Campaign',
            'description': 'Hire 5 Python devs',
            'priority': 8,
            'status': 'pending'
        })
        
        assert task_id is not None
        
        # Get active tasks
        tasks = await storage.get_active_tasks()
        assert len(tasks) == 1
        assert tasks[0]['id'] == task_id
    
    @pytest.mark.asyncio
    async def test_log_decision(self, storage):
        """Test decision logging"""
        await storage.log_decision({
            'decision_type': 'scale-up',
            'reasoning': 'High task load',
            'context': {'load': 0.95}
        })
        
        # Verify log entry (using generic list_all for now or could add a specific method)
        # For now, just ensure it doesn't crash
        pass
    
    @pytest.mark.asyncio
    async def test_record_comm(self, storage):
        """Test recording communications"""
        await storage.record_comm({
            'from_agent': 'the-commander',
            'to_agent': 'recruiter-1',
            'message_type': 'directive',
            'content': {'action': 'pause-hiring'}
        })


class TestStorageWithHTPC:
    """Test storage with HTPC integration (mocked)"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_dual_write_with_htpc_success(self, temp_dir):
        """Test dual-write when HTPC is available"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful HTPC response
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.post = mock_post
            mock_client.return_value.aclose = AsyncMock()
            
            storage = AgentStorage(
                agent_id="test-agent",
                data_dir=temp_dir,
                htpc_url="http://localhost:8001",
                enable_htpc=True
            )
            
            # Perform write
            await storage.write_data('test_table', {'id': '123', 'value': 'test'})
            
            # Verify HTPC was called
            assert mock_post.called
            
            storage.conn.close()
            await storage.close()
    
    @pytest.mark.asyncio
    async def test_dual_write_with_htpc_failure(self, temp_dir):
        """Test dual-write when HTPC fails (should queue)"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock failed HTPC response
            mock_post = AsyncMock(side_effect=Exception("HTPC unavailable"))
            mock_client.return_value.post = mock_post
            mock_client.return_value.aclose = AsyncMock()
            
            storage = AgentStorage(
                agent_id="test-agent",
                data_dir=temp_dir,
                htpc_url="http://localhost:8001",
                enable_htpc=True
            )
            
            # Perform write
            await storage.write_data('test_table', {'id': '123', 'value': 'test'})
            
            # Verify data was queued
            queue_size = storage.get_sync_queue_size()
            assert queue_size > 0
            
            storage.conn.close()
            await storage.close()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
