import whisper

# use base or small not turbo
model = whisper.load_model("small")
result = model.transcribe("audio2.wav", language='en')
print(result["text"])