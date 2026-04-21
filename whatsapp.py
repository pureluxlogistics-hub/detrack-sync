from flask import Flask, request
import requests
import json
import re
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

app = Flask(__name__)

VERIFY_TOKEN = 'purelux123'
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
DETRACK_BASE_URL = 'https://app.detrack.com/api/v2/dn/jobs'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds_json = json.loads(os.environ.get('CREDENTIALS_JSON'))
    creds = service_account.Credentials.from_service_account_info(
        creds_json, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_calendar_event(job):
    try:
        service = get_calendar_service()
        event = {
            'summary': job.get('do_number', 'New Job'),
            'location': job.get('address', ''),
            'description': job.get('instructions', ''),
            'start': {
                'dateTime': job.get('date', '') + 'T' + job.get('job_time', '09:00') + ':00',
                'timeZone': 'Australia/Sydney',
            },
            'end': {
                'dateTime': job.get('date', '') + 'T' + job.get('job_time', '10:00') + ':00',
                'timeZone': 'Australia/Sydney',
            },
        }
        service.events().insert(calendarId='primary', body=event).execute()
        print('Calendar event created!')
    except Exception as e:
        print('Calendar error:', e)

def parse_job(text):
    job = {}
    for line in text.split('\n'):
        line = line.strip()
        if line.lower().startswith('name:'):
            job['do_number'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('date:'):
            job['date'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('time:'):
            job['job_time'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('pick up:'):
            job['address'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('instruction:'):
            job['instructions'] = line.split(':', 1)[1].strip()
    return job

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    try:
        messages = data['entry'][0]['changes'][0]['value']['messages']
        for message in messages:
            if message['type'] == 'text':
                text = message['text']['body']
                if 'name:' in text.lower() and 'date:' in text.lower():
                    job = parse_job(text)
                    if job:
                        create_calendar_event(job)
                        payload = {'data': job}
                        response = requests.post(
                            DETRACK_BASE_URL,
                            json=payload,
                            headers={'X-API-KEY': DETRACK_API_KEY}
                        )
                        print('Job created:', response.status_code, response.text)
    except Exception as e:
        print('Error:', e)
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
