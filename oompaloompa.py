from smolagents import CodeAgent, LiteLLMModel
import threading
from queue import Queue
import os
from dotenv import load_dotenv

load_dotenv()

# Fixed model for Codestral
MODEL_ID = "mistral/codestral-latest"

print("OOM Ready.")

class OompaLoompaManager:
    def __init__(self):
        api_key = os.getenv("CODESTRAL_API_KEY")
        if not api_key:
            print("Warning: CODESTRAL_API_KEY environment variable not set.")
            api_key = "YOUR_API_KEY"

        # Using the dedicated Codestral endpoint
        self.model = LiteLLMModel(
            model_id=MODEL_ID,
            api_base="https://codestral.mistral.ai/v1",
            api_key=api_key,
        )
        self.threads = []
        self.queues = {}

    def genpt(self, question: str) -> str:
        return f"""
You are an autonomous reasoning agent.

GOAL
- Provide the final answer to the user's question.

RULES
1. Only produce a final answer.
2. No reasoning, no logs, no summaries.
3. Please give a very long and detailed answer.
3. Always use the tools at your disposal to get the answer.
4. Use final_answer(output) to deliver your output.
5. Always say where you find a answer. Include that in your final answer.

USER QUESTION:
{question}
"""

    def setup_agent(self, id, prompt, tools=[]):
        agent = CodeAgent(
            tools=tools,
            model=self.model,
            add_base_tools=True,
            max_steps=100,
        )
        q = Queue()
        self.queues[id] = q
        td = threading.Thread(target=self.run_agent, args=(agent, q, prompt))
        self.threads.append(td)

    def run_agent(self, agent, queue, prompt):
        queue.put(agent.run(prompt))

    def start_all_agents(self):
        for td in self.threads:
            td.start()

    def get_agent_result(self, id):
        q = self.queues.get(id)
        if q:
            return q.get()
        return None

    def join_all(self):
        for td in self.threads:
            td.join()


# --- Example usage ---
if __name__ == "__main__":
    manager = OompaLoompaManager()
    manager.setup_agent("agent1", manager.genpt("What is the capital of France?"))
    manager.setup_agent("agent2", manager.genpt("What is the largest mammal on Earth?"))
    manager.setup_agent("agent3", manager.genpt("Who wrote 'Pride and Prejudice'?"))
    manager.setup_agent(
        "agent4", manager.genpt("What is the speed of light in vacuum?")
    )
    manager.setup_agent(
        "agent5", manager.genpt("What is the tallest mountain in the world?")
    )
    manager.start_all_agents()
    manager.join_all()
    result1 = manager.get_agent_result("agent1")
    result2 = manager.get_agent_result("agent2")
    result3 = manager.get_agent_result("agent3")
    result4 = manager.get_agent_result("agent4")
    result5 = manager.get_agent_result("agent5")

    lst = [result1, result2, result3, result4, result5]
    for i, res in enumerate(lst):
        print(f"Result from agent{i+1}: {res}")
