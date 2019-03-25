Looking for an overview of what you can find in the Clubhouse API Cookbook? You've come to the right place!

### General questions
[How do I authenticate?](https://github.com/clubhouse/api-cookbook/blob/master/Authentication.md)
Not sure how to get access to your Clubhouse with the API? Start here.

[How do I get the next page of results?](https://github.com/clubhouse/api-cookbook/blob/master/Pagination.md)
Pagination can be tough! This will help you through it.

[How do I get set up to use these scripts on my Mac?](https://github.com/clubhouse/api-cookbook/blob/master/set-up-instructions.md)

[How do I get set up to use these scripts on my PC?](https://github.com/clubhouse/api-cookbook/blob/master/windows-set-up-instructions.md)

### Specific use case examples

## [I want to regularly send some Stories to Slack](https://github.com/clubhouse/api-cookbook/tree/master/stories-to-slack)

The support team at Clubhouse uses a version of this script to help us get back to customers about bug fixes and shipped features.

[This script](https://github.com/clubhouse/api-cookbook/tree/master/stories-to-slack) searches for work completed between the last business day and today, checks for support tickets on each Story, and preps data to send to Slack. The name of the Story, a link to the Story, and a count of the number of tickets on the Story are sent to a specific Slack channel.

We use this to help the support team quickly find Stories where they need to follow up, but with modifications you could use it for things like daily squad updates, personal reminders, and more.

## [There's incomplete work in my sprint. I need to update all the labels for the next sprint.](https://github.com/clubhouse/api-cookbook/tree/master/change-label)

Many teams use Labels to represent sprints. When there's unfinished work that needs to be rolled into the next sprint, [this script](https://github.com/clubhouse/api-cookbook/tree/master/change-label) can help automate that process. As a bonus, you can also use this script to create labels with custom colors. 

## I need to report on cycle time

Cycle time information for Epics and Milestones can be useful reporting tools. These scripts get the cycle time and lead time for an individual Epic or Milestone.

[How to I get the lead and cycle time for a Milestone?](https://github.com/clubhouse/api-cookbook/tree/master/kanban-metrics)

[How do I get the lead and cycle time for an Epic?](https://github.com/clubhouse/api-cookbook/tree/master/kanban-metrics)
