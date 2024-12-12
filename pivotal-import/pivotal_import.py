#!/usr/bin/env python
# This imports a pivotal export CSV into Shortcut. Requires that users
# and states are properly mapped in users.csv and states.csv.
# See README.md for prerequisites, setup, and usage.
import argparse
import csv
import re
import sys
from datetime import datetime
from collections import Counter

from lib import *

parser = argparse.ArgumentParser(
    description="Imports the Pivotal Tracker CSV export to Shortcut",
)
parser.add_argument(
    "--apply", action="store_true", help="Actually creates the entities inside Shortcut"
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


"""The batch size when running in batch mode"""
BATCH_SIZE = 100

"""The labels associated with all stories and epics that are created with this import script."""
PIVOTAL_TO_SHORTCUT_LABEL = "pivotal->shortcut"
_current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
PIVOTAL_TO_SHORTCUT_RUN_LABEL = f"pivotal->shortcut {_current_datetime}"

"""The label associated with all chore stories created from release types in Pivotal."""
PIVOTAL_RELEASE_TYPE_LABEL = "pivotal-release"

"""The label indicating a story had reviews in Pivotal."""
PIVOTAL_HAD_REVIEW_LABEL = "pivotal-had-review"


def sc_creator(items):
    """Create Shortcut entities utilizing bulk APIs whenever possible.

    Accepts a list of dicts that must have at least two keys `type`
    and `entity`. `type` must be one of:
    - epic
    - iteration
    - story

    `entity` must be the payload that is sent to the Shortcut API.

    Mutates and returns the list of items with two new keys:
    - `imported_id`: the id of the entity that was created
    - `imported_entity`: the full entity that was created
    """
    batch_stories = []

    def create_stories(stories):
        entities = [s["entity"] for s in stories]
        created_entities = sc_post("/stories/bulk", {"stories": entities})
        for created, story in zip(created_entities, stories):
            story["imported_entity"] = created
        return stories

    for item in items:
        if item["type"] == "story":
            batch_stories.append(item)
        elif item["type"] == "epic":
            res = sc_post("/epics", item["entity"])
            item["imported_entity"] = res
        elif item["type"] == "iteration":
            res = sc_post("/iterations", item["entity"])
            item["imported_entity"] = res
        elif item["type"] == "label":
            res = sc_post("/labels", item["entity"])
            item["imported_entity"] = res
        else:
            raise RuntimeError("Unknown entity type {}".format(item["type"]))

        if len(batch_stories) >= BATCH_SIZE:
            create_stories(batch_stories)
            batch_stories.clear()

    if batch_stories:
        create_stories(batch_stories)

    return items


def transform_pivotal_link(text, ctx):
    """Transform Pivotal Tracker links to Shortcut story links.

    Args:
        text: Text containing Pivotal Tracker links
        ctx: Context dictionary containing ID mappings

    Returns:
        str: Text with transformed links
    """
    # Transform full URLs
    url_pattern = r'https://www\.pivotaltracker\.com/story/show/(\d+)'
    def url_replace(match):
        pt_id = match.group(1)
        sc_id = ctx.get("id_mapping", {}).get(pt_id)
        return f'https://app.shortcut.com/shortcut/story/{sc_id if sc_id else pt_id}'
    text = re.sub(url_pattern, url_replace, text)

    # Transform ID references (#123)
    id_pattern = r'#(\d+)'
    def id_replace(match):
        pt_id = match.group(1)
        sc_id = ctx.get("id_mapping", {}).get(pt_id)
        return f'[{sc_id}]' if sc_id else f'#{pt_id}'
    return re.sub(id_pattern, id_replace, text)

def transform_github_link(url):
    """Transform GitHub PR/branch links to external link format.

    Args:
        url (str): GitHub URL for PR or branch

    Returns:
        str: Standardized external link format
    """
    # Already in standard format - GitHub URLs work as-is
    return url

def url_to_external_links(url):
    if "pivotaltracker.com" in url:
        return []  # Skip Pivotal links - they'll be transformed in text
    if "github.com" in url:
        return [transform_github_link(url)]
    return [url]  # Preserve existing behavior for other URLs


def parse_labels(labels: str):
    return [{"name": label} for label in re.split(r"\s*,\s*", labels)]


def parse_priority(priority):
    lowered = priority.lower()
    if lowered == "none":
        return None
    else:
        return lowered


col_map = {
    "accepted at": ("accepted_at", parse_date_time),
    "created at": ("created_at", parse_date_time),
    "current state": "pt_state",
    "deadline": ("deadline", parse_date_time),
    "description": "description",
    "estimate": ("estimate", int),
    "id": "external_id",
    "iteration": "pt_iteration_id",
    "iteration end": ("pt_iteration_end_date", parse_date),
    "iteration start": ("pt_iteration_start_date", parse_date),
    "labels": ("labels", parse_labels),
    "priority": ("priority", parse_priority),
    "requested by": "requester",
    "title": "name",
    "type": "story_type",
    "url": ("external_links", url_to_external_links),
}

nested_col_map = {
    "blocker status": "blocker_state",
    "blocker": "blocker",
    "comment": ("comments", parse_comment),
    "owned by": "owners",
    "reviewer": "reviewers",
    "review type": "review_types",
    "review status": "review_states",
    "task status": "task_states",
    "task": "task_titles",
}

# These are the keys that are currently correctly populated in the
# build_entity map. They can be passed to the SC api unchanged. This
# list is effectively an allow list of top level attributes.
select_keys = {
    "story": [
        "comments",
        "created_at",
        "custom_fields",
        "deadline",
        "description",
        "estimate",
        "external_id",
        "external_links",
        "follower_ids",
        "group_id",
        "iteration_id",
        "labels",
        "name",
        "owner_ids",
        "requested_by_id",
        "story_type",
        "tasks",
        "workflow_state_id",
    ],
    "epic": [
        "created_at",
        "description",
        "external_id",
        "group_ids",
        "labels",
        "name",
    ],
}

review_as_comment_text_prefix = """\\[Pivotal Importer\\] Reviewers have been added as followers on this Shortcut Story.

The following table describes the state of their reviews when they were imported into Shortcut from Pivotal Tracker:

| Reviewer | Review Type | Review Status |
|---|---|---|"""


def escape_md_table_syntax(s):
    return s.replace("|", "\\|")


def parse_row(row, headers, ctx=None):
    d = dict()
    for ix, val in enumerate(row):
        v = val.strip()
        if not v:
            continue

        col = headers[ix]
        if col in col_map:
            col_info = col_map[col]
            if isinstance(col_info, str):
                if col == "description" and ctx and "id_mapping" in ctx:
                    # Transform Pivotal links in description
                    v = transform_pivotal_link(v, ctx)
                d[col_info] = v
            else:
                (key, translator) = col_info
                if col == "url":
                    # URL field uses url_to_external_links translator
                    d[key] = translator(v)
                else:
                    d[key] = translator(v)

        if col in nested_col_map:
            col_info = nested_col_map[col]
            key = None
            if isinstance(col_info, str):
                key = col_info
            else:
                (key, translator) = col_info
                v = translator(v)
            d.setdefault(key, []).append(v)

        # Handle GitHub PR/branch links
        if col in ["pull_request", "git_branch"] and v:
            d.setdefault("external_links", []).append(transform_github_link(v))

    return d


def build_run_label_entity():
    return {"type": "label", "entity": {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}}


def build_entity(ctx, d):
    """Process the row to generate the payload needed to create the entity in Shortcut."""
    # ensure Shortcut entities have a Label that identifies this import
    d.setdefault("labels", []).extend(
        [{"name": PIVOTAL_TO_SHORTCUT_LABEL}, {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}]
    )

    # The Shortcut Team/Group ID to assign to stories/epics,
    # may be None which the REST API interprets correctly.
    group_id = ctx["group_id"]

    # reconcile entity types
    type = "story"
    if d["story_type"] == "epic":
        type = "epic"

    # process comments
    comments = []
    for comment in d.get("comments", []):
        new_comment = comment.copy()
        author = new_comment.get("author")
        if author:
            del new_comment["author"]
            author_id = ctx["user_config"].get(author)
            if author_id:
                new_comment["author_id"] = author_id
        comments.append(new_comment)
    # other things we process are reified as comments,
    # so we'll add comments to the d later in processing

    # releases become Shortcut Stories of type "chore"
    if d["story_type"] == "release":
        d["story_type"] = "chore"
        d.setdefault("labels", []).append({"name": PIVOTAL_RELEASE_TYPE_LABEL})

    iteration = None
    pt_iteration_id = d["pt_iteration_id"] if "pt_iteration_id" in d else None
    if type == "story":
        # assign to team/group
        d["group_id"] = group_id
        # process workflow state
        pt_state = d.get("pt_state")
        if pt_state:
            d["workflow_state_id"] = ctx["workflow_config"][pt_state]

        # process tasks
        tasks = [
            {"description": title, "complete": state == "completed"}
            for (title, state) in zip(
                d.get("task_titles", []), d.get("task_states", [])
            )
        ]
        if tasks:
            d["tasks"] = tasks

        # process user fields
        user_to_sc_id = ctx["user_config"]
        requester = d.get("requester")
        if requester:
            # if requester isn't found, this will cause the api to use
            # the owner of the token as the requester
            sc_requester_id = user_to_sc_id.get(requester)
            if sc_requester_id:
                d["requested_by_id"] = sc_requester_id

        owners = d.get("owners")
        if owners:
            d["owner_ids"] = [
                # filter out owners that aren't found
                user_to_sc_id[owner]
                for owner in owners
                if owner in user_to_sc_id
            ]

        reviewers = d.get("reviewers")
        if reviewers:
            d["follower_ids"] = [
                user_to_sc_id[reviewer]
                for reviewer in reviewers
                if reviewer in user_to_sc_id
            ]
            d.setdefault("labels", []).append({"name": PIVOTAL_HAD_REVIEW_LABEL})

        # format table of all reviewers, types, and statuses as a comment on the imported story
        if reviewers:
            comment_text = review_as_comment_text_prefix
            for reviewer, review_type, review_status in zip(
                d.get("reviewers", []),
                d.get("review_types", []),
                d.get("review_states", []),
            ):
                reviewer = escape_md_table_syntax(reviewer)
                review_type = escape_md_table_syntax(review_type)
                review_status = escape_md_table_syntax(review_status)
                comment_text += f"\n|{reviewer}|{review_type}|{review_status}|"
            comments.append(
                {"author_id": d.get("requested_by_id", None), "text": comment_text}
            )

        # Custom Fields
        custom_fields = []
        # process priority as Priority custom field
        pt_priority = d.get("priority")
        if pt_priority:
            custom_fields.append(
                {
                    "field_id": ctx["priority_custom_field_id"],
                    "value_id": ctx["priority_config"][pt_priority],
                }
            )

        if custom_fields:
            d["custom_fields"] = custom_fields

        if pt_iteration_id:
            # Python dicts are not hashable and thus can't be
            # put into a set. To avoid extra-extra bookeeping,
            # capturing this as a trivially-parsable string
            # which can be accrued in a set in the entity
            # collector.
            start_date = d["pt_iteration_start_date"]
            end_date = d["pt_iteration_end_date"]
            iteration = "|".join([pt_iteration_id, start_date, end_date])

        # as a last step, ensure comments (both those that were comments
        # in Pivotal, and those we add during import to fill feature gaps)
        # are all added to the d dict
        if comments:
            d["comments"] = comments
        elif "comments" in d:
            del d["comments"]

    elif type == "epic":
        # While Pivotal's model does not have a requester or owners for
        # Epics, we can still apply the provided Team/Group assignment.
        d["group_ids"] = [group_id] if group_id is not None else []

    entity = {k: d[k] for k in select_keys[type] if k in d}
    return {
        "type": type,
        "entity": entity,
        "iteration": iteration,
        "pt_iteration_id": pt_iteration_id,
        "parsed_row": d,
    }


def load_mapping_csv(csv_file, from_key, to_key, to_transform=identity):
    d = {}
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            val_str = row.get(to_key)
            val = None
            if val_str:
                val = to_transform(val_str)
            d[row[from_key]] = val

    return d


def load_priorities(csv_file):
    logger.debug(f"Loading priorities from {csv_file}")
    return load_mapping_csv(csv_file, "pt_priority", "shortcut_custom_field_value_id")


def load_users(csv_file):
    logger.debug(f"Loading users from {csv_file}")
    email_to_id = {user["email"]: user["id"] for user in fetch_members()}
    user_to_email = load_mapping_csv(csv_file, "pt_user_name", "shortcut_user_email")
    return {
        pt_user: email_to_id.get(sc_email)
        for pt_user, sc_email in user_to_email.items()
        if sc_email
    }


def load_workflow_states(csv_file):
    logger.debug(f"Loading workflow states from {csv_file}")
    return load_mapping_csv(csv_file, "pt_state", "shortcut_state_id", int)


def get_mock_emitter():
    _mock_global_id = 0

    def _get_next_id():
        nonlocal _mock_global_id
        id = _mock_global_id
        _mock_global_id += 1
        return id

    def mock_emitter(items):
        for item in items:
            entity_id = _get_next_id()
            created_entity = item["entity"].copy()
            created_entity["id"] = entity_id
            created_entity["entity_type"] = item["type"]
            created_entity["app_url"] = f"https://example.com/entity/{entity_id}"
            item["imported_entity"] = created_entity
            print(
                'Creating {} {} "{}"'.format(
                    item["type"], entity_id, item["entity"]["name"]
                )
            )
        return items

    return mock_emitter


def collect_epic_label_mapping(epics):
    """
    Return a dict mapping label names to Shortcut Epic ID.
    """
    epic_label_map = {}
    for epic in epics:
        for label in epic["entity"]["labels"]:
            label_name = label["name"]
            if (
                label_name is not PIVOTAL_TO_SHORTCUT_LABEL
                and label_name is not PIVOTAL_TO_SHORTCUT_RUN_LABEL
            ):
                epic_label_map[label_name] = epic["imported_entity"]["id"]
    return epic_label_map


def assign_stories_to_epics(stories, epics):
    """
    Mutate the `stories` to set an epic_id if that story is assigned to that epic.
    """
    epic_label_map = collect_epic_label_mapping(epics)
    for story in stories:
        for label in story["entity"].get("labels", []):
            label_name = label["name"]
            epic_id = epic_label_map.get(label_name)
            logger.debug(f"story epic id {epic_id}")
            if epic_id is not None:
                story["entity"]["epic_id"] = epic_id
    return stories


def collect_pt_iteration_mapping(iterations):
    """
    Return a dict mapping Pivotal iteration IDs to their corresponding Shortcut Iteration IDs.
    """
    d = {}
    for iteration in iterations:
        pt_iteration_id = iteration["pt_iteration_id"]
        sc_iteration_id = iteration["imported_entity"]["id"]
        d[str(pt_iteration_id)] = sc_iteration_id
    return d


def assign_stories_to_iterations(stories, iterations):
    """
    Mutate the `stories` to set an iteration_id if that story is assigned to that iteration.
    """
    pt_iteration_mapping = collect_pt_iteration_mapping(iterations)
    for story in stories:
        pt_iteration_id = story["pt_iteration_id"]
        if pt_iteration_id:
            sc_iteration_id = pt_iteration_mapping[str(pt_iteration_id)]
            story["entity"]["iteration_id"] = sc_iteration_id
    return stories


class EntityCollector:
    """Collect and process entities for import into Shortcut.

    The emitter is a function that takes a list of entities and
    performs the actions needed to create those entities in
    Shortcut. Must return a list of ids that represent the created
    entities.
    """

    def __init__(self, emitter=None):
        _mock_global_id = 0
        self.stories = []
        self.epics = []
        self.files = []
        # set of strings in {id}|{start}|{end} format
        # because dicts aren't hashable in Python
        self.iteration_strings = set()
        # to be populated at commit()
        self.iterations = []
        self.labels = []
        if emitter is None:
            emitter = get_mock_emitter()
        self.emitter = emitter

    def collect(self, item):
        if item["type"] == "story":
            self.stories.append(item)
            if item["iteration"]:
                self.iteration_strings.add(item["iteration"])
        elif item["type"] == "epic":
            self.epics.append(item)
        elif item["type"] == "label":
            self.labels.append(item)
        else:
            raise RuntimeError("Unknown entity type {}".format(item["type"]))

        return {item["type"]: 1}

    def link_entities(self):
        # find all epics and their associated label
        # find all stories
        pass

    def commit(self):
        # create all the default labels
        self.labels = self.emitter(self.labels)
        for label in self.labels:
            if PIVOTAL_TO_SHORTCUT_RUN_LABEL == label["entity"]["name"]:
                label_url = label["imported_entity"]["app_url"]
                print(
                    f"Import Started\n\n==> Click here to monitor import progress: {label_url}"
                )

        # create all the epics and find their associated Shortcut epic ids
        self.epics = self.emitter(self.epics)
        print("Finished creating {} epics".format(len(self.epics)))
        assign_stories_to_epics(self.stories, self.epics)

        # create all iterations and find their associated Shortcut iteration ids
        iteration_entities = []
        for iteration_string in self.iteration_strings:
            id, start_date, end_date = iteration_string.split("|")
            name = f"PT {id}"
            iteration_entities.append(
                {
                    "type": "iteration",
                    "pt_iteration_id": id,
                    "entity": {
                        "name": name,
                        "start_date": start_date,
                        "end_date": end_date,
                    },
                }
            )
        self.iterations = self.emitter(iteration_entities)
        print("Finished creating {} iterations".format(len(self.iterations)))
        assign_stories_to_iterations(self.stories, self.iterations)

        # upload files attached to stories so they can be associated during Story creation
        for story in self.stories:
            pt_id = story["entity"]["external_id"]
            pt_files_dir = f"data/{pt_id}"
            if os.path.isdir(pt_files_dir):
                file_entities = sc_upload_files(
                    [
                        os.path.join(dirpath, f)
                        for (dirpath, _, filenames) in os.walk(pt_files_dir)
                        for f in filenames
                    ]
                )
                self.files += [
                    {"imported_entity": file_entity} for file_entity in file_entities
                ]
                story["entity"]["file_ids"] = [
                    file_entity["id"] for file_entity in file_entities
                ]

        # create all the stories
        self.stories = self.emitter(self.stories)
        print("Finished creating {} stories".format(len(self.stories)))

        # Aggregate all the created stories, epics, iterations, and labels into a list of maps
        created_entities = []
        created_set = set()
        for item in self.epics + self.iterations + self.files + self.stories:
            entity = item["imported_entity"]
            if entity["id"] not in created_set:
                created_entities.append(entity)
                created_set.add(entity["id"])

        return created_entities


def process_pt_csv_export(ctx, pt_csv_file, entity_collector):
    stats = Counter()
    stats.update(entity_collector.collect(build_run_label_entity()))

    with open(pt_csv_file) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]

        # First pass: collect all stories to build ID mapping
        story_rows = []
        for row in reader:
            story_rows.append(row)
            row_info = parse_row(row, header, ctx)
            if "id" in row_info:
                ctx["id_mapping"][row_info["id"]] = None  # Placeholder for Shortcut ID

        # Reset file pointer for second pass
        csvfile.seek(0)
        next(reader)  # Skip header

        # Second pass: process stories with complete mapping
        for row in story_rows:
            row_info = parse_row(row, header, ctx)
            entity = build_entity(ctx, row_info)
            if entity["type"] == "story":
                # Update ID mapping with new Shortcut ID
                pt_id = entity["parsed_row"]["id"]
                if "imported_entity" in entity:
                    ctx["id_mapping"][pt_id] = entity["imported_entity"]["id"]
            logger.debug("Emitting Entity: %s", entity)
            stats.update(entity_collector.collect(entity))

    print("Summary of data to be imported")
    print_stats(stats)


