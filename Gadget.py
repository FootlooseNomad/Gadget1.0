import pyautogui
import subprocess
import os
import tkinter as tk
from tkinter import scrolledtext
import speech_recognition as sr
from gtts import gTTS
from PIL import ImageGrab
import cv2
import time
import playsound
import threading
import queue
from pynput.keyboard import Controller, Key

# Global variables
mic_muted = False
debug_mode = True  # Set to False to disable debug messages
prompt_queue = queue.Queue()
keyboard = Controller()

# Debug function
def debug(message):
    if debug_mode:
        print(f"DEBUG: {message}")

# Function to hold down a key
def hold_key(keyToPress):
    global keyboard
    key = getattr(Key, keyToPress, keyToPress)  # Dynamically get the key attribute or use the string if not found in Key
    keyboard.press(key)
    print(f"Holding down {keyToPress} key.")

# Function to release a key
def release_key(keyToRelease):
    global keyboard
    key = getattr(Key, keyToRelease, keyToRelease)  # Dynamically get the key attribute or use the string if not found in Key
    keyboard.release(key)
    print(f"Released {keyToRelease} key.")

# Function to start the Llama model using the command prompt
def start_llama_model(model_name):
    command = f"ollama run {model_name}"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    debug("Llama model started successfully.")
    return process

# Function to interact with Llama
def interact_with_llama(process, user_input):
    try:
        debug(f"Sending input to Llama: {user_input}")
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
        debug(f"Received response from Llama: {response}")
        return response
    
    except Exception as e:
        debug(f"Error interacting with Llama: {e}")
        return None

# Function to handle AI responses
def handle_ai_response(response):
    requests = []
    parts = response.splitlines()
    for part in parts:
        if part.startswith("Audio:"):
            audio = part.split(":", 1)[1].strip().strip("'")
            speak_text(audio)
        elif part.startswith("Text:"):
            text = part.split(":", 1)[1].strip().strip("'")
            display_text(f"Llama: {text}")
        elif part.startswith("Requests:"):
            requests = part.split(":", 1)[1].strip().split(",")
        elif part.startswith("Mouse:"):
            mouse_params = part.split(":", 1)[1].strip().split(",")
            x_pos = int(mouse_params[0].strip())
            y_pos = int(mouse_params[1].strip())
            action = mouse_params[2].strip()
            move_mouse(x_pos, y_pos, action)
        elif part.startswith("Keyboard:"):
            keyboard_params = part.split(":", 1)[1].strip().split(",")
            for param in keyboard_params:
                key_action = param.strip().split()
                key = key_action[0].strip()
                action = key_action[1].strip().lower()

                if action == "press":
                    hold_key(key)
                elif action == "release":
                    release_key(key)

    return requests

# Function to enqueue prompts
def enqueue_prompt(prompt):
    global prompt_queue #Access the global prompt_queue variable
    prompt_queue.put(prompt)
    debug(f"Prompt added to queue: {prompt}")

# Function to process the prompt queue
def process_queue():
    global prompt_queue #Access the global prompt_queue variable
    while True:
        if not prompt_queue.empty():
            prompt = prompt_queue.get()
            response = interact_with_llama(llama_process, prompt)
            handle_ai_response(response)
        else:
            time.sleep(1)  # Sleep briefly to avoid busy-waiting

# Function to move the mouse based on AI instructions
def move_mouse(x, y, action):
    if action == "move":
        pyautogui.moveTo(x, y)
        debug(f"Mouse moved to ({x}, {y})")
    elif action == "click":
        pyautogui.click(x, y)
        debug(f"Mouse clicked at ({x}, {y})")
    elif action == "drag":
        pyautogui.dragTo(x, y, duration=0.5)  # Duration can be adjusted
        debug(f"Mouse dragged to ({x}, {y})")

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
    debug(f"Spoken text: {text}")
    
    # Unmute the microphone if it was originally unmuted
    if not original_mic_state:
        toggle_mic_mute()

# Function to display text in the chat history
def display_text(text):
    chat_history.insert(tk.END, text + "\n")
    debug(f"Displayed text: {text}")

