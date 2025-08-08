from google import genai
import os 

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Set your API key here. I am not showing mine

# response = client.models.generate_content(
#     model="gemini-2.5-flash", contents="what do you know about humanoids"
# )
# print(response.text)


dialog = client.chats.create(model="gemini-2.5-flash")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat.")
        break
    response = dialog.send_message(user_input)
    print("NUBI: " + response.text)
    