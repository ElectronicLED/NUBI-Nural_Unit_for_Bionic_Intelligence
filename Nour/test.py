import tts_gemini

voices = ["Zephyr",          "Kore",
          "Orus",          "Autonoe",
          "Umbriel",          "Erinome",
          "Laomedeia",          "Schedar",
          "Achird",          "Sadachbia",
          "Puck",          "Fenrir",
          "Aoede",          "Enceladus",
          "Algieba",          "Algenib",
          "Achernar",          "Gacrux",
          "Zubenelgenubi",          "Sadaltager",
          "Charon",          "Leda",
          "Callirrhoe",          "Iapetus",
          "Despina",          "Rasalgethi",
          "Alnilam",          "Pulcherrima",
          "Vindemiatrix",          "Sulafat",
          ]
# Algieba
voices = ["Achernar", "Achird", "Algenib", "Alnilam", "Aoede", "Autonoe", 
          "Callirrhoe", "Charon", 
            "Despina",
            "Enceladus", "Erinome", 
            "Fenrir", 
            "Gacrux", 
            "Iapetus", 
            "Kore", 
            "Laomedeia","Leda",
            "Orus", 
            "Puck", 
            "Pulcherrima", 
            "Rasalgethi", 
            "Sadachbia", "Sadaltager", "Schedar", "Sulafat"
            , "Umbriel", 
            "Vindemiatrix", 
            "Zephyr", "Zubenelgenubi"]

for i in range(29):
    if i in [25,28]:
        print(i, voices[i])
        tts_gemini.say(line= "Hello my name is NUBI", voice_name=voices[i], output_file_name=f"{i}_{voices[i]}")