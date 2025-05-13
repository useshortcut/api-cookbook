from   boltons.dictutils        import OrderedMultiDict
from   itertools                import islice
import json
import os
import regex

from   PivotalExport            import PivotalBlocker, PivotalExport
from   ShortcutMetadata         import ShortcutMetadata
from   ShortcutObject           import ShortcutObject, ShortcutStoryLink

def write_storylinks_for_story( sm, blockee_scid, pbs: list[PivotalBlocker], prefix: str ):

    # Skip if there are no blockers to write
    if not pbs: return
    
    # Read existing set of Story Links for story
    story       = ShortcutObject( sm, 'stories', blockee_scid )
    sls_current = set( story.storylinks )

    # Construct desired Story Links
    sls_pivotal = set((
        ShortcutStoryLink(
            subject_id = blocker_scid,
            verb       = 'blocks',
            object_id  = blockee_scid,
        )
        for pb in pbs
        if ( blocker_scid := sm.scid_from_ptid['story'].get(pb.blocker_id,None) )
    ))
    
    # Skip if there are no blockers to write
    if not sls_pivotal: return    

    # Decide which ones to write, eliminating duplicates so as to guarantee idempotency
    sls_towrite = sls_pivotal - sls_current
    sls_toskip  = sls_pivotal & sls_current

    # Report plan
    print( f'{prefix}For story {blockee_scid:8d} ({story.name}):' )
    for sl in sls_toskip  : print( f'  Skipping : {sl}' )
    for sl in sls_towrite : print( f'  WRITING  : {sl}' )

    # Execute writes
    story.clear()
    story.storylinks = list(sls_towrite)
    story.write()

def main():

    # Read extracts from the Pivotal export data and from Shortcut (metadata only)
    pe = PivotalExport( '../data/pivotal_export.csv' )
    sm = ShortcutMetadata()

    # Consolidate PivotalBlocker objects by Shortcut ID of 'blockee' in preparation for iterating over Shortcut stories
    md = OrderedMultiDict(
        ( scid, pb )
        for pb in pe.gen_blockers()
        if pb.blockee_type not in { 'epic', 'release' } # All others become Shortcut stories
        if ( scid := sm.scid_from_ptid['story'].get(pb.blockee_id,None) )
    )

    # Report the total number of entries to write
    scids = list( scid for scid in sm.scid_from_ptid['story'].values() if md.getlist(scid) )
    scidn = len( scids )
    print( f'Number of stories to write: {scidn}' )

    # Iterate over Shortcut stories, writing its story links wherever appropriate
    for i, scid in enumerate(scids): write_storylinks_for_story( sm, scid, md.getlist(scid), prefix = f'{i} of {scidn}: ' )

main()
