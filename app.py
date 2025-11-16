"""
McDonald's NYC - Times Square Contact Form Backend
Flask application to handle contact form submissions via Telegram Bot API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from html import escape
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Telegram Bot API Configuration (Placeholder variables)
# Replace these with your actual Bot Token and Chat ID
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def sanitize_input(text):
    """
    Sanitize user input to prevent XSS attacks and clean the data.
    Removes potentially dangerous characters and HTML tags.
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Escape special HTML characters
    text = escape(text)
    
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Strip whitespace
    text = text.strip()
    
    return text


def validate_email(email):
    """
    Validate email format using regex.
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone):
    """
    Validate phone number format (optional field).
    Accepts various formats with digits, spaces, dashes, parentheses, and + sign.
    """
    if not phone:
        return True  # Phone is optional
    
    # Remove common phone formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if remaining characters are digits
    return cleaned.isdigit() and len(cleaned) >= 10


def format_message_for_telegram(name, email, phone, message):
    """
    Format the contact form data into a readable Telegram message.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    telegram_message = f"""
🔔 *New Contact Form Submission*

📅 *Date:* {timestamp}
📍 *Location:* McDonald's NYC - Times Square

👤 *Name:* {name}
📧 *Email:* {email}
📱 *Phone:* {phone if phone else 'Not provided'}

💬 *Message:*
{message}

---
This message was sent from the McDonald's Times Square contact form.
"""
    
    return telegram_message


@app.route('/submit', methods=['POST'])
def submit_contact_form():
    """
    Handle POST request from contact form.
    Validate, sanitize, and send data via Telegram Bot API.
    """
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validate required fields
        validation_errors = []
        
        if not name:
            validation_errors.append("Name is required")
        elif len(name) < 2:
            validation_errors.append("Name must be at least 2 characters long")
        elif len(name) > 100:
            validation_errors.append("Name must be less than 100 characters")
        
        if not email:
            validation_errors.append("Email is required")
        elif not validate_email(email):
            validation_errors.append("Invalid email format")
        
        if not message:
            validation_errors.append("Message is required")
        elif len(message) < 10:
            validation_errors.append("Message must be at least 10 characters long")
        elif len(message) > 1000:
            validation_errors.append("Message must be less than 1000 characters")
        
        # Validate optional phone field
        if phone and not validate_phone(phone):
            validation_errors.append("Invalid phone number format")
        
        # Return validation errors if any
        if validation_errors:
            return jsonify({
                'success': False,
                'message': 'Validation errors: ' + ', '.join(validation_errors)
            }), 400
        
        # Sanitize all input
        name = sanitize_input(name)
        email = sanitize_input(email)
        phone = sanitize_input(phone) if phone else ""
        message = sanitize_input(message)
        
        # Check if Telegram credentials are configured
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
            return jsonify({
                'success': False,
                'message': 'Server configuration error: Telegram Bot Token or Chat ID not configured'
            }), 500
        
        # Format message for Telegram
        telegram_message = format_message_for_telegram(name, email, phone, message)
        
        # Send message via Telegram Bot API
        telegram_payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': telegram_message,
            'parse_mode': 'Markdown'
        }
        
        try:
            telegram_response = requests.post(
                TELEGRAM_API_URL,
                json=telegram_payload,
                timeout=10  # 10 second timeout
            )
            
            telegram_response.raise_for_status()
            
            # Check if Telegram API returned success
            if telegram_response.json().get('ok'):
                return jsonify({
                    'success': True,
                    'message': 'Thank you! Your message has been sent successfully. We will get back to you soon.'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to send message. Please try again later.'
                }), 500
                
        except requests.exceptions.RequestException as e:
            # Log the error (in production, use proper logging)
            print(f"Telegram API error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to send message. Please try again later.'
            }), 500
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'McDonald\'s NYC - Times Square Contact Form API'
    }), 200


if __name__ == '__main__':
    # Run the Flask app
    # In production, use a production WSGI server like Gunicorn or uWSGI
    app.run(debug=True, host='0.0.0.0', port=5000)

