from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import logging
from difflib import get_close_matches

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# GROQ AI SETUP  (Free — sign up at https://console.groq.com)
# ══════════════════════════════════════════════════════════════
from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

AI_AVAILABLE = False
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    AI_AVAILABLE = True
    logger.info("Groq AI ready.")
except Exception as e:
    logger.warning(f"Groq not available: {e}. Using knowledge base fallback.")

app = Flask(__name__)
CORS(app, origins="*")

# ══════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════
DB_PATH = "users.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                reply TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

init_db()

# ══════════════════════════════════════════════════════════════
# RICH KNOWLEDGE BASE  (used when Groq is unavailable)
# ══════════════════════════════════════════════════════════════
qa_pairs = {
    "heart attack": (
        "🚨 Heart Attack Warning Signs:\n"
        "• Chest pain or pressure (squeezing, tightness)\n"
        "• Pain spreading to arm, jaw, neck or back\n"
        "• Shortness of breath\n"
        "• Cold sweat, nausea or light-headedness\n\n"
        "🆘 What to do: Call emergency services (112/911) immediately. "
        "Chew an aspirin (325mg) if not allergic. Do NOT drive yourself to the hospital."
    ),
    "symptoms": (
        "❤️ Common Heart Disease Symptoms:\n"
        "• Chest pain, tightness or discomfort\n"
        "• Shortness of breath during activity or at rest\n"
        "• Palpitations (racing or irregular heartbeat)\n"
        "• Fatigue and weakness\n"
        "• Dizziness or fainting\n"
        "• Swollen ankles or feet (sign of heart failure)\n\n"
        "⚠️ If you experience any of these, consult a doctor promptly."
    ),
    "chest pain": (
        "🚨 Chest Pain — Take Seriously!\n"
        "Possible causes:\n"
        "• Heart attack (crushing pain, spreads to arm/jaw)\n"
        "• Angina (pain during exertion, relieved by rest)\n"
        "• Acid reflux (burning sensation)\n"
        "• Muscle strain\n\n"
        "⚠️ Any new or unexplained chest pain should be evaluated by a doctor immediately. "
        "Do not ignore it — it's better to be safe."
    ),
    "blood pressure": (
        "🩺 Blood Pressure Guide:\n"
        "• Normal: below 120/80 mmHg\n"
        "• Elevated: 120–129 / below 80\n"
        "• High (Stage 1): 130–139 / 80–89\n"
        "• High (Stage 2): 140+ / 90+\n"
        "• Crisis: above 180/120 — seek emergency care\n\n"
        "💊 How to lower BP naturally:\n"
        "• Reduce salt intake (below 2.3g/day)\n"
        "• Exercise regularly (30 min/day)\n"
        "• Lose excess weight\n"
        "• Limit alcohol\n"
        "• Manage stress with meditation or yoga\n"
        "• Eat potassium-rich foods (banana, spinach)"
    ),
    "cholesterol": (
        "🔬 Cholesterol Levels:\n"
        "• Total cholesterol: below 200 mg/dL (good)\n"
        "• LDL (bad): below 100 mg/dL\n"
        "• HDL (good): above 60 mg/dL\n"
        "• Triglycerides: below 150 mg/dL\n\n"
        "🥗 How to improve cholesterol:\n"
        "• Eat oats, beans, avocado, olive oil, nuts\n"
        "• Avoid trans fats, fried food, processed snacks\n"
        "• Exercise — it raises HDL (good cholesterol)\n"
        "• Quit smoking\n"
        "• Doctors may prescribe statins if lifestyle changes aren't enough"
    ),
    "diet": (
        "🥗 Heart-Healthy Diet Tips:\n\n"
        "✅ Eat more:\n"
        "• Fruits and vegetables (5 portions/day)\n"
        "• Whole grains (oats, brown rice, whole wheat)\n"
        "• Fatty fish (salmon, mackerel — 2x/week)\n"
        "• Nuts and seeds (almonds, walnuts, flaxseed)\n"
        "• Olive oil, avocado\n"
        "• Legumes (lentils, beans, chickpeas)\n\n"
        "❌ Avoid or reduce:\n"
        "• Processed and packaged foods\n"
        "• Red and processed meats (bacon, sausage)\n"
        "• Sugary drinks and sweets\n"
        "• Trans fats and deep-fried foods\n"
        "• Excess salt\n\n"
        "💡 Best diets: Mediterranean diet or DASH diet"
    ),
    "exercise": (
        "🏃 Exercise for Heart Health:\n\n"
        "📌 Weekly targets (American Heart Association):\n"
        "• 150 minutes of moderate activity (brisk walking, cycling)\n"
        "• OR 75 minutes of vigorous activity (running, swimming)\n"
        "• Strength training 2x per week\n\n"
        "🏃 Best heart exercises:\n"
        "• Walking — easiest to start with\n"
        "• Swimming — low impact, great for joints\n"
        "• Cycling — builds endurance\n"
        "• Yoga — reduces stress and BP\n"
        "• Dancing — fun cardio!\n\n"
        "⚠️ Start slow if you're new to exercise. Consult a doctor before starting "
        "a new program if you have existing heart conditions."
    ),
    "heart rate": (
        "💓 Heart Rate Guide:\n"
        "• Normal resting: 60–100 bpm\n"
        "• Athletes: 40–60 bpm (normal for them)\n"
        "• Bradycardia (too slow): below 60 bpm\n"
        "• Tachycardia (too fast): above 100 bpm at rest\n\n"
        "📱 How to check: Count pulse at wrist or neck for 60 seconds.\n\n"
        "⚠️ See a doctor if your resting heart rate is consistently above 100 "
        "or below 50, especially with dizziness or chest discomfort."
    ),
    "stress": (
        "🧘 Stress & Heart Health:\n"
        "Chronic stress raises blood pressure and inflammation, increasing heart risk.\n\n"
        "✅ Stress management tips:\n"
        "• Practice deep breathing (4-7-8 technique)\n"
        "• Meditate for 10–15 minutes daily\n"
        "• Exercise regularly — releases endorphins\n"
        "• Get 7–8 hours of sleep\n"
        "• Talk to friends, family or a therapist\n"
        "• Limit caffeine and alcohol\n"
        "• Take breaks from screens and news\n"
        "• Spend time in nature"
    ),
    "smoking": (
        "🚭 Smoking & Heart Disease:\n"
        "Smoking is one of the biggest risk factors for heart disease.\n\n"
        "❤️ Benefits of quitting:\n"
        "• After 20 minutes: BP and heart rate drop\n"
        "• After 24 hours: Heart attack risk begins to fall\n"
        "• After 1 year: Heart disease risk is halved\n"
        "• After 5 years: Stroke risk equals a non-smoker\n\n"
        "💡 Quitting tips:\n"
        "• Nicotine patches or gum\n"
        "• Consult a doctor for medication (Varenicline/Bupropion)\n"
        "• Join a support group\n"
        "• Avoid triggers (alcohol, coffee breaks with smokers)"
    ),
    "medication": (
        "💊 Common Heart Medications:\n"
        "• Statins (Atorvastatin, Rosuvastatin) — lower LDL cholesterol\n"
        "• Beta-blockers (Metoprolol, Atenolol) — slow heart rate, reduce BP\n"
        "• ACE inhibitors (Lisinopril, Ramipril) — lower BP, protect kidneys\n"
        "• Aspirin — prevents blood clots (usually 75–100mg daily)\n"
        "• Blood thinners (Warfarin, Rivaroxaban) — prevent stroke/clots\n"
        "• Nitroglycerin — relieves angina chest pain quickly\n\n"
        "⚠️ Never start or stop heart medications without consulting your doctor."
    ),
    "diabetes": (
        "🩺 Diabetes & Heart Health:\n"
        "Diabetics have 2–4x higher risk of heart disease.\n\n"
        "Why: High blood sugar damages blood vessels and nerves, "
        "leading to hardened arteries and heart disease.\n\n"
        "✅ Protect your heart if you have diabetes:\n"
        "• Control blood sugar (HbA1c below 7%)\n"
        "• Monitor BP (target below 130/80)\n"
        "• Keep LDL cholesterol below 100 mg/dL\n"
        "• Exercise daily\n"
        "• Don't smoke\n"
        "• Take prescribed medications regularly"
    ),
    "prevention": (
        "✅ Heart Disease Prevention:\n\n"
        "The 'Life's Essential 8' by American Heart Association:\n"
        "1. Eat healthy (Mediterranean/DASH diet)\n"
        "2. Be physically active (150 min/week)\n"
        "3. Quit smoking\n"
        "4. Maintain healthy weight (BMI 18.5–24.9)\n"
        "5. Manage blood pressure (below 120/80)\n"
        "6. Control cholesterol (LDL below 100)\n"
        "7. Manage blood sugar\n"
        "8. Get quality sleep (7–9 hours/night)\n\n"
        "📅 Regular health check-ups are key — know your numbers!"
    ),
    "weight": (
        "⚖️ Weight & Heart Health:\n"
        "Being overweight strains the heart and raises BP, cholesterol, and diabetes risk.\n\n"
        "💡 Healthy targets:\n"
        "• BMI: 18.5–24.9\n"
        "• Waist circumference: below 94cm (men), below 80cm (women)\n\n"
        "✅ Tips to lose weight safely:\n"
        "• Create a small calorie deficit (300–500 cal/day)\n"
        "• Eat more protein and fibre — they keep you full\n"
        "• Reduce sugar and processed carbs\n"
        "• Walk at least 8,000 steps/day\n"
        "• Avoid crash diets — slow and steady is best for the heart"
    ),
    "sleep": (
        "😴 Sleep & Heart Health:\n"
        "Poor sleep raises BP, inflammation and stress hormones — all bad for the heart.\n\n"
        "💤 Recommendations:\n"
        "• Adults need 7–9 hours per night\n"
        "• Sleep apnea (snoring + gasping) significantly raises heart risk — get tested!\n\n"
        "✅ Better sleep tips:\n"
        "• Go to bed and wake up at the same time\n"
        "• Avoid screens 1 hour before bed\n"
        "• Keep bedroom cool and dark\n"
        "• Avoid caffeine after 2pm\n"
        "• Avoid heavy meals before bedtime"
    ),
    "alcohol": (
        "🍷 Alcohol & Heart Health:\n"
        "Excessive drinking raises BP, causes irregular heartbeat (AFib), "
        "and weakens the heart muscle.\n\n"
        "📌 Safe limits:\n"
        "• Men: up to 2 standard drinks/day\n"
        "• Women: up to 1 standard drink/day\n\n"
        "⚠️ Heavy drinking can cause:\n"
        "• Cardiomyopathy (weakened heart muscle)\n"
        "• Atrial fibrillation (irregular heartbeat)\n"
        "• High blood pressure\n"
        "• Weight gain"
    ),
}

