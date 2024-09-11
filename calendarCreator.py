import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pdfAnalyzer import extract_text_from_pdf
from pdfAnalyzer import analyze_text_with_openai
import json
import re

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def createEvent(service, summary, description, start_datetime, end_datetime, location=None, attendees=None, isAllDay=False, recurrence=None):
    if isAllDay:
        event = {
            'summary': summary,
            'location': location if location else '',
            'description': description,
            'start': {
                'date': start_datetime.date().isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'date': end_datetime.date().isoformat() if end_datetime else (start_datetime + datetime.timedelta(days=1)).date().isoformat(),
                'timeZone': 'America/New_York',
            },
            'attendees': attendees if attendees else [],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 1440},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
    else:
        event = {
            'summary': summary,
            'location': location if location else '',
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'attendees': attendees if attendees else [],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 1440},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

    if recurrence:
        event['recurrence'] = [recurrence]
                               
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))
    except Exception as e:
        print(f"Failed to create event '{summary}': {e}")

def convertTextToJson(extractedText):
    events = []

    for line in extractedText.splitlines():
        line = line.strip()
        if not line:
            continue

        if "Lecture" in line or "Midterm" in line or "Exam" in line or "Assignment" in line or "Quiz" in line or "Lab" in line or "Tutorial" in line or "DGDS" in line:
            parts = line.split(": ", 2)
            if len(parts) > 2:
                summary = f"{parts[0]}: {parts[1].strip()}"
                date_time_str = parts[2].strip()

                date_time_parts = re.split(r",\s*(?=(?:[^:]+:\s*)?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", date_time_str)

                if len(date_time_parts) >= 2:
                    start_datetime_str = date_time_parts[-2]
                    end_datetime_str = date_time_parts[-1]

                    try:
                        if "T" in start_datetime_str and "T" in end_datetime_str:
                            
                            start_datetime = datetime.datetime.fromisoformat(start_datetime_str)
                            end_datetime = datetime.datetime.fromisoformat(end_datetime_str)

                            recurrence = None
                            if "Lecture" in summary or 'Tutorial' in summary or "DGD's" in summary or "Lab" in summary:
                                recurrence = 'RRULE:FREQ=WEEKLY;COUNT=15'

                            event = {
                                "summary": summary,
                                "location": "In Person",
                                "description": "Lecture or Midterm Session",
                                "start": {
                                    "dateTime": start_datetime.isoformat(),
                                    "timeZone": "America/New_York"
                                },
                                "end": {
                                    "dateTime": end_datetime.isoformat(),
                                    "timeZone": "America/New_York"
                                },
                                "recurrence": [recurrence] if recurrence else [],
                                "reminders": {
                                    "useDefault": False,
                                    "overrides": [
                                        {"method": "email", "minutes": 1440},
                                        {"method": "popup", "minutes": 10}
                                    ]
                                }
                            }
                            events.append(event)
                        else:
                        
                            start_date = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d")
                            end_date = start_date + datetime.timedelta(days=1)

                            event = {
                                "summary": summary,
                                "location": "In Person",
                                "description": f"{summary} - All-Day Event",
                                "start": {
                                    "date": start_date.strftime("%Y-%m-%d"),
                                    "timeZone": "America/New_York"
                                },
                                "end": {
                                    "date": end_date.strftime("%Y-%m-%d"),
                                    "timeZone": "America/New_York"
                                },
                                "reminders": {
                                    "useDefault": False,
                                    "overrides": [
                                        {"method": "email", "minutes": 1440},
                                        {"method": "popup", "minutes": 10}
                                    ]
                                }
                            }
                            events.append(event)
                    except ValueError as e:
                        print(f"Error parsing date/time for event '{summary}': {e}")
                        continue
                else:
                    print(f"Skipping line with no valid datetime found: {line}")
                    continue

        elif any(keyword in line for keyword in ["Date not specified", "Time not specified", "to be scheduled", "to be determined"]):
            print(f"Skipping event with unspecified date or time: {line}")
            continue
        else:
            print(f"Skipping line with unknown format: {line}")

    return json.dumps(events, indent=4)


def main(pdfPath):
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)

    text = extract_text_from_pdf(pdfPath)
    
    if not text.strip():
        print("No text found in the PDF.")
        return

    extractedText = analyze_text_with_openai(text)
    print("OpenAI API Response:", extractedText)

    if not extractedText.strip() or extractedText == "{}":
        print("The API response is empty or invalid. Please check the input text or API settings.")
        return

    eventsJson = convertTextToJson(extractedText)
    print("Events JSON:", eventsJson)

    try:
        eventDetails = json.loads(eventsJson)

        for event in eventDetails:
            summary = event.get('summary', 'No summary provided')
            description = event.get('description', 'No description provided')

            if 'dateTime' in event.get('start', {}):
                start_datetime = datetime.datetime.fromisoformat(event['start']['dateTime'])
                end_datetime = datetime.datetime.fromisoformat(event['end']['dateTime']) if 'dateTime' in event.get('end', {}) else (start_datetime + datetime.timedelta(hours=1))
                recurrence = 'RRULE:FREQ=WEEKLY;COUNT=15' if "Lecture" in summary or 'Tutorial' in summary or "DGD's" in summary or "Lab" in summary else None  
                print(f"Creating event: {summary}, Start: {start_datetime}, End: {end_datetime}, Recurrence: {recurrence}")  #
                createEvent(service, summary, description, start_datetime, end_datetime, event.get('location'), event.get('attendees'), recurrence=recurrence)
            elif 'date' in event.get('start', {}):
                start_date = datetime.datetime.fromisoformat(event['start']['date'])
                start_datetime = datetime.datetime.combine(start_date, datetime.time(23, 0))
                end_datetime = start_datetime + datetime.timedelta(hours=1)
                print(f"Creating all-day event: {summary}, Start: {start_datetime}, End: {end_datetime}")
                createEvent(service, summary, description, start_datetime, end_datetime, event.get('location'), event.get('attendees'), isAllDay=True)

    except json.JSONDecodeError as e:
        print(f"JSON decoding failed: {e}")

if __name__ == '__main__':
    main('/Users/joshuafong/Desktop/Projects/calendarCreator/2024-Fall-Term-CEG-2136-A00-Computer-Architecture-I.pdf')
