"""
agent/travel_agent.py
Core LangChain ReAct agent — fresh + stable Day 3 version.
"""

import os
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

Use this format STRICTLY:

Question: the input question you must answer
Thought: what you need to do next
Action: the tool to use, one of [{tool_names}]
Action Input: the input to the tool
Observation: the result of the tool
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have all the information to write the final itinerary
Final Answer: [complete formatted itinerary following the output template]

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""
)


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
        handle_parsing_errors="Parsing error. Use format: Thought: / Action: / Action Input: / Observation:. Never skip Action after Thought.",
        return_intermediate_steps=True,
    )


def _recover_from_steps(steps: list) -> str:
    """Assemble readable output from tool observations when agent hits iteration limit."""
    if not steps:
        return ""
    parts = ["## Trip Plan (auto-recovered)\n"]
    for action, observation in steps:
        obs = str(observation).strip()
        if obs and "error" not in obs.lower()[:20]:
            parts.append(obs)
            parts.append("")
    return "\n".join(parts) if len(parts) > 1 else ""


def run_agent_for_ui(query: str, model: str = "openai/gpt-4o-mini"):
    """
    Run agent for Streamlit UI.
    Returns (output_text, steps, error_or_None).
    Always returns usable output even on iteration limit.
    """
    try:
        executor = build_agent(model=model)
        result = executor.invoke({"input": query})
        steps = result.get("intermediate_steps", [])
        raw = result.get("output", "")

        if not raw.strip() or "Agent stopped" in raw or "iteration limit" in raw.lower():
            raw = _recover_from_steps(steps)

        return (format_itinerary(raw) if raw.strip() else ""), steps, None

    except Exception as e:
        return "", [], str(e)


def run_replan_for_ui(original_itinerary: str, change_request: str, model: str = "openai/gpt-4o-mini"):
    """
    Re-plan based on user's change request in chat.
    Returns (new_output_text, steps, error_or_None).
    """
    prompt = REPLANNING_PROMPT_TEMPLATE.format(
        previous_summary=original_itinerary[:2000],
        change_request=change_request,
    )
    return run_agent_for_ui(prompt, model=model)