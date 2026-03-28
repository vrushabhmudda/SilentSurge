import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

key = os.getenv("GROQ_API_KEY")
print(f"Key loaded: {key[:8]}...")  # shows first 8 chars to confirm it loaded

client = Groq(api_key=key)
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say exactly: SilentSurge is online."}]
)
print(response.choices[0].message.content)


