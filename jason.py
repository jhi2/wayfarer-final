import json
import tools as t
from oompaloompa import OompaLoompaManager

# ---------------- CONFIG ----------------

#Use the default model

TOOLS = [
    t.tripadvisor_search,
    t.less_overwhelming_google_search,
    t.get_events,
    t.view_site,
    t.google_flights_search,
    t.fetch_airbnb_listings,
]

# ---------------- PROMPT ----------------

import json
import tools as t
from oompaloompa import OompaLoompaManager

# ---------------- CONFIG ----------------

#("google/gemma-3-12b-it")

TOOLS = [
    t.tripadvisor_search,
    t.less_overwhelming_google_search,
    t.get_events,
    t.view_site,
    t.google_flights_search,
    t.fetch_airbnb_listings,
]

# ---------------- PROMPT ----------------

def genpt1(payload: dict) -> str:
    return f"""
Dynamic Travel Orchestrator Prompt – Multi-task Workers

You are a Travel AI Orchestrator. You receive JSON input describing a travel plan, including destination, accommodation, transport, and activity preferences. You also may receive a list of available activities.

Rules:

Input:

A JSON object describing travel preferences (like TEST_FORM).

A list of possible activities (like TEST_ACTIVITIES).

Output format:
Always output exactly in this JSON format:

{{
  "worker1": ["task 1 in plain English", "task 2 in plain English", "..."],
  "worker2": ["task 1 in plain English", "task 2 in plain English", "..."]
}}

Include only workers that have tasks.

Each worker may receive multiple tasks.

Tasks must be clear, actionable, and independent.

Do not add any extra text outside the JSON.

Task generation rules:

Generate tasks that directly use the information in the JSON and activity list.

Tasks can include:

- Researching and comparing hotels or accommodations based on preferences.
- Checking flights or transport options.
- Suggesting relevant activities, tours, or events.
- Creating food or museum itineraries.

Each task must be independent; workers cannot communicate.

Avoid assigning overlapping tasks.

Worker limits:

Maximum 9 workers.

Assign as many workers as needed based on the tasks.

Example output:

{{
  "worker1": [
    "Research Hilton hotels in downtown Chicago that are 4-star, include breakfast, have a gym, and do not allow pets.",
    "Compare prices and availability for these hotels from January 4 to January 31, 2026."
  ],
  "worker2": [
    "Find direct economy flights to Chicago from your origin city, with carry-on only, no red-eye, departing January 4 and returning January 31, 2026, with a window seat.",
    "Check flight flexibility options and provide alternatives if available."
  ],
  "worker3": [
    "Create a walking tour itinerary in Chicago including top museums and food-focused spots.",
    "Identify food festivals or events happening during January in Chicago."
  ],
  "worker4": [
    "List outdoor parks and sports events in Chicago suitable for a mix of activities.",
    "Find any cultural events or exhibitions that match the travel dates."
  ]
}}

Strict rules:

Do not explain your reasoning.

Do not include anything outside the JSON.

Tasks must be actionable and self-contained.

USER DATA:
{json.dumps(payload, indent=2)}
"""


# ---------------- UTIL ----------------

def read_map():
    with open("./map.json") as f:
        return json.load(f)

def normalize_json_return(raw):
    """
    smolagents may return:
    - dict (already parsed)
    - JSON string
    """
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON returned:\n{raw}") from e

    raise RuntimeError(f"Unexpected return type: {type(raw)}")

# ---------------- ORCHESTRATOR ----------------

def go1(map_data, picks, form_answers):
    payload = {
        "form_results": form_answers,
        "question_map": map_data,
        "activities": picks,
    }

    oom = OompaLoompaManager()
    oom.setup_agent(
        id="orchestrator",
        prompt=genpt1(payload),
        tools=[t.less_overwhelming_google_search],
    )

    oom.start_all_agents()
    oom.join_all()

    raw = oom.get_agent_result("orchestrator")
    return normalize_json_return(raw)

# ---------------- WORKERS ----------------

def dotheactuaalthing(picks, qans, tools=TOOLS):
    task_map = go1(read_map(), picks, qans)

    oom = OompaLoompaManager()
    results = {}

    for worker_name, tasks in task_map.items():
        # Convert list of tasks to a single string for smolagents
        if isinstance(tasks, list):
            task_prompt = "\n".join(f"- {t}" for t in tasks)
        else:
            task_prompt = str(tasks)  # fallback in case it's a single string

        oom.setup_agent(
            id=worker_name,
            prompt=task_prompt+"In your answer, always say where you found a specific price or activity.",
            tools=tools,
        )

    oom.start_all_agents()
    oom.join_all()

    for worker_name in task_map:
        results[worker_name] = oom.get_agent_result(worker_name)

    return results

# ---------------- TEST DATA ----------------

TEST_FORM = {
    "destination": {
        "1": "Chicago",
        "2": "USA",
        "3": "Urban",
        "4": "Cold",
        "5": "Food-focused",
        "6": "Museums",
    },
    "accommodation_preferences": {
        "1": "Hotel",
        "2": "Hilton",
        "3": "4-star",
        "4": "Breakfast included",
        "5": "Downtown",
        "6": "Gym",
        "7": "No pets",
    },
    "transport_preferences": {
        "1": "Plane",
        "2": "Direct",
        "3": "Economy",
        "4": "2026-01-04",
        "5": "2026-01-31",
        "6": "Carry-on only",
        "7": "No red-eye",
        "8": "2",
        "9": "0",
        "10": "Flexible",
        "11": "Window seat",
    },
    "activities_preferences": {
        "1": "Mix",
        "2": "Food",
        "3": "Walking",
        "4": "Events",
        "5": "Museums",
        "6": "Yes",
        "7": "No nightlife",
    },
}

TEST_ACTIVITIES = [
    "activity_Walking-tours",
    "activity_Food-festivals",
    "activity_Museums",
    "activity_Sports-events",
    "activity_Outdoor-parks",
]

# ---------------- MAIN ----------------

if __name__ == "__main__":
    out = dotheactuaalthing(TEST_ACTIVITIES, TEST_FORM)
    print(json.dumps(out, indent=2))
