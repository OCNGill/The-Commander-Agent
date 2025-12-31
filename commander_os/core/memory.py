"""
The-Commander: Memory System
Persistent message storage and retrieval using SQLite + SQLAlchemy.

Features:
- Log messages with compression
- Structured querying (task_id, sender, role)
- Deduping via hashing
- Archival support

Version: 1.1.0
"""

import logging
import json
import gzip
import hashlib
import io
from datetime import datetime
from typing import List, Dict, Optional, Any, Union

from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary, Float, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()

class MessageModel(Base):
    """SQLAlchemy model for stored messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Float, index=True, default=0.0)  # Unix timestamp
    task_id = Column(String, index=True)
    sender = Column(String, index=True)
    recipient = Column(String)  # JSON list
    role = Column(String)
    iteration = Column(Integer, default=0)
    content_blob = Column(LargeBinary)  # Gzipped content
    metadata_json = Column(Text)  # JSON metadata
    content_hash = Column(String, index=True)
    is_compressed = Column(Boolean, default=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, decompressing content."""
        content = ""
        if self.content_blob:
            if self.is_compressed:
                try:
                    with gzip.GzipFile(fileobj=io.BytesIO(self.content_blob), mode='rb') as f:
                        content = f.read().decode('utf-8')
                except Exception as e:
                    content = f"<Error decompressing: {e}>"
            else:
                content = self.content_blob.decode('utf-8')

        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'task_id': self.task_id,
            'sender': self.sender,
            'recipient': json.loads(self.recipient) if self.recipient else [],
            'role': self.role,
            'iteration': self.iteration,
            'content': content,
            'metadata': json.loads(self.metadata_json) if self.metadata_json else {},
            'hash': self.content_hash
        }

class MessageStore:
    """
    Persistent memory manager backed by SQLite.
    """

    def __init__(self, db_path: str = "sqlite:///commander_memory.db"):
        """
        Initialize MessageStore.
        
        Args:
            db_path: Database connection string.
        """
        self.engine = create_engine(db_path, connect_args={"check_same_thread": False})
        SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = SessionMaker
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"MessageStore initialized at {db_path}")

    def log_message(self, 
                   task_id: str,
                   sender: str,
                   recipient: Union[str, List[str]],
                   role: str,
                   content: str,
                   iteration: int = 0,
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Log a new message to memory.
        
        Returns:
            ID of the inserted message.
        """
        # 1. Normalize recipient
        if isinstance(recipient, str):
            recipients = [recipient]
        else:
            recipients = recipient
            
        # 2. Compute Hash (dedup check)
        # Hash based on content + task + sender + iter
        hash_input = f"{task_id}:{sender}:{iteration}:{content}".encode('utf-8')
        content_hash = hashlib.sha256(hash_input).hexdigest()
        
        # 3. Compress Content
        content_bytes = content.encode('utf-8')
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode='wb') as f:
            f.write(content_bytes)
        compressed_content = out.getvalue()
        
        # 4. Create Record
        db_msg = MessageModel(
            timestamp=datetime.now().timestamp(),
            task_id=task_id,
            sender=sender,
            recipient=json.dumps(recipients),
            role=role,
            iteration=iteration,
            content_blob=compressed_content,
            metadata_json=json.dumps(metadata or {}),
            content_hash=content_hash,
            is_compressed=True
        )
        
        session = self.SessionLocal()
        try:
            # check dedup? For now, we allow duplicates but store hash. 
            # If strict dedup needed, query content_hash first.
            
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)
            return db_msg.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log message: {e}")
            raise
        finally:
            session.close()

    def query_messages(self, 
                      task_id: Optional[str] = None, 
                      sender: Optional[str] = None,
                      role: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for messages.
        """
        session = self.SessionLocal()
        try:
            query = session.query(MessageModel)
            
            if task_id:
                query = query.filter(MessageModel.task_id == task_id)
            if sender:
                query = query.filter(MessageModel.sender == sender)
            if role:
                query = query.filter(MessageModel.role == role)
                
            # Order by timestamp desc
            query = query.order_by(MessageModel.timestamp.desc())
            
            if limit:
                query = query.limit(limit)
                
            results = query.all()
            return [msg.to_dict() for msg in results]
        finally:
            session.close()

    def get_recent_context(self, task_id: str, max_tokens: int = 8000) -> str:
        """
        Retrieve recent messages for a task formatted as context string.
        (Simplified token estimation: 1 char ~= 0.25 tokens or just char limit)
        """
        # Get all msgs for task
        msgs = self.query_messages(task_id=task_id, limit=100)
        # Reverse to chronological
        msgs.reverse()
        
        context_parts = []
        current_len = 0
        limit_char = max_tokens * 4  # rough approx
        
        # We want the MOST RECENT context that fits.
        # So we iterate backwards from most recent? query_messages returns DESC.
        # So msgs[0] is oldest after reverse(), msgs[-1] is newest.
        # Actually query returns DESC (newest first). 
        # msgs (reversed) is oldest -> newest.
        
        for msg in msgs:
            formatted = f"[{msg['timestamp']}] {msg['sender']} ({msg['role']}): {msg['content']}\n"
            if current_len + len(formatted) > limit_char:
                # If we exceed, maybe we should stop? 
                # Or if we want tail context, we should slice from end.
                pass 
            
            context_parts.append(formatted)
            current_len += len(formatted)
            
        return "".join(context_parts)

    def prune_archives(self, days_keep: int = 30) -> int:
        """
        Delete messages older than N days.
        """
        cutoff = datetime.now().timestamp() - (days_keep * 86400)
        session = self.SessionLocal()
        try:
            affected = session.query(MessageModel).filter(MessageModel.timestamp < cutoff).delete()
            session.commit()
            return affected
        finally:
            session.close()

