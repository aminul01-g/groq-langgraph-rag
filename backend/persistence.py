"""
Backend persistence module for LangGraph checkpoints
Uses SQLite for reliable, persistent checkpoint storage
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Create data directory for SQLite database

# Use a local data directory by default, or respect environment variable
DATA_DIR_PATH = os.getenv("DATA_DIR", "data")
DATA_DIR = Path(DATA_DIR_PATH)
if not DATA_DIR.is_absolute():
    # Make relative to this file's parent directory
    DATA_DIR = Path(__file__).parent / DATA_DIR
    
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "checkpoints.db"


def init_checkpoint_db():
    """Initialize the checkpoint database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create checkpoints table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            thread_id TEXT PRIMARY KEY,
            checkpoint_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            message_role TEXT NOT NULL,
            message_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES checkpoints(thread_id)
        )
    """)
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            chunks_count INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            embedding_id TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def save_checkpoint(thread_id: str, checkpoint_data: Dict[str, Any]):
    """Save checkpoint data for a session"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        checkpoint_json = json.dumps(checkpoint_data)
        
        # Insert or replace checkpoint
        cursor.execute("""
            INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (thread_id, checkpoint_json))
        
        conn.commit()
        print(f" Checkpoint saved for thread {thread_id}")
    except Exception as e:
        print(f" Error saving checkpoint: {e}")
    finally:
        conn.close()


def load_checkpoint(thread_id: str) -> Optional[Dict[str, Any]]:
    """Load checkpoint data for a session"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT checkpoint_data FROM checkpoints WHERE thread_id = ?
        """, (thread_id,))
        
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    except Exception as e:
        print(f" Error loading checkpoint: {e}")
        return None
    finally:
        conn.close()


def save_chat_message(thread_id: str, role: str, content: str):
    """Save a chat message to the database"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO chat_history (thread_id, message_role, message_content)
            VALUES (?, ?, ?)
        """, (thread_id, role, content))
        
        conn.commit()
    except Exception as e:
        print(f" Error saving chat message: {e}")
    finally:
        conn.close()


def load_chat_history(thread_id: str) -> list:
    """Load all chat messages for a session"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT message_role, message_content, created_at FROM chat_history
            WHERE thread_id = ?
            ORDER BY created_at ASC
        """, (thread_id,))
        
        messages = []
        for role, content, timestamp in cursor.fetchall():
            messages.append({
                "role": role,
                "content": content,
                "timestamp": timestamp
            })
        return messages
    except Exception as e:
        print(f" Error loading chat history: {e}")
        return []
    finally:
        conn.close()


def save_document_metadata(filename: str, chunks_count: int, embedding_id: Optional[str] = None):
    """Save document metadata"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO documents (filename, chunks_count, embedding_id)
            VALUES (?, ?, ?)
        """, (filename, chunks_count, embedding_id))
        
        conn.commit()
        print(f" Document metadata saved for {filename}")
    except Exception as e:
        print(f" Error saving document metadata: {e}")
    finally:
        conn.close()


def get_all_documents() -> list:
    """Get all uploaded documents"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT filename, chunks_count, uploaded_at FROM documents
            ORDER BY uploaded_at DESC
        """)
        
        documents = []
        for filename, chunks, timestamp in cursor.fetchall():
            documents.append({
                "filename": filename,
                "chunks_count": chunks,
                "uploaded_at": timestamp
            })
        return documents
    except Exception as e:
        print(f" Error loading documents: {e}")
        return []
    finally:
        conn.close()


def delete_document(filename: str):
    """Delete document metadata"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM documents WHERE filename = ?
        """, (filename,))
        
        conn.commit()
        print(f" Document metadata deleted for {filename}")
    except Exception as e:
        print(f" Error deleting document metadata: {e}")
    finally:
        conn.close()


def clear_all_documents():
    """Clear all document metadata"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM documents")
        conn.commit()
        print(" All document metadata cleared")
    except Exception as e:
        print(f" Error clearing documents: {e}")
    finally:
        conn.close()


def get_session_stats() -> Dict[str, Any]:
    """Get statistics about stored sessions"""
    init_checkpoint_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Count sessions
        cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
        session_count = cursor.fetchone()[0]
        
        # Count total messages
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        message_count = cursor.fetchone()[0]
        
        # Count documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        document_count = cursor.fetchone()[0]
        
        # Get total chunks
        cursor.execute("SELECT SUM(chunks_count) FROM documents")
        total_chunks = cursor.fetchone()[0] or 0
        
        return {
            "sessions": session_count,
            "messages": message_count,
            "documents": document_count,
            "total_chunks": total_chunks
        }
    except Exception as e:
        print(f" Error getting session stats: {e}")
        return {}
    finally:
        conn.close()


# Initialize database on module import
init_checkpoint_db()
