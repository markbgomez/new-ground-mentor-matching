#!/usr/bin/env python3
"""
Gmail OAuth Authorization Script
Performs a one-time desktop OAuth flow for mgomez@project127.org requesting the gmail.send scope.
Stores the resulting refresh token JSON in Secret Manager under 'gmail-sender-oauth'.
"""
import os
import json
import sys

def main():
    print("=== Gmail OAuth Authorization Flow ===")
    client_secret_path = os.environ.get("GMAIL_CLIENT_SECRET", "infra/client_secret.json")
    if not os.path.exists(client_secret_path):
        print(f"Error: {client_secret_path} not found.")
        print("Please download Desktop OAuth client credentials from Google Cloud Console")
        print("and save as infra/client_secret.json, or export GMAIL_CLIENT_SECRET=/path/to/secret.json")
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.cloud import secretmanager
    except ImportError:
        print("Required packages missing. Installing google-auth-oauthlib and google-cloud-secret-manager...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth-oauthlib", "google-cloud-secret-manager"])
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.cloud import secretmanager

    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    project_id = os.environ.get("GCP_PROJECT", "new-ground-mentor-matching")
    client = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{project_id}/secrets/gmail-sender-oauth"

    payload = json.dumps(token_data).encode("UTF-8")
    response = client.add_secret_version(
        request={"parent": secret_path, "payload": {"data": payload}}
    )
    print(f"Successfully updated Secret Manager secret! New version: {response.name}")
    print("Demo mode reminder: All emails will be redirected to mgomez@project127.org.")

if __name__ == "__main__":
    main()
