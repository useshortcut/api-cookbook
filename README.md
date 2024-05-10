# Welcome to the Shortcut REST API Cookbook

The Shortcut REST API is a powerful tool that can make your work easier and enhance the ways that you use your Shortcut data.
We created this material to get you started using the Shortcut REST API to solve common requests, even if you don't regularly use APIs.

Maybe you need to get average Cycle time for the Epic you just completed, or you need to change the Label for incomplete work in a Sprint; this will show you how.

Some of these examples will guide you through using your command line to run the script. In other cases, we'll provide example code for specific tasks which will show you where to make small changes to interact with the data in your Shortcut account. You can also use this material as a starting place and make further adjustments for your particular needs.

Do you have an example you think we should cover? Please let us know! You can open an Issue on this repository so other teams can publicly add their interest, or email support@shortcut.com.

Found a typo or other small issue? Please feel free to submit a PR!

Questions and suggestions are welcome as Issues, or send us an email support@shortcut.com. We'd love to hear from you!

## Requirements

All of the cookbook scripts are written in Python 3 and use the [Requests Library](http://docs.python-requests.org/en/master/).
If you're comfortable checking your Python installation, installing Requests, using a virtual environment, and setting environment variables, please jump to [the recipes](#cookbook-recipes).

If you'd like a walk-through of getting set up to run these example scripts, please check out the setup instructions:
- [Mac](https://github.com/useshortcut/api-cookbook/blob/main/set-up-instructions.md)
- [PC](https://github.com/useshortcut/api-cookbook/blob/main/windows-set-up-instructions.md)

## Cookbook Recipes

### [Send some Stories to Slack](https://github.com/useshortcut/api-cookbook/tree/main/stories-to-slack)

The support team at Shortcut uses a version of this script to help us get back to customers about bug fixes and shipped features.

[This script](https://github.com/useshortcut/api-cookbook/tree/main/stories-to-slack) searches for work completed between the last business day and today, checks for support tickets on each Story, and preps data to send to Slack. The name of the Story, a link to the Story, and a count of the number of tickets on the Story are sent to a specific Slack channel.

We use this to help the support team quickly find Stories where they need to follow up, but with modifications you could use it for things like daily squad updates, personal reminders, and more.

### [There's incomplete work in my sprint. I need to update all the labels for the next sprint.](https://github.com/useshortcut/api-cookbook/tree/main/change-label)

Many teams use Labels to represent sprints. When there's unfinished work that needs to be rolled into the next sprint, [this script](https://github.com/useshortcut/api-cookbook/tree/main/change-label) can help automate that process. As a bonus, you can also use this script to create labels with custom colors.

### I need to report on cycle time

Cycle time information for Epics and Objectives can be useful reporting tools. These scripts get the cycle time and lead time for an individual Epic or Objective. You can find cycle time information on stories using the charts provided within Shortcut itself.

[How to I get the lead and cycle time for an Objective?](https://github.com/useshortcut/api-cookbook/tree/main/kanban-metrics/objective_metrics.py)

[How do I get the lead and cycle time for an Epic?](https://github.com/useshortcut/api-cookbook/tree/main/kanban-metrics/epic_metrics.py)

### Export Epic Comments to CSV

Export the comments for either a single epic or all epics in your Shortcut Workspace using the [epic-comments recipe](./epic-comments).

## FAQ

[How do I get set up to use these scripts on my Mac?](https://github.com/useshortcut/api-cookbook/blob/main/set-up-instructions.md)

[How do I get set up to use these scripts on my PC?](https://github.com/useshortcut/api-cookbook/blob/main/windows-set-up-instructions.md)

[How do I authenticate?](https://github.com/useshortcut/api-cookbook/blob/main/Authentication.md)

[How do I get the next page of results?](https://github.com/useshortcut/api-cookbook/blob/main/Pagination.md)
