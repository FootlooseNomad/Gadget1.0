import select
import json
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
prompt_queue = queue.PriorityQueue()
keyboard = Controller()

# Delta time for smoother operations
delta_time = 0.05  # 50ms sleep time between checks

def main():
    global llama_process
    model_name = "llama3.1"  # Replace with your actual model name

    # Start the Llama model
    llama_process = start_llama_model(model_name)

    # Create the GUI
    root = create_gui()

    # Load previous session if available
    load_session()

    # Start the queue processing in a separate thread
    queue_thread = threading.Thread(target=process_queue, daemon=True)  # Daemon thread ends with main thread
    queue_thread.start()

    # Initial prompt to be sent to Llama model
    initial_prompt = """You are 'Gadget', version 1.0
Made by Tobias Jacob du Preez (using llama3.1 made by Meta)

You and the system will interact using the following formats:

**For Input Data (received from the user or the system):**
- Audio: 'spoken text from audio' 
- Text: 'text prompt from user'
- Screenshot: [image]
- Camera: [image]

**For Output Data (How you can respond(You can include multiple response types under one another as neccesary, the system sepparates some format fields into their respective parramaters)):**
- Audio: 'text to be spoken' #This is the initial response method to the users 'Audio:' input field, switch to 'Text' output format, or back, as per user request.
- Text: 'text to be displayed' #Always respond to user 'Text' input field with this respective 'Text' output format
- Mouse: x position, y position, action  # Include only if needed for current prime directive, like moving the mouse
- Keyboard: 'text to type'  # Include only if needed for current prime directive, like editing code
- HoldKey: 'key name' #To hold down a specific key, like 'Shift' or 'Ctrl' or any key. You can use this to play games like a human would.
- ReleaseKey: 'key name' #To release a specific key previously held down
- Requests: screen(When you have a task, this request can be used recursively to keep you informed of your work as it will call a function that shows you the screen. Remember to wait for programs to open and load before sending interactive output. When you finished the last task the user assigned to you, you may stop sending this request.), camera(only when relevant to task) 

The last three output fields are to be used at your own discretion, note you can interact with the system through the parameters of the keyboard and mouse fields, structure your data requests and outputs according to your task. Remember to wait for programs to open and load before interacting accordingly.

Please generate audio (using 'Audio') and text (using 'Text') responses separately. The system will handle these outputs independently, with audio being spoken to the user and text being displayed in the chat interface. Only include 'camera' in the 'Requests' field if it is required for the task you are currently tracking.
Output the following in both the audio and text fields, using the provided output format: Hi, I am your Gadget1.0 assistant, please state my current prime directive.
    
System will recursively send prompts, some may include no relevant data due to user absence.
Once you completed with a task, inform the user when they become present.
"""
    
    enqueue_prompt(initial_prompt)  # Enqueue the initial prompt

    # Start the Tkinter main loop
    root.mainloop()

def start_llama_model(model_name):
    try:
        # Use the full path to the Ollama executable
        command = rf"C:\Users\Tobias\AppData\Local\Programs\Ollama\Ollama.exe run {model_name}"
        
        # Start the subprocess without shell=True, using the full path
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
        debug("Llama model started successfully.")
        return process
    except Exception as e:
        debug(f"Failed to start Llama model: {e}")
        return None

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
            enqueue_prompt(prompt, priority=1)  # Highest priority for text input

    user_input.bind("<Return>", lambda event: on_submit())
    
    # Button to process audio input
    audio_button = tk.Button(root, text="Speak", command=process_audio_input)
    audio_button.pack(pady=10)

    # Button to toggle microphone mute state
    mute_button = tk.Button(root, text="Mute/Unmute Mic", command=toggle_mic_mute)
    mute_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", on_close)  # Register the on_close function for the close event

    return root

def process_queue():
    global prompt_queue
    while True:
        try:
            priority, prompt = prompt_queue.get(timeout=5)  # Get item from the queue
            response = interact_with_llama(llama_process, prompt)
            handle_ai_response(response)  # Process the AI response with the priority queue
        except queue.Empty:
            debug("Queue is empty, continuing...")
        except Exception as e:
            debug(f"Error processing queue: {e}")
        time.sleep(delta_time)

def enqueue_prompt(prompt, priority=3):
    global prompt_queue
    prompt_queue.put((priority, prompt))  # Add the priority to the queue item
    debug(f"Prompt added to queue with priority {priority}: {prompt}")

# Primary Interaction Functions

def interact_with_llama(process, user_input):
    if process is None:
        debug("Llama process is not running (process is None).")
        return None

    # Log process status before interaction
    process_status = process.poll()
    if process_status is not None:
        debug(f"Llama process has already terminated with status {process_status}.")
        return None
    else:
        debug("Llama process is running (before sending input).")

    try:
        debug(f"Sending input to Llama: {user_input}")
        process.stdin.write(user_input.encode() + b'\n')
        process.stdin.flush()

        output, error = process.communicate(timeout=30)  # Increased timeout to 30 seconds

        if output:
            response = output.decode()
            debug(f"Received response from Llama: {response}")
        if error:
            debug(f"Error from Llama: {error.decode()}")

    except subprocess.TimeoutExpired:
        debug("Timeout expired while waiting for Llama's response.")
        process.kill()
        response = None

    except OSError as e:
        debug(f"Error interacting with Llama (OSError): {e}")
        response = None

    except Exception as e:
        debug(f"Unexpected error interacting with Llama: {e}")
        response = None

    # Log process status after interaction
    process_status = process.poll()
    if process_status is not None:
        debug(f"Llama process has terminated with status {process_status} (after interaction).")
    else:
        debug("Llama process is still running (after interaction).")

    return response

