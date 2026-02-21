import os 
from flask import Flask, render_template, request, jsonify
from groq import Groq
from duckduckgo_search import DDGS
from tinydb import TinyDB, Query
from datetime import datetime

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROOQ_API_KEY"))

db = TinyDB('memory.json')
messages_table = db.table('messages')

def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        return "\n".join([r['body'] for r in results])

def get_memory():
    all_messages = messages_table.all()
    return [{"role": m["role"], "content": m["content"]} for m in all_messages[-20:]]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")

    if "search" in user_input.lower() or "what is" in user_input.lower() or "latest" in user_input.lower():
        search_results = search_web(user_input)
        user_input_with_search = f"{user_input}\n\nWeb search results:\n{search_results}"
    else:
        user_input_with_search = user_input

    messages_table.insert({"role": "user", "content": user_input, "time": str(datetime.now())})

    memory = get_memory()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a personal AI assistant and understanding partner for Nihal. You remember everything about him from past conversations. Be helpful, friendly and personal."},
            *memory[:-1],
            {"role": "user", "content": user_input_with_search}
        ]
    )

    reply = response.choices[0].message.content
    messages_table.insert({"role": "assistant", "content": reply, "time": str(datetime.now())})

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)