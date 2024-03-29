from __future__ import print_function
import os.path
import pickle
import argparse
import time
import logging
import yaml
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def load_allowed_users(file_path):
    """Load the list of allowed users from a YAML file."""
    try:
        with open(file_path, 'r') as file:
            users = yaml.safe_load(file)
        return [user['email'] for user in users]
    except FileExistsError as e:
        return []


def authenticate_with_google_drive(auth_port, credentials_path, token_path):
    """Authenticate with Google Drive and return the service object."""
    creds = None
    try:
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                if auth_port > 0:
                    # to forward traffic from host to docker container
                    creds = flow.run_local_server(port=auth_port, bind_addr="0.0.0.0")
                else:
                    creds = flow.run_local_server(port=auth_port)
            with open(token_path, 'wb') as token:
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


def google_drive_list_request(service, query, fields, page_token=None):
    """Make a list request to the Google Drive API."""
    try:
        return service.files().list(
            q=query,
            pageSize=1000,
            fields=fields,
            pageToken=page_token
        ).execute()
    except HttpError as error:
        logging.error('Google Drive API request failed: %s' % str(error))
        return None


def process_files(service, folder_id, rate_limit, current_path, allowed_emails, dry_run):
    """Process files under the specified folder recursively."""
    try:
        # Get files in the folder
        page_token = None
        while True:
            file_results = google_drive_list_request(
                service,
                "'{}' in parents".format(folder_id),
                "nextPageToken, files(id, name, permissions)",
                page_token
            )

            if file_results is None:
                break

            file_items = file_results.get('files', [])

            for item in file_items:
                logging.debug(u'Checking {0}/{1} ({2})'.format(current_path, item['name'], item['id']))
                permissions = item.get('permissions', [])
                for perm in permissions:
                    # Revoke 'open for anyone' permission
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
                    # Revoke permissions if the email isn't in the allowed list
                    if bool(allowed_emails):
                        if perm['type'] == 'user' and perm['emailAddress'] not in allowed_emails:
                            if not dry_run:
                                try:
                                    service.permissions().delete(
                                        fileId=item['id'],
                                        permissionId=perm['id']
                                    ).execute()
                                    logging.info(
                                        'Revoked permission from %s for: %s' % (perm['emailAddress'], item['name']))
                                except HttpError as error:
                                    logging.error('Google Drive API request failed: %s' % error)
                            else:
                                logging.info(
                                    'Would revoke permission from %s for: %s' % (perm['emailAddress'], item['name']))

            page_token = file_results.get('nextPageToken', None)
            if page_token is None:
                break

        # Now process subfolders
        folder_results = google_drive_list_request(
            service,
            "'{}' in parents and mimeType='application/vnd.google-apps.folder'".format(folder_id),
            "files(id, name)"
        )

        if folder_results is not None:
            folder_items = folder_results.get('files', [])

            for item in folder_items:
                logging.info(u'Processing folder {0}/{1} ({2})'.format(current_path, item['name'], item['id']))
                process_files(
                    service=service,
                    folder_id=item['id'],
                    rate_limit=rate_limit,
                    current_path=current_path + '/' + item['name'],
                    allowed_emails=allowed_emails,
                    dry_run=dry_run)

    except Exception as e:
        logging.error('An error occurred during processing: %s' % str(e))


def main():
    """Main function."""
    # Parsing command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder-name', type=str, required=True, help='Name of the folder to process')
    parser.add_argument('--rate-limit', type=float, default=0.5, help='Rate limit in seconds between requests')
    parser.add_argument('--auth-port', type=int, default=0, help='Port for the authentication server')
    parser.add_argument('--credentials-path', type=str, default='./credentials.json',
                        help='Path to the credentials file')
    parser.add_argument('--token-path', type=str, default='./token.pickle', help='Path to the token file')
    parser.add_argument('--users-file', type=str, help='Path to a YAML file containing the list of allowed users')
    parser.add_argument('--log-level', type=str, default='INFO',
                        help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--dry-run', action='store_true', help='Run script in dry-run mode')
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format='%(asctime)s - %(levelname)s - %(message)s')

    if not args.dry_run:
        confirm = input("This script will make changes to the files. Are you sure you want to continue? (Y/N): ")
        if not confirm.lower() == 'y':
            return

    service = authenticate_with_google_drive(args.auth_port, args.credentials_path, args.token_path)
    if service is None:
        return

    folder_id, current_path = get_folder_id(service, args.folder_name)
    if folder_id is None:
        return

    allowed_emails = []
    if bool(args.users_file):
        allowed_emails = load_allowed_users(args.users_file)

    process_files(
        service=service,
        folder_id=folder_id,
        rate_limit=args.rate_limit,
        current_path=current_path,
        allowed_emails=allowed_emails,
        dry_run=args.dry_run)


if __name__ == '__main__':
    main()
