These scripts are designed to be run after completion of a full import. Each fills in a gap left by the importer. Many could be run long after you've imported and started using a workspace. But see the next section!

# Community Contribution

I (Tom Ngo at Lumin.ai) wrote these scripts because they help preserve Pivotal information that's important for our team. I'm sharing them because I think others have similar needs; but unfortunately we aren't in a position to spend a lot of time bulletproofing or supporting enhancement requests.

Therefore, from a legal perspective, I'm releasing this under the MIT License, as is, and without warranty.

But more importantly, please take precautions to preserve your team's precious work. I suggest taking some or all of the following steps before you run the code for real:
* Practice on a test workspace.
* Review the code. See the end of this README for tips on how to do that efficiently.
* Modify the code to stop after operating on one story, for example, and inspect the results to gauge according to your liking. 
* If your workspace is small, consider adding a confirmation prompt before each change.

If you edit the code, you'll notice that we have an unusual coding convention at Lumin.ai that, among other things, uses horizontal whitespace to emphasize differences between lines of code by aligning similarities, and to reduce the cognitive burden associated with understanding nested expressions. Sorry to make your PEP-8 linter blare; you might want to turn that off temporarily. :)

# Why to Use

The following information in our Pivotal workspace is important to us, but not preserved by the importer. If this information is important to you too, we hope these scripts will give you a headstart in closing the gap.

* References to Pivotal stories and epics
* Blockers in Pivotal
* Git Pull Requests

Also:

* We also often put one story in many epics, and Shortcut's object model requires a given story to be contained in at most one epic. One of these utilities deals with that case, applying heuristics that are particular to our organization's conventions.
* In our case, we needed to retire a test user and merge it into a real user (i.e., change requester, owner, and follower references from the test user to the real user).

# What to Expect

## Design Goals

I wrote these scripts in a hurry; but I did pay attention to a few design goals in order to save time.
* Post import: Unlike the importer, which is best run when you have nothing in your workspace, each of these scripts wants to run when your workspace is fully populated.
* Idempotency: Each script is designed so that if you run it many times, you won't wind up with significant duplication. See details in next subsection.
* Small scope: To decouple implementations, I thought it would be best to make each script do one small thing.
* Caching: Most of the scripts save certain results of Shortcut API reads to files in `cache/*.json`. They don't attempt to test whether an existing cache file is stale. Take a peek in there to see what each file stores, and delete any file that contains stale information.

## Capabilities and Known Limitations

Use this section to understand what's possible. To get into details regarding how to use, please scroll down to the How to Use section.

### Not much dry-run functionality

I didn't try very hard to enable dry runs because my de-risking methodology was to run these scripts repeatedly against a test workspace. If you'd like to attempt a dry run, I'd suggest editing `ShortcutMetadata.call_sc` to allow only GETs and simply log everything else.

### Pivotal references

The script `transform_id_mappings.py` transforms references to Pivotal objects into references to Shortcut objects, doing so in various places in the Shortcut workspace. It doesn't read the Pivotal export file at all; rather, it builds a mapping by reading from the `external_id` of each Shortcut epic and story, which the importer populates from Pivotal.

What it recognizes:

* It transforms references like `#1234567` and `##12345` to links like `https://app.shortcut.com/your-slug/story/12345` (as opposed to references like `[sc-1234567]`).
* I decided not to translate references like `https://pivotaltracker.com...` because in our PT workspace, all but 4 of such references were to individual comments, and the Pivotal export doesn't preserve enough information to build a mapping from Pivotal comment IDs to Shortcut comment IDs. If you value your story-level and epic-level `https://pivotaltracker.com...` links, please add the appropriate pattern to `transform_id_mappings.py`; all you need is a new element in the `pats` list.

Where it looks:

* It covers Description and Comments.
* It doesn't cover Tasks.
* It doesn't cover Blockers. We handle those in a different way. Read on...

This script does nothing but edit the contents of your Shortcut workspace. Hence it doesn't do anything about links to Pivotal entities that appear in other places, such as Slack. But another community member has written a proxy to catch those cases. See [this Slack conversation](https://shortcutcommunity.slack.com/archives/C07QAKTQX43/p1744757655552959?thread_ts=1744756108.363919&cid=C07QAKTQX43).

### Pivotal blockers

Since the importer doesn't do anything at all with blockers, the script `inject_blockers.py` adds Shortcut Story Links that represent blockers, using the Pivotal export as its source of information. 

