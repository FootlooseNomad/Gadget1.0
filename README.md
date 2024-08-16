# Gadget1.0
      
      [!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!]
      [!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!]
      
AI assistant to automate ANY task

(Uses Ollama(llama3.1 by default)) 
      
      [!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!]
      [!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!]
      
1. Install python 3.x
2. Download Ollama
3. Run this command in cmd prompt: pip install subprocess32==3.5.4 os-sys==2.1.4 tkinter==0.1.0 SpeechRecognition==3.8.1 gTTS==2.2.3 Pillow==9.1.0 opencv-python==4.5.3.56 playsound==1.2.2 threading==0.1
4. Run this command in cmd prompt: cd directory\of\Gadget.py file(do not include "\Gadget.py" in the directory)

      [!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!]
      [!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!][!KNOWN TO BE UNCENSORED!!][!!!USE AT OWN DISCRETION!!!]

5. Run this command in the same cmd prompt window as previous step: python Gadget.py

6. REQUIRES INTENSE GRAPHICAL PROCESSING RESOURCES


In this release:

GUI Creation:
A GUI is created using tkinter to allow the user to interact with the system via text input, buttons for audio input, and control over the microphone (mute/unmute).
Voice Interaction:
The system can capture audio from the microphone using speech_recognition, convert it to text using Google's speech recognition API, and then send that text to the AI model for processing.

Text-to-Speech (TTS):
Responses from the AI can be converted to speech using the gTTS library and played back to the user. During playback, the microphone is muted to avoid interference.

AI Model Interaction:
The system interacts with the Llama AI model via the command line using the subprocess module. User inputs (from text or audio) are sent to the AI, and responses are processed accordingly.

Keyboard and Mouse Control:
The code uses the pynput library to simulate keyboard and mouse actions. The AI can control these peripherals based on the commands it generates.

Queue System:
User inputs are enqueued and processed in sequence. This ensures that multiple requests can be handled efficiently without overwhelming the system.

Debugging:
A debug mode is available, controlled by a global variable, that prints out detailed information about the system's operations for troubleshooting purposes.

Image Capture:
The system can capture screenshots and images from the camera. These images can be sent to the AI for processing as part of the interaction.

Threading:
The code uses threading to handle tasks concurrently, such as processing the queue of user inputs while maintaining the GUI's responsiveness.

Shutdown Handling:
The system handles clean shutdowns, ensuring that the AI model process is terminated correctly when the GUI is closed. 

Coming in the future:

Improved error handling and recovery mechanisms:
Saving and loading sessions with llama functionality. Subprocess crash handeling, recovery and monitoring.

OS utilization:
AI ability to call OS commandline commands, to speed up various system interactions. Commands will have to be sanitized to prevent damaging commands from accidentaly being processed.

More GUI elements:
Especialy regarding other new features

Multiple user voice detection and interpretation:
This step is crucial because the AI currently mutes the user microphone untill done speaking so as to not hear itself. This step will allow the AI to distinguish it's own input and ignore it.
Ability to interrupt the AI whilst it's speaking and for the AI to interpret where it was interrupted to dynamically reason with users and in general more dynamic conversation features.
