from   itertools                import islice
import json
import os
import regex

from   ShortcutMetadata         import ShortcutMetadata
from   ShortcutObject           import ShortcutObject


def make_edited_string( s: str, scid_from_ptid, url_slug ):
    '''
    Return an edited copy of `s`, or None if the output would have been identical to the input
    '''

    # Remember the original string (note that Python strings are immutable, so making a copy is unnecessary and would be a no-op)
    s_orig = s

    # Define patterns to spot
    pats = [
        ( 'story', r'(?<!#|PR\s)#(?P<id>\d+)(?!\]|\d)' ), # ACHTUNG! The negative lookahead at the end of this is designed to ignore strings like '[#1234567]' and '[Fixes #2345678]' and 'PR #1234'. Remove it if you want those transformed.
        ( 'epic',            r'##(?P<id>\d+)(?!\]|\d)' ), # ACHTUNG! The negative lookahead at the end of this is designed to ignore strings like '[##123456]' and '[Fixes ##234567]'. Remove it if you want those transformed.
    ]

    # Apply them
    for type, pat in pats:
        for m in list(regex.finditer(pat,s))[::-1]: # iterate over matches, ordering right to left to preserve validity of indices to the left of each successive match
            orig = s[ m.start() : m.end() ]
            print( f'orig = |{orig}|')
            ptid = m.group('id'); assert ptid
            scid = scid_from_ptid[type].get(ptid,None)
            if not scid:
                print( f'Warning: Scanning your workspace did not produce a Shortcut ID corresponding to Pivotal Tracker ID {ptid}, but the latter does appear in the string {orig}' )
                continue
            s = s[:m.start()] + f'https://app.shortcut.com/{url_slug}/{type}/{scid}' + s[m.end():]

    # Return the edited string, or None if it's identical to the original string
    return s if s != s_orig else None

def edit_item( sm, type, scid ):

    print( f'Editing {scid} in {type}...' )

    item       = ShortcutObject( sm, type, scid )
    item.desc  =      make_edited_string( item.desc, sm.scid_from_ptid, sm.url_slug )
    item.comms = { k: make_edited_string( v,         sm.scid_from_ptid, sm.url_slug ) for k,v in item.comms.items() }
    item.write()

def main():

    sm = ShortcutMetadata()
    for scid in sm.scid_from_ptid['epic']  .values(): edit_item( sm, 'epics',   scid )
    for scid in sm.scid_from_ptid['story'] .values(): edit_item( sm, 'stories', scid )

main()
