from flask import Flask, render_template, request, redirect, flash, url_for, session
import os
import json
import mysql.connector
from threading import Thread
import cv2
import numpy as np
import base64
import requests
from mysql.connector import Error
from mysql.connector import errorcode
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Ensure the directory for storing registered faces exists
if not os.path.exists('registered_faces'):
    os.makedirs('registered_faces')

# JSON file to store registered users
users_file = 'registered_users.json'

# Load registered users from JSON file
def load_registered_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

# Save registered users to JSON file
def save_registered_users(users):
    with open(users_file, 'w') as file:
        json.dump(users, file)
    # Save a copy to another directory
    shutil.copy(users_file, 'C:/Users/User/Desktop/working facial rec with storage and turning servo/gatePart123/gatePart/registered_users.json')

# Ensure registered_users is initialized as a list
registered_users = load_registered_users()
if not isinstance(registered_users, list):
    registered_users = []

# Function to save face image and its copy
def save_face_image(name, img_np):
    img_path = os.path.join('registered_faces', f'{name}.jpg')
    
    # Save the image to the 'registered_faces' directory
    success = cv2.imwrite(img_path, img_np)
    if success:
        print(f"Image saved successfully at {img_path}")  # Debugging statement
    else:
        print(f"Failed to save image at {img_path}")  # Debugging statement
    
    # Verify the source image exists
    if os.path.exists(img_path):
        print(f"Source image {img_path} exists.")  # Debugging statement
        
        # Ensure the target directory exists
        target_dir = 'C:/Users/User/Desktop/working facial rec with storage and turning servo/gatePart123/gatePart/registered_faces_copy'
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Target directory {target_dir} created.")  # Debugging statement
        
        # Construct the target path
        target_path = os.path.join(target_dir, f'{name}.jpg')
        try:
            shutil.copy(img_path, target_path)
            print(f"Image copied to {target_path}")  # Debugging statement
        except Exception as e:
            print(f"Failed to copy image to {target_path}: {e}")  # Debugging statement
    else:
        print(f"Source image {img_path} does not exist.")

# Function to get a database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="dbintelligate"
    )

