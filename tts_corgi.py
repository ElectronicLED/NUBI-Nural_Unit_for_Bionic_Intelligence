from TTS.api import TTS
import torch


# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# TTS with on the fly voice conversion
api = TTS("tts_models/en/sam/tacotron-DDC").to(device)
api.tts_to_file(
    text="hello world",
    file_path="output.wav"
)