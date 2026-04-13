from typing import Annotated
from pathlib import Path
import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openrouter import ChatOpenRouter
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from tools import calculate_budget, search_flights, search_hotels

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


# 1. Readd the System Prompt
with open(BASE_DIR / "system_prompt.txt", "r", encoding="utf-8") as f:
	SYSTEM_PROMPT = f.read()


# 2. Declare State Agent
class AgentState(TypedDict):
	messages: Annotated[list, add_messages]


# 3. Initialize LLM and Tools
tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenRouter(
    # model="nvidia/nemotron-3-super-120b-a12b:free", # Specify any OpenRouter model string
	model=os.getenv("MODEL_NAME")
)

llm_with_tools = llm.bind_tools(tools_list)


# 4. Agent Node
def agent_node(state: AgentState):
	messages = state["messages"]
	if not isinstance(messages[0], SystemMessage):
		messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

	response = llm_with_tools.invoke(messages)

	# Logging
	if response.tool_calls:
		for tc in response.tool_calls:
			print(f"Call Tools: {tc['name']} ({tc['args']})")
	else:
		print("LLMs Answer Directly")

	return {"messages": [response]}


# 5. Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# Edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()


# 6. ChatLoop
if __name__ == "__main__":
	print("=" * 50)
	print("TravelBuddy - Smart Traveling Assistant")
	print(" Welcome back, LoveCrush")

	while True:
		user_input = input("\nYou: ").strip()
		if user_input.lower() in {"quit", "exit", "q"}:
			break
		if not user_input:
			continue
		print("Thinking...")
		result = graph.invoke({"messages": [("human", user_input)]})
		final = result["messages"][-1]
		print(f"\nTravelBuddy: {final.content}")
