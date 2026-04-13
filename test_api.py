import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
# Set your API key
# Initialize the model
llm = ChatOpenRouter(
    model="qwen/qwen3.6-plus:free", # Specify any OpenRouter model string
)

# Invoke the model
response = llm.invoke("Who are you")
print(response.content)