def write_created_entities_csv(created_entities):
    with open(shortcut_imported_entities_csv, "w") as f:
        writer = csv.DictWriter(
            f, ["id", "type", "name", "epic_id", "iteration_id", "url"]
        )
        writer.writeheader()
        for entity in created_entities:
            writer.writerow(
                {
                    "id": entity["id"],
                    "type": entity["entity_type"],
                    "name": entity["name"],
                    "epic_id": entity["epic_id"] if "epic_id" in entity else None,
                    "iteration_id": (
                        entity["iteration_id"] if "iteration_id" in entity else None
                    ),
                    "url": entity["app_url"] if "app_url" in entity else entity["url"],
                }
            )


def build_ctx(cfg):
    ctx = {
        "group_id": cfg["group_id"],
        "priority_config": load_priorities(cfg["priorities_csv_file"]),
        "priority_custom_field_id": cfg["priority_custom_field_id"],
        "user_config": load_users(cfg["users_csv_file"]),
        "workflow_config": load_workflow_states(cfg["states_csv_file"]),
        "id_mapping": {},  # Initialize empty mapping for Pivotal->Shortcut IDs
    }
    logger.debug("Built context %s", ctx)
    return ctx


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    emitter = None
    if args.apply:
        emitter = sc_creator

    entity_collector = EntityCollector(emitter)

    # We need to make API requests before fully validating local config.
    validate_environment()
    cfg = load_config()
    ctx = build_ctx(cfg)
    print_rate_limiting_explanation()
    process_pt_csv_export(ctx, cfg["pt_csv_file"], entity_collector)

    created_entities = entity_collector.commit()
    write_created_entities_csv(created_entities)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