@app.route('/')
def index():
    return render_template('index.html', users=registered_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        face_data = request.form['faceData']
        project_name = request.form['projectName']
        voornaam = request.form['voornaam']
        achternaam = request.form['achternaam']
        username = request.form['username']
        wachtwoord = request.form['wachtwoord']
        email = request.form['email']
        kentekennummer = request.form['Kentekennummer']
        merk = request.form['Merk']
        model = request.form['Model']
        kleur = request.form['Kleur']

        if face_data:
            try:
                # Process the base64 encoded image
                image_data = face_data.split(',')[1]
                nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
                img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if img_np is not None:
                    # Save the image using the save_face_image function
                    save_face_image(name, img_np)

                    # Database operations
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    # Start transaction
                    cursor.execute("START TRANSACTION")

                    # Insert project information
                    cursor.execute("INSERT INTO projectinfo (ProjectNaam) VALUES (%s)", (project_name,))
                    project_id = cursor.lastrowid

                    # Insert user information
                    cursor.execute(
                        """INSERT INTO personaccount 
                        (ProjectID, Voornaam, Achternaam, Username, wachtwoord, Email) 
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                        (project_id, voornaam, achternaam, username, wachtwoord, email)
                    )

                    # Get the user ID
                    account_id = cursor.lastrowid

                    # Insert car information
                    cursor.execute(
                        """INSERT INTO accountcars 
                        (AccountOwner, Kentekennummer, automerk, model, kleur) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        (account_id, kentekennummer, merk, model, kleur)
                    )

                    # Commit transaction
                    conn.commit()
                    cursor.close()
                    conn.close()

                    # Add user to registered users list and save to file
                    registered_users.append({'name': name, 'welcome': False})
                    save_registered_users(registered_users)

                    flash("Registration successful!")
                    return redirect(url_for('index'))
                else:
                    flash("Failed to decode image. Please try again.")
                    return redirect('/register')
            except mysql.connector.Error as err:
                # Rollback transaction on error
                conn.rollback()
                flash(f"Database error: {err}")
                return redirect('/register')
            except Exception as e:
                # Handle any other exceptions
                flash(f"Error: {str(e)}")
                return redirect('/register')
        else:
            flash("No image data received. Please try again.")
            return redirect('/register')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    username = session.get('username')  # Get the username from the session

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch subperson accounts with owner's full name for the logged-in user
    cursor.execute("""
        SELECT spa.PersonID, spa.AccountOwner, spa.SubPersonVoornaam, spa.SubPersonAchternaam,
               CONCAT(pa.Voornaam, ' ', pa.Achternaam) AS OwnerFullName
        FROM subpersonaccount spa
        JOIN personaccount pa ON spa.AccountOwner = pa.AccountID
        WHERE pa.Username = %s
    """, (username,))
    subperson_accounts = cursor.fetchall()

    # Fetch account cars with owner's full name for the logged-in user
    cursor.execute("""
        SELECT ac.AutoID, ac.AccountOwner, ac.Kentekennummer, ac.automerk, ac.model, ac.kleur,
               CONCAT(pa.Voornaam, ' ', pa.Achternaam) AS OwnerFullName
        FROM accountcars ac
        JOIN personaccount pa ON ac.AccountOwner = pa.AccountID
        WHERE pa.Username = %s
    """, (username,))
    account_cars = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('dashboard.html', username=username, subperson_accounts=subperson_accounts, account_cars=account_cars)

@app.route('/register-car')
def register_car():
    return render_template('register-car.html')

@app.route('/register-person')
def register_person():
    return render_template('register-person.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the username from the session
    flash("You have been logged out.")
    return redirect(url_for('login'))

@app.route('/logout_dashboard')
def logout_dashboard():
    session.pop('username', None)  # Clear the username from the session
    flash("You have been logged out.")
    return redirect(url_for('index'))  # Redirect to the index page

@app.route('/registercar', methods=['GET', 'POST'])
def registercar():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        brand = request.form['brand']
        model = request.form['model']
        color = request.form['color']

        username = session.get('username')
        if not username:
            flash("You need to be logged in to register a car.", 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Retrieve account ID of the logged-in user
            cursor.execute("SELECT AccountID FROM personaccount WHERE Username = %s", (username,))
            result = cursor.fetchone()
            if result:
                account_id = result[0]

                # Fetch all rows to clear the result set
                while cursor.nextset():
                    pass

                # Print the captured form data for debugging
                print(f"AccountID: {account_id}, License Plate: {license_plate}, Brand: {brand}, Model: {model}, Color: {color}")

                # Insert car data into accountcars table
                cursor.execute("""
                    INSERT INTO accountcars (AccountOwner, Kentekennummer, automerk, model, kleur)
                    VALUES (%s, %s, %s, %s, %s)
                """, (account_id, license_plate, brand, model, color))

                # Commit the transaction
                conn.commit()

                # Clear the form fields
                license_plate = ""
                brand = ""
                model = ""
                color = ""

                flash("Car registered successfully.", 'success')
            else:
                flash("Account not found. Please log in and try again.", 'error')
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('registercar.html')

@app.route('/registersubperson', methods=['GET', 'POST'])
def registersubperson():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']

        username = session.get('username')
        if not username:
            flash("You need to be logged in to register a person.", 'error')
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Retrieve account ID of the logged-in user
            cursor.execute("SELECT AccountID FROM personaccount WHERE Username = %s", (username,))
            result = cursor.fetchone()
            if result:
                account_id = result[0]

                # Fetch all rows to clear the result set
                while cursor.nextset():
                    pass

                # Print the captured form data for debugging
                print(f"AccountID: {account_id}, First Name: {first_name}, Last Name: {last_name}, Email: {email}, Phone Number: {phone_number}")

                # Insert subperson data into subpersonaccount table
                cursor.execute("""
                    INSERT INTO subpersonaccount (AccountOwner, SubPersonVoornaam, SubPersonAchternaam, Email, PhoneNumber)
                    VALUES (%s, %s, %s, %s, %s)
                """, (account_id, first_name, last_name, email, phone_number))

                # Commit the transaction
                conn.commit()

                # Clear the form fields
                first_name = ""
                last_name = ""
                email = ""
                phone_number = ""

                flash("Person registered successfully.", 'success')
            else:
                flash("Account not found. Please log in and try again.", 'error')
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('registersubperson.html')

if __name__ == '__main__':
    app.run(debug=True)
