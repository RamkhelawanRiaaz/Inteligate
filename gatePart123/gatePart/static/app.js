// Initialize arrays to store registered persons and cars
let registeredPersons = JSON.parse(localStorage.getItem('registeredPersons')) || [];
let registeredCars = JSON.parse(localStorage.getItem('registeredCars')) || [];

// Function to register a person
function registerPerson() {
    const name = document.getElementById('person-name').value;
    const email = document.getElementById('person-email').value;
    const phone = document.getElementById('person-phone').value;

    if (name && email && phone) {
        const person = { name, email, phone };
        registeredPersons.push(person);
        localStorage.setItem('registeredPersons', JSON.stringify(registeredPersons));
        alert('Person registered successfully.');
    } else {
        alert('Please fill in all fields.');
    }
}

// Function to remove a registered person
function removePerson(index) {
    registeredPersons.splice(index, 1);
    localStorage.setItem('registeredPersons', JSON.stringify(registeredPersons));
    loadRegisteredPersons();
}

// Function to load and display registered persons
function loadRegisteredPersons() {
    const tableBody = document.getElementById('persons-table-body');
    tableBody.innerHTML = '';

    registeredPersons.forEach((person, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${person.name}</td>
            <td>${person.email}</td>
            <td>${person.phone}</td>
            <td><button class="btn btn-danger" onclick="removePerson(${index})">Remove</button></td>
        `;
        tableBody.appendChild(row);
    });
}

// Function to register a car
function registerCar() {
    const licensePlate = document.getElementById('car-license-plate').value;
    const brand = document.getElementById('car-brand').value;
    const model = document.getElementById('car-model').value;
    const color = document.getElementById('car-color').value;

    if (licensePlate && brand && model && color) {
        const car = { licensePlate, brand, model, color };
        registeredCars.push(car);
        localStorage.setItem('registeredCars', JSON.stringify(registeredCars));
        alert('Car registered successfully.');
    } else {
        alert('Please fill in all fields.');
    }
}

// Function to remove a registered car
function removeCar(index) {
    registeredCars.splice(index, 1);
    localStorage.setItem('registeredCars', JSON.stringify(registeredCars));
    loadRegisteredCars();
}

// Function to load and display registered cars
function loadRegisteredCars() {
    const tableBody = document.getElementById('cars-table-body');
    tableBody.innerHTML = '';

    registeredCars.forEach((car, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${car.licensePlate}</td>
            <td>${car.brand}</td>
            <td>${car.model}</td>
            <td>${car.color}</td>
            <td><button class="btn btn-danger" onclick="removeCar(${index})">Remove</button></td>
        `;
        tableBody.appendChild(row);
    });
}

// Call loadRegisteredPersons function when the view-persons page is loaded
if (location.pathname.endsWith('view-persons.html')) {
    loadRegisteredPersons();
}

// Call loadRegisteredCars function when the view-cars page is loaded
if (location.pathname.endsWith('view-cars.html')) {
    loadRegisteredCars();
}

function showSignUp() {
    location.href = 'signup.html';
}

function showLogin() {
    location.href = 'index.html';
}

function signUp() {
    const email = document.getElementById('signup-email').value;
    const phone = document.getElementById('signup-phone').value;
    const password = document.getElementById('signup-password').value;

    if (email && phone && password) {
        alert('Signed up successfully! Proceeding to license registration.');
        location.href = 'license.html';
    } else {
        alert('Please fill in all fields.');
    }
}

function registerLicensePlate() {
    const licensePlate = document.getElementById('license-plate').value;

    if (licensePlate) {
        alert('License plate registered successfully! Proceeding to face image upload.');
        location.href = 'face-upload.html';
    } else {
        alert('Invalid license plate format.');
    }
}

function uploadFaceImage() {
    const faceImage = document.getElementById('face-image').files[0];

    if (faceImage) {
        alert('Face image uploaded successfully! Proceeding to dashboard.');
        location.href = 'dashboard.html';
    } else {
        alert('Please upload a clear face image.');
    }
}

function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    if (email && password) {
        alert('Logged in successfully! Proceeding to dashboard.');
        location.href = 'dashboard.html';
    } else {
        alert('Invalid login credentials.');
    }
}

function logout() {
    location.href = 'index.html';
}
