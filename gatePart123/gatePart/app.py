import cv2
import torch
from ultralytics import YOLO
import pytesseract
import os
import mysql.connector
import subprocess
from flask import Flask, request, redirect, flash, render_template_string
import numpy as np
import base64
import requests
import json
import shutil

# Flask app setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with your actual secret key

# Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Load the YOLOv8 model
model = YOLO('templates/model/best.pt')  # Replace with your model path

# Initialize video capture with IP camera
cap = cv2.VideoCapture('http://192.168.1.21:8080/video')  # Corrected IP address format

# Ensure the 'images' directory exists
if not os.path.exists('images'):
    os.makedirs('images')

frame_count = 0
saved_image_count = 0
max_images = 5  # Maximum number of images to save

registered_users = [{'name': 'user1', 'welcome': False}]

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="dbintelligate"
    )

def check_license_plate_in_db(plate_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accountcars WHERE Kentekennummer = %s", (plate_number,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def read_license_plate_with_subprocess(image_path):
    # Run tesseract using subprocess and capture the output
    command = [pytesseract.pytesseract.tesseract_cmd, image_path, 'stdout', '--psm', '8']
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

def recognize_face():
    cap.release()  # Release the license plate capture
    cap_face = cv2.VideoCapture(0)  # Initialize video capture for face recognition (0 for default camera)

    while True:
        ret, frame = cap_face.read()
        if not ret:
            print("Failed to grab frame for face recognition")
            break

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        print(f"Detected faces: {faces}")  # Debug: Check if faces are detected

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]

            for user in registered_users:
                registered_img_path = f'C:/Users/User/Desktop/working facial rec with storage and turning servo/gatePart123/gatePart/registered_faces_copy/{user["name"]}.jpg'
                print(f"Checking registered image for {user['name']} at path: {registered_img_path}")  # Debug
                
                if not os.path.exists(registered_img_path):
                    print(f"Registered image for {user['name']} not found.")
                    continue

                registered_img = cv2.imread(registered_img_path, 0)
                if registered_img is None:
                    print(f"Failed to read image for {user['name']} at path: {registered_img_path}")
                    continue

                print(f"Matching face for {user['name']}")
                res = cv2.matchTemplate(roi_gray, registered_img, cv2.TM_CCOEFF_NORMED)
                threshold = 0.5  # Try a lower threshold
                loc = np.where(res >= threshold)
                print(f"Template matching result locations: {loc}")

                if len(loc[0]) > 0:
                    print(f"Face recognized for {user['name']}")
                    user['welcome'] = True
                    save_registered_users(registered_users)
                    flash(f"Face recognized! Welcome {user['name']}.")

                    try:
                        response = requests.get('http://192.168.1.44/servo?position=90')
                        if response.status_code == 200:
                            print("Servo moved to 90 degrees successfully.")
                        else:
                            print("Failed to move servo. Status code:", response.status_code)
                    except Exception as e:
                        print(f"Error sending request to ESP32: {e}")

                    return True

        cv2.imshow('Face Recognition', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap_face.release()
    cv2.destroyAllWindows()
    return False

def run_code():
    global frame_count, saved_image_count

    while saved_image_count < max_images:
        ret, frame = cap.read()

        if not ret:
            print("Failed to grab frame")
            break

        print(f"Processing frame {frame_count}")

        results = model(frame)
        print("Detection results:", results)

        if not results or len(results[0].boxes) == 0:
            print("No results from model")
            continue

        annotated_frame = results[0].plot()

        for result in results[0].boxes:
            if saved_image_count >= max_images:
                break
            
            x1, y1, x2, y2 = map(int, result.xyxy[0].tolist())
            cropped_plate = frame[y1:y2, x1:x2]
            cropped_image_path = f'images/license_plate_{frame_count}.png'
            cv2.imwrite(cropped_image_path, cropped_plate)
            frame_count += 1
            saved_image_count += 1

            gray = cv2.cvtColor(cropped_plate, cv2.COLOR_BGR2GRAY)
            _, binary_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            preprocessed_image_path = f'images/license_plate_{frame_count}_preprocessed.png'
            cv2.imwrite(preprocessed_image_path, binary_image)

            license_plate_text = read_license_plate_with_subprocess(preprocessed_image_path)
            license_plate_text = ''.join(filter(str.isalnum, license_plate_text))
            print("Detected License Plate Text:", license_plate_text)

            result = check_license_plate_in_db(license_plate_text)
            if result:
                print(f"License plate {license_plate_text} found in the database.")
                if recognize_face():  # Call face recognition
                    return True  # Return True to indicate overall success

            print(f"License plate {license_plate_text} not found in the database.")

        cv2.imshow('YOLOv8 Live Video', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False  # Return False if no plate found or max images processed

def save_registered_users(users):
    with open('registered_users.json', 'w') as file:
        json.dump(users, file)
    shutil.copy('registered_users.json', 'C:/Users/User/Desktop/working facial rec with storage and turning servo/gatePart123/gatePart/registered_users.json')

login_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        #videoElement {
            width: 30%;
            height: 40%;
        }
    </style>
</head>
<body>
    <h1>Login</h1>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul>
        {% for category, message in messages %}
          <li class="{{ category }}">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <video id="videoElement" autoplay></video>
    <br>
    <button onclick="captureImage()">Capture Image</button>
    <br><br>
    <form action="{{ url_for('index') }}" method="post">
        <input type="hidden" id="faceData" name="faceData">
        <br><br>
        <input type="submit" value="Login">
    </form>

    <script>
        var video = document.getElementById('videoElement');

        function startVideoStream() {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(stream) {
                    video.srcObject = stream;
                    video.play();
                })
                .catch(function(err) {
                    console.log("An error occurred: " + err);
                });
        }

        function captureImage() {
            var canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            var imageDataURL = canvas.toDataURL('image/jpeg');
            document.getElementById('faceData').value = imageDataURL;
        }

        window.onload = function() {
            startVideoStream();
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        face_data = request.form['faceData']

        if face_data:
            image_data = face_data.split(',')[1]
            nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_np is not None:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                print(f"Detected faces: {faces}")  # Debug: Check if faces are detected

                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]

                    for user in registered_users:
                        registered_img_path = f'C:/Users/User/Desktop/working facial rec with storage and turning servo/gatePart123/gatePart/registered_faces_copy/{user["name"]}.jpg'
                        print(f"Checking registered image for {user['name']} at path: {registered_img_path}")  # Debug
                        
                        if not os.path.exists(registered_img_path):
                            print(f"Registered image for {user['name']} not found.")
                            continue

                        registered_img = cv2.imread(registered_img_path, 0)
                        if registered_img is None:
                            print(f"Failed to read image for {user['name']} at path: {registered_img_path}")
                            continue

                        print(f"Matching face for {user['name']}")
                        res = cv2.matchTemplate(roi_gray, registered_img, cv2.TM_CCOEFF_NORMED)
                        threshold = 0.5
                        loc = np.where(res >= threshold)
                        print(f"Template matching result locations: {loc}")

                        if len(loc[0]) > 0:
                            user['welcome'] = True
                            save_registered_users(registered_users)
                            flash(f"Face recognized! Welcome {user['name']}.")

                            try:
                                response = requests.get('http://192.168.1.44/servo?position=90')
                                if response.status_code == 200:
                                    print("Servo moved to 90 degrees successfully.")
                                else:
                                    print("Failed to move servo. Status code:", response.status_code)
                            except Exception as e:
                                print(f"Error sending request to ESP32: {e}")

                            return redirect('/')
                
                flash("Face not recognized. Please try again.")
                return redirect('/')
            else:
                flash("Failed to decode image. Please try again.")
                return redirect('/')
        else:
            flash("No image data received. Please capture an image.")
            return redirect('/')

    return render_template_string(login_template)

if __name__ == '__main__':
    found_in_db = run_code()
    if not found_in_db:
        print("No license plate found in the database.")
    app.run(debug=True)
