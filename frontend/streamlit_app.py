import streamlit as st
import requests
import json
from typing import Optional
import time
from datetime import datetime
from persistence import (
    load_chat_history, save_chat_history, load_documents, 
    save_documents, get_session_list
)

# Page configuration
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling - FIXING ALIGNMENT AND VISIBILITY ISSUES
st.markdown("""
<style>
    :root {
        --primary-bg: #1a1a1a;
        --secondary-bg: #2a2a2a;
        --tertiary-bg: #353535;
        --text-primary: #ececec;
        --text-secondary: #a0a0a0;
        --accent-green: #10a37f;
        --border-color: #404040;
    }

    /* Base theme overrides */
    html, body, .stApp {
        background-color: var(--primary-bg);
        color: var(--text-primary);
    }
    
    /* Improve spacing and layout */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: var(--primary-bg);
        border-right: 1px solid var(--border-color);
    }

    /* Common elements text color */
    h1, h2, h3, h4, h5, h6, p, li, span, div {
        color: var(--text-primary);
    }

    /* Buttons - Standardize look */
    .stButton button {
        background-color: var(--tertiary-bg);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }

    .stButton button:hover {
        background-color: var(--secondary-bg);
        border-color: var(--accent-green);
        color: var(--text-primary);
    }

    /* Input fields */
    .stTextInput input, .stSelectbox select {
        background-color: var(--secondary-bg);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }

    .stTextInput input:focus {
        border-color: var(--accent-green);
        box-shadow: 0 0 0 1px var(--accent-green);
    }

    /* Chat bubble styling */
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin: 10px 0;
    }

    .user-bubble {
        background-color: var(--accent-green);
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        max-width: 75%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    .assistant-message {
        display: flex;
        justify-content: flex-start;
        margin: 10px 0;
    }

    .assistant-bubble {
        background-color: var(--secondary-bg);
        color: var(--text-primary);
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        max-width: 75%;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background-color: var(--secondary-bg);
        padding: 20px;
        border-radius: 10px;
        border: 1px dashed var(--border-color);
    }

    [data-testid="stFileUploader"] section {
         background-color: transparent;
    }

    /* Expander header */
    .streamlit-expanderHeader {
        background-color: var(--secondary-bg);
        color: var(--text-primary);
        border-radius: 5px;
    }

    /* Metrics and Cards */
    [data-testid="stMetricValue"] {
        color: var(--accent-green);
    }
    
    /* Scrollbar customization */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--primary-bg); 
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--tertiary-bg); 
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555; 
    }

    /* Welcome screen */
    .welcome-container {
        text-align: center;
        padding: 40px 20px;
    }
    
    .welcome-title {
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 10px;
        color: var(--text-primary);
    }
    
    .welcome-subtitle {
        font-size: 1.1rem;
        color: var(--text-secondary);
    }

</style>
""", unsafe_allow_html=True)

# Configuration
import os
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
    st.session_state.messages = load_chat_history(st.session_state.session_id)
    
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
    
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = load_documents()

if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"

