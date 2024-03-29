This script imports a Pivotal Tracker CSV export file into a Shortcut workspace.

# Prerequisites and Setup

In order to run this, you will require a Pivotal account and the ability to sign up for a Shortcut account, as well as a working internet connection.

1. Sign up for a Shortcut account at [https://www.shortcut.com/signup](https://www.shortcut.com/signup).
1. [Create an API token](https://app.shortcut.com/settings/account/api-tokens) and [export it into your environment](../Authentication.md).
1. Export your Pivotal project to CSV and save the file to `data/pivotal_export.csv`.
1. Create/Invite all users you want to reference into your Shortcut workspace.
1. Run `./setup` to install Python dependencies.
1. Run [`initialize.py`](initialize.py) to initialize `data/users.csv` and `data/states.csv`.
1. Ensure there is exactly one Shortcut user mapped for all referenced users in `data/users.csv`.
1. Ensure there is exactly one Shortcut workflow state mapped for all referenced Pivotal states in `data/states.csv`.

# Operation

Before you run the import, you should go through the steps in **Prerequisites and Setup**. You can check that the prerequisites are superficially met by running [`pivotal-import.py`](pivotal-import.py) which by default will not write any changes to your Shortcut workspace. You can use this mode to validate that you've configured the import correctly.

If `pivotal-import.py` completes without errors, you can run the script with the `--apply` flag, which will enable writing to the Shortcut API.

# Known Limitations

This script has some limitations you should know about. Most prominently, it will not redirect any URLs in the description of your Pivotal stories or epics. Also, as of this version, file attachments (including Google Drive attachments), project history, and story history are not imported into Shortcut in any way.

# Customization

It's possible that this tool does not do exactly what you'd like it to - if that's the case, we have tried to make it straightforward to modify. Make reference to the [Shortcut API](https://developer.shortcut.com/api/rest/v3) and the other examples in this cookbook, and please let us know in [our Discord](https://discord.com/channels/887801174496006216/887831741019070534) what you're doing with it!

# Contributing

Any contributions you make are greatly appreciated!

If you have a suggestion that would make this better, please fork this repository and create a pull request. Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
