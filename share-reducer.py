from __future__ import print_function
import os.path
import pickle
import argparse
import time
import logging
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def authenticate_with_google_drive():
    """Authenticate with Google Drive and return the service object."""
    creds = None
    try:
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
    except FileNotFoundError as e:
        logging.error('File not found: %s' % str(e))
        return None
    except GoogleAuthError as e:
        logging.error('Authentication failed: %s' % str(e))
        return None

    return build('drive', 'v3', credentials=creds)


def get_folder_id(service, folder_name):
    """Get and return folder id of the specified folder."""
    try:
        if folder_name == '/':
            return 'root', ''

        # Searching for the folder
        folder_results = service.files().list(
            q="name='{}' and mimeType='application/vnd.google-apps.folder'".format(folder_name),
            fields="files(id, name)").execute()
        folder_items = folder_results.get('files', [])

        if not folder_items:
            logging.error('No folder found.')
            return None, None

        return folder_items[0]['id'], folder_name
    except HttpError as e:
        logging.error('Google Drive API request failed: %s' % str(e))
        return None, None


def process_files(service, folder_id, rate_limit, current_path, dry_run):
    """Process files under the specified folder recursively."""
    try:
        # Get files in the folder
        page_token = None
        while True:
            file_results = service.files().list(
                q="'{}' in parents".format(folder_id),
                pageSize=1000, fields="nextPageToken, files(id, name, permissions)",
                pageToken=page_token).execute()
            file_items = file_results.get('files', [])

            if not file_items:
                logging.info('No files found in the folder.')
                continue

            for item in file_items:
                logging.info(u'{0}/{1} ({2})'.format(current_path, item['name'], item['id']))
                permissions = item.get('permissions', [])
                for perm in permissions:
                    if perm['type'] == 'anyone':
                        if not dry_run:
                            try:
                                service.permissions().delete(
                                    fileId=item['id'],
                                    permissionId=perm['id']
                                ).execute()
                                logging.info('Changed sharing settings for file: %s' % item['name'])
                            except HttpError as error:
                                logging.error('Google Drive API request failed: %s' % error)
                        else:
                            logging.info('Would change sharing settings for file: %s' % item['name'])
                        time.sleep(rate_limit)

            page_token = file_results.get('nextPageToken', None)
            if page_token is None:
                break

        # Now process subfolders
        folder_results = service.files().list(
            q="'{}' in parents and mimeType='application/vnd.google-apps.folder'".format(folder_id),
            fields="files(id, name)").execute()
        folder_items = folder_results.get('files', [])

        for item in folder_items:
            process_files(service, item['id'], rate_limit, current_path + '/' + item['name'], dry_run)
    except Exception as e:
        logging.error('An error occurred during processing: %s' % str(e))


def main():
    """Main function."""
    # Parsing command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder-name', type=str, required=True, help='Name of the folder to process')
    parser.add_argument('--rate-limit', type=float, default=0.5, help='Rate limit in seconds between requests')
    parser.add_argument('--dry-run', action='store_true', help='Run script in dry-run mode')
    args = parser.parse_args()

    if not args.dry_run:
        confirm = input("This script will make changes to the files. Are you sure you want to continue? (Y/N): ")
        if not confirm.lower() == 'y':
            return

    service = authenticate_with_google_drive()
    if service is None:
        return

    folder_id, current_path = get_folder_id(service, args.folder_name)
    if folder_id is None:
        return

    process_files(service, folder_id, args.rate_limit, current_path, args.dry_run)


if __name__ == '__main__':
    main()
