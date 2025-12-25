"""
Persistence layer for Streamlit app
Handles saving and loading chat history and document metadata
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

PERSISTENCE_DIR = Path.home() / ".rag_chatbot"
CHAT_HISTORY_FILE = PERSISTENCE_DIR / "chat_history.json"
DOCUMENTS_FILE = PERSISTENCE_DIR / "documents.json"


def ensure_persistence_dir():
    """Ensure persistence directory exists"""
    PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)


def load_chat_history(session_id: str) -> List[Dict[str, Any]]:
    """Load chat history for a specific session"""
    ensure_persistence_dir()
    
    if not CHAT_HISTORY_FILE.exists():
        return []
    
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            all_chats = json.load(f)
            return all_chats.get(session_id, [])
    except Exception as e:
        print(f"Error loading chat history: {e}")
        return []


def save_chat_history(session_id: str, messages: List[Dict[str, Any]]):
    """Save chat history for a specific session"""
    ensure_persistence_dir()
    
    try:
        # Load existing data
        all_chats = {}
        if CHAT_HISTORY_FILE.exists():
            with open(CHAT_HISTORY_FILE, 'r') as f:
                all_chats = json.load(f)
        
        # Update with new messages
        all_chats[session_id] = messages
        
        # Save back
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(all_chats, f, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")


def load_documents() -> List[str]:
    """Load list of uploaded documents"""
    ensure_persistence_dir()
    
    if not DOCUMENTS_FILE.exists():
        return []
    
    try:
        with open(DOCUMENTS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("documents", [])
    except Exception as e:
        print(f"Error loading documents: {e}")
        return []


def save_documents(documents: List[str]):
    """Save list of uploaded documents"""
    ensure_persistence_dir()
    
    try:
        data = {
            "documents": documents,
            "last_updated": datetime.now().isoformat()
        }
        with open(DOCUMENTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving documents: {e}")


def add_document(document_name: str) -> List[str]:
    """Add a document to the list"""
    documents = load_documents()
    if document_name not in documents:
        documents.append(document_name)
        save_documents(documents)
    return documents


def remove_document(document_name: str) -> List[str]:
    """Remove a document from the list"""
    documents = load_documents()
    if document_name in documents:
        documents.remove(document_name)
        save_documents(documents)
    return documents


def clear_all_documents():
    """Clear all documents"""
    save_documents([])


def get_session_list() -> List[Dict[str, Any]]:
    """Get list of all sessions with message counts"""
    ensure_persistence_dir()
    
    if not CHAT_HISTORY_FILE.exists():
        return []
    
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            all_chats = json.load(f)
            sessions = []
            for session_id, messages in all_chats.items():
                sessions.append({
                    "session_id": session_id,
                    "message_count": len(messages),
                    "last_message_time": messages[-1].get("timestamp", "N/A") if messages else "N/A"
                })
            return sorted(sessions, key=lambda x: x["last_message_time"], reverse=True)
    except Exception as e:
        print(f"Error getting session list: {e}")
        return []
