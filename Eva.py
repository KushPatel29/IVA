import pyaudio
import pvporcupine
import struct
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import subprocess
import ctypes
import time
import json
import wolframalpha
import requests
import pyjokes
import winshell
import wikipedia
from twilio.rest import Client
from urllib.request import urlopen
from ecapture import ecapture as ec
from ytmusicapi import YTMusic
import yagmail
from newsapi import NewsApiClient
import vlc
import openai
import load_dotenv

load_dotenv()  # Load variables from .env

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    engine.say(text)
    engine.runAndWait()

def speak(text):
    print(text)
    text_to_speech(text)

def takeCommand():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening...")
        audio = recognizer.listen(source)
    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query
    except Exception as e:
        print(e)
        speak("Unable to Recognize your voice.")
        return "None"

def wishMe():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good Morning Sir!")
    elif 12 <= hour < 18:
        speak("Good Afternoon Sir!")
    else:
        speak("Good Evening Sir!")
    speak("How can I help You")

def search_platform(query, platform):
    if platform == 'wikipedia':
        try:
            results = wikipedia.summary(query, sentences=3)
            speak("According to Wikipedia")
            print(results)
            speak(results)
        except wikipedia.exceptions.PageError:
            speak("I'm sorry, I couldn't find any results for that query.")
        except wikipedia.exceptions.DisambiguationError as e:
            speak("There were multiple matches for that query. Please be more specific.")
            print(e.options)
    elif platform == 'youtube':
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
    elif platform == 'google':
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
    elif platform == 'stackoverflow':
        url = f"https://stackoverflow.com/search?q={query}"
        webbrowser.open(url)
    else:
        return "Platform not supported"
    webbrowser.open(url)

# Function to play the music URL using VLC
def play_music_url(url):
    player = vlc.MediaPlayer()
    media = vlc.Media(url)
    player.set_media(media)
    player.play()

def play_music(query):
    # Load RapidAPI credentials from environment variables
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    rapidapi_host = os.getenv("RAPIDAPI_HOST")

    url = "https://deezerdevs-deezer.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": rapidapi_host
    }
    params = {"q": query}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            first_track = data['data'][0]
            track_title = first_track['title']
            track_artist = first_track['artist']['name']
            track_url = first_track['preview']
            
            play_music_url(track_url)
            speak(f"Now playing {track_title} by {track_artist}")
        else:
            speak("Sorry, I couldn't find any matching songs.")
    else:
        speak("Sorry, there was an error while searching for the song.")

def send_email(to_email, subject, body):
    try:
        # Load email credentials from environment variables
        email_address = os.getenv("EMAIL_ADDRESS")
        email_password = os.getenv("EMAIL_PASSWORD")

        yag = yagmail.SMTP(email_address, email_password)
        yag.send(to=to_email, subject=subject, contents=body)
        speak("Email has been sent!")
    except Exception as e:
        print(e)
        speak("I am not able to send this email")

def calculate(query):
    # Load WolframAlpha API key from environment variables
    app_id = os.getenv("WOLFRAMALPHA_API_KEY")
    client = wolframalpha.Client(app_id)
    try:
        res = client.query(query)
        answer = next(res.results).text
        speak("The answer is " + answer)
    except Exception as e:
        print(e)
        speak("Sorry, I couldn't calculate that.")

def get_weather(city_name):
    # Load Weather API Key from environment variables
    weather_api_key = os.getenv("WEATHERAPI_KEY")
    base_url = f"https://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city_name}&aqi=no"
    response = requests.get(base_url)
    data = response.json()

    if 'error' in data:
        speak("City Not Found")
    else:
        current_temperature = data['current']['temp_c']
        current_pressure = data['current']['pressure_mb']
        current_humidity = data['current']['humidity']
        weather_description = data['current']['condition']['text']

        print("Temperature (in Celsius) =", current_temperature)
        print("Pressure (in mb) =", current_pressure)
        print("Humidity =", current_humidity, "%")
        print("Description =", weather_description)

        speak(f"The temperature in {city_name} is {current_temperature} degrees Celsius with {weather_description}.")
        speak(f"The atmospheric pressure is {current_pressure} millibars and the humidity is {current_humidity} percent.")

# Initialize the News API client with your API key
news_api_key = os.getenv("NEWSAPI_KEY")
api = NewsApiClient(api_key=news_api_key)

def get_news():
    try:
        top_headlines = api.get_top_headlines(country='ca')
    
        if 'articles' in top_headlines:
            articles = top_headlines['articles']
            speak('Here are some top news from Vancouver:')
        
            for i, article in enumerate(articles, start=1):
                print(f"{i}. {article['title']}\n")
                print(f"{article['description']}\n")
                speak(f"{i}. {article['title']}\n")
        else:
            speak("No articles found.")
    
    except Exception as e:
        print(f"Error: {e}")

def ask_gpt(prompt):
    # Load OpenAI API key from environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use an up-to-date model or your chosen model
        prompt=prompt,
        max_tokens=100
    )
    return response.choices[0].text.strip()

