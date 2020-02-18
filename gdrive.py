from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import argparse

# If modifying these scopes, delete the file token.pickle.
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES) #client_secrets_file
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--release.dir', dest='release_dir', help='path to release folder', required=True)
    parser.add_argument('--app.name', dest='app_name', help='app name that will be used as file name', required=True)
    parser.add_argument('--changelog.file', dest='changelog_file', help='path to changelog file', required=True)
    parser.add_argument('--template.file', dest='template_file', help='path to email template file', required=True)
    # parser.add_argument('--dropbox.token', dest='dropbox_token', help='dropbox access token', required=True)
    # parser.add_argument('--dropbox.folder', dest='dropbox_folder', help='dropbox target folder', required=True)
    parser.add_argument('--zapier.hook', dest='zapier_hook', help='zapier email web hook', required=True)
    parser.add_argument('--zapier.authprefix', dest='zapier_auth_prefix', help='zapier email web hook prefix',required=True)
    parser.add_argument('--zapier.auth', dest='zapier_auth', help='zapier email web hook key', required=True)
    parser.add_argument('--email.to', dest='email_to', help='email recipients', required=True)
    parser.add_argument('--client_secrets.file', dest='release_dir', help='path to release folder', required=True)

    options = parser.parse_args()
    main()