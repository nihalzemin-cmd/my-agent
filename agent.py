import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from duckduckgo_search import DDGS

load_dotenv()

app = FastAPI()

api_key = os.getenv("API_KEY")
client = Groq(api_key=api_key)

memory = []

class Query(BaseModel):
    message: str

def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        return "\n".join([r['body'] for r in results])

@app.post("/chat")
def chat(query: Query):
    user_input = query.message

    if any(word in user_input.lower() for word in ["search", "what is", "latest"]):
        search_results = search_web(user_input)
        user_input = f"{user_input}\n\nWeb search results:\n{search_results}"

    memory.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a personal AI assistant. Use web search results when provided."},
            *memory
        ]
    )

    reply = response.choices[0].message.content
    memory.append({"role": "assistant", "content": reply})

    return {"reply": reply}