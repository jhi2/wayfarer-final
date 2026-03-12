from tools import *
from oompaloompa import OompaLoompaManager
import tools
import ast
import litellm
import time


def normalize_result(result):
    if isinstance(result, str):
        try:
            parsed = ast.literal_eval(result)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        raise ValueError(f"Agent returned invalid list string: {result}")
    if isinstance(result, list):
        return result
    raise TypeError(f"Unexpected agent result type: {type(result)}")


def genpt(input: str) -> str:
    return f"""You are an autonomous reasoning agent.
GOAL
- Provide activities in a particular area based on user preferences.
RULES
1. Only produce a final answer.
2. No reasoning, no logs, no summaries.
3. Always use the tools at your disposal to get the answer.
4. Only base the answer on tools.
5. (Deal-Braker) - ONLY PROVIDE THE LIST AS THE ANSWER, NO OTHER TEXT.
6. You MUST USE A TOOL! AND THE FINAL ANSWER MUST BE BASED ON THE TOOL OUTPUT.
7. THE TOOL OUTPT MUST VERY STONGLY INFLUENCE THE FINAL OUTPUT.
Feel free to use multiple tool calls.
OUTPUT SECHMA
 - Use final_answer(...) to output your output.
 - Only provide ['activity_name','activity_name',etc. you can list up to 9 activities.]
 - Only provide GEERAL CLASSES OF ACTIVITIES, DO NOT provide specific names of activities or locations.
USER INPUT:
{input}
"""


def find_act(location):
    try:

        ooml = OompaLoompaManager()
        ooml.setup_agent(
            id="activity_agent",
            prompt=genpt("location:" + location),
            tools=[
                tools.less_overwhelming_google_search,
                tools.tripadvisor_search,
                tools.view_site,
            ],
        )
        ooml.start_all_agents()
        ooml.join_all()
        result = ooml.get_agent_result("activity_agent")
        print("Agent Result:", result)
        return normalize_result(result)
    except litellm.APIConnectionError:
        try:
            time.sleep(10)

            ooml = OompaLoompaManager()
            ooml.setup_agent(
                id="activity_agent",
                prompt=genpt("location:" + location),
                tools=[
                    tools.less_overwhelming_google_search,
                    tools.tripadvisor_search,
                    tools.view_site,
                ],
            )
            ooml.start_all_agents()
            ooml.join_all()
            result = ooml.get_agent_result("activity_agent")
            print("Agent Result:", result)
            return normalize_result(result)
        except litellm.APIConnectionError:

            return [['big-giant-error-contact-your-admin']]


def run_with_qeueue(location, queue):
    activities = find_act(location)
    queue.put(activities)


if __name__ == "__main__":
    print(find_act("Somwhere near the beach in Florida"))