def process_command(query):
    if 'open wikipedia' in query:
        speak("What do you want to search on Wikipedia?")
        search_query = takeCommand()
        search_platform(search_query, 'wikipedia')

    elif 'open youtube' in query:
        speak("What do you want to search on Youtube?")
        search_query = takeCommand()
        search_platform(search_query, 'youtube')

    elif 'open google' in query:
        speak("What do you want to search on Google?")
        search_query = takeCommand()
        search_platform(search_query, 'google')

    elif 'open stackoverflow' in query:
        speak("What do you want to search on Stack Overflow?")
        search_query = takeCommand()
        search_platform(search_query, 'stackoverflow')

    elif 'play music' in query or "play song" in query:
        speak("Here you go with music")
        speak("What song do you want to play?")
        search_query = takeCommand()
        play_music(search_query)

    elif "ask" in query:
        prompt = query.split("ask", 1)[1].strip()
        response = ask_gpt(prompt)
        speak(response)

    elif 'the time' in query:
        strTime = datetime.datetime.now().strftime("%H:%M:%S")
        speak(f"Sir, the time is {strTime}")

    elif 'email to' in query:
        try:
            speak("What should I say?")
            content = takeCommand()
            to = "Receiver email address"
            send_email(to, "Subject", content)
        except Exception as e:
            print(e)
            speak("I am not able to send this email")

    elif 'send a mail' in query:
        try:
            speak("What should I say?")
            content = takeCommand()
            speak("Whom should I send?")
            to = input()
            send_email(to, "Subject", content)
        except Exception as e:
            print(e)
            speak("I am not able to send this email")

    elif 'how are you' in query:
        speak("I am fine, Thank you")
        speak("How are you, Sir")

    elif 'fine' in query or "good" in query:
        speak("It's good to know that you are fine")

    elif 'joke' in query:
        speak(pyjokes.get_joke())

    elif "calculate" in query:
        try:
            speak("What do you want me to calculate?")
            calculation_query = takeCommand()
            calculate(calculation_query)
        except Exception as e:
            print(e)
            speak("Sorry, I couldn't calculate that.")

    elif 'search' in query or 'play' in query:
        query = query.replace("search", "")
        query = query.replace("play", "")
        webbrowser.open(query)

    elif "who made you" in query or "who created you" in query:
        speak("I have been created by Kush.")

    elif 'exit' in query:
        speak("Thanks for giving me your time")
        exit()

    elif 'who i am' in query:
        speak("If you talk then definitely you are human.")

    elif "why you came to world" in query:
        speak("Thanks to Kush. Further, it's a secret")

    elif 'is love' in query:
        speak("It is the 7th sense that destroys all other senses")

    elif "who are you" in query:
        speak("I am your virtual assistant created by Kush")

    elif 'reason for you' in query:
        speak("I was created as a Minor project by Mister Kush")

    elif 'news' in query:
        get_news()

    elif 'lock window' in query:
        speak("locking the device")
        ctypes.windll.user32.LockWorkStation()

    elif 'shutdown system' in query:
        speak("Hold On a Sec! Your system is on its way to shut down")
        subprocess.call('shutdown / p /f')

    elif 'empty recycle bin' in query:
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=True)
        speak("Recycle Bin Recycled")

    elif "don't listen" in query or "stop listening" in query:
        speak("For how much time you want me to stop listening?")
        a = int(takeCommand())
        time.sleep(a)

    elif "where is" in query:
        query = query.replace("where is", "")
        location = query
        speak("User asked to Locate")
        speak(location)
        webbrowser.open("https://www.google.nl/maps/place/" + location)

    elif "camera" in query or "take a photo" in query:
        ec.capture(0, "Eva Camera", "img.jpg")

    elif "restart" in query:
        subprocess.call(["shutdown", "/r"])

    elif "hibernate" in query or "sleep" in query:
        speak("Hibernating")
        subprocess.call("shutdown / h")

    elif "log off" in query or "sign out" in query:
        speak("Make sure all the applications are closed before sign-out")
        time.sleep(5)
        subprocess.call(["shutdown", "/l"])

    elif "write a note" in query:
        speak("What should I write, sir?")
        note = takeCommand()
        file = open('Eva.txt', 'w')
        speak("Sir, Should I include date and time?")
        snfm = takeCommand()
        if 'yes' in snfm or 'sure' in snfm:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            file.write(strTime)
            file.write(" :- ")
            file.write(note)
        else:
            file.write(note)
        file.close()

    elif "show note" in query:
        speak("Showing Notes")
        file = open("Eva.txt", "r")
        content = file.read()
        print(content)
        speak(content[:100])  # speak first 100 characters or so
        file.close()

    elif "Eva" in query:
        wishMe()
        speak("Eva one point O in your service Mister")

    elif "weather" in query:
        speak("Please tell me the city name.")
        city_name = takeCommand()
        get_weather(city_name)

    elif "what is" in query or "who is" in query:
        # Another WolframAlpha usage
        app_id = os.getenv("WOLFRAMALPHA_API_KEY")
        client = wolframalpha.Client(app_id)
        res = client.query(query)
        try:
            answer = next(res.results).text
            print(answer)
            speak(answer)
        except StopIteration:
            print("No results")

    else:
        speak("Sorry, I didn't understand that command.")

def main():
    # Load your Picovoice Porcupine Access Key from environment variables
    picovoice_access_key = os.getenv("PICOVOICE_ACCESS_KEY")
    porcupine_keyword_path = os.getenv("PORCUPINE_KEYWORD_PATH")

    handle = pvporcupine.create(
        access_key=picovoice_access_key,
        keyword_paths=[porcupine_keyword_path],
        sensitivities=[0.99]
    )
    sample_rate = handle.sample_rate
    frames_per_buffer = handle.frame_length
    audio = pyaudio.PyAudio()
    print("Listening for wake word 'Hello Eva'...")

    stream = audio.open(
        rate=sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=frames_per_buffer
    )

    while True:
        pcm = stream.read(frames_per_buffer)
        pcm = struct.unpack_from("h" * frames_per_buffer, pcm)

        keyword_index = handle.process(pcm)
        if keyword_index >= 0:
            text_to_speech("Hello")
            print("Wake word detected!")
            query = takeCommand()
            process_command(query)

if __name__ == "__main__":
    main()
