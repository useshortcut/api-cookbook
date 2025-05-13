from   boltons.dictutils        import OrderedMultiDict
from   dataclasses              import dataclass
from   itertools                import islice
import json
import os
import regex
from   typing                   import Iterable

from   PivotalExport            import PivotalBlocker, PivotalExport, PivotalItemLabelRec
from   ShortcutMetadata         import ShortcutMetadata
from   ShortcutObject           import ShortcutObject, ShortcutStoryLink

VERBOSE = True

@dataclass
class ChangeOrder:
    story         : ShortcutObject
    storyrec      : PivotalItemLabelRec
    epicrec       : PivotalItemLabelRec
    epic_scid_old : int
    epic_scid_new : int

def score_epic_given_story( epicrec: PivotalItemLabelRec, storyrec: PivotalItemLabelRec ) -> float:
    '''
    Using heuristics that will be unique to each organization, assign a score that's highest for
    the Pivotal epic that's most likely to be the one primary epic for the given story.
    '''

    # In our organization, the score depends only on the name
    ename  = epicrec.item_name.lower()
    sname  = storyrec.item_name.lower()

    # Handle some very organization-specific special names
    if sname.startswith( 'cell'    ) : sname = sname[:4] + ' ' + sname[4:]
    if sname.startswith( 'channel' ) : sname = sname[:7] + ' ' + sname[7:]
    if ename == 'portal'          : return 1
    if ename.startswith( 'soon' ) : return 0

    # Handle our organization's "prefix" rule
    if sname.startswith( ename  ) : return 100 * len(ename)

    # Fall back to a bag-of-words comparison
    ewords = set( word for w in regex.split( r'\W+', ename ) if ( word := w.strip() ) )
    swords = set( word for w in regex.split( r'\W+', sname ) if ( word := w.strip() ) )
    score = 1 + len( ewords & swords )
    return score

def choose_favorite_epic( storyrec: PivotalItemLabelRec, epicrecs: list[PivotalItemLabelRec] ) -> PivotalItemLabelRec:

    # Choose the favorite
    epicrec = max(
        epicrecs,
        key = lambda e: score_epic_given_story( epicrec = e, storyrec = storyrec )
    )

    if VERBOSE and len(epicrecs) > 1:
        print( f'Story: {storyrec.item_name}' )
        print( f'  FAVE: { epicrec.item_name if epicrec else "None" }' )
        for e in epicrecs: print( f'  Epic: {e.item_name}' )

    # Return the favorite's Pivotal ID or None
    return epicrec

def make_epicrec_from_storyrec( storyrecs: list[PivotalItemLabelRec], epicrec_from_label: dict[str,PivotalItemLabelRec] ) -> dict[PivotalItemLabelRec,PivotalItemLabelRec]:

    def gen_epicrecs( storyrec ):
        for label in storyrec.labels:
            epicrec = epicrec_from_label.get(label,None)
            if epicrec: yield epicrec

    return {
        storyrec: choose_favorite_epic( storyrec, epicrecs )
        for storyrec in storyrecs
        if ( epicrecs := list( gen_epicrecs(storyrec) ) )
        if len( epicrecs ) > 1
    }

def make_epicrec_from_label( itemlabelrecs: Iterable[PivotalItemLabelRec] ) -> dict[str,PivotalItemLabelRec]:
    '''
    Given an iterable of all PivotalItemLabelRec objects from Pivotal, return a dictionary from label to the one such object representing the exactly one epic that contains the label
    '''

    # Build OMD from label to PivotalItemLabelRec objects for each of the possible epics
    omd_itemlabelrecs_from_label = OrderedMultiDict(
        ( label, itemlabelrec )
        for itemlabelrec in itemlabelrecs
        if  itemlabelrec.item_type == 'epic'
        for label in itemlabelrec.labels
    )

    # Warn the user that we cannot handle a label that appears in many epics (but we don't think these exist in a typical Pivotal workspace)
    for label in omd_itemlabelrecs_from_label:
        itemlabelrecs = omd_itemlabelrecs_from_label.getlist(label)
        if len( itemlabelrecs ) > 2: print( f'WARNING: Skipping label {label} because it appears in multiple epics: {[ r.item_id for r in itemlabelrecs ]}' )

    # Return a dictionary containing only cases in which a label appears in exactly one epic
    return {
        label: epicrecs[0]
        for label in omd_itemlabelrecs_from_label
        if ( epicrecs := omd_itemlabelrecs_from_label.getlist(label) ) 
        if len( epicrecs ) == 1
    }

