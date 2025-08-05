from google import genai
import os 

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Set your API key here

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="what do you know about humanoids"
)
print(response.text)