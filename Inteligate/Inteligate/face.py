from flask import Flask, request, redirect, flash, render_template_string
import numpy as np
import cv2
import base64
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with your actual secret key

# Mock registered users and function for saving users
registered_users = [{'name': 'user1', 'welcome': False}]

def save_registered_users(users):
    pass  # Implement this function to save user data

# Inline template for login.html
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
            # Process the base64 encoded image
            image_data = face_data.split(',')[1]
            nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_np is not None:
                # Recognize
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]

                    for user in registered_users:
                        registered_img = cv2.imread(f'registered_faces/{user["name"]}.jpg', 0)
                        if registered_img is None:
                            continue
                        
                        res = cv2.matchTemplate(roi_gray, registered_img, cv2.TM_CCOEFF_NORMED)
                        threshold = 0.6
                        loc = np.where(res >= threshold)

                        if len(loc[0]) > 0:
                            user['welcome'] = True
                            save_registered_users(registered_users)
                            flash(f"Face recognized! Welcome {user['name']}.")

                            # Send a signal to the ESP32
                            try:
                                print("Sending request to ESP32...") # Debugging statement
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
    print("Available routes:")
    print(app.url_map)  # Print the URL map for debugging
    app.run(debug=True)
