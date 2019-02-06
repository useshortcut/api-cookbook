# api-cookbook
A collection of information people can use for reference when writing API scripts. 

Example code for specific tasks that can be used as is, or adjusted for a variety of use cases.

#### Check Python version and install Requests
***

All of the cookbook scripts are written in Python 3. The first thing to do is to make sure you have Python 3 installed.

Open Terminal 
Type `python3 --version` and press Return

You'll see the default version of Python 3 that is installed on your Mac. It's probably Python 3.6.4 or 3.6.5. That's totally fine. We do *not* want to change that since there may be other things on your system that use Python 3.6.x.


We'll need the [Requests Library](http://docs.python-requests.org/en/master/) which you can install with pip.
First though, check if you have pip installed.

In Terminal type `pip3 --version`
If it's installed, you'll get back something like `pip 10.0.1 from /usr/local/lib/python3.6/site-packages/pip (python 3.6)`. 

If it's not installed, this would be a good time to ask for help. :D

All set? Let's get Requests installed:

In Terminal type `pip3 install requests`

***
#### Environment Variable
***

Get your [Clubouse API token](https://help.clubhouse.io/hc/en-us/articles/205701199-Clubhouse-API-Tokens).

Set your Clubhouse API token as an environment variable in .profile :

1. `cd ~` - to go to your home directory
2. `nano .profile` - to open that file in the nano text editor
3. Add the line `export CH_API='YOUR_TOKEN'` to the file in nano, where YOUR_TOKEN is your actual API token from Clubhouse. Keep the single quotes around the token.
4. Press ⌃O (control key and the letter 'o') then return to save the changes - this is like the ⌘S (Command-S )to save in most programs.
5. Press ⌃X (control key and letter 'x') to exit.
6. Close your Terminal window - this is necessary for the change to be applied!
7. Open new Terminal window and test your environment variable by typing:
`echo $CH_API`
