# Iva(Interactive Voice Assistant) Voice Assistant on Raspberry Pi

Eva is a Python-based voice assistant that you can deploy on typical desktops and on a **Raspberry Pi**, turning it into a free, fully functional AI device. It can handle tasks like:

- Searching the web on Wikipedia, YouTube, Google, and Stack Overflow  
- Playing music via the Deezer RapidAPI  
- Sending emails with `yagmail`  
- Getting real-time weather details using the Weather API  
- Fetching news headlines using the News API  
- Computing with WolframAlpha  
- Chatting via OpenAI’s GPT API  
- Tell jokes, lock/shut down (on desktop), create notes, etc.

## Table of Contents
1. [Features](#features)  
2. [Requirements](#requirements)  
3. [Raspberry Pi Setup](#raspberry-pi-setup)  
4. [Installation](#installation)  
5. [Environment Variables](#environment-variables)  
6. [Usage](#usage)  
7. [Customization](#customization)  
8. [Troubleshooting](#troubleshooting)  
9. [License](#license)

---

## Features

- **Voice Activation**: Uses [Picovoice Porcupine](https://github.com/Picovoice/porcupine) for wake-word detection (“Hello Eva”).  
- **Speech Recognition**: Leverages [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) with Google’s speech recognition API.  
- **Speech Synthesis**: Converts text to speech using [pyttsx3](https://pypi.org/project/pyttsx3/).  
- **Web Search**: Automatically opens results on Google, YouTube, Wikipedia, and Stack Overflow.  
- **Music Playback**: Fetches songs from Deezer (via RapidAPI) and plays previews using VLC.  
- **Email Sending**: Integrates with `yagmail` for Gmail-based sending.  
- **Weather Information**: Fetches current weather from WeatherAPI.  
- **News Headlines**: Retrieves top headlines from NewsAPI.  
- **Mathematical/Knowledge Queries**: Interfaces with WolframAlpha.  
- **ChatGPT Support**: Asks OpenAI’s API for extended chat or Q&A.  
- **System Commands**: Lock, shut down, or empty recycle bin (Windows-only).  
- **Cross-Platform**: Runs on Windows, Linux, macOS, **and** Raspberry Pi.

---

## Requirements

- **Python 3.7 or later**  
- A functioning microphone and speaker (USB mic, USB speaker, or a 3.5 mm jack on Raspberry Pi).  
- **pyaudio** sometimes requires additional system dependencies. (On Raspberry Pi, see below.)

### Python Libraries

A typical `requirements.txt` might include:

```txt
pyaudio
pvporcupine
speechrecognition
pyttsx3
wolframalpha
requests
pyjokes
winshell
wikipedia
twilio
yagmail
newsapi-python
ytmusicapi
python-dotenv
pyvlc
ecapture
```

On a Raspberry Pi, you may need to install `libportaudio2` or other dependencies before installing PyAudio.

---

## Raspberry Pi Setup

1. **Update Your Pi**  
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

2. **Install Dependencies**  
   - **PyAudio**:  
     ```bash
     sudo apt-get install portaudio19-dev python3-pyaudio
     ```
   - **VLC**:  
     ```bash
     sudo apt-get install vlc
     ```
   - (Optional) Some libraries might need `libatlas-base-dev` or other system packages.  
     ```bash
     sudo apt-get install libatlas-base-dev
     ```
   
3. **Enable Audio Inputs and Outputs**  
   - If you’re using a USB mic/speaker, ensure they’re correctly recognized in `raspi-config` or by `arecord -l` and `aplay -l`.

4. **Python Environment**  
   - It’s recommended that a virtual environment be created. For instance:
     ```bash
     sudo apt-get install python3-venv
     python3 -m venv venv
     source venv/bin/activate
     ```

5. **Clone This Repository & Install Requirements**  
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
   pip install -r requirements.txt
   ```

6. **Set Up Environment Variables** (see [Environment Variables](#environment-variables)).

---

## Installation

> **Note**: The installation steps below are for general usage on any system. For Raspberry Pi–specific notes, see [Raspberry Pi Setup](#raspberry-pi-setup).

1. **Clone or download this repository**  
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
   ```

2. **Create a virtual environment** (optional but recommended)  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (see [Environment Variables](#environment-variables)).

5. **Run the script**  
   ```bash
   python main.py
   ```
   *Replace `main.py` with your actual entry point if it differs.*

---

## Environment Variables

To keep your secrets private (like API keys and email credentials), this project uses environment variables.  

1. **Create a `.env` file** in the project root (same location as `main.py` or `requirements.txt`).  
2. **Add the following content** (replace with actual values):

   ```bash
   # RapidAPI credentials
   RAPIDAPI_KEY=your_rapidapi_key
   RAPIDAPI_HOST=deezerdevs-deezer.p.rapidapi.com

   # Email credentials
   EMAIL_ADDRESS=your_email@gmail.com
   EMAIL_PASSWORD=your_email_password

   # WolframAlpha
   WOLFRAMALPHA_API_KEY=your_wolframalpha_api_key

   # Weather API
   WEATHERAPI_KEY=your_weatherapi_key

   # News API
   NEWSAPI_KEY=your_newsapi_key

   # OpenAI
   OPENAI_API_KEY=your_openai_api_key

   # Picovoice Porcupine Access Key & Keyword Path
   PICOVOICE_ACCESS_KEY=your_picovoice_access_key
   PORCUPINE_KEYWORD_PATH=/path/to/Hello-Eva_en_windows_v3_0_0.ppn
   ```

3. **Ignore `.env`**  
   Make sure your `.gitignore` includes `.env` so it isn’t committed.

---

## Usage

1. **Start the assistant**:  
   ```bash
   python main.py
   ```
   - The assistant will listen for the wake word **“Hello Eva”**.  

2. **Interact via voice**:  
   - When you see “Wake word detected!” or hear “Hello,” you can speak your commands.  
   - Example phrases:
     - “Open Wikipedia”  
     - “Open YouTube”  
     - “Play music”  
     - “What is the weather in London?”  
     - “Tell me a joke.”  
     - “Ask GPT how to make pancakes.”  
     - “Lock window” (Windows only)  
     - “Shut down system” (Windows only)  
     - “Show note” or “Write a note”  
     - “Exit.”

3. **Automate Startup** (Raspberry Pi)  
   - If you want Eva to run automatically on boot, consider adding a cron job (`crontab -e`) or a system service that launches `main.py` on startup.

---

## Customization

- **Voice Settings**: Modify the rate or volume in the `text_to_speech` function.  
- **Wake Word**: Adjust Picovoice parameters in `main()` (e.g., sensitivity).  
- **APIs**: Add or remove functionality in `process_command`.  
- **Raspberry Pi–Specific Commands**: Some commands (e.g., lock, empty recycle bin) won’t work on Raspberry Pi. You can remove or adapt them.

---

## Troubleshooting

1. **Audio Issues on Raspberry Pi**:
   - Make sure your USB mic and speakers are detected.  
   - Run `sudo raspi-config` to configure audio input/output.  
   - Use `arecord` / `aplay` tests to verify the mic and speaker.

2. **PyAudio Install Errors**:
   - Install system dependencies: `sudo apt-get install portaudio19-dev python3-pyaudio`.

3. **Porcupine Access Key**:
   - Check your `.env` for `PICOVOICE_ACCESS_KEY`.  
   - Ensure the correct `.ppn` file path for `PORCUPINE_KEYWORD_PATH`.

4. **Speech Recognition Issues**:
   - Google’s recognition sometimes struggles with poor audio.  
   - Ensure a stable internet connection.

5. **API Rate Limits**:
   - Make sure your accounts (OpenAI, RapidAPI, etc.) have sufficient usage quota.

---

## License

This project is licensed under the [MIT License](LICENSE.md).  
Feel free to modify and distribute as needed, but remember to follow the terms of use for any third-party services (OpenAI, WolframAlpha, WeatherAPI, etc.).

---

**Congratulations!** You now have a working AI device on your Raspberry Pi without any recurring fees beyond your hardware and optional subscriptions for premium API usage. Enjoy your own personal, free-to-run AI Assistant!  
