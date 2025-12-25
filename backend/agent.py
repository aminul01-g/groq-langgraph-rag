from typing import TypedDict, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import os
from config import GROQ_API_KEY
from langchain_groq import ChatGroq
from vectorstore import get_retriever
from config import TAVILY_API_KEY
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.runnables import RunnableConfig
from persistence import DB_PATH


# Tools
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
tavily = TavilySearch(max_results=3)

@tool
def web_search_tool(query: str) -> str:
    """Uptodate web info via Tavily"""
    try:
        result = tavily.invoke({"query": query})
        if isinstance(result, dict) and 'results' in result:
            formatted_results = []
            for item in result['results']:
                title = item.get('title', 'No title')
                content = item.get('content', 'No content')
                url = item.get('url', '')
                formatted_results.append(f"Title: {title}\n Content: {content}\nURL:{url}")
            return "\n\n".join(formatted_results) if formatted_results else "No results found"
        else:
            return str(result)
            
    except Exception as e:
        return f"WEB_Error::{e}"




@tool
def rag_search_tool(query: str) -> str:
    """Top-k chunks from the knowledge Base"""
    try:
        retriever_instance = get_retriever()
        docs = retriever_instance.invoke(query, k=3)
        return "\n\n".join(d.page_content for d in docs) if docs else ""
    
    except Exception as e:
        return f"RAG_Error::{e}"



#Pydentic Schemas for structured outpt
class RouteDecision(BaseModel):
    route: Literal['rag', 'web', 'answer', 'end']
    reply: str | None = Field(None, description="ONLY set this field when route is 'end'. For all other routes ('rag', 'web', 'answer'), this MUST be None.")


class RagJudge(BaseModel):
    sufficient: bool = Field(..., description="True if retrieved information is sufficient to answer the users question, otherwise false")


# LLM Instances with structured schemas
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

router_llm = ChatGroq(
    model = "llama-3.3-70b-versatile", 
    temperature = 0).with_structured_output(RouteDecision)

judge_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0).with_structured_output(RagJudge)

answer_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0)




#State : Shared Data Structure
class AgentState(TypedDict, total = False):
    messages: List[BaseMessage]
    route: Literal['rag', 'web', 'answer', 'end']
    rag: str
    web: str
    web_search_enabled: bool


# Node: For Individual functions
# --- Node 1: router (decision) ---