# Function to capture microphone input and convert it to text
def listen_to_microphone():
    global mic_muted
    if mic_muted:
        debug("Microphone is muted.")
        return None
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        debug("Listening for audio...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            debug(f"Recognized audio: {text}")
            return text
        except sr.UnknownValueError:
            debug("Could not understand the audio.")
            return None
        except sr.RequestError as e:
            debug(f"Error with the recognition service: {e}")
            return None

# Function to toggle microphone mute state
def toggle_mic_mute():
    global mic_muted
    mic_muted = not mic_muted
    status = "muted" if mic_muted else "unmuted"
    debug(f"Microphone has been {status}.")

# Function to create the GUI for user input and display
def create_gui():
    global root
    root = tk.Tk()
    root.title("Llama Chat Interface")

    # Chat history text box
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
            enqueue_prompt(prompt)  # Enqueue the prompt instead of sending it directly

    user_input.bind("<Return>", lambda event: on_submit())
    
    # Button to process audio input
    audio_button = tk.Button(root, text="Speak", command=process_audio_input)
    audio_button.pack(pady=10)

    # Button to toggle microphone mute state
    mute_button = tk.Button(root, text="Mute/Unmute Mic", command=toggle_mic_mute)
    mute_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", on_close)  # Register the on_close function for the close event

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
    if 'screen' in requests:
        screen_image = capture_screenshot()
        display_text(f"Screen data captured at: {screen_image}")
        next_prompt = f"Screenshot: {screen_image}\n"
        response = interact_with_llama(llama_process, next_prompt)
        handle_ai_response(response)
        
    if 'camera' in requests:
        camera_image = capture_camera_image()
        display_text(f"Camera data captured at: {camera_image}")
        next_prompt = f"Camera: {camera_image}\n"
        response = interact_with_llama(llama_process, next_prompt)
        handle_ai_response(response)

# Function to capture a screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_path = "screenshot.png"
    screenshot.save(screenshot_path)
    debug(f"Screenshot saved at: {screenshot_path}")
    return f"file://{os.path.abspath(screenshot_path)}"

# Function to capture an image from the camera
def capture_camera_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        camera_image_path = "camera_image.png"
        cv2.imwrite(camera_image_path, frame)
        debug("Camera image captured.")
    cam.release()
    return f"file://{os.path.abspath(camera_image_path)}"

# Function to move the mouse based on AI instructions
def move_mouse(x, y, action):
    if action == "move":
        # Code to move the mouse to (x, y)
        debug(f"Moving mouse to ({x}, {y})")

# Function to handle window close event
def on_close():
    global llama_process
    print("Closing the application...")
    
    # Notify AI about shutdown
    shutdown_prompt = "System shutdown initiated. Prepare to halt."
    interact_with_llama(llama_process, shutdown_prompt)
    
    llama_process.terminate()  # Ensure llama process is terminated
    
    root.destroy()  # Close the GUI window
    print("Application closed.")

# Main function to run the program
def main():
    global llama_process
    model_name = "llama3.1"  # Replace with your actual model name
    llama_process = start_llama_model(model_name)
    root = create_gui()
    root.mainloop()

    # Start the queue processing in a separate thread
    queue_thread = threading.Thread(target=process_queue)
    queue_thread.start()


    initial_prompt = """
    You are 'Gadget', version 1.0 made by Tobias Jacob du Preez, using llama3.1 made by Meta.

    You will interact with the system using the following formats:

    **For Input Data (received from the user or the system):**
    - Audio: 'spoken text from audio' 
    - Text: 'text prompt from user'
    - Screenshot: [image]
    - Camera: [image]

    **For Output Data (generated by the AI(You)):**
    - Audio: 'text to be spoken' #This is the initial response method to the users 'Audio:' input field, switch to 'Text' output format, or back, as per user request.
    - Text: 'text to be displayed' #Always respond to user 'Text' input field with this respective 'Text' output format
    - Mouse: x position, y position, action  # Include only if needed for current prime directive, like moving the mouse
    - Keyboard: 'text to type'  # Include only if needed for current prime directive, like editing code
    - HoldKey: 'key name' #To hold down a specific key, like 'Shift' or 'Ctrl' or any key. You can use this to play games like a human would.
    - ReleaseKey: 'key name' #To release a specific key previously held down
    - Requests: screen(When you have a task, this request can be used recursively to keep you informed of your work as it will call a function that shows you the screen. Remeber towait for programs to open and load before sending interactive output. When you finished the last task the user assigned to you, you may stop sending this request.), camera(only when relevant to task) 

    The last three output fields are to be used at your own discretion, note you can interact with the system through the parrameters of the keyboard and mouse fields, structure your data requests and outputs according to your task remember to wait for programs to open and load before interacting accordingly.

    Please generate audio (using 'Audio') and text (using 'Text') responses separately. The system will handle these outputs independently, with audio being spoken to the user and text being displayed in the chat interface. Only include 'camera' in the 'Requests' field if it is required for the task you are currently tracking.
    Output the following in both the audio and text fields, using the provided output format: Hi, I am your Gadget1.0 assistant, please state my current prime directive.
    
    System will recursively send prompts, some may include no relevant data due to user absence.
    Once you completed with a task, inform the user when they become present.
    """
    enqueue_prompt(initial_prompt)  # Enqueue the initial prompt

if __name__ == "__main__":
    main()