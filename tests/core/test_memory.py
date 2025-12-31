"""
Test Suite: MemorySystem
Tests for commander_os.core.memory

Run with: pytest tests/core/test_memory.py -v
"""

import pytest
import os
from commander_os.core.memory import MessageStore

@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary DB path."""
    return f"sqlite:///{tmp_path}/test_memory.db"

@pytest.fixture
def memory_store(test_db_path):
    """Create MessageStore instance."""
    return MessageStore(test_db_path)

class TestMessageStore:
    """Tests for MessageStore."""

    def test_log_and_retrieve(self, memory_store):
        """Test logging a message and retrieving it."""
        msg_id = memory_store.log_message(
            task_id="task-1",
            sender="agent-1",
            recipient="agent-2",
            role="coder",
            content="Hello world",
            iteration=1
        )
        assert msg_id is not None
        
        # Retrieve
        msgs = memory_store.query_messages(task_id="task-1")
        assert len(msgs) == 1
        assert msgs[0]['content'] == "Hello world"
        assert msgs[0]['sender'] == "agent-1"
        assert msgs[0]['recipient'] == ["agent-2"]

    def test_compression(self, memory_store):
        """Test that long content is handled (compressed)."""
        long_content = "A" * 10000
        msg_id = memory_store.log_message(
            task_id="task-2",
            sender="agent-1",
            recipient="agent-2",
            role="coder",
            content=long_content
        )
        
        msgs = memory_store.query_messages(task_id="task-2")
        assert msgs[0]['content'] == long_content

    def test_query_filters(self, memory_store):
        """Test filtering messages."""
        memory_store.log_message(task_id="t1", sender="a1", recipient="a2", role="r1", content="cnt1")
        memory_store.log_message(task_id="t1", sender="a2", recipient="a1", role="r2", content="cnt2")
        memory_store.log_message(task_id="t2", sender="a1", recipient="a2", role="r1", content="cnt3")
        
        # Filter by task
        assert len(memory_store.query_messages(task_id="t1")) == 2
        # Filter by sender
        assert len(memory_store.query_messages(sender="a1")) == 2
        # Filter by role
        assert len(memory_store.query_messages(role="r2")) == 1

    def test_get_recent_context(self, memory_store):
        """Test context retrieval formatting."""
        memory_store.log_message(task_id="t3", sender="User", recipient="Agent", role="user", content="Hi")
        memory_store.log_message(task_id="t3", sender="Agent", recipient="User", role="assistant", content="Hello")
        
        context = memory_store.get_recent_context(task_id="t3")
        
        assert "User (user): Hi" in context
        assert "Agent (assistant): Hello" in context

    def test_prune_archives(self, memory_store):
        """Test pruning old messages."""
        # This is tricky without manipulating timestamps.
        # We rely on the SQL not throwing error, and logic being correct.
        # Mocking datetime.now() would be needed for precise test, 
        # or we manually insert a record with old timestamp.
        
        # Manually insert old record via session
        from commander_os.core.memory import MessageModel
        session = memory_store.SessionLocal()
        old_msg = MessageModel(
            timestamp=100.0, # 1970
            task_id="old",
            sender="old",
            content_blob=b"",
        )
        session.add(old_msg)
        session.commit()
        session.close()
        
        count = memory_store.prune_archives(days_keep=1)
        assert count == 1
        
        left = memory_store.query_messages(task_id="old")
        assert len(left) == 0
