"""
agent/travel_agent.py
Core LangChain ReAct agent — stable, parse-error-proof version.
"""

import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from tools.flight_tool import flight_search_tool
from tools.hotel_tool import hotel_search_tool
from tools.places_tool import places_discovery_tool
from tools.weather_tool import weather_lookup_tool
from tools.budget_tool import budget_estimation_tool
from agent.prompts import TRAVEL_AGENT_SYSTEM_PROMPT, REPLANNING_PROMPT_TEMPLATE
from utils.formatter import format_itinerary

load_dotenv()

TOOLS = [
    flight_search_tool,
    hotel_search_tool,
    places_discovery_tool,
    weather_lookup_tool,
    budget_estimation_tool,
]

REACT_PROMPT = PromptTemplate.from_template(
    TRAVEL_AGENT_SYSTEM_PROMPT
    + """

You have access to the following tools:
{tools}

Use EXACTLY this format — no deviations:

Question: the input question
Thought: what you need to do
Action: one of [{tool_names}]
Action Input: key:value pairs without quotes
Observation: tool result
(repeat Thought/Action/Action Input/Observation as needed)
Thought: I have all information needed to write the itinerary
Final Answer: [complete itinerary]

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
)


def _extract_final_answer(text: str) -> str:
    """
    Extract Final Answer content from raw LLM output or error string.
    Handles cases where LangChain parse fails but the answer exists in the text.
    """
    # Pattern 1: standard Final Answer: ...
    match = re.search(r"Final Answer\s*:\s*(.+)", text, re.DOTALL | re.IGNORECASE)
    if match:
        answer = match.group(1).strip()
        # Clean up common trailing artifacts
        answer = re.sub(r"\s*>.*$", "", answer, flags=re.MULTILINE)
        if len(answer) > 200:
            return answer

    return ""


def _parse_error_handler(error) -> str:
    """
    Called by AgentExecutor on parse failure.
    Try to extract a Final Answer from the raw error text.
    If found, return it as the observation so the agent can use it.
    If not, give a one-line correction instruction (not a paragraph).
    """
    answer = _extract_final_answer(str(error))
    if answer:
        # Prefix it so the agent treats this as its conclusion
        return f"FINAL_ANSWER_EXTRACTED:{answer}"
    return "Thought: I now have all the information.\nFinal Answer:"


def build_agent(model: str = "openai/gpt-4o-mini", temperature: float = 0.3) -> AgentExecutor:
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "http://localhost"),
            "X-Title": os.getenv("OPENROUTER_APP_TITLE", "AI Travel Planner"),
        },
    )

    agent = create_react_agent(llm=llm, tools=TOOLS, prompt=REACT_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=8,
        max_execution_time=90,
        handle_parsing_errors=_parse_error_handler,
        return_intermediate_steps=True,
    )


def _recover_from_steps(steps: list) -> str:
    """Assemble output from tool observations when agent hits iteration limit."""
    if not steps:
        return ""
    parts = ["## Trip Plan\n"]
    for action, observation in steps:
        obs = str(observation).strip()
        if obs and "error" not in obs.lower()[:20]:
            parts.append(obs)
            parts.append("")
    return "\n".join(parts) if len(parts) > 1 else ""


def _clean_output(raw: str) -> str:
    """
    Post-process agent output:
    - Strip FINAL_ANSWER_EXTRACTED prefix if present
    - Strip parse error boilerplate lines
    - Extract Final Answer if buried in text
    """
    if not raw:
        return ""

    # Strip our own extraction prefix
    if raw.startswith("FINAL_ANSWER_EXTRACTED:"):
        return raw[len("FINAL_ANSWER_EXTRACTED:"):].strip()

    # Strip known error boilerplate + LLM closing remarks
    boilerplate = [
        "For troubleshooting, visit:",
        "OUTPUT_PARSING_FAILURE",
        "Format error. Write:",
        "Parsing error. Use format:",
        "Agent stopped due to",
        "iteration limit",
    ]
    closing_patterns = [
        r"^enjoy your .{0,60}!?\s*$",
        r"^have a .{0,60}!?\s*$",
        r"^feel free to .{0,80}!?\s*$",
        r"^if you (have|need) .{0,80}!?\s*$",
        r"^safe travels.*$",
        r"^bon voyage.*$",
        r"^happy travels.*$",
    ]
    lines = raw.split("\n")
    cleaned = []
    for l in lines:
        if any(b.lower() in l.lower() for b in boilerplate):
            continue
        if any(re.match(p, l.strip(), re.IGNORECASE) for p in closing_patterns):
            continue
        cleaned.append(l)
    result = "\n".join(cleaned).strip()

    # If still looks like a parse error blob, extract Final Answer from it
    if len(result) < 200 or "OUTPUT_PARSING" in result:
        extracted = _extract_final_answer(raw)
        if extracted:
            return extracted

    return result


def run_agent_for_ui(query: str, model: str = "openai/gpt-4o-mini"):
    """
    Run agent for Streamlit UI.
    Returns (output_text, steps, error_or_None).
    Always returns usable output — recovers from parse errors and iteration limit.
    """
    try:
        executor = build_agent(model=model)
        result = executor.invoke({"input": query})
        steps = result.get("intermediate_steps", [])
        raw = result.get("output", "")

        # Clean parse error artifacts from output
        cleaned = _clean_output(raw)

        # If still empty or too short, recover from intermediate steps
        if not cleaned or len(cleaned) < 200:
            cleaned = _recover_from_steps(steps)

        return (format_itinerary(cleaned) if cleaned.strip() else ""), steps, None

    except Exception as e:
        err_str = str(e)
        # Try to salvage a Final Answer even from exception text
        extracted = _extract_final_answer(err_str)
        if extracted:
            return format_itinerary(extracted), [], None
        return "", [], err_str


def run_replan_for_ui(original_itinerary: str, change_request: str, model: str = "openai/gpt-4o-mini"):
    """Re-plan based on user chat change request."""
    prompt = REPLANNING_PROMPT_TEMPLATE.format(
        previous_summary=original_itinerary[:2000],
        change_request=change_request,
    )
    return run_agent_for_ui(prompt, model=model)