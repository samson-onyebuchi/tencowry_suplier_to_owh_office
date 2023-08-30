import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from pymongo import MongoClient

import threading
import os

app = Flask(__name__)

try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client["Tencowry"]
    collection = db["Suppliers"]
except Exception as e:
    error_message = f"Error connecting to the database: {str(e)}"
    print(error_message)

# Email configuration
EMAIL_ADDRESS = 'nnadisamson63@gmail.com'
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def update_and_notify(order_id, data):
    # Update order status and location in the database
    updated_order = collection.find_one_and_update(
        {"_id": order_id},
        {"$set": {"status": data["status"], "location": data["location"]}},
        return_document=True
    )

    if not updated_order:
        return

    # Send email to customer
    customer_email = data['customer_email']
    customer_subject = 'Order Update'
    customer_body = f"Your order ({order_id}) status has been updated to {data['status']}."
    send_email(customer_email, customer_subject, customer_body)

    # Send email to admin
    admin_email = data['admin_email']
    admin_subject = 'Order Update'
    admin_body = f"Order ({order_id}) status has been updated to {data['status']}.\nLocation: {data['location']}"
    send_email(admin_email, admin_subject, admin_body)

    # Simulated logging
    print(f"Order {order_id} status updated: {data['status']} - Location: {data['location']}")



@app.route('/api/orders/<string:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()

    # Extract admin and customer email from the request body
    admin_email = data['admin_email']
    customer_email = data['customer_email']

    # Use threading to perform updates and notifications asynchronously
    thread = threading.Thread(target=update_and_notify, args=(order_id, data))
    thread.start()

    response = {
        'message': 'Order status has been successfully updated. Customer and admin notifications are in progress.'
    }

    return jsonify(response)

