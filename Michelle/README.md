# Verbal Communication Module - Setup Guide

This guide outlines the steps to install the necessary dependencies and configure the environment for the Verbal Communication project.

## Step 1: Install FFmpeg
The `whisper` library requires FFmpeg to handle audio processing.

1.  **Download FFmpeg:**
    * Go to the FFmpeg builds page and download the "release-essentials" `.zip` file.
2.  **Extract:**
    * Extract the folder to `C:\ffmpeg`.
3.  **Add to Path:**
    * Press the **Windows Key**, type "Env", and select **Edit the system environment variables**.
    * Click **Environment Variables**. 
    * Under "System variables", find `Path` and click **Edit**. 
    * Click **New** and paste: `C:\ffmpeg\bin` 
    * Click **OK** on all windows. 
4.  **Verify:**
    * Open a new Command Prompt (CMD) and run the following command. If text appears, installation is successful.
    ```bash
    ffmpeg -version
    ```

## Step 2: Install Python Libraries

**Python Version Used:** 3.13.9 

Run the following command to install the required libraries: 

```bash
pip install numpy sounddevice soundfile openai-whisper pvporcupine gtts cohere

```

## Step 3: Audio Device Configuration

> **! IMPORTANT**
> The code defaults to `INPUT_DEVICE_ID = 8` and `OUTPUT_DEVICE_ID = 10`, which are specific to the developer's machine. You **must** find your own device IDs. 
> 
> 

### How to find your Device IDs:

1. Ensure the `sounddevice` library is installed. 


2. Locate the file `Audio_Recording.ipynb` in the folder `1-Audio_Recording`. 


3. In the first block of code ("Testing voice recording to a file"), uncomment the following lines: 


```python
# print(sd.query_devices())
# print(sd.default.device)

```


4. Run the code to list all available devices. 


5. **Select your devices:** Choose the index for your input and output. Ensure both devices support a sampling rate of **48000.0**. 


6. 
**Update the main code:** Open `V_com.ipynb` and update the `INPUT_DEVICE_ID` and `OUTPUT_DEVICE_ID` under the `# === DEVICE SELECTION ===` section. 



## Step 4: File & Folder Setup

You need to update the file paths in `V_com.ipynb` to match your local file structure.

**Quick Setup:** The easiest method is to unzip the project to your Desktop and replace `C:\Users\Michelle Gh` with your own username in the paths below. 

Update the `# === DIRECTORIES & FILE PATHS ===` section with your specific paths: 

```python
# === DIRECTORIES & FILE PATHS ===

AUDIO_RECORD_PATH = r"C:\Users\YOUR_USERNAME\Desktop\Graduation Project\Verbal Communication\6-V_COM\1-AUDIO_RECORD_PATH\recorded_input.wav"

STT_OUTPUT_PATH = r"C:\Users\YOUR_USERNAME\Desktop\Graduation Project\Verbal Communication\6-V_COM\2-STT_OUPUT_PATH\STT_Output.txt"

AI_REPLY_PATH = r"C:\Users\YOUR_USERNAME\Desktop\Graduation Project\Verbal Communication\6-V_COM\3-AI_REPLY_PATH\ai_reply.txt"

TTS_OUTPUT_PATH = r"C:\Users\YOUR_USERNAME\Desktop\Graduation Project\Verbal Communication\6-V_COM\4-TTS_OUTPUT_PATH\Robot_Response.wav"

YES_PATH = r"C:\Users\YOUR_USERNAME\Desktop\Graduation Project\Verbal Communication\6-V_COM\5-YES_PATH\yes-masterrr.mp3"

WAKEWORD_MODEL = r"C:\Users\YOUR_USERNAME\Desktop\Graduation Project\Verbal Communication\6-V_COM\6-WAKEWORD_MODEL\Hey-Robot_en_windows_v3_0_0.ppn"

```