* For a blocker that's `blocked` in the Pivotal world, it makes a Story Link in the Shortcut world.
* It ignores any blocker that's `resolved` in the Pivotal world, only because I don't know how to represent it in the Shortcut world. It's possible that by the time you read this, we'll know; see [this Slack thread](https://shortcutcommunity.slack.com/archives/C07QAKTQX43/p1744994596842229?thread_ts=1744955512.130359&cid=C07QAKTQX43).

The script doesn't attempt to read existing Story Links and suppress duplication. I've found empirically (bravo!) that the Shortcut API for creating a Story Link desists from making duplicates.

### Git Pull Requests and Branches

The script `inject_github_prs.py` adds Git Pull Requests to Shortcut Stories. It uses the Pivotal export as its source of information. It achieves its idempotency by leaning on the existing Shortcut-to-GitHub integration: all it does is add a comment to the appropriate PR, containing a link to the story, and the SC-GH integration does the rest beautifully. See [this Slack thread](https://shortcutcommunity.slack.com/archives/C07QAKTQX43/p1744900053772999?thread_ts=1744899471.023159&cid=C07QAKTQX43).

Limitations:
* It doesn't do anything with Branches. That's because we at Lumin.ai don't make references to branches. If you'd like to add support for this, note that PivotalExport.py in this directory does read those references out of the Pivotal export. You'll just need to write a script to use that information to inject the branch information into Shortcut.
* It's not 100% idempotent. If you run this script multiple times, you'll wind up with multiple redundant comments in each affected GitHub PR. But thanks to the SC-GH integration, I believe you won't see duplication in the Shortcut workspace itself. This is the one caveat to my idempotency remark in the Design Goals subsection above.
* It's important to know in advance which GitHub repos appear in your Pivotal export (see Shortcut integration, below). But I didn't write any code to automatically list all GitHub repos that appear in your Pivotal export. I assume most teams already know which repos contribute. If you'd like to write code to do that, the easiest place would be in PivotalExport.py, in the test code at the bottom.

### The "Favorite" epic of a given story

Background:
* In Pivotal, a given story can be in multiple epics.
* In Shortcut, a given story can be in only one epic. (However, the multiple epic references from Pivotal are represented as multiple Labels in Shortcut.)
* The importer chooses the epic that's last in lexical order of Pivotal epic-label name. Note that Pivotal initializes the label name to be equal to the epic name (lower-cased), but does not automatically rename a label if the epic is renamed.

I'm not sure how many teams care about this, but ours does. We do often have one story in many epics, and usually one of them is the one that deserves a containment relationship. The criteria for choosing that epic will be very dependent on an individual organization’s processes and conventions. In the case of our organization, we do have a way to programmatically identify that one special epic for a given story.

The script `assign_favorite_epic_per_story.py` finds each story whose labels imply membership in multiple Pivotal epics. For each such story, it uses our heuristic rules to identify one epic. It mutates the story to point to that favorite epic. 

To adapt this script to your organization's needs, please edit the function `score_epic_given_story`. The script simply takes the highest-scoring epic, allowing the python built-in function `max` to break any ties arbitrarily.

# How to Use

The previous section focuses on how to decide whether to use a given script, and strays into some aspects of how to use. This section mentions a few dangling items.

## Prerequisites

### Shortcut-GitHub integration

The script `inject_github_prs.py` needs you to have set up the Shortcut-to-GitHub integration as instructed in the Shortcut docs. Before you run that script, ensure that the integration is configured to point at least all of the GitHub repos that are referenced in your Pivotal export.

Look out! If you already set up the SC-GH integration while working with a test workspace, you'll likely need to remove the integration and install it afresh.

### Python libraries

These utilities use five libraries that aren't used by the importer. To install them:
```sh
cd post-import-utils
pip install -r requirements.txt
```

You'll likely want to do this inside the virtual environment created by the importer.

### API tokens

API tokens are expected to be stored in two envars:
```sh
export SHORTCUT_API_TOKEN="<your Shortcut token>" # just like the importer
export GITHUB_API_TOKEN="<your GitHub PAT>"
```

To get your GitHub PAT:
* Navigate to github.com > [your face] > Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens > Generate new token
* Restrict it to a short expiration window, one repository.
* Give it Permissions > Repository permissions > Pull requests > Read/write.

### Parameters

None of the scripts take command-line parameters. The API tokens tell them what Shortcut workspace to point to. But a couple of scripts need to be edited before running:

* `transform_id_mappings.py`: Edit the list called `pats`. It specifies regexes for recognizing Pivotal story and epic references. If you don't edit it, you'll get regexes tailored to our team's conventions: it recognizes `#1234567` and `##12345`, and  skips patterns like `PR #1234` and `[#1234567]` and `[Fixes #1234567]`
* `merge_users.py`: Edit `user_email_lose` and `user_email_gain` at the top.

### Understanding the code

I'd really prefer that you understand the code before you run it. Here are some tips on how to grok it fast:

* Run `python ShortcutMetadata.py`. That'll execute a test main at the bottom that dumps several data structures. Copy output to an editor, prettify, and absorb.
* Run `python ShortcutObject.py` after editing the test main at the bottom to look at some epics and stories that exist in your workspace.
* Run `python PivotalExport.py`. Copy output to an editor, prettify, and absorb.
* Read each of the lower-case named Python scripts. Each is short and hopefully self-explanatory.

## Sample commands

```sh
python transform_id_mappings.py
python inject_blockers.py
python inject_github_prs.py
python merge_users.py  # edit first; see Parameters subsection above
python assign_favorite_epic_per_story.py
```

