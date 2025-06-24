from flask import Flask, render_template, jsonify, request
import webbrowser
import threading
import time
import json
import os
from datetime import datetime
from src.gmail_client import GmailClient
from src.llm_service import LLMService
from config.config import MAX_EMAILS_TO_PROCESS

app = Flask(__name__)

DATA_FILE = 'emails_data.json'

def load_emails():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_emails(emails):
    with open(DATA_FILE, 'w') as f:
        json.dump(emails, f, indent=2)

def simple_categorize_email(subject, content):
    text = f"{subject} {content}".lower()
    categories = []
    CATEGORIES = {
        'IMPORTANT': ['urgent', 'important', 'critical', 'asap'],
        'DEADLINE': ['deadline', 'due', 'by', 'before'],
        'ACTION_REQUIRED': ['action required', 'please respond', 'needs your attention'],
        'MEETING': ['meeting', 'schedule', 'appointment', 'call']
    }
    for category, keywords in CATEGORIES.items():
        if any(keyword.lower() in text for keyword in keywords):
            categories.append(category)
    return categories

def simple_summarize_email(content):
    sentences = content.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 1:
        summary = f"{sentences[0]}... {sentences[-1]}"
    elif len(sentences) == 1:
        summary = sentences[0]
    else:
        summary = "No content to summarize"
    if len(summary) > 200:
        summary = summary[:200] + "..."
    return summary

def process_email_with_llm(email_data, llm_service):
    """Process a single email with LLM-powered analysis."""
    if not email_data:
        return None

    subject = email_data.get('subject', '')
    content = email_data.get('content', '')
    sender = email_data.get('from', '')
    from_name = email_data.get('from_name', '')
    from_email = email_data.get('from_email', '')

    print(f"[DEBUG] Processing email with LLM: {subject[:50]}...")

    importance_level = llm_service.classify_email_importance(subject, content)
    summary = simple_summarize_email(content)
    deadlines = []
    has_deadline = False
    important_links = []
    attachments_mentioned = []

    print(f"[DEBUG] LLM Analysis - Importance: {importance_level}")
    print(f"[DEBUG] Summary: {summary[:100]}...")

    return {
        'id': email_data.get('id'),
        'subject': subject,
        'from': sender,
        'from_name': from_name,
        'from_email': from_email,
        'importance_level': importance_level,
        'deadlines': deadlines,
        'summary': summary,
        'important_links': important_links,
        'attachments_mentioned': attachments_mentioned,
        'is_important': importance_level == 'Very Important',
        'has_deadline': has_deadline,
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def process_email_simple(email_data):
    if not email_data:
        return None
    subject = email_data.get('subject', '')
    content = email_data.get('content', '')
    sender = email_data.get('from', '')
    from_name = email_data.get('from_name', '')
    from_email = email_data.get('from_email', '')
    categories = simple_categorize_email(subject, content)
    summary = simple_summarize_email(content)
    return {
        'id': email_data.get('id'),
        'subject': subject,
        'from': sender,
        'from_name': from_name,
        'from_email': from_email,
        'categories': categories,
        'deadlines': [],
        'summary': summary,
        'is_important': 'IMPORTANT' in categories,
        'has_deadline': 'DEADLINE' in categories,
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process-emails', methods=['POST'])
def process_emails():
    try:
        save_emails([])
        gmail_client = GmailClient()
        print("[DEBUG] Initializing LLM service...")
        llm_service = LLMService()
        use_llm = llm_service.api_key is not None
        if use_llm:
            print("[DEBUG] Using LLM-powered processing")
        else:
            print("[DEBUG] API key not found, using simple processing")
        print("[DEBUG] Authenticating with Gmail API...")
        gmail_client.authenticate()
        print("[DEBUG] Fetching unread messages...")
        messages = gmail_client.list_messages(
            query='is:unread in:inbox', max_results=MAX_EMAILS_TO_PROCESS)
        processed_emails = []
        for message in messages:
            print(f"[DEBUG] Processing message ID: {message['id']}")
            full_message = gmail_client.get_message(message['id'])
            if not full_message:
                continue
            email_data = gmail_client.get_message_content(full_message)
            print("DEBUG EMAIL DATA:", email_data)
            if not email_data:
                continue
            if use_llm:
                processed_data = process_email_with_llm(email_data, llm_service)
            else:
                processed_data = process_email_simple(email_data)
            if not processed_data:
                continue
            processed_emails.append(processed_data)
        save_emails(processed_emails)
        processing_method = "LLM-powered" if use_llm else "Simple"
        return jsonify({
            'success': True,
            'message': f'Processed {len(processed_emails)} emails using {processing_method} analysis',
            'emails': processed_emails,
            'method': processing_method
        })
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing emails: {str(e)}'
        }), 500

@app.route('/api/emails')
def get_emails():
    try:
        emails = load_emails()
        email_list = []
        for email in emails:
            email_list.append({
                'id': email['id'],
                'subject': email['subject'],
                'from': email.get('from', ''),
                'from_name': email.get('from_name', ''),
                'from_email': email.get('from_email', ''),
                'is_important': email['is_important'],
                'has_deadline': email['has_deadline'],
                'categories': email['categories'],
                'processed_at': email['processed_at']
            })
        return jsonify({
            'success': True,
            'emails': email_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading emails: {str(e)}'
        }), 500

@app.route('/api/email/<email_id>')
def get_email_summary(email_id):
    try:
        emails = load_emails()
        email = next((e for e in emails if e['id'] == email_id), None)
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email not found'
            }), 404
        return jsonify({
            'success': True,
            'email': email
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading email: {str(e)}'
        }), 500

def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("🚀 Starting Gmail Intelligent Processor (LLM Version)...")
    print("🌐 Opening web browser...")
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    app.run(debug=True, use_reloader=False)