# ==================== SIDEBAR ====================
with st.sidebar:
    # Top section - Logo and title
    st.title("🤖 RAG Chatbot")
    
    # New chat button
    if st.button("➕ New Chat", use_container_width=True, key="new_chat"):
        st.session_state.session_id = f"session_{int(time.time())}"
        st.session_state.messages = []
        st.session_state.user_input = ""
        st.rerun()
    
    st.divider()
    
    # Navigation
    st.subheader("Navigation")
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        if st.button("💬 Chat", use_container_width=True, key="nav_chat"):
            st.session_state.current_page = "chat"
            st.rerun()
    
    with nav_col2:
        if st.button("📤 Upload", use_container_width=True, key="nav_upload"):
            st.session_state.current_page = "upload"
            st.rerun()
    
    with nav_col3:
        if st.button("📊 Trace", use_container_width=True, key="nav_trace"):
            st.session_state.current_page = "trace"
            st.rerun()
    
    st.divider()
    
    # Chat history section
    st.subheader("Recent Chats")
    sessions = get_session_list()
    
    if sessions:
        with st.container(height=200):
            for session in sessions[:10]:
                session_id = session["session_id"]
                msg_count = session["message_count"]
                display_name = f"Session ({msg_count} msgs)"
                
                if st.button(
                    f"💭 {display_name}",
                    use_container_width=True,
                    key=f"session_{session_id}"
                ):
                    st.session_state.session_id = session_id
                    st.session_state.messages = load_chat_history(session_id)
                    st.session_state.current_page = "chat"
                    st.rerun()
    else:
        st.caption("No chat history available")
    
    st.divider()
    
    # Configuration section
    st.subheader("Settings")
    
    api_url = st.text_input(
        "API Endpoint",
        value=API_BASE_URL,
        help="Backend API URL (e.g., http://localhost:8000)",
        key="api_url_input"
    )
    
    enable_web_search = st.toggle(
        "Enable Web Search",
        value=True,
        help="Allow the agent to search the web for current information"
    )
    
    st.divider()
    
    # Document management
    st.subheader("Knowledge Base")
    st.metric("Documents Indexed", len(st.session_state.uploaded_documents))
    
    if st.session_state.uploaded_documents:
        with st.expander("View Document List"):
            for doc in st.session_state.uploaded_documents:
                st.caption(f"📄 {doc}")
    
    if st.button("🗑️ Clear Database", use_container_width=True, type="secondary"):
        with st.spinner("Clearing knowledge base..."):
            try:
                response = requests.delete(
                    f"{api_url}/clear-knowledge-base/",
                    timeout=30
                )
                if response.status_code == 200:
                    st.session_state.uploaded_documents = []
                    st.success("Knowledge base cleared!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to clear: {response.status_code}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

    st.markdown("---")
    st.caption(f"Session: {st.session_state.session_id[:8]}...")

# ==================== MAIN CONTENT ====================
if st.session_state.current_page == "chat":
    # Chat interface container
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div class="welcome-container">
                <div class="welcome-title">How can I help you?</div>
                <div class="welcome-subtitle">Upload PDF documents to context-aware Q&A or ask general questions.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display chat history
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <div class="user-bubble">{message['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-message">
                        <div class="assistant-bubble">{message['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Spacer
        st.markdown("<div style='height: 50px'></div>", unsafe_allow_html=True)
        
    # Input area fixed at bottom
    with st.container():
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.chat_input("Type your message here...", key="chat_input")
            
        if user_input:
            # Add user message
            timestamp = datetime.now().strftime("%H:%M:%S")
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": timestamp
            }
            st.session_state.messages.append(user_message)
            save_chat_history(st.session_state.session_id, st.session_state.messages)
            
            # Show spinner while waiting for response
            with st.spinner("Applying RAG & Thinking..."):
                try:
                    response = requests.post(
                        f"{api_url}/chat/",
                        json={
                            "session_id": st.session_state.session_id,
                            "query": user_input,
                            "enable_web_search": enable_web_search
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        bot_response = data.get("response", "No response received.")
                        
                        assistant_message = {
                            "role": "assistant",
                            "content": bot_response,
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "trace_events": data.get("trace_events", [])
                        }
                        st.session_state.messages.append(assistant_message)
                        save_chat_history(st.session_state.session_id, st.session_state.messages)
                        st.rerun()
                    else:
                        st.error(f"API Error: {response.status_code} - {response.text}")
                
                except requests.exceptions.ConnectionError:
                    st.error("❌ Connection refused. Is the backend server running properly on port 8000?")
                except Exception as e:
                    st.error(f"❌ Error occurred: {str(e)}")

elif st.session_state.current_page == "upload":
    st.title("📤 Document Upload")
    st.markdown("Upload PDF files to populate your Knowledge Base (RAG).")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        # File info card
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📄 **File:** {uploaded_file.name}")
            with col2:
                st.info(f"📏 **Size:** {uploaded_file.size / 1024:.2f} KB")
        
        if st.button("Start Upload & Indexing", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Connecting to backend...")
            progress_bar.progress(10)
            
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                
                status_text.text("Uploading file...")
                progress_bar.progress(30)
                
                response = requests.post(
                    f"{api_url}/upload-document/",
                    files=files,
                    timeout=120
                )
                
                progress_bar.progress(80)
                
                if response.status_code == 200:
                    data = response.json()
                    status_text.text("Indexing complete!")
                    progress_bar.progress(100)
                    
                    if "filename" in data:
                        st.session_state.uploaded_documents.append(data["filename"])
                        save_documents(st.session_state.uploaded_documents)
                        st.success(f"✅ Successfully added **{uploaded_file.name}** to knowledge base.")
                        time.sleep(2)
                        st.rerun()
                        
                elif response.status_code == 403:
                    progress_bar.empty()
                    status_text.empty()
                    st.error("""
                    ### ⛔ Access Denied (403 Error)
                    The server rejected the upload request. This typically happens due to:
                    1. **CORS Issues**: The backend might not be allowing requests from this frontend origin.
                    2. **Firewall/Proxy**: Network security rules blocking the upload.
                    3. **File Permissions**: Server permission issues.
                    
                    **Try this:**
                    - Check backend logs for detailed error usage.
                    - Ensure `CORSMiddleware` is configured in FastAPI.
                    - Verify the file is a valid PDF.
                    """)
                else:
                    progress_bar.empty()
                    st.error(f"❌ Upload failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                progress_bar.empty()
                st.error("❌ **Connection Failed**: Could not reach backend server. Please verify it is running at the specified URL.")
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ Unexpected Error: {str(e)}")

elif st.session_state.current_page == "trace":
    st.title("📊 Agent Trace Viewer")
    st.markdown("Inspect the internal reasoning steps of the last agent execution.")
    
    if not st.session_state.messages:
        st.info("Start a chat to generate trace data.")
    else:
        last_trace = None
        # Find last message with trace events
        for message in reversed(st.session_state.messages):
            if message.get("trace_events"):
                last_trace = message.get("trace_events", [])
                break
        
        if last_trace:
            st.success(f"Found {len(last_trace)} trace events from latest response.")
            
            for i, event in enumerate(last_trace, 1):
                event_type = event.get('event_type', 'generic')
                node = event.get('node_name', 'unknown')
                
                with st.expander(f"Step {i}: {node} ({event_type})"):
                    st.markdown(f"**Description:** {event.get('description')}")
                    st.json(event)
        else:
            st.warning("No trace data found in recent messages.")
