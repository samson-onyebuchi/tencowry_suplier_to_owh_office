import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

import threading
import os

app = Flask(__name__)

try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["Tencowry"]
    collection = db["Suppliers"]
except Exception as e:
    error_message = f"Error connecting to the database: {str(e)}"
    db = None  # Define db even in case of an exception

# Email configuration
EMAIL_ADDRESS = 'nnadisamson63@gmail.com'
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        error_message = f"Error sending email: {str(e)}"

def update_and_notify(order_id, data):
    try:
        if db is None:
            raise Exception("Database connection error")

        # Check if the order_id exists in the database
        existing_order = db.collection.find_one({"_id": ObjectId(order_id)})
        if existing_order:
            # Update order status and location in the database
            updated_order = db.collection.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"status": data["status"], "location": data["location"]}}
            )

            if updated_order.matched_count == 0:
                return (f"Failed to update order with order_id {order_id} in the database")
        else:
            raise Exception(f"Order with order_id {order_id} not found in the database")
        
        # Send emails and logging logic...
        # You can add your email and logging logic here

        return "Order status has been successfully updated. Customer and admin notifications are in progress."
    except Exception as e:
        error_message = str(e)
        raise Exception(error_message)

@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()

    # Extract admin and customer email from the request body
    admin_email = data['admin_email']
    customer_email = data['customer_email']

    try:
        # Use threading to perform updates and notifications asynchronously
        thread = threading.Thread(target=update_and_notify, args=(order_id, data))
        thread.start()

        return jsonify({'message': 'Order status has been successfully updated. Customer and admin notifications are in progress.'})
    except Exception as e:
        error_message = str(e)
        return jsonify({'error': 'Internal server error', 'message': error_message}), 500

