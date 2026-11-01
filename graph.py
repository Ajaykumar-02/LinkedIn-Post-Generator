import os
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode


# ─── State ──────────────────────────────────────────────────────────────────────
class State(TypedDict):
    topic: str
    messages: Annotated[list, add_messages]
    draft: str
    review_feedback: str
    is_approved: bool
    attempt: int


# ─── Prompts (same as the original script) ──────────────────────────────────────
WRITER_SYSTEM_PROMPT = (
    "You are an expert LinkedIn content writer. Your job is to write "
    "engaging, professional LinkedIn posts about the given topic. "
    "If the topic requires up-to-date information, statistics, or "
    "current trends, use the web search tool to gather fresh context "
    "before writing. If you have already received feedback on a "
    "previous draft, carefully address every point in the new draft. "
    "Rules for good LinkedIn posts: strong hook in the first line, "
    "1 clear takeaway, easy to skim (short paragraphs), around "
    "150–200 words, ends with a question or call-to-action to invite "
    "engagement. Do not use hashtags."
)

REVIEWER_SYSTEM_PROMPT = (
    "You are a strict LinkedIn content reviewer. You judge whether a "
    "post is publish-ready. Evaluate against these criteria:\n"
    "1. Strong hook in the first line\n"
    "2. One clear, valuable takeaway\n"
    "3. Easy to skim — uses short paragraphs\n"
    "4. Roughly 150-200 words\n"
    "5. Ends with an engaging question or CTA\n"
    "6. Professional but human tone (not corporate-robotic)\n"
    "7. No hashtags\n\n"
    "Respond in exactly this format:\n"
    "VERDICT: APPROVED or REJECTED\n"
    "FEEDBACK: <one short paragraph explaining why>\n\n"
    "Be strict but fair. Approve only if the post genuinely meets all "
    "criteria. Reject if even one criterion is clearly missing."
)


# ─── Tools and LLMs ─────────────────────────────────────────────────────────────
def get_resources() -> dict:
    """Create the Tavily tool and the two Groq LLMs (needs GROQ_API_KEY and TAVILY_API_KEY)."""
    from langchain_groq import ChatGroq
    from langchain_tavily import TavilySearch

    search_tool = TavilySearch(max_results=3)
    tools = [search_tool]

    writer_llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="openai/gpt-oss-20b",
        temperature=0.2,
    )

    reviewer_llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="openai/gpt-oss-120b",
        temperature=0.2,
    )

    return {
        "tools": tools,
        "writer_llm": writer_llm,
        "writer_llm_with_tools": writer_llm.bind_tools(tools),
        "reviewer_llm": reviewer_llm,
    }


