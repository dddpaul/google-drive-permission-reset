from __future__ import print_function
import os.path
import pickle
import argparse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def process_files(service, folder_id):
    # Get files in the folder
    file_results = service.files().list(
        q="'{}' in parents".format(folder_id),
        pageSize=1000, fields="nextPageToken, files(id, name, permissions)").execute()
    file_items = file_results.get('files', [])

    if not file_items:
        print('No files found in the folder.')
    else:
        print('Files:')
        for item in file_items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
            permissions = item.get('permissions', [])
            for perm in permissions:
                if perm['type'] == 'anyone':
                    try:
                        service.permissions().delete(
                            fileId=item['id'],
                            permissionId=perm['id']
                        ).execute()
                        print('Changed sharing settings for file: %s' % item['name'])
                    except HttpError as error:
                        print('An error occurred: %s' % error)

    # Now process subfolders
    folder_results = service.files().list(
        q="'{}' in parents and mimeType='application/vnd.google-apps.folder'".format(folder_id),
        fields="files(id, name)").execute()
    folder_items = folder_results.get('files', [])

    for item in folder_items:
        print('Entering subfolder:', item['name'])
        process_files(service, item['id'])


def main():
    # Parsing command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder-name', type=str, required=True, help='Name of the folder to process')
    args = parser.parse_args()

    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    if args.folder_name == '/':
        folder_id = 'root'
    else:
        # Searching for the folder
        folder_results = service.files().list(
            q="name='{}' and mimeType='application/vnd.google-apps.folder'".format(args.folder_name),
            fields="files(id, name)").execute()
        folder_items = folder_results.get('files', [])

        if not folder_items:
            print('No folder found.')
            return

        folder_id = folder_items[0]['id']

    process_files(service, folder_id)


if __name__ == '__main__':
    main()
