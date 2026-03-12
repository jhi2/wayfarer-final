import flask
from flask import *
import json
from dynamically_generate_html import dynamically_generate_html
from aist1 import find_act
import threading as th
from queue import Queue
import os
from uuid import uuid4
from datetime import timedelta
from jason import dotheactuaalthing
from okdk import dothething
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)

# ---------------- CONSTANTS ----------------
UUID_COOKIE = "uuid_it"
UUID_MAX_AGE = 60 * 60 * 24 * 365 * 900  # 900 years

# ---------------- GLOBAL STATE ----------------
# Task Queue 1 (Activity Discovery)
task_queue_1 = Queue()
results_1 = {}  # {user_uuid: result}
current_task_1 = None # user_uuid

# Task Queue 2 (Full Itinerary)
task_queue_2 = Queue()
results_2 = {}  # {user_uuid: result}
current_task_2 = None # user_uuid

# ---------------- HELPERS ----------------
def get_user_uuid():
    uid = request.cookies.get(UUID_COOKIE)
    if not uid:
        abort(403, "User not initialized. Visit /go/<qid> first.")
    return uid

def is_mobile():
    user_agent = request.headers.get("User-Agent", "")
    mobile_agents = ["Mobile", "Android", "iPhone", "iPad", "Windows Phone"]
    return any(agent in user_agent for agent in mobile_agents)

def get_questions(questionnaire_id, step):
    data = json.load(open("questionaire.json"))
    qdata = data["questionnaires"][questionnaire_id][str(step)]
    pop = False
    multichoice = None
    if len(qdata) >= 3:
        if qdata[2] == "pop":
            pop = True
        elif isinstance(qdata[2], list):
            multichoice = qdata[2]
    return qdata, pop, multichoice

# ---------------- WORKERS ----------------
def worker_1_loop():
    global current_task_1
    while True:
        user_uuid, dest = task_queue_1.get()
        current_task_1 = user_uuid
        try:
            print(f"[Worker 1] Processing task for {user_uuid}")
            activities = find_act(dest)
            results_1[user_uuid] = activities
        except Exception as e:
            print(f"[Worker 1] Error: {e}")
            results_1[user_uuid] = [["Error processing activities"]]
        finally:
            current_task_1 = None
            task_queue_1.task_done()

def worker_2_loop():
    global current_task_2
    while True:
        user_uuid, picks, fom = task_queue_2.get()
        current_task_2 = user_uuid
        try:
            print(f"[Worker 2] Processing task for {user_uuid}")
            hmm = dotheactuaalthing(picks, fom)
            dtt = dothething(guide_text=hmm, ipt=fom)
            results_2[user_uuid] = dtt
        except Exception as e:
            print(f"[Worker 2] Error: {e}")
            results_2[user_uuid] = "<h1>Error generating itinerary</h1>"
        finally:
            current_task_2 = None
            task_queue_2.task_done()

# Start background workers
th.Thread(target=worker_1_loop, daemon=True).start()
th.Thread(target=worker_2_loop, daemon=True).start()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    if not is_mobile():
        return render_template("home.html")
    return "Please access this application from a desktop device."

@app.route("/go/<qid>")
def fredir(qid):
    resp = redirect(url_for("mainapp", stage=1, questionnaire_id=qid))
    if not request.cookies.get(UUID_COOKIE):
        resp.set_cookie(UUID_COOKIE, str(uuid4()), max_age=UUID_MAX_AGE, httponly=True, samesite="Lax", path="/")
    return resp

# ---------------- QUESTIONNAIRE ----------------
@app.route("/app/questionaire/<int:stage>/<questionnaire_id>", methods=["GET", "POST"])
def mainapp(stage, questionnaire_id):
    data = json.load(open("questionaire.json"))
    questionnaire = data["questionnaires"][questionnaire_id]
    last_step = max(int(k) for k in questionnaire.keys())
    if stage > last_step:
        return redirect(url_for("mainappff", stage=stage, questionnaire_id=questionnaire_id))
    if request.method == "POST":
        value = request.form.get(f"q{stage}", "")
        raw_cookie = request.cookies.get("questionnaire_answers", "{}")
        answers = json.loads(raw_cookie) if raw_cookie else {}
        answers.setdefault(questionnaire_id, {})
        answers[questionnaire_id][str(stage)] = value
        resp = redirect(url_for("mainapp", stage=stage + 1, questionnaire_id=questionnaire_id))
        resp.set_cookie("questionnaire_answers", json.dumps(answers), max_age=UUID_MAX_AGE, httponly=True, samesite="Lax", path="/")
        return resp
    qdata, pop, multichoice = get_questions(questionnaire_id, stage)
    return render_template("questionaire.html", stage=stage, question=dynamically_generate_html(qdata, stage), pop=pop, multichoice=multichoice, questionnaire_id=questionnaire_id, max_stages=last_step)

