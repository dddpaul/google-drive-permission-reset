# Google Drive Permission Changer

This Python script modifies the permissions of files and folders in Google Drive, removing public access and preserving access to specific users. The script uses the Google Drive API to interact with the user's Drive content.

## Dependencies

The script is written in Python and uses several packages, including `googleapiclient`, `google_auth_oauthlib`, `pickle`, and `argparse`. It's recommended to use a Python virtual environment to manage these dependencies.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/<your_username>/<your_repo_name>.git
cd <your_repo_name>
```

1. Install the dependencies:
```bash
pip install -r requirements.txt
```
    
1. Set up your credentials:

* Go to the [Google Cloud Console](https://console.cloud.google.com/)
* Create a new project, then select it
* Search for 'Google Drive API', enable it for your project
* Go to 'Credentials', then 'Create credentials', and select 'OAuth client ID'
* Download the JSON file and rename it to 'credentials.json'

1. Generate your `token.pickle`:

Run the script once without arguments. A browser window will open asking you to authorize the app. After authorization, `token.pickle` file will be created. It is required for the API to authenticate with Google Drive.

## Usage

Use the -h or --help argument to get information about the script's arguments:
```bash
python drive_permission_changer.py --help
```

Basic usage:
```bash
python drive_permission_changer.py --folder-name MyFolder
```

This command will start processing the folder named 'MyFolder' and its subfolders.

Optional arguments:

* `--dry-run`: Run the script without making actual changes. This is useful for testing.
* `--auth-port`: The port for the authentication server. Default is 0. Used for running inside Docker.
* `--credentials-path`: The path to the 'credentials.json' file. Default is './credentials.json'. Used for running inside Docker.
* `--token-path`: The path to the 'token.pickle' file. Default is './token.pickle'. Used for running inside Docker.

Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

Note: The steps for creating 'credentials.json' are just a brief overview, the full procedure is more complex and depends on the Google Cloud Console interface, which might change over time. You may want to link to an up-to-date tutorial or to the official Google API Python client docs.
