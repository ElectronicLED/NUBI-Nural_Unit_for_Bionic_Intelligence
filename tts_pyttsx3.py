import pyttsx3 


# Initialize the engine
engine = pyttsx3.init("espeak")  # Use espeak-ng as the TTS engine



engine.setProperty('rate', 200)  # Default is usually 200
engine.setProperty('volume', 1.0)  # Max volume



# voices = engine.getProperty('voices')
# for voice in voices:
#     print(f"Voice: {voice.name}, ID: {voice.id}")  # List available voices

# print(len(voices))
# # Set a specific voice by ID (replace 'voice.id' with the desired one)
# for i in range(len(voices)):
#     engine.setProperty('voice', voices[i].id)
#     print(f"Setting voice to: {voices[i].name}  ID: {voices[i].id}")
#     engine.say('The quick brown fox jumped over the lazy dog.')
#     engine.runAndWait()
#     if input() == 'q':
#         break




while(1):    
    

    MyText = input("Enter text to speak: ")
    #print("Did you say",MyText)
    engine.say(MyText) 
    engine.runAndWait()

'''This is project NUBI speaking
not stephen hawking
NUBI stands for Nural Unit for Bionic Intelligence.

'''