@app.route("/app/questionaire/stage/<int:stage>/<questionnaire_id>", methods=["GET", "POST"])
def mainappff(stage, questionnaire_id):
    data = json.load(open("questionaire.json"))
    questionnaire = data["questionnaires"][questionnaire_id]
    last_step = max(int(k) for k in questionnaire.keys())
    if stage > last_step:
        return redirect(url_for("qcompleted", questionnaire_id=questionnaire_id))
    if request.method == "POST":
        value = request.form.get(f"q{stage}", "")
        raw_cookie = request.cookies.get("questionnaire_answers", "{}")
        answers = json.loads(raw_cookie) if raw_cookie else {}
        answers.setdefault(questionnaire_id, {})
        answers[questionnaire_id][str(stage)] = value
        resp = redirect(url_for("mainappff", stage=stage + 1, questionnaire_id=questionnaire_id))
        resp.set_cookie("questionnaire_answers", json.dumps(answers), max_age=UUID_MAX_AGE, httponly=True, samesite="Lax", path="/")
        return resp
    qdata, pop, multichoice = get_questions(questionnaire_id, stage)
    return render_template("questionaire.html", stage=stage, question=dynamically_generate_html(qdata, stage), pop=pop, multichoice=multichoice, questionnaire_id=questionnaire_id, max_stages=last_step)

# ---------------- PICKS ----------------
@app.route("/go/qcompleted/<questionnaire_id>")
def qcompleted(questionnaire_id):
    if questionnaire_id == "destination":
        return redirect(url_for("actpicks1"))
    if questionnaire_id == "accommodation_preferences":
        return redirect(url_for("mainapp", questionnaire_id="transport_preferences", stage=1))
    if questionnaire_id == "transport_preferences":
        return redirect(url_for("mainapp", questionnaire_id="activities_preferences", stage=1))
    if questionnaire_id == "activities_preferences":
        return redirect(url_for("fist", picks=request.cookies.get("picks_done"), fom=request.cookies.get("questionnaire_answers")))

@app.route("/picks/tbcomplete/", methods=["GET","POST"])
def handle_activity_selection():
    if request.method == "POST":
        picks = [thing.replace(" ", "-") for thing in request.form.keys()]
        resp = make_response(redirect(url_for("mainapp", questionnaire_id="accommodation_preferences", stage=1)))
        resp.set_cookie("picks_done", json.dumps(picks), max_age=UUID_MAX_AGE, httponly=True, samesite="Lax", path="/")
        return resp
    return redirect(url_for("clear_uuid_cookie"))

@app.route("/picks/ast2/")
def ast2p():
    return render_template("am2.html")

@app.route("/picks/fullcomplete/")
def pickssuc2():
    raw_htm = request.args.get("jsonstr", "")
    clean_htm = raw_htm.replace(r"\n", "").replace(r'"]', "").replace(r'["', "")
    full_template = '  <style>body{font-family:sans-serif; color:#343231; }</style> <br><a href="{{ url_for(\'clear_uuid_cookie\') }}">Go Back Home</a>' + clean_htm + ' <br><a href="{{ url_for(\'clear_uuid_cookie\') }}">Go Back Home</a>'
    
    return render_template_string(full_template)

@app.route("/picks/s1n2atstwat/")
def picksuc2():
    jsst = request.args.get("jsonstr")
    ldd = json.loads(jsst)
    ld1 = ldd[0]
    return render_template("sp1.html",activities=ld1)

# ---------------- AI 2 SUBMISSION ----------------
@app.route("/aimain/<picks>/<fom>")
def fist(picks, fom):
    user_uuid = get_user_uuid()
    # Check if user already has a pending or completed result to avoid double submission
    if user_uuid in results_2:
        return redirect(url_for("ast2p"))
    
    # Check if already in queue
    already_in_queue = any(task[0] == user_uuid for task in list(task_queue_2.queue))
    if not already_in_queue and current_task_2 != user_uuid:
        try:
            picks_list = json.loads(picks)
            fom_dict = json.loads(fom)
            task_queue_2.put((user_uuid, picks_list, fom_dict))
        except Exception as e:
            return f"Error parsing input: {e}", 400

    return redirect(url_for("ast2p"))

