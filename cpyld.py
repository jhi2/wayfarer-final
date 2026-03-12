import json

def safe_parse_nested_json(value):
    """
    Recursively parse JSON strings in dicts/lists.
    Leaves normal strings alone.
    """
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("{") or value.startswith("["):
            try:
                return safe_parse_nested_json(json.loads(value))
            except json.JSONDecodeError:
                return value  # fallback: leave string as-is
        return value
    elif isinstance(value, dict):
        return {k: safe_parse_nested_json(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [safe_parse_nested_json(v) for v in value]
    else:
        return value


def normalize_activity_tag(tag: str) -> str:
    if not isinstance(tag, str):
        return str(tag)
    tag = tag.replace("activity_", "").replace("-", " ")
    return tag.title()


def clean_cookie_payload(cookies):
    """
    Safely clean a cookie payload, including nested JSON strings.
    Returns AI-ready JSON dict.
    """
    # Ensure dict
    if isinstance(cookies, str):
        try:
            cookies = json.loads(cookies)
        except json.JSONDecodeError:
            # fallback: treat as empty
            cookies = {}

    cookies = safe_parse_nested_json(cookies)

    picks_done = cookies.get("picks_done", [])
    questionnaire_answers = cookies.get("questionnaire_answers", {})

    clean_activities = [normalize_activity_tag(a) for a in picks_done]

    return {
        "destination": questionnaire_answers.get("destination", {}),
        "activity_classes": clean_activities,
        "accommodation_preferences": questionnaire_answers.get("accommodation_preferences", {}),
        "transport_preferences": questionnaire_answers.get("transport_preferences", {}),
        "activities_preferences": questionnaire_answers.get("activities_preferences", {}),
    }
