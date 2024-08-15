import subprocess
import os
import tkinter as tk
from tkinter import scrolledtext
import speech_recognition as sr
from gtts import gTTS
from PIL import ImageGrab
import cv2
import time
import playsound  # Import playsound to handle audio playback

# Global variable to track microphone mute state
mic_muted = False

# Function to start the Llama model using the command prompt
def start_llama_model(model_name):
    command = f"ollama run {model_name}"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    print("Llama model started successfully.")
    return process

# Function to interact with Llama
def interact_with_llama(process, user_input):
    try:
        print(f"Sending input to Llama: {user_input}")
        process.stdin.write(user_input.encode() + b'\n')
        process.stdin.flush()

        output = b""
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output += line
            if line.strip() == b"":
                break
        
        response = output.decode()
        print(f"Received response from Llama: {response}")
        return response
    
    except Exception as e:
        print(f"Error interacting with Llama: {e}")
        return None

# Function to handle AI responses
def handle_ai_response(response):
    requests = []
    parts = response.splitlines()
    for part in parts:
        if part.startswith("Dialogue:"):
            dialogue = part.split(":", 1)[1].strip().strip("'")
            speak_text(dialogue)
        elif part.startswith("Text:"):
            text = part.split(":", 1)[1].strip().strip("'")
            display_text(f"Llama: {text}")
        elif part.startswith("Requests:"):
            requests = part.split(":", 1)[1].strip().split(",")
    return requests

# Function to convert text to speech and mute the microphone during playback
def speak_text(text):
    global mic_muted
    original_mic_state = mic_muted
    
    # Mute the microphone
    if not mic_muted:
        toggle_mic_mute()
    
    tts = gTTS(text=text, lang='en')
    tts.save("response.mp3")
    
    # Use playsound to play the audio file and ensure the program waits for it to finish
    playsound.playsound("response.mp3", True)
    print(f"Spoken text: {text}")
    
    # Unmute the microphone if it was originally unmuted
    if not original_mic_state:
        toggle_mic_mute()

# Function to display text in the chat history
def display_text(text):
    chat_history.insert(tk.END, text + "\n")
    print(f"Displayed text: {text}")

# Function to capture microphone input and convert it to text
def listen_to_microphone():
    global mic_muted
    if mic_muted:
        print("Microphone is muted.")
        return None
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for audio...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized audio: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Error with the recognition service: {e}")
            return None

# Function to toggle microphone mute state
def toggle_mic_mute():
    global mic_muted
    mic_muted = not mic_muted
    status = "muted" if mic_muted else "unmuted"
    print(f"Microphone has been {status}.")

# Function to create the GUI for user input and display
def create_gui():
    root = tk.Tk()
    root.title("Llama Chat Interface")

    global chat_history
    chat_history = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
    chat_history.pack(padx=10, pady=10)

    user_input = tk.Entry(root, width=50)
    user_input.pack(padx=10, pady=5)

    def on_submit():
        prompt = user_input.get()
        if prompt:
            display_text(f"You: {prompt}")
            user_input.delete(0, tk.END)
            requests = interact_with_llama(llama_process, prompt)
            handle_requests_and_respond(requests, prompt)

    user_input.bind("<Return>", lambda event: on_submit())
    
    # Button to process audio input
    audio_button = tk.Button(root, text="Speak", command=process_audio_input)
    audio_button.pack(pady=10)

    # Button to toggle microphone mute state
    mute_button = tk.Button(root, text="Mute/Unmute Mic", command=toggle_mic_mute)
    mute_button.pack(pady=10)

    return root

# Function to process microphone input and send to AI
def process_audio_input():
    text_from_audio = listen_to_microphone()
    if text_from_audio:
        display_text(f"Microphone: {text_from_audio}")
        requests = interact_with_llama(llama_process, text_from_audio)
        handle_requests_and_respond(requests, text_from_audio)

# Function to handle requests and respond accordingly
def handle_requests_and_respond(requests, initial_prompt):
    # Prepare additional data if requested
    screen_image = ""
    camera_image = ""
    
    if 'screen' in requests:
        screen_image = capture_screenshot()
        display_text(f"Screen data captured at: {screen_image}")
        
    if 'camera' in requests:
        camera_image = capture_camera_image()
        display_text(f"Camera data captured at: {camera_image}")
        
    # Construct the new prompt with the requested data
    next_prompt = f"Text: '{initial_prompt}'\n"
    if screen_image:
        next_prompt += f"Screenshot: {screen_image}\n"
    if camera_image:
        next_prompt += f"Camera: {camera_image}\n"
    
    print(f"Constructed prompt: {next_prompt}")
    
    # Wait for AI to finish generating response
    time.sleep(120)
    response = interact_with_llama(llama_process, next_prompt)
    handle_ai_response(response)

# Function to capture a screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_path = "screenshot.png"
    screenshot.save(screenshot_path)
    print(f"Screenshot saved at: {screenshot_path}")
    return f"file://{os.path.abspath(screenshot_path)}"

# Function to capture an image from the camera
def capture_camera_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        camera_image_path = "camera_image.png"
        cv2.imwrite(camera_image_path, frame)
        print("Camera image captured.")
    cam.release()
    return f"file://{os.path.abspath(camera_image_path)}"

# Main function to run the program
def main():
    model_name = "llama3.1"  # Replace with your actual model name
    global llama_process
    llama_process = start_llama_model(model_name)

    initial_prompt = """
    Your current tracked task is 'dialogue only'.

    You will interact with the system using the following formats:

    **For Input Data (received from the user or the system):**
    - Dialogue: 'text from audio' or 'text prompt from user'
    - Text: 'text prompt from user'
    - Screenshot: [image]
    - Camera: [image]

    **For Output Data (generated by the AI):**
    - Dialogue: 'text to be spoken'
    - Text: 'text to be displayed'
    - Mouse: x position, y position, action  # Include only if needed for current prime directive, like moving the mouse
    - Keyboard: 'text to type'  # Include only if needed for current prime directive, like editing code
    - Requests: screen, camera  # Include only if needed for current prime directive, like knowing what the screen looks like

    The last three output fields are to be used at your own discretion, note you can recursively interact with the system through a feedback loop, structure your data requests and outputs according to your task.

    Please generate audio (using 'Dialogue') and text (using 'Text') responses separately. The system will handle these outputs independently, with audio being spoken to the user and text being displayed in the chat interface. Only include 'screen' or 'camera' in the 'Requests' field if these data types are required for the task you are currently tracking.
    Output the following in both the audio and text fields, using the provided output format: Hi, I am your Gadget1.0 assistant, please state my current prime directive.
    
    System will recursively send prompts, some may include no relevant data due to user absence. 
    """
    interact_with_llama(llama_process, initial_prompt)

    root = create_gui()
    root.mainloop()

    llama_process.terminate()

if __name__ == "__main__":
    main()