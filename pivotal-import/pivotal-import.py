#!/usr/bin/env python
# This imports a pivotal export CSV into Shortcut. Requires that users
# and states are properly mapped in users.csv and states.csv.
# See README.md for prerequisites, setup, and usage.
import argparse
import csv
import logging
import sys
from datetime import datetime

from lib import *

parser = argparse.ArgumentParser(
    description='Imports the Pivotal Tracker CSV export to Shortcut',
)
parser.add_argument('--apply', action='store_true', required=False)
parser.add_argument('--bulk', action='store_true', required=False)

def console_emitter(item):
    print(item)

def single_story_emitter(item):
    sc_post('/stories', item)

_bulk_accumulator = []
_bulk_limit = 20
def bulk_emitter(bulk_commit_fn):

    def flush():
        bulk_commit_fn(_bulk_accumulator)
        _bulk_accumulator.clear()

    def emitter(item):
        _bulk_accumulator.append(item)

        if len(_bulk_accumulator) >= _bulk_limit:
            flush()

    emitter.flush = flush
    return emitter

def bulk_console_emitter(items):
    print(items)

def bulk_story_creator(items):
    sc_post('/stories/bulk', { 'stories': items })


def url_to_external_links(url):
    return [url]

def split_labels(labels: str):
    return labels.split(', ')

def pivotal_state_to_workflow_state_id(state: str):
    # TODO use the actual workflow state mapping
    return state

def parse_date(d: str):
    return datetime.strptime(d, '%b %d, %Y').isoformat()

def parse_username(name):
    # TODO convert the name to the best guess for the users
    return name


col_map = {
    'title': 'name',
    'description': 'description',
    'type': 'story_type',
    'estimate': ('estimate', int),
    'priority': 'priority',
    'current state': 'pt_state',
    'labels': ('labels', split_labels),
    'url': ('external_links', url_to_external_links),
    'created at': ('created_at', parse_date),
    'accepted at': ('accepted_at', parse_date),
    'deadline': ('deadline', parse_date),
    'requested by': ('requester', parse_username),


}

nested_col_map = {
    'blocker': 'blocker',
    'blocker status': 'blocker_state',
    'task': 'task',
    'task status': 'task_state',
    'comment': 'comment'
}

# These are the keys that are currently correctly populated in the
# build_story map. They can be passed to the SC api unchanged. This
# list is effectively an allow list of top level attributes.
story_keys = [
    'name',
    'description',
    'external_links',
    'workflow_state_id',
]

def build_story(row: list[str], header: list[str], wf_map):

    d = dict()

    for ix, val in enumerate(row):
        v = val.strip()
        if not v:
            continue


        col = header[ix]
        if col in col_map:
            col_info = col_map[col]
            if isinstance(col_info, str):
                d[col_info] = v
            else:
                (key, translator) = col_info
                d[key] = translator(v)

        if col in nested_col_map:
            key = nested_col_map[col]
            d.setdefault(key, list()).append(v)

    # process workflow state
    pt_state = d.get('pt_state')
    if pt_state:
        d['workflow_state_id'] = wf_map[pt_state]

    if d['story_type'] not in ['bug','feature','chore']:
        return None

    return {k:d[k] for k in story_keys if k in d}


def load_workflow_states(csv_file):
    logger.debug(f'Loading workflow states from {csv_file}')
    d = {}
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sc_state_id = row.get('shortcut_state_id')
            if sc_state_id:
              d[row['pt_state']] = int(sc_state_id)
    return d


def main(argv):
    args = parser.parse_args(argv[1:])
    emitter = console_emitter

    if args.apply:
        if args.bulk:
            emitter = bulk_emitter(bulk_story_creator)
        else:
            emitter = single_story_emitter
    else:
        if args.bulk:
            emitter = bulk_emitter(bulk_console_emitter)
        else:
            emitter = console_emitter

    cfg = load_config()
    wf_map = load_workflow_states(cfg["states_csv_file"])
    with open(cfg["pt_csv_file"]) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            story = build_story(row, header, wf_map)
            if story:
                emitter(story)

    if hasattr(emitter, 'flush'):
        emitter.flush()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