def handle_ai_response(response):
    if response is None:
        debug("Received None response from Llama. Skipping processing.")
        return

    response_queue = queue.PriorityQueue()  # Create a priority queue for handling responses
    
    parts = response.splitlines()
    for part in parts:
        if part.startswith("Text:"):
            text = part.split(":", 1)[1].strip().strip("'")
            response_queue.put((1, ("text", text)))  # Text has the highest priority
        elif part.startswith("Audio:"):
            audio = part.split(":", 1)[1].strip().strip("'")
            response_queue.put((2, ("audio", audio)))  # Audio has the second highest priority
        elif part.startswith("Mouse:") or part.startswith("Keyboard:"):
            command = part.split(":", 1)[1].strip()
            response_queue.put((3, ("command", command)))  # Commands have the third priority
        elif part.startswith("Requests:"):
            requests = part.split(":", 1)[1].strip().split(",")
            for request in requests:
                if request == "screen":
                    response_queue.put((4, ("screen", None)))  # Screen capture requests have the fourth priority
                elif request == "camera":
                    response_queue.put((4, ("camera", None)))  # Camera requests have the fourth priority

    # Process the queued responses based on their priority
    while not response_queue.empty():
        priority, (response_type, data) = response_queue.get()
        
        if response_type == "text":
            display_text(f"Llama: {data}")
        elif response_type == "audio":
            speak_text(data)
        elif response_type == "command":
            command_parts = data.split(",")
            for cmd in command_parts:
                key_action = cmd.strip().split()
                if len(key_action) == 3:  # Mouse command
                    x_pos = int(key_action[0].strip())
                    y_pos = int(key_action[1].strip())
                    action = key_action[2].strip()
                    move_mouse(x_pos, y_pos, action)
                elif len(key_action) == 2:  # Keyboard command
                    key = key_action[0].strip()
                    action = key_action[1].strip().lower()
                    if action == "press":
                        hold_key(key)
                    elif action == "release":
                        release_key(key)
        elif response_type == "screen":
            capture_screenshot()
        elif response_type == "camera":
            capture_camera_image()

def process_audio_input():
    text_from_audio = listen_to_microphone()
    if text_from_audio:
        display_text(f"Microphone: {text_from_audio}")
        enqueue_prompt(text_from_audio, priority=2)  # Medium priority for voice input

# GUI and User Interaction Helpers

def on_close():
    global llama_process
    debug("Closing the application...")
    
    try:
        if llama_process and llama_process.poll() is None:  # Check if the process is still running
            shutdown_prompt = "System shutdown initiated. Prepare to halt."
            interact_with_llama(llama_process, shutdown_prompt)
    except Exception as e:
        debug(f"Error during shutdown interaction: {e}")
    
    save_session()
    
    # Terminate the subprocess if it's still running
    if llama_process and llama_process.poll() is None:
        llama_process.terminate()
        llama_process.wait()  # Ensure complete termination of the subprocess

    #Close the GUI window
    root.destroy()
    debug("Application closed.")

def display_text(text):
    chat_history.insert(tk.END, text + "\n")
    debug(f"Displayed text: {text}")

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

# Auxiliary Functions

def speak_text(text):
    def speak():
        global mic_muted
        original_mic_state = mic_muted

        if not mic_muted:
            toggle_mic_mute()

        tts = gTTS(text=text, lang='en')
        tts.save("response.mp3")

        playsound.playsound("response.mp3", True)
        debug(f"Spoken text: {text}")

        if not original_mic_state:
            toggle_mic_mute()

    threading.Thread(target=speak).start()

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

def hold_key(keyToPress):
    global keyboard
    key = getattr(Key, keyToPress, keyToPress)  # Dynamically get the key attribute or use the string if not found in Key
    keyboard.press(key)
    print(f"Holding down {keyToPress} key.")

def release_key(keyToRelease):
    global keyboard
    key = getattr(Key, keyToRelease, keyToRelease)  # Dynamically get the key attribute or use the string if not found in Key
    keyboard.release(key)
    print(f"Released {keyToRelease} key.")

def toggle_mic_mute():
    global mic_muted
    mic_muted = not mic_muted
    status = "muted" if mic_muted else "unmuted"
    debug(f"Microphone has been {status}.")

# Utility and Debugging

def debug(message):
    if debug_mode:
        print(f"DEBUG: {message}")

def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_path = "screenshot.png"
    screenshot.save(screenshot_path)
    debug(f"Screenshot saved at: {screenshot_path}")
    return f"file://{os.path.abspath(screenshot_path)}"

def capture_camera_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        camera_image_path = "camera_image.png"
        cv2.imwrite(camera_image_path, frame)
        debug("Camera image captured.")
    cam.release()
    return f"file://{os.path.abspath(camera_image_path)}"

def save_session(filename="session_data.json"):
    session_data = {
        "chat_history": chat_history.get(1.0, tk.END).strip()  # Get all chat history
        # Add more data here if needed
    }
    
    with open(filename, 'w') as f:
        json.dump(session_data, f)
    print(f"Session saved to {filename}")

def load_session(filename="session_data.json"):
    try:
        with open(filename, 'r') as f:
            session_data = json.load(f)
        
        # Load chat history
        chat_history.insert(tk.END, session_data.get("chat_history", ""))
        print(f"Session loaded from {filename}")
        
    except FileNotFoundError:
        print("No session file found, starting fresh.")

if __name__ == "__main__":
    main()