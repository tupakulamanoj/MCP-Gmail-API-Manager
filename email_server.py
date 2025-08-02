import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import json
import re
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

mcp = FastMCP("EmailServer")

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly","https://www.googleapis.com/auth/gmail.send"]


def get_gmail_messages():
    """Shows basic usage of the Gmail API.
    Returns the user's top 100 Gmail messages as JSON.
    """
    print("[DEBUG] Starting Gmail API authentication...")
    creds = None
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists("token.json"):
        print("[DEBUG] Found existing token.json")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        print("[DEBUG] No token.json found")
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print("[DEBUG] Credentials invalid or missing")
        if creds and creds.expired and creds.refresh_token:
            print("[DEBUG] Refreshing expired credentials")
            creds.refresh(Request())
        else:
            print("[DEBUG] Starting OAuth flow")
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("credentials.json file not found. Please download it from Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        print("[DEBUG] Credentials saved")

    try:
        print("[DEBUG] Building Gmail service...")
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        
        print("[DEBUG] Fetching messages list...")
        # Get top 100 messages
        results = service.users().messages().list(
            userId="me", 
            maxResults=100
        ).execute()
        messages = results.get("messages", [])
        
        print(f"[DEBUG] Found {len(messages)} messages")

        if not messages:
            return {
                "status": "success", 
                "count": 0, 
                "messages": [], 
                "debug_info": "No messages found in Gmail"
            }

        emails_data = []
        
        for i, message in enumerate(messages[:100], 1):  # Limit to 10 for debugging
            try:
                print(f"[DEBUG] Processing message {i}/{len(messages[:10])}")
                # Get full message details
                msg = service.users().messages().get(
                    userId="me", 
                    id=message["id"],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipient')
                
                # Create email object
                email_obj = {
                    "email_number": i,
                    "message_id": message['id'],
                    "thread_id": msg.get('threadId', ''),
                    "subject": subject,
                    "from": sender,
                    "to": to,
                    "date": date,
                    "snippet": msg.get('snippet', 'No snippet available'),
                    "labels": msg.get('labelIds', []),
                    "size_estimate": msg.get('sizeEstimate', 0)
                }
                
                emails_data.append(email_obj)
                
            except HttpError as msg_error:
                print(f"[DEBUG] Error processing message {i}: {msg_error}")
                emails_data.append({
                    "email_number": i,
                    "message_id": message['id'],
                    "error": str(msg_error)
                })
                continue

        # Return as dict (not JSON string)
        result = {
            "status": "success",
            "count": len(emails_data),
            "messages": emails_data,
            "debug_info": f"Successfully processed {len(emails_data)} messages"
        }
        
        print(f"[DEBUG] Returning result with {len(emails_data)} messages")
        return result

    except HttpError as error:
        print(f"[DEBUG] Gmail API error: {error}")
        return {
            "status": "error",
            "error": str(error),
            "count": 0,
            "messages": [],
            "debug_info": f"Gmail API error: {str(error)}"
        }
    except Exception as e:
        print(f"[DEBUG] Unexpected error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "count": 0,
            "messages": [],
            "debug_info": f"Unexpected error: {str(e)}"
        }

@mcp.tool()
def get_emails_tool() -> dict:
    """
    A tool that returns the user's top 100 Gmail messages as a dictionary.
    Returns a structured response with email data including subjects, senders, dates, and snippets.
    """
    print("[TOOL DEBUG] get_emails_tool() called")
    try:
        result = get_gmail_messages()
        print(f"[TOOL DEBUG] Tool returning: status={result.get('status')}, count={result.get('count')}")
        return result
    except Exception as e:
        print(f"[TOOL DEBUG] Exception in tool: {e}")
        return {
            "status": "error",
            "error": str(e),
            "count": 0,
            "messages": [],
            "debug_info": f"Tool exception: {str(e)}"
        }

if __name__ == "__main__":
    print("[DEBUG] Starting MCP server...")
    mcp.run()