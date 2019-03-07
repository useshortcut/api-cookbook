In this guide, we'll take you through all the things you might need to get set up to run the Clubhouse API Cookbook scripts.
We'll cover:
- [Opening a command line interface](anchor link)
- [Checking what version of Python you have installed](anchor link)
- [Installing Python 3](anchor link)
- [Setting your Environment Variable](anchor link)
- [Setting up and using a virtual environment](anchor link)
- [Installing the Requests library](anchor link)
- [Downloading the Clubhouse API Cookbook](anchor link)


***

#### Opening a command line interface

The command line also gets called cmd, CLI, prompt, console or terminal - all of these are referring to a text based way to work with files on your computer.

We'll use a few commands as we get things set up and run Cookbook scripts, but won't go into detail about all the things you can do with the command line.

Command line cheat sheets are a great way to get familiar with the commonly used commands to interact with your system.


Different operating systems have different command line interfaces. 

**On Mac:**
Open Applications, then click Utilities. Click the Terminal app to open the command line.

**On Windows:**
You may have to try a few ways to find your command line - different versions of Windows have different ways of accessing the command line.

- Go to the Start menu or screen, and enter "Command Prompt" in the search field.
- Go to Start menu then click Windows System. Click Command Prompt to open the command line.
- Go to Start menu the click All Programs. Click into Accessories, then click Command Prompt.

**On Linux:**
Check in Applications in either the Accessories folder or the Applications folder for the Terminal app. 
If you're running a distro that doesn't have Terminal in one of those places, you probably know how to launch it. :)


Once you have a command line window open, its time to check your current Python version.


#### Checking what version of Python you have installed

All of the Cookbook scripts use Python 3, so we need to make sure you have Python 3 installed.

Open your [command line](anchor link)
Type `python3 --version` and press Enter/Return

You'll see the default version of Python 3 that is installed on your system.
If nothing is present, you'll need to install Python 3.

#### Installing Python 3

If you already use a package manager like Homebrew(Mac) or Chocolatey(Windows) install Python 3 with your package manager.

