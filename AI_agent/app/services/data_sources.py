from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import pickle
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GmailSource:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        if not self.credentials_path:
            raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable not set")
        self.creds = None

    def authenticate(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

    def fetch_emails(self, days_back: int = 7) -> List[Dict[str, Any]]:
        self.authenticate()
        service = build('gmail', 'v1', credentials=self.creds)
        
        # Calculate date range
        date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        query = f'after:{date}'
        
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        emails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            emails.append({
                'id': msg['id'],
                'subject': next((header['value'] for header in msg['payload']['headers'] 
                               if header['name'] == 'Subject'), ''),
                'body': msg['snippet'],
                'date': next((header['value'] for header in msg['payload']['headers'] 
                            if header['name'] == 'Date'), '')
            })
        
        return emails

class SlackSource:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def fetch_messages(self, channel_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        try:
            # Calculate timestamp for days_back
            oldest = (datetime.now() - timedelta(days=days_back)).timestamp()
            
            result = self.client.conversations_history(
                channel=channel_id,
                oldest=oldest
            )
            
            messages = []
            for msg in result['messages']:
                messages.append({
                    'id': msg['ts'],
                    'text': msg['text'],
                    'user': msg.get('user', ''),
                    'date': datetime.fromtimestamp(float(msg['ts'])).isoformat()
                })
            
            return messages
            
        except SlackApiError as e:
            print(f"Error fetching messages: {e.response['error']}")
            return [] 