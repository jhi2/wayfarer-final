import json

def slugify(s: str) -> str:
    return (
        s.strip()
         .lower()
         .replace("?", "")
         .replace(",", "")
         .replace(".", "")
         .replace("/", "")
         .replace("(", "")
         .replace(")", "")
         .replace(" ", "-")
    )

def build_id(section, question_text):

    return f"{slugify(section)}-{slugify(question_text)}"

def stuffff():
    result = {}

    with open("./questionaire.json") as f:
        q = json.load(f)

    qn = q["questionnaires"]

    for section in qn:   
        result[section] = {}
        for qkey in qn[section]:             
            question_text = qn[section][qkey][0]
            result[section][qkey] = {
                "id": build_id(section, question_text)
            }

    return result

with open("./map.json", "w") as f:
    json.dump(stuffff(), f, indent=2)