Otherwise, grab the appropriate download for your operating system from the [Python Software Foundation](https://www.python.org/downloads/).

_Special note for Windows users:_ During installation make sure you tick the "Add Python 3.x to PATH" or 'Add Python to your environment variables' in the Setup window.

***
#### Setting your Environment Variable
***

Get your [Clubhouse API token](https://help.clubhouse.io/hc/en-us/articles/205701199-Clubhouse-API-Tokens) from the Clubhouse UI.

If you are just testing things out, or don't need to regularly access the Clubhouse API, you can set a temporary environment variable.

In your command line window, type `export CLUBHOUSE_API_TOKEN='YOUR_TOKEN_VALUE'` where YOUR_TOKEN_VALUE is your actual API token from Clubhouse. Keep the single quotes around the token.

When you close your command line window, this variable will be removed, and you'll need to add it again every time to you want to use something in the Cookbook.


If you're going to use the API often, it will save you time if you set your API token as a system variable. 

On Windows 10:
1. Open the Power User Task Menu, by right-clicking the very bottom-left corner of the screen.
2. Click System.
3. In the Settings window, scroll down to the Related settings section and click the System info link.
4. In the System window, click the Advanced system settings link in the left navigation pane.
5. In the System Properties window, click on the Advanced tab, then click the Environment Variables button near the bottom of that tab.
6. At the bottom of the window, click New and enter the `CLUBHOUSE_API_TOKEN` as the variable name and the token that you created in Clubhouse as the variable value.

On Mac:

We're assuming you're using bash since it's the default user shell. If you're using a different shell, and aren't sure how to set a variable for your set-up, check the documentation for the shell you're using.

If you have other system variables set, like AWS credentials, and aren't sure where those credentials are, you may want to check with a technical lead on your team so you can set your Clubhouse API variable in the same file.


You'll use Terminal to set your Clubhouse API token as an environment variable in ~/.bash_profile :

1. Type `cd ~` and press Return to go to your home directory
2. Type `nano .bash_profile` and press Return to open .bash_profile in the nano text editor (Feel free to use your preferred text editor instead)
3. Add the line `export CLUBHOUSE_API_TOKEN='YOUR_TOKEN_VALUE'` to the file in nano, where YOUR_TOKEN_VALUE is your actual API token from Clubhouse. Keep the single quotes around the token.
4. Press ⌃O (control key and the letter 'o') then return to save the changes - this is like the ⌘S (Command-S )to save in most programs.
5. Press ⌃X (control key and letter 'x') to exit.
6. Close your Terminal window - this is necessary for the change to be applied!
7. Open new Terminal window and test your environment variable by typing:
`echo $CLUBHOUSE_API_TOKEN`


#### Setting up and using a virtual environment

Setting up a virtual environment is not 100% necessary if you don't regularly use a lot of Python, but it is highly recommended.
It's a good practice that can save you trouble in the future and can make the next step easier!

A virtual environment will keep installed Python packages separate from your system environment (everything on your computer that's not in a virtual environment). 
This helps keep all of your code dependencies separate and makes it possible to work with code that has different and possibly incompatible dependencies. 
Without a virtual environment, you could end up with dependencies interfering with each other - which is a real pain to debug.
Be kind to your future self and set-up a virtual environment for working with this Cookbook. We'll help guide you through it!

If you're regularly working with Python 2, you're probably already using [virtualenv](hhttps://virtualenv.pypa.io/en/latest/). We'll assume you're comfortable working with that without our guidance. :)

The remainder of these instructions will use [venv](https://docs.python.org/3/library/venv.html) to create a virtual environment.

Let's get started!

1. Choose the location where you'll keep the Cookbook scripts. We'll use a folder named `ClubhouseCookbook` in our home directory, but you can make a folder anywhere that makes sense for you, and rename it as well.
In your [command line](anchor link) window type:
`mkdir ClubhouseCookbook`
and press Enter/Return.

2. We want to create the virtual environment in the directory(folder) that we just created.
In your command line window type:
`cd ClubhouseCookbook`
and press Enter/Return.

3. Make a virtual environment. 
We'll make one called `cookbook`. You can use any name, but be sure to avoid spaces, accents, or special characters and keep it all lowercase.
If you're on Windows, in your command line window type:

`python -m venv cookbook`

For Mac and Linux, in your command line window type:
`python3 -m venv cookbook`

4. Start your virtual environment.
On Windows, `cookbook\Scripts\activate`
On Mac/Linux `source cookbook/bin/activate`

When your virtual environment is active, you'll see `(cookbook)` at the beginning of your command line prompt.

Now we're ready to install Requests!


#### Installing the Requests library

We'll need the [Requests Library](http://docs.python-requests.org/en/master/) which you can install with pip.

-- I don't think we need this section when using a virtual environment, but will leave it while we test ---
First though, check if you have pip installed.

On the command line type `pip --version`
If it's installed, you'll get back something like `pip 10.0.1 from /usr/local/lib/python3.6/site-packages/pip (python 3.6)`. 

If it's not installed, this would be a good time to ask for help. :D

All set? Let's get Requests installed:

--- end section that we may not need ----


In Terminal type `pip install requests`

That covers the last installation requirement. Let's go get the Cookbook!

#### Downloading the Clubhouse API Cookbook

There are a few options around how to get the Clubhouse API Cookbook scripts onto your computer.
Since we set up the Requests library in a virtual environment, we'll want to put the Cookbook in that same environment.

If you've been following along in your command line window, you should still be in the ClubhouseCookbook folder. If not you'll need to navigate to that folder or the folder you're using to hold the Cookbook scripts.
Once you're in that folder in your command line window paste `git clone https:linkitylink` and press Enter/Return

If you'd prefer to get the Cookbook without using the command line, you can down load a zipped folder from GitHub's UI. You'll need to unzip the folder and then move all of the contents in to the location that you set up your virtual environment.




