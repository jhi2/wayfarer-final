import os
import json
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from smolagents import tool

# ------------------- CONSTANTS -------------------
# Limit tool output to prevent blowing up model context window (256k tokens)
MAX_OUTPUT_LENGTH = 15_000 

# ------------------- API KEYS (ENV ONLY) -------------------
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not SERPAPI_KEY:
    raise RuntimeError("SERPAPI_KEY env var not set")

if not RAPIDAPI_KEY:
    raise RuntimeError("RAPIDAPI_KEY env var not set")

# ------------------- HELPERS -------------------
def safe_json_dump(data):
    """Dumps JSON and truncates if it exceeds safe limits for the LLM context."""
    s = json.dumps(data)
    if len(s) > MAX_OUTPUT_LENGTH:
        return s[:MAX_OUTPUT_LENGTH] + "... [Output Truncated for Context Safety]"
    return s

# ------------------- LOGGER -------------------
class SimpleLogger:
    def log(self, msg: str, level=None):
        print(msg)


logger = SimpleLogger()


# ------------------- DEMO TOOL -------------------
@tool
def demotool(input: str) -> str:
    """
    Demo tool for testing.

    Args:
        input (str): Any input string to test the tool.

    Returns:
        str: Confirmation string indicating the tool ran.
    """
    logger.log("This is a demo tool")
    logger.log(f"Input received: {input}")
    return "This is a demo tool"


# ------------------- SEARCH TOOLS -------------------
@tool
def tripadvisor_search(query: str) -> str:
    """
    Perform a TripAdvisor search.

    Args:
        query (str): Search query string.

    Returns:
        str: JSON string of TripAdvisor search results.
    """
    logger.log(f"TripAdvisor search: {query}")
    params = {
        "engine": "tripadvisor",
        "q": query,
        "ssrc": "a",
        "api_key": SERPAPI_KEY,
    }
    return safe_json_dump(GoogleSearch(params).get_dict())


@tool
def google_search(query: str) -> str:
    """
    Perform a full Google search.

    Args:
        query (str): Search query string.

    Returns:
        str: JSON string of Google search results.
    """
    logger.log(f"Google search: {query}")
    params = {"engine": "google", "q": query, "api_key": SERPAPI_KEY}
    return safe_json_dump(GoogleSearch(params).get_dict())


@tool
def less_overwhelming_google_search(query: str) -> str:
    """
    Return top 3 organic Google search results only.

    Args:
        query (str): Search query string.

    Returns:
        str: JSON string of top 3 organic Google results.
    """
    logger.log(f"Lite Google search: {query}")
    params = {"engine": "google", "q": query, "api_key": SERPAPI_KEY}
    results = GoogleSearch(params).get_dict()
    organic = results.get("organic_results", [])[:3]

    simplified = [
        {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
        for r in organic
    ]
    return safe_json_dump(simplified)


@tool
def get_events(query: str) -> str:
    """
    Get events from Google Events.

    Args:
        query (str): Event search query string.

    Returns:
        str: JSON string of event results.
    """
    logger.log(f"Event search: {query}")
    params = {"engine": "google_events", "q": query, "api_key": SERPAPI_KEY}
    results = GoogleSearch(params).get_dict()
    return safe_json_dump(results.get("events_results", []))


# ------------------- WEB SCRAPER -------------------
@tool
def view_site(url: str) -> str:
    """
    Fetch readable text content from a webpage.

    Args:
        url (str): URL of the website.

    Returns:
        str: Cleaned textual content of the page.
    """
    logger.log(f"Fetching site: {url}")
    try:
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        text = soup.get_text(separator=" ")
        cleaned = " ".join(t.strip() for t in text.split() if t.strip())
        if len(cleaned) > MAX_OUTPUT_LENGTH:
            return cleaned[:MAX_OUTPUT_LENGTH] + "... [Webpage Content Truncated]"
        return cleaned
    except Exception as e:
        return f"Error fetching site: {str(e)}"


# ------------------- FLIGHTS -------------------
@tool
def google_flights_search(
    dep: str,
    arr: str,
    out_date: str,
    ret_date: str,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    currency: str = "USD",
) -> str:
    """
    Search Google Flights for a trip.

    Args:
        dep (str): Departure airport code.
        arr (str): Arrival airport code.
        out_date (str): Outbound date YYYY-MM-DD.
        ret_date (str): Return date YYYY-MM-DD.
        adults (int): Number of adult passengers.
        children (int): Number of children.
        infants_in_seat (int): Number of infants in seat.
        infants_on_lap (int): Number of infants on lap.
        currency (str): Currency code, default USD.

    Returns:
        str: JSON string of flight search results.
    """
    logger.log(f"Flight search {dep}->{arr}")
    params = {
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "api_key": SERPAPI_KEY,
        "departure_id": dep,
        "arrival_id": arr,
        "outbound_date": out_date,
        "return_date": ret_date,
        "currency": currency,
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
    }

    return safe_json_dump(GoogleSearch(params).get_dict())


# ------------------- AIRBNB -------------------
@tool
def fetch_airbnb_listings(
    location: str,
    checkin: str,
    checkout: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
    currency: str = "USD",
) -> str:
    """
    Fetch Airbnb listings for a location and date range.

    Args:
        location (str): City or place name.
        checkin (str): Check-in date YYYY-MM-DD.
        checkout (str): Check-out date YYYY-MM-DD.
        adults (int): Number of adults.
        children (int): Number of children.
        infants (int): Number of infants.
        pets (int): Number of pets.
        currency (str): Currency code, default USD.

    Returns:
        str: JSON string of Airbnb listings.
    """
    logger.log(f"Airbnb search: {location}")
    url = "https://airbnb19.p.rapidapi.com/api/v2/searchPropertyByLocation"
    params = {
        "query": location,
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "children": children,
        "infants": infants,
        "pets": pets,
        "priceMin": "1",
        "minBedrooms": "1",
        "minBeds": "1",
        "minBathrooms": "1",
        "currency": currency,
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "airbnb19.p.rapidapi.com",
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        return safe_json_dump(response.json())
    except Exception as e:
        return f"Error fetching Airbnb listings: {str(e)}"