def gen_changeorders( sm: ShortcutMetadata, epicrec_from_storyrec: dict ):

    # Outer loop is over associations found by make_epicrec_from_storyrec()
    for storyrec, epicrec in epicrec_from_storyrec.items():

        # If no epic was identified, skip
        if not epicrec: continue

        # Look up Shortcut IDs from Pivotal IDs
        story_scid = sm.scid_from_ptid['story'] .get( storyrec.item_id, None )
        epic_scid  = sm.scid_from_ptid['epic']  .get( epicrec.item_id,  None )

        # If either scid is missing, warn and do nothing
        if not ( story_scid and epic_scid ):
            print( f'WARNING: Did not write anything to Shortcut regarding linkage of Pivotal story "{storyrec.item_name}" to Pivotal epic "{epicrec.item_name}" because their Shortcut IDs are not both truthy: {story_scid} and {epic_scid}' ) 
            continue

        # If the the write would be a no-op, inform and do nothing
        story  = ShortcutObject( sm, 'stories', story_scid )
        epic_scid_old = story.epic_id
        if epic_scid == epic_scid_old:
            print( f'No need for change: story "{storyrec.item_name}" is already in epic "{epicrec.item_name}"' )
            continue

        # Order a change
        yield ChangeOrder(
            story         = story,
            storyrec      = storyrec,
            epicrec       = epicrec,
            epic_scid_old = epic_scid_old,
            epic_scid_new = epic_scid,
        )

def write_epic_to_story( sm: ShortcutMetadata, co: ChangeOrder, prefix: str ):

    # Write to Shortcut
    print( f'{prefix}Story "{co.storyrec.item_name}" currently is assigned to this epic: https://app.shortcut.com/{sm.url_slug}/epic/{co.epic_scid_old}.' )
    x = input( f'    Do you want to assign it instead to "{co.epicrec.item_name}" (https://app.shortcut.com/{sm.url_slug}/epic/{co.epic_scid_new})? [y/N]: ' )
    if x.lower() != 'y':
        print( f'    ...skipping' )
        return
    co.story.clear()
    co.story.epic_id = co.epic_scid_new
    co.story.write()
    print( f'    ...DONE!' )

def main():

    # For each epic and story, find its list of labels
    sm                     = ShortcutMetadata()
    pe                     = PivotalExport( '../data/pivotal_export.csv' )
    itemlabelrecs          = list( pe.gen_itemlabelrecs() )

    # For each Pivotal story that has at least one label, identify its one favorite Pivotal epic
    epicrec_from_label     = make_epicrec_from_label( itemlabelrecs )
    epicrec_from_storyrec  = make_epicrec_from_storyrec(
        storyrecs             = [ rec for rec in itemlabelrecs if rec.item_type != 'epic' ],
        epicrec_from_label    = epicrec_from_label
    )

    # Compare with reality to see how many changes are needed
    changeorders           = list( gen_changeorders( sm, epicrec_from_storyrec ) )
    changeordern           = len( changeorders )

    # Report key numbers
    print( f'Number epics and stories with at least  one label : {len(itemlabelrecs)}'         )
    print( f'Number           stories with more than one label : {len(epicrec_from_storyrec)}' )
    print( f'Number of change orders to consider               : {changeordern}'               )

    # Write them
    for i, co in enumerate(changeorders): write_epic_to_story( sm, co, prefix = f'{i} of {changeordern}: ' )

main()
