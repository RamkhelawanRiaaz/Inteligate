import cv2
import torch
from ultralytics import YOLO
import pytesseract
import os
import mysql.connector
import subprocess

# Specify the Tesseract executable path
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
            else:
                print(f"License plate {license_plate_text} not found in the database.")
            break

        cv2.imshow('YOLOv8 Live Video', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    run_code()
