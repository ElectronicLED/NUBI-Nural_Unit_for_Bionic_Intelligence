# Installation: pip install TTS
from TTS.api import TTS
from playsound import playsound



###################### Testing all sounds ##################################################3
# model_names = ["tts_models/en/ljspeech/tacotron2-DDC",
#                #"tts_models/en/ek1/tacotron2",
#                "tts_models/en/ljspeech/glow-tts",
#                #"tts_models/en/ljspeech/tacotron2-DCA",
#                #"tts_models/en/ljspeech/speedy-speech-wn",
#                #"tts_models/en/sam/tacotron-DDC",
#                #"tts_models/en/vctk/sc-glow-tts",
#                ]

# for i in range(len(model_names)):
#     print(f"\n\n\nModel {i}: {model_names[i]}\n\n\n\n")

#     tts = TTS(model_name=model_names[i], progress_bar=True, gpu=True)
#     tts.tts_to_file(text="Hello My Name Is NUBI", file_path=f"{i}.wav")

##################################################################################################


# file_path = "sounds/corgi_output.wav"  # Specify the output file path
# tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=True, gpu=False)
# tts.tts_to_file(text="Hello My Name Is NUBI. I am 3 months old", file_path=file_path)
# playsound(file_path)

def say(line="Hi", voice_name="Fenrir", output_file_name="output_file"):
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=True, gpu=False)
    tts.tts_to_file(text=line, file_path=output_file_name+".wav")
    playsound(output_file_name+".wav")