def router_node(state: AgentState) -> AgentState:
    print("\n--- Entering router_node ---")
    query = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
    
    # Get web_search_enabled from state
    web_search_enabled = state.get("web_search_enabled", True)
    print(f"Router received web search info : {web_search_enabled}")
 
    system_prompt = (
        "You are an intelligent routing agent designed to direct user queries to the most appropriate tool."
        "Your primary goal is to provide accurate and relevant information by selecting the best source."
        "Prioritize using the **internal knowledge base (RAG)** for factual information that is likely "
        "to be contained within pre-uploaded documents or for common, well-established facts."
    )
    
    if web_search_enabled:
        system_prompt += (
            "You **CAN** use web search for queries that require very current, real-time, or broad general knowledge "
            "that is unlikely to be in a specific, static knowledge base (e.g., today's news, live data, very recent events)."
            "\n\nChoose one of the following routes:"
            "\n- 'rag': For queries about specific entities, historical facts, product details, procedures, or any information that would typically be found in a curated document collection (e.g., 'What is X?', 'How does Y work?', 'Explain Z policy')."
            "\n- 'web': For queries about current events, live data, very recent news, or broad general knowledge that requires up-to-date internet access (e.g., 'Who won the election yesterday?', 'What is the weather in London?', 'Latest news on technology')."
        )
    else:
        system_prompt += (
            "**Web search is currently DISABLED.** You **MUST NOT** choose the 'web' route."
            "If a query would normally require web search, you should attempt to answer it using RAG (if applicable) or directly from your general knowledge."
            "\n\nChoose one of the following routes:"
            "\n- 'rag': For queries about specific entities, historical facts, product details, procedures, or any information that would typically be found in a curated document collection, AND for queries that would normally go to web search but web search is disabled."
            "\n- 'answer': For very simple, direct questions you can answer without any external lookup (e.g., 'What is your name?')."
        )

    system_prompt += (
        "\n- 'answer': For very simple, direct questions you can answer without any external lookup (e.g., 'What is your name?')."
        "\n- 'end': For pure greetings or small-talk where no factual answer is expected (e.g., 'Hi', 'How are you?'). If choosing 'end', you MUST provide a 'reply'."
        "\n\nExample routing decisions:"
        "\n- User: 'What are the treatment of diabetes?' -> Route: 'rag' (Factual knowledge, likely in KB)."
        "\n- User: 'What is the capital of France?' -> Route: 'rag' (Common knowledge, can be in KB or answered directly if LLM knows)."
        "\n- User: 'Who won the NBA finals last night?' -> Route: 'web' (Current event, requires live data)."
        "\n- User: 'How do I submit an expense report?' -> Route: 'rag' (Internal procedure)."
        "\n- User: 'Tell me about quantum computing.' -> Route: 'rag' (Foundational knowledge can be in KB. If KB is sparse, judge will route to web if enabled)."
        "\n- User: 'Hello there!' -> Route: 'end', reply='Hello! How can I assist you today?'"
    )

    messages = [
        ("system", system_prompt),
        ("user", query)
    ]

    result: RouteDecision = router_llm.invoke(messages)

    initial_route_decision = result.route
    route_override_reason = None

    #Override the router decision to go for web search
    if not web_search_enabled and result.route == "web":
        result.route = "rag"
        route_override_reason = "web search disabled by user."
        print(f"Router decision overriden: changed from web to rag")

    print(f"Route final decision: {result.route}, reply (if 'end'): {result.reply}")

    out = {
        "messages" : state['messages'],
        "route" : result.route,
        "web_search_enabled" : web_search_enabled
    }

    if route_override_reason:
        out ['initial_router_decision'] = initial_route_decision
        out ["route_override_reason"] = route_override_reason


    if result.route == "end":
        out["messages"] = state["messages"] + [AIMessage(content=result.reply)]

    
    print("Existing router node")
    return out





# Node 2 : Rag

def rag_node(state: AgentState) -> AgentState:
    print("Entering the rag node.")
    query = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),"")
    web_search_enabled = state.get("web_search_enabled", True)
    print(f"Route received web search info:{web_search_enabled}")
    print(f"RAG Query:{query}")


    chunks = rag_search_tool.invoke(query)

    # Logic to handel tje chunks
    if chunks.startswith("RAG_Error::"):
        print(f"RAG Error:{chunks}, checking web search enabled status")

        # if rag fails, and web search is enabled
        next_route = "web" if web_search_enabled else "answer"
        return {**state, "rag":"", "route": next_route}
    
    if chunks:
        print(f"Retrived RAG chunks : {chunks[:500]}...")
    else:
        print(f"No RAG Chunk Retrived")
    
    judge_messages = [
        ("system", (
            "You are a judge evaluating if the **retrieved information** is **sufficient and relevant** "
            "to fully and accurately answer the user's question. "
            "Consider if the retrieved text directly addresses the question's core and provides enough detail. "
            "If the information is incomplete, vague, outdated, or doesn't directly answer the question, it's NOT sufficient. "
            "If it provides a clear, direct, and comprehensive answer, it IS sufficient. "
            "If no relevant information was retrieved at all (e.g., 'No results found'), it is definitely NOT sufficient.\n\n"
            "Examples:\n"
            "- Question: 'What is the capital of France?' Retrieved: 'Paris is the capital of France.' -> sufficient: true\n"
            "- Question: 'What are the symptoms of diabetes?' Retrieved: 'Diabetes is a chronic condition.' -> sufficient: false (Doesn't answer symptoms)\n"
            "- Question: 'How to fix error X in software Y?' Retrieved: 'No relevant information found.' -> sufficient: false"
        )),
        ("user", f"Question: {query} \n\n Retrieved info: {chunks} \n\nIs this sufficient to answer the question?")
        ]
    
    RegJudge = judge_llm.invoke(judge_messages)
    verdict = RegJudge

    print(f"Rag Judge verdict: {verdict.sufficient}")
    print("Existing rag_node")

    # Decide the next route based on sufficiency and web_search info
    if verdict.sufficient:
        next_route = "answer"
    else:
        next_route = "web" if web_search_enabled else "answer"
        print(f"Rag not sufficient. Web search enabled :{web_search_enabled}. next route: {next_route}")

    return {
        **state,
        "rag" : chunks,
        "route": next_route,
        "web_search_enabled": web_search_enabled
    }    






#Node 3: Web Search

def web_node(state: AgentState )-> AgentState:
    print("\n--- Entering web_node ---")
    query = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
    web_search_enabled = state.get("web_search_enabled", True)
    if not web_search_enabled:
        print("web search node entered but search is disabled")
        return {**state, "web":"web search was disabled by user", "route" : "answer"}

    print (f"web search query:{query}")
    snippets = web_search_tool.invoke(query)


    if snippets.startswith("WEB_Error"):
        print(f"web error: {snippets}. predicting answer with limited info")
        return{**state, "web":"","route":"answer"}
    
    print(f"web snippets retrieved: {snippets[:200]}")
    print("Exiting web_node")
    return{**state, "web":snippets, "route":"answer"}


# Node 4: Finally Answer

def answer_node (state: AgentState) -> AgentState:
    print("\n--- Entering answer_node ---")
    user_query = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")


    ctx_parts = []
    if state.get("rag"):
        ctx_parts.append("knowledge Base Information: \n" + state["rag"])

    if state.get("web"):
        if state["web"] and not state["web"].startswith("web search was disabled"):
            ctx_parts.append("web search results:\n"+state["web"])

    context = "\n\n".join(ctx_parts)
    if not context.strip():
        context = "No external context is availabled for this query. Try to answer based on general knowledge."


    prompt = f"""
                Please answer the user's question using the provided context.
                If the context is empty or irrelavant, try to answer based on you general knowledge.
            

                Question: {user_query}    
                context: {context}

                Provide a helpful, accurate, and concise response based on the available information.
            """
    print (f"prompt sent to answer_llm: {prompt[:500]}...")
    ans = answer_llm.invoke([HumanMessage(content=prompt)]).content
    print(f"Final answer: {ans[:200]}...")
    print("Exiting answer node")
    

    return{
        **state,
        "messages" : state["messages"] + [AIMessage(content=ans)],

    }



# --- Routing helpers ---
def from_router(st: AgentState) -> Literal["rag", "web", "answer", "end"]:
    return st["route"]

def after_rag(st: AgentState) -> Literal["answer", "web"]:
    return st["route"]

def after_web(_) -> Literal["answer"]:
    return "answer"


# --- Build graph ---
def build_agent():
    """Builds and compiles the LangGraph agent."""
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("rag_lookup", rag_node)
    graph.add_node("web_search", web_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("router")
    
    graph.add_conditional_edges(
        "router",
        from_router,
        {
            "rag": "rag_lookup",
            "web": "web_search",
            "answer": "answer",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "rag_lookup",
        after_rag,
        {
            "answer": "answer",
            "web": "web_search"
        }
    )
    
    graph.add_edge("web_search", "answer")
    graph.add_edge("answer", END)

    # Use SQLite persistence for reliable checkpointing
    # IMPORTANT: Use a separate database file to avoid conflicts with backend/persistence.py
    # which creates its own checkpoints table with a different schema
    import sqlite3
    from pathlib import Path
    langgraph_db_path = Path(__file__).parent / "data" / "langgraph_checkpoints.db"
    langgraph_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(langgraph_db_path), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    
    # Setup the database schema (creates tables if they don't exist)
    checkpointer.setup()

    # Compile graph with SQLite storage
    agent = graph.compile(checkpointer=checkpointer)
    print(agent)
    return agent

rag_agent = build_agent()
