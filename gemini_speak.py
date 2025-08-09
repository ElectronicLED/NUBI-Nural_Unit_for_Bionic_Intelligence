from google import genai
import pyttsx3
import os 

engine = pyttsx3.init("espeak")  # Use espeak-ng as the TTS engine

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Set your API key here i am not showin mine

# response = client.models.generate_content(
#     model="gemini-2.5-flash", contents=input("How can I help you today? " + "\n")
# ).text


chat = client.chats.create(model="gemini-2.5-flash")

# initial prompt to let it know what it is
response = chat.send_message('''Your name is NUBI. 
    You are Nour ElDeens Shalaby's graduation project: humanoid bipedal robot. 
    NUBI stands for Neural Unit for Bionic Intelligence''').text
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat.")
        break
    response = chat.send_message(user_input).text
    response = response.replace("*", "")  # Remove asterisks if present
    print("NUBI: " + response)
    engine.say(response)
    engine.runAndWait()