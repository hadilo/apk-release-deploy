from __future__ import print_function

import io
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import argparse
from apiclient import errors

# If modifying these scopes, delete the file token.pickle.
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

def callback(request_id, response, exception):
    if exception:
        print(exception)
    else:
        print("Permission Id: %s" % response.get('id'))

def shareFile(drive_service, file_id, email):
    batch = drive_service.new_batch_http_request(callback=callback)
    user_permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    batch.add(drive_service.permissions().create(
            fileId=file_id,
            body=user_permission,
            fields='id',
    ))
    batch.execute()

def delete_file(drive_service, file_id):
  """Permanently delete a file, skipping the trash.
  Args:
    service: Drive API service instance.
    file_id: ID of the file to delete.
  """
  try:
    drive_service.files().delete(fileId=file_id).execute()
  except errors.HttpError as error:
    print('An error occurred: %s' % error)

def download(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

def upload(drive_service, name, file):
    file_metadata = {'name': name}
    media = MediaFileUpload(file)
    file = drive_service.files().create(body=file_metadata,media_body=media,fields='id').execute()
    print('File ID: %s' % file.get('id'))

# Call the Drive v3 API
def getListAll(drive_service):
    results = drive_service.files().list(pageSize=10, fields="files(id, name, webContentLink, webViewLink)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(item)


if __name__ == '__main__':
    from google.oauth2 import service_account

    # SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'service.json'
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # delegated_credentials = credentials.with_subject('devhadi@gmail.com')
    drive_service = build('drive', 'v3', credentials=credentials)

    getListAll(drive_service)

    # download(drive_service, "1HwwsnULoutorJWR3LVf7eZVgNWkKkXyC")

    # delete_file(drive_service, "1HwwsnULoutorJWR3LVf7eZVgNWkKkXyC")

