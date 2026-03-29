import pickle
import base64
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import requests
import schedule
import time

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
DETRACK_API_KEY = '337a57672f55b3d71d1ab5ea0adfd2c668d3fbff2ec10a35'
DETRACK_BASE_URL = 'https://app.detrack.com/api/v2/dn/jobs'

def get_calendar_service():
    creds = None
    token_b64 = os.environ.get('TOKEN_PICKLE_B64')
    if token_b64:
        token_data = base64.b64decode(token_b64)
        creds = pickle.loads(token_data)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    service = build('calendar', 'v3', credentials=creds)
    return service

def job_exists(do_number):
    response = requests.get(DETRACK_BASE_URL + '/' + do_number, headers={'X-API-KEY': DETRACK_API_KEY})
    return response.status_code == 200

def sync_jobs():
    service = get_calendar_service()
    events_result = service.events().list(calendarId='primary', maxResults=50, orderBy='startTime', singleEvents=True, timeMin=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())).execute()
    events = events_result.get('items', [])
    for event in events:
        do_number = event.get('summary')
        if job_exists(do_number):
            print('Skipping (already exists):', do_number)
            continue
        start = event.get('start', {})
        date = start.get('dateTime', start.get('date', ''))[:10]
        job_data = {
            'data': {
                'type': 'Delivery',
                'do_number': do_number,
                'date': date,
                'address': event.get('location', ''),
                'instructions': event.get('description', '')
            }
        }
        response = requests.post(DETRACK_BASE_URL, json=job_data, headers={'X-API-KEY': DETRACK_API_KEY})
        print('Sent job:', do_number, '- Response:', response.status_code, response.text)

schedule.every(1).minutes.do(sync_jobs)

while True:
    schedule.run_pending()
    time.sleep(1)