from google import genai
from google.genai import types
import wave
from pydub import AudioSegment
import io

# Set up the wave file to save the output:
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

client = genai.Client()

response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents="Say cheerfully: Have a wonderful day!",
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
               voice_name='Kore',
            )
         )
      ),
   )
)

data = response.candidates[0].content.parts[0].inline_data.data
print(data[:32])

# Save raw PCM data as WAV
wave_file("output.wav", data, channels=1, rate=16000, sample_width=2)
wave_file("output8.wav", data, channels=1, rate=24000, sample_width=1)
wave_file("output_stereo.wav", data, channels=2, rate=24000, sample_width=2)
print("Saved raw PCM as output.wav")

# import io
# from pydub import AudioSegment

# # Assuming 'audio_bytes' contains your raw audio data in bytes
# # You need to know the original format of these bytes (e.g., 'wav', 'pcm')
# audio_bytes = b"..." # Replace with your actual audio bytes

# try:
#     # Create an AudioSegment from the bytes, specifying the original format
#     # Example: if your bytes are raw WAV data
#     audio_segment = AudioSegment.from_file(io.BytesIO(data), format="wav")

#     # Export the AudioSegment as an MP3 file
#     audio_segment.export("output.wav", format="wav")
#     print("Bytes successfully converted to output.wav")

# except Exception as e:
#     print(f"Error converting bytes to MP3: {e}")
#     print("Ensure FFmpeg is installed and the input format is correct.")


# file_name='out.wav'
# audio = AudioSegment.from_file(io.BytesIO(data), format="mp3")
# audio.export("out.wav", format="wav")
# wave_file(file_name, data) # Saves the file to current directory

