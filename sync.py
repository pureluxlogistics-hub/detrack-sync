import pickle
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
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token_file:
            creds = pickle.load(token_file)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token_file:
            pickle.dump(creds, token_file)
    service = build('calendar', 'v3', credentials=creds)
    return service

def sync_jobs():
    service = get_calendar_service()
    events_result = service.events().list(calendarId='primary', maxResults=10, orderBy='startTime', singleEvents=True, timeMin=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())).execute()
    events = events_result.get('items', [])
    for event in events:
        start = event.get('start', {})
        date = start.get('dateTime', start.get('date', ''))[:10]
        job_data = {
          'data': {
            'type': 'Delivery',
            'do_number': event.get('summary'),
            'date': date,
            'address': event.get('location', ''),
            'instructions': event.get('description', '')
        }
}
        response = requests.post(DETRACK_BASE_URL, json=job_data, headers={'X-API-KEY': DETRACK_API_KEY})
        print('Sent job:', event.get('summary'), '- Response:', response.status_code, response.text)

schedule.every(1).minutes.do(sync_jobs)

while True:
    schedule.run_pending()
    time.sleep(1)