# ══════════════════════════════════════════════════════════════
# KNOWLEDGE BASE MATCHING
# ══════════════════════════════════════════════════════════════
def check_qa(user_input):
    q = user_input.lower()
    for key, answer in qa_pairs.items():
        if key in q:
            return answer
    words = q.split()
    keys  = list(qa_pairs.keys())
    for word in words:
        match = get_close_matches(word, keys, n=1, cutoff=0.75)
        if match:
            return qa_pairs[match[0]]
    return None

# ══════════════════════════════════════════════════════════════
# GROQ AI RESPONSE
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are HeartCare AI ❤️ — a knowledgeable, caring, and friendly 
heart health assistant. You provide detailed, accurate, and easy-to-understand advice 
about heart health, symptoms, medications, diet, exercise, blood pressure, cholesterol, 
stress, and lifestyle.

Rules:
- Always give detailed, helpful answers (not one-liners)
- Use bullet points and emojis to make answers easy to read
- For emergency symptoms (chest pain, heart attack), always urge calling emergency services
- Always recommend consulting a doctor for personal medical decisions
- Be warm, supportive and encouraging
- Answer only health-related questions. For unrelated topics, politely redirect."""

def ask_ai(user_input, history=None):
    if not AI_AVAILABLE:
        kb = check_qa(user_input)
        if kb:
            return kb
        return (
            "❤️ HeartCare AI\n\n"
            "I can help with questions about:\n"
            "• Heart attack symptoms\n"
            "• Blood pressure & cholesterol\n"
            "• Heart-healthy diet & exercise\n"
            "• Stress management\n"
            "• Medications\n\n"
            "Please ask me a specific question!"
        )

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history and len(history) > 0:
            for h in history[-10:]:
                messages.append({
                    "role": h.get("role", "user"),
                    "content": h.get("content", "")
                })
        else:
            messages.append({"role": "user", "content": user_input})

        logger.info(f"Sending {len(messages)} messages to Groq...")

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # ✅ updated model
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        logger.info("Groq replied successfully.")
        return reply

    except Exception as e:
        logger.error(f"Groq error: {e}")
        kb = check_qa(user_input)
        if kb:
            return kb
        return "⚠️ AI is temporarily unavailable. Please try again in a moment."

# ══════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════

@app.route('/')
def home():
    return jsonify({"status": "HeartCare AI Running ❤️"})


@app.route('/signup', methods=['POST'])
def signup():
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"message": "Required fields missing"}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, hashed))
        return jsonify({"message": "Signup successful"})
    except:
        return jsonify({"message": "User already exists"}), 400


@app.route('/login', methods=['POST'])
def login():
    data     = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    with get_db() as conn:
        row = conn.execute(
            "SELECT password FROM users WHERE username=?", (username,)
        ).fetchone()

    if row and bcrypt.checkpw(password.encode(), row["password"].encode()):
        return jsonify({"message": "Login success", "username": username})

    return jsonify({"message": "Invalid credentials"}), 401


@app.route('/chat', methods=['POST'])
def chat():
    data     = request.get_json() or {}
    msg      = data.get("message", "").strip()
    username = data.get("username", "")
    history  = data.get("history", [])

    if not msg:
        return jsonify({"reply": "Please type a message."})

    response = ask_ai(msg, history)

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO chats (username, message, reply) VALUES (?, ?, ?)",
                (username, msg, response)
            )
    except Exception as e:
        logger.error(f"DB error: {e}")

    return jsonify({"reply": response})


@app.route('/history', methods=['POST'])
def history():
    data     = request.get_json() or {}
    username = data.get("username", "")

    with get_db() as conn:
        rows = conn.execute(
            "SELECT message, reply, created_at FROM chats WHERE username=? ORDER BY id DESC LIMIT 50",
            (username,)
        ).fetchall()

    return jsonify({"history": [dict(r) for r in rows]})


# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)
