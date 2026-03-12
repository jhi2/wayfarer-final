# !pip install 'smolagents[litellm]'
"WARNING:THIS IS A LEGACY CODE."

from smolagents import CodeAgent, LiteLLMModel, tool, ModalExecutor
import serpapi
from serpapi import GoogleSearch
import requests
from bs4 import BeautifulSoup
import json
import logging
import os


def genpt(input):
    pt = f"""
You are an autonomous reasoning agent.

GOAL
- Your only objective is to produce a final answer to the user’s question.
- Always use one of the available tools to fetch the most current information,
even if you think you already know the answer.

OPERATING RULES
1. At every step, ask internally:
   “Does this action directly help answer the user’s question?”
   If not, do NOT take that action.

2. You may use tools or browsing ONLY if necessary.
   If you already have enough information to give a reasonable answer,
   STOP immediately and answer.

3. You may attempt a tool AT MOST ONCE.
   If it fails, mark it unavailable and continue without tools.

4. Do not explore background information, unrelated topics,
   or side facts that do not directly reduce uncertainty.

5. You MUST always produce a final answer,
   even if assumptions are required (state them briefly).

TOOL USAGE POLICY
- You may use as many tools as needed to answer the user’s question.
- Always choose the least expensive tool first, but you may chain tools if required.
- If a tool fails once, mark it unavailable and continue with others.
- Never call a tool that does not exist in the available list.

AVAILABLE TOOLS (ONLY THESE EXIST)
- less_overwhelming_google_search
- get_events
- tripadvisor_search
- view_site
- final_answer

You MUST NOT call any other tools.
If a tool is not listed above, it does not exist.

STOPPING CONDITION
- As soon as you can provide a plausible, helpful answer,
  call final_answer(...) and stop.
ANSWER REQUIREMENTS
- The final answer MUST name at least one specific,
  real-world destination.
- Generic article titles, lists, or search result names
  are NOT valid answers.
-Give a exremely detailed final answer with all relevant information about the destination(s) you provide. zTHe answer msut be at least 300 characters long.
OUTPUT FORMAT
- You MUST call final_answer(...)
- Provide ONLY the final answer text.
- No reasoning, no logs, no summaries.
-Make sure the answer gives all details.
HOW FINALANSWER WORKS
- Call final_answer("the answer you come up with")
USER QUESTION:
{input}
"""
    return pt


# api_key = "4066f05dc8244ddad3ec475386f2374399264a982dd43332c72dbf51fbf901d0"
api_key = os.getenv("api_key")


class SimpleLogger:
    def log(self, msg: str, level=None):
        print(msg)  # prints to console, could add timestamps if you want


logger = SimpleLogger()


# @tool
def demotool(input: str) -> str:
    """Demo tool"""
    print("This is a demo tool")
    print(f"Input received: {input}")
    return "This is a demo tool"


@tool
def tripadvisor_search(query: str) -> str:
    """Perform a TripAdvisor search for the given query.
    Args:
        query (str): The search query.
    Returns:
        str: JSON string of the search results.
    """
    print(f"Performing TripAdvisor search for query: {query}")
    params = {"engine": "tripadvisor", "q": query, "ssrc": "a", "api_key": api_key}
    search = GoogleSearch(params)
    results = search.get_dict()
    return json.dumps(results)


@tool
def google_search(query: str) -> str:
    """Perform a Google search for the given query.
    Args:
        query (str): The search query.
    Returns:
        str: JSON string of the search results.
    """
    print(f"Performing Google search for query: {query}")
    params = {"engine": "google", "q": query, "api_key": api_key}
    search = GoogleSearch(params)
    results = search.get_dict()
    return json.dumps(results)


@tool
def less_overwhelming_google_search(query: str) -> str:
    """Perform a simplified Google search for the given query. THis function wil lonly give the top three organic results. Use google_search for full results. THis is the perferred search function to use. Only use google_search if you need more detailed resultsm, ath the risk of extremely increced processing time.
    Args:
        query (str): The search query.
    Returns:
        str: JSON string of the search results.
    """
    print(f"Performing Google search for query: {query}")
    params = {"engine": "google", "q": query, "api_key": api_key}
    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])
    simplified_results = []
    for result in organic_results:
        simplified_results.append(
            {
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
            }
        )
    return json.dumps(simplified_results)


@tool
def get_events(query: str) -> str:
    """Get events for a given query.
    Args:
        query (str): The search query.
    Returns:
        str: JSON string of the events.
    """
    print(f"Getting events for query: {query}")
    params = {"engine": "google_events", "q": query, "api_key": api_key}
    search = GoogleSearch(params)
    results = search.get_dict()
    return json.dumps(results["events_results"])


@tool
def view_site(url: str) -> str:
    """Fetch and return the text content of the given URL. DONT OVERUSE THIS TOOL, IT WILL SLOW DOWN THE AGENT.
    Args:
        url (str): The URL of the website to fetch.
    Returns:
        str: The text content of the website.
    """
    print(f"Fetching content from URL: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return " ".join(chunk for chunk in chunks if chunk)


def google_flights_search(
    dep,
    arr,
    out_date,
    ret_date,
    adults=1,
    children=0,
    infants_in_seat=0,
    infants_on_lap=0,
    currency="USD",
) -> str:
    """Search Google Flights and return results as JSON string.
    Args:
        dep (str): Departure airport code.
        arr (str): Arrival airport code.
        out_date (str): Outbound date in YYYY-MM-DD format.
        ret_date (str): Return date in YYYY-MM-DD format.
        adults (int): Number of adult passengers.
        children (int): Number of child passengers.
        infants_in_seat (int): Number of infants in seat.
        infants_on_lap (int): Number of infants on lap.
        currency (str): Currency code for prices.
    Returns:
        str: JSON string of the flight search results.
    """
    params = {
        k: str(v)
        for k, v in {
            "api_key": api_key,
            "engine": "google_flights",
            "hl": "en",
            "gl": "us",
            "departure_id": dep,
            "arrival_id": arr,
            "outbound_date": out_date,
            "return_date": ret_date,
            "currency": currency,
            "adults": adults,
            "children": children,
            "infants_in_seat": infants_in_seat,
            "infants_on_lap": infants_on_lap,
        }.items()
    }
    return json.dumps(GoogleSearch(params).get_dict())


# --- Setup model ---
model = LiteLLMModel(
    model_id="ollama_chat/llama3.2",
    api_base="http://localhost:11434",
    api_key="YOUR_API_KEY",
    num_ctx=10000,
)

agent = CodeAgent(
    tools=[tripadvisor_search, view_site, less_overwhelming_google_search, get_events],
    model=model,
    add_base_tools=True,
    max_steps=100,
    # executor=ModalExecutor(additional_imports=["smolagents", "flask", "google-search-results", "beautifulsoup4", "requests"], logger=logger),
)

# --- Run agent with streaming ---
prompt = genpt(
    "Plan a trip to Paris, France in the spring. Suggest must-see attractions, local events, and dining options."
)

result = agent.run(prompt)
print("Result:", result)