# ---------------- AI 1 SUBMISSION ----------------
@app.route("/picks/1/")
def actpicks1():
    user_uuid = get_user_uuid()
    raw_cookie = request.cookies.get("questionnaire_answers", "{}")
    answers = json.loads(raw_cookie)
    dest = answers["destination"]["1"]
    
    # Add to queue if not already there or running or finished
    if user_uuid not in results_1:
        already_in_queue = any(task[0] == user_uuid for task in list(task_queue_1.queue))
        if not already_in_queue and current_task_1 != user_uuid:
            task_queue_1.put((user_uuid, dest))
            
    return render_template("actpick1wr.html")

# ---------------- POLLING ----------------
@app.route("/isthethreaddone/1/")
def isthethreaddone():
    user_uuid = get_user_uuid()
    if user_uuid in results_1:
        return jsonify(doneyet="Yes", status="Complete!")
    
    if current_task_1 == user_uuid:
        return jsonify(doneyet="Nope", status="AI is working on your request now...")

    # Calculate position
    queue_list = [task[0] for task in list(task_queue_1.queue)]
    if user_uuid in queue_list:
        # Position = (1 if someone else is currently processing) + (index in queue) + 1
        others_processing = 1 if (current_task_1 and current_task_1 != user_uuid) else 0
        pos = others_processing + queue_list.index(user_uuid) + 1
        return jsonify(doneyet="Nope", status=f"You are at position {pos} in the queue")
    
    return jsonify(doneyet="Nope", status="Waiting to enter queue...")

@app.route("/isthethreaddone/2/")
def isthethreaddone2():
    user_uuid = get_user_uuid()
    if user_uuid in results_2:
        return jsonify(doneyet="Yes", status="Complete!")
    
    if current_task_2 == user_uuid:
        return jsonify(doneyet="Nope", status="AI is working on your request now...")

    queue_list = [task[0] for task in list(task_queue_2.queue)]
    if user_uuid in queue_list:
        others_processing = 1 if (current_task_2 and current_task_2 != user_uuid) else 0
        pos = others_processing + queue_list.index(user_uuid) + 1
        return jsonify(doneyet="Nope", status=f"You are at position {pos} in the queue")

    return jsonify(doneyet="Nope", status="Waiting to enter queue...")

# ---------------- QUEUE READERS (Now Result Readers) -----------------
@app.route("/endpoint/q_reader/")
def q_endpoint():
    user_uuid = get_user_uuid()
    if user_uuid in results_1:
        return jsonify([results_1[user_uuid]])
    return jsonify({"status": "Not ready or not found"}), 202

@app.route("/endpoint/q2_reader/")
def q2_endpoint():
    user_uuid = get_user_uuid()
    if user_uuid in results_2:
        return jsonify([results_2[user_uuid]])
    return jsonify({"status": "Not ready or not found"}), 202

# ---------------- SP1 ROUTE -----------------
@app.route("/sp1")
def sp1():
    jsonstr = request.args.get("jsonstr", "[]")
    try:
        data = json.loads(jsonstr)
        activities = data[0] if isinstance(data, list) and len(data) > 0 else []
    except Exception:
        activities = []
    return render_template("sp1.html", activities=activities)

# ---------------- COOKIE CLEAR -----------------
@app.route("/go/clr_cke/")
def clear_uuid_cookie():
    user_uuid = request.cookies.get(UUID_COOKIE)
    if user_uuid:
        # Cleanup results when user leaves
        results_1.pop(user_uuid, None)
        results_2.pop(user_uuid, None)

    resp = redirect(url_for("home"))
    resp.set_cookie(UUID_COOKIE, "", expires=0, max_age=0, path="/", httponly=True, samesite="Lax")
    resp.set_cookie("questionnaire_answers", "", expires=0, max_age=0, path="/", httponly=True, samesite="Lax")
    resp.set_cookie("picks_done", "", expires=0, max_age=0, path="/", httponly=True, samesite="Lax")
    return resp

@app.route("/ckd/")
def ckd():
    return jsonify(request.cookies)

# ---------------- RUN -----------------
if __name__ == "__main__":
    from waitress import serve
    print("Starting production server on http://0.0.0.0:5000")
    serve(app, host="0.0.0.0", port=5000, threads=6)
