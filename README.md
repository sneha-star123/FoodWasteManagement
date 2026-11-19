# Food Waste Reduction & Expiry Management System

## Project Description

Food Waste Reduction & Expiry Management System is a web-based application developed to help users manage food inventory, monitor expiry dates, track food consumption, record food wastage, and analyse food-related expenses.

The system helps users reduce unnecessary food waste by providing expiry tracking, low-stock alerts, waste analysis, shopping-list management, and data-based suggestions.

## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js

### Backend
- Python
- Flask

### Database
- SQLite

### Additional Modules
- Java - Inventory and expiry calculations
- C - Waste percentage, cost and savings calculations

## Main Features

- User Registration and Login
- Secure Password Hashing
- Food Inventory Management
- Add, Edit and Delete Food Items
- Automatic Expiry Status
- Expiry Tracking
- Food Consumption Tracking
- Low Stock Detection
- Food Waste Recording
- Waste Percentage Analysis
- Estimated Financial Loss Calculation
- Shopping List
- Recipe Suggestions
- Analytics Dashboard
- Charts and Statistics
- Personalised Food Management Insights
- User Profile
- Responsive Design

## Food Expiry Status

The system automatically calculates food status based on the expiry date.

- Fresh - More than 3 days remaining
- Expiring Soon - 0 to 3 days remaining
- Expired - Expiry date has passed

## Project Structure

FoodWasteSystem/
│
├── app.py
├── database.db
├── requirements.txt
├── README.md
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── add_food.html
│   ├── inventory.html
│   ├── expiry.html
│   ├── consumption.html
│   ├── waste.html
│   ├── shopping.html
│   ├── recipes.html
│   ├── analytics.html
│   └── profile.html
│
├── java/
│   └── InventoryExpiryLogic.java
│
└── c/
    └── WasteCalculator.c

## Database

The application uses SQLite to store:

- User information
- Food inventory
- Consumption records
- Waste records
- Shopping-list items
- Purchase history

## Installation

Open the project folder in VS Code.

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install the required packages:

pip install -r requirements.txt

## Run the Application

Start the Flask application:

python app.py

Open the following address in a browser:

http://127.0.0.1:5000

## Java Module

Go to the Java folder:

cd java

Compile:

javac InventoryExpiryLogic.java

Run:

java InventoryExpiryLogic

## C Module

Go to the C folder:

cd c

Compile:

gcc WasteCalculator.c -o WasteCalculator.exe

Run:

.\WasteCalculator.exe

## Future Scope

The system can be extended with Artificial Intelligence and Machine Learning features such as:

- Food consumption prediction
- Expiry risk prediction
- Food waste prediction
- Personalised recommendations
- Smart recipe generation
- Smart purchasing suggestions
- Consumption pattern analysis
- Food demand forecasting

## Expected Outcome

The proposed system provides a digital platform for managing food inventory and reducing food waste. It helps users monitor expiry dates, track consumption, identify waste patterns, control food-related expenses, and make better food-management decisions.

## Project Type

College-Level AIML Project

## Developed Using

Python, Flask, SQLite, HTML, CSS, JavaScript, Java and C.