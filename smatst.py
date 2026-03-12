from smolagents import CodeAgent
from smolagents.models import LiteLLMModel

model = LiteLLMModel(
    model_id="ollama/gpt-oss:120b-cloud",
    api_base="http://localhost:11434",
)

agent = CodeAgent(
    model=model,
    max_steps=100,
    tools=[]
)

result = agent.run(
    "Write a Python function that returns the first 10 prime numbers."
)

print("\n=== RESULT ===")
result()
