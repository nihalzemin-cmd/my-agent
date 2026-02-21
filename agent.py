from groq import Groq
from duckduckgo_search import DDGS

client = Groq(api_key="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")

memory = []

def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        return "\n".join([r['body'] for r in results])

print("🤖 Your Personal AI Agent is ready!")
print("Type 'quit' to exit\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        break
    
    if "search" in user_input.lower() or "what is" in user_input.lower() or "latest" in user_input.lower():
        print("🔍 Searching the web...")
        search_results = search_web(user_input)
        user_input = f"{user_input}\n\nWeb search results:\n{search_results}"
    
    memory.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a personal AI assistant. Use web search results when provided to give accurate answers."},
            *memory
        ]
    )
    
    reply = response.choices[0].message.content
    memory.append({"role": "assistant", "content": reply})
    
    print(f"\nAgent: {reply}\n")