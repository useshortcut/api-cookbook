from    dataclasses             import asdict, dataclass
import  os
import  requests
from    ShortcutMetadata        import ShortcutMetadata

@dataclass( frozen = True, eq = True ) # These settings make objects of this class hashable. We'll need that for set operations used by the caller.
class ShortcutStoryLink:
    subject_id : int|None
    verb       : str
    object_id  : int|None

class ShortcutObject:

    def __init__( self, sm: ShortcutMetadata, type: str, scid ):
        '''
        Represents one Shortcut epic or story.
        Odd but practical semantics: during a write, if any of the following are falsy or missing, that means 'the same as what's already in the cloud'
          - self.desc
          - self.comms[i]
          - self.storylinks[i]
        '''

        # Memorize params
        self.sm             = sm
        self.type           = type
        self.scid           = scid

        # Read object
        obj                 = self.sm.call_sc( requests.get, url_path = f'{self.type}/{self.scid}' )
        self.name    : str  = obj.get('name','')
        self.desc    : str  = obj.get('description','')
        self.comms   : dict = { d.get('id',None): d.get('text') for d in obj.get('comments',[]) }
        self.epic_id : int  = obj.get('epic_id',0)
        self.storylinks     = [
            ShortcutStoryLink(
                subject_id = d.get( 'subject_id', None ),
                verb       = d.get( 'verb',       ''   ),
                object_id  = d.get( 'object_id',  None ),
            )
            for d in obj.get('story_links',[])
        ]

    def clear( self ):

        self.desc       = ''
        self.comms      = {}
        self.epic_id    = 0
        self.storylinks = []

    def write( self ):

        if self.desc:       self.sm.call_sc( requests.put,  url_path = f'{self.type}/{self.scid}', body = { 'description': self.desc    } )
        if self.epic_id:    self.sm.call_sc( requests.put,  url_path = f'{self.type}/{self.scid}', body = { 'epic_id'    : self.epic_id } ) # we rely on caller not to make a truthy epic_id for an Epic

        for k,v in self.comms.items():
            if v:           self.sm.call_sc( requests.put,  url_path = f'{self.type}/{self.scid}/comments/{k}', body = { 'text': v } )

        for sl  in self.storylinks:
                            self.sm.call_sc( requests.post, url_path = f'story-links', body = asdict(sl) )


if __name__ == '__main__':

    from throttlex import Throttler

    sm        = ShortcutMetadata()
    so        = ShortcutObject( sm, 'epics', 68715 )
    print( so.desc )
    print( so.comms )
