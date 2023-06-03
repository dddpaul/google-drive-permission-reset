# Google Drive Permission Reset

This Python script modifies the permissions of files and folders in Google Drive, removing public access and preserving
access to specific users. The script uses the Google Drive API to interact with the user's Drive content.

## Dependencies

The script is written in Python and uses several packages,
including `googleapiclient`, `google_auth_oauthlib`, `pickle`, and `argparse`. It's recommended to use a Python virtual
environment to manage these dependencies.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/dddpaul/google-drive-permission-reset.git
cd google-drive-permission-reset
```

2. Install the dependencies (could be skipped for Docker usage):

```bash
pip install -r requirements.txt
```
You should use `pip3` instead of `pip` on some systems.

3. Set up your credentials:

* Go to the [Google Cloud Console](https://console.cloud.google.com/)
* Create a new project, then select it
* Search for 'Google Drive API', enable it for your project
* Go to 'Credentials', then 'Create credentials', and select 'OAuth client ID'
* Download the JSON file and rename it to 'credentials.json'

Note: The steps for creating 'credentials.json' are just a brief overview, the full procedure is more complex and
depends on the Google Cloud Console interface, which might change over time. You may want to link to an up-to-date
tutorial or to the official Google API Python client docs.

4. Generate your `token.pickle`:

Run the script once without arguments. A browser window will open asking you to authorize the app. After
authorization, `token.pickle` file will be created. It is required for the API to authenticate with Google Drive.

## Usage

Use the -h or --help argument to get information about the script's arguments:

```bash
python permission-reset.py --help
```

Basic usage:

```bash
python drive_permission_changer.py --folder-name MyFolder
```

This command will start processing the folder named 'MyFolder' and its subfolders.

Optional arguments:

* `--dry-run`: Run the script without making actual changes. This is useful for testing.
* `--auth-port`: The port for the authentication server. Default is 0. Used for running inside Docker.
* `--credentials-path`: The path to the 'credentials.json' file. Default is './credentials.json'. Used for running
  inside Docker.
* `--token-path`: The path to the 'token.pickle' file. Default is './token.pickle'. Used for running inside Docker.

Docker usage:

```bash
./docker-run.sh  --folder-name MyFolder
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
