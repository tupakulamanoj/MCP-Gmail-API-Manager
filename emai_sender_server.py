import base64
import mimetypes
import os
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("EmailSender")


@mcp.tool()
def send_email(toaddress: str, subject: str, body: str, filename: str = None):
    """
    Send an email with optional file attachment.

    Args:
        toaddress (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): Text content of the email.
        filename (str): Optional path to a file to attach.

    Returns:
        dict: Sent message object.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()

        # Set main email headers and content
        message["To"] = toaddress
        message["From"] = "manojthupakula06080@gmail.com"
        message["Subject"] = subject
        message.set_content(body)

        # Handle file attachment (if any)
        if filename and os.path.exists(filename):
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type is None:
                mime_type = "application/octet-stream"
            maintype, subtype = mime_type.split("/", 1)

            with open(filename, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(filename)
                message.add_attachment(file_data, maintype, subtype, filename=file_name)

        # Encode and send the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )

        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None

    return send_message


if __name__ == "__main__":
    mcp.run()