# ─── Graph ──────────────────────────────────────────────────────────────────────
def build_graph(resources: dict, max_attempts: int = 3):
    tools = resources["tools"]
    writer_llm = resources["writer_llm"]
    writer_llm_with_tools = resources["writer_llm_with_tools"]
    reviewer_llm = resources["reviewer_llm"]

    def writer_node(state: State) -> dict:
        """Writes (or rewrites) the LinkedIn post. Can call Tavily to search first."""
        attempt = state.get("attempt", 0) + 1
        topic = state["topic"]
        previous_feedback = state["review_feedback"]

        if attempt == 1:
            user_message = (
                f"Write a LinkedIn post on this topic {topic}"
                f"if you need current info search the web first "
            )
        else:
            user_message = (
                f"your previous draft on '{topic}' was rejected"
                f"Here is the reviewer's feedback \n\n {previous_feedback}\n\n"
                f"Write a new, improved draft that fixes every issue mentiond"
                f"do not repeat the same mistake"
            )
        messages = [("system", WRITER_SYSTEM_PROMPT), ("human", user_message)]
        response = writer_llm_with_tools.invoke(messages)

        return {
            "messages": [("human", user_message), response],
            "attempt": attempt,
        }

    tool_node = ToolNode(tools)

    def write_after_search_node(state: State) -> dict:
        """After the web search, the writer reads the results and writes the actual post.
        (In the original graph the search results went straight to the reviewer, so the
        writer never saw them and the draft stayed empty.)"""
        msgs = state["messages"]
        # use only the messages of the current attempt (from the last human message)
        start = max(i for i, m in enumerate(msgs) if getattr(m, "type", "") == "human")
        response = writer_llm.invoke([("system", WRITER_SYSTEM_PROMPT)] + list(msgs[start:]))
        return {"messages": [response]}

    def extract_draft_node(state: State) -> dict:
        """Pulls the final text out of the last message as the draft."""
        last_message = state["messages"][-1]
        return {"draft": last_message.content}

    def reviewer_node(state: State) -> dict:
        """Reviews the draft and decides: approve or reject with feedback."""
        draft = state["draft"]

        prompt = (
            f"review this LinkedIn post draft : \n"
            f"{draft}\n"
            f"give your reviews"
        )
        response = reviewer_llm.invoke(
            [("system", REVIEWER_SYSTEM_PROMPT), ("human", prompt)]
        )
        review_text = response.content.strip()

        is_approved = "APPROVED" in review_text.upper().split("FEEDBACK")[0]

        if "FEEDBACK:" in review_text:
            feedback = review_text.split("FEEDBACK:", 1)[1].strip()
        else:
            feedback = review_text

        return {
            "review_feedback": feedback,
            "is_approved": is_approved,
        }

    def should_use_tool(state: State):
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return "extract_draft"

    def should_stop_looping(state: State):
        if state["is_approved"]:
            return END
        if state["attempt"] >= max_attempts:
            return END
        return "writer"

    graph = StateGraph(State)

    graph.add_node("writer", writer_node)
    graph.add_node("tools", tool_node)
    graph.add_node("write_after_search", write_after_search_node)
    graph.add_node("extract_draft", extract_draft_node)
    graph.add_node("reviewer", reviewer_node)

    graph.add_edge(START, "writer")
    graph.add_conditional_edges("writer", should_use_tool)

    graph.add_edge("tools", "write_after_search")
    graph.add_edge("write_after_search", "extract_draft")
    graph.add_edge("extract_draft", "reviewer")

    graph.add_conditional_edges("reviewer", should_stop_looping)

    return graph.compile()


# ─── Running the graph for the UI ───────────────────────────────────────────────
def parse_sources(content) -> list:
    """Reads the Tavily tool output and returns [{"title", "url"}, ...]."""
    import json
    try:
        obj = json.loads(content) if isinstance(content, str) else content
        results = obj.get("results", []) if isinstance(obj, dict) else []
        return [{"title": r.get("title", ""), "url": r.get("url", "")} for r in results]
    except Exception:
        return []


def run_generation(compiled_app, topic: str):
    """Runs the graph and yields small events, so the UI can show live progress.

    Events: writer, sources, draft, review
    """
    initial_state = {
        "topic": topic,
        "messages": [],
        "draft": "",
        "review_feedback": "",
        "is_approved": False,
        "attempt": 0,
    }

    # 5 nodes per attempt, so the default recursion limit of 25 would be too small
    config = {"recursion_limit": 80}

    for update in compiled_app.stream(initial_state, config=config, stream_mode="updates"):
        for node, data in update.items():
            if node == "writer":
                ai_message = data["messages"][-1]
                calls = getattr(ai_message, "tool_calls", None) or []
                query = calls[0].get("args", {}).get("query") if calls else None
                yield {"event": "writer", "attempt": data["attempt"], "query": query}

            elif node == "tools":
                sources = []
                for m in data["messages"]:
                    sources += parse_sources(m.content)
                yield {"event": "sources", "sources": sources}

            elif node == "extract_draft":
                yield {"event": "draft", "draft": data["draft"]}

            elif node == "reviewer":
                yield {
                    "event": "review",
                    "approved": data["is_approved"],
                    "feedback": data["review_feedback"],
                }
