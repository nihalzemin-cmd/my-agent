import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from groq import Groq
from duckduckgo_search import DDGS
from tinydb import TinyDB, Query
from datetime import datetime

load_dotenv()

app = Flask(__name__)
api_key = os.getenv("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)
else:
    class MockClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    class Message:
                        content = "I'm currently in deployment mode. Please ensure the `GROQ_API_KEY` is correctly configured in your environment settings to enable my full assistant capabilities."
                    class Choice:
                        message = Message()
                    class Response:
                        choices = [Choice()]
                    return Response()
            completions = Completions()
        chat = Chat()
    
    client = MockClient()
    print("WARNING: GROQ_API_KEY not found. Operating in fallback mode.")


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

    def generate():
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a personal AI assistant and understanding partner. You remember everything about him from past conversations. Be helpful, friendly and personal."},
                *memory[:-1],
                {"role": "user", "content": user_input_with_search}
            ],
            stream=True
        )

        full_reply = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                yield content

        messages_table.insert({"role": "assistant", "content": full_reply, "time": str(datetime.now())})

    return Response(stream_with_context(generate()), mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0",
    port=port)