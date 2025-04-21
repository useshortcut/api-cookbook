import  backoff
from    boltons.iterutils       import get_path
from    dataclasses             import dataclass
from    itertools               import islice
import  json
import  os
import  requests
from    throttlex               import Throttler

@dataclass
class ShortcutUser:
    scid            : str
    name            : str
    email           : str

@dataclass
class ShortcutStoryMeta: # Can represent metadata of a story or epic
    type_single     : str # 'story'   or 'epic'
    type_plural     : str # 'stories' or 'epics'
    scid            : str
    name            : str
    owner_scids     : list[str]
    follower_scids  : list[str]
    requester_scid  : str

class ShortcutMetadata:

    def __init__( self ):

        # Set API params
        self.uri_base       = 'https://api.app.shortcut.com/api/v3'
        self.headers        = { 'Shortcut-Token': os.getenv('SHORTCUT_API_TOKEN'), 'Content-Type': 'application/json' }
        self.throttler      = Throttler( max_req = 199, period = 60 )

        # Get URL slug and mapping from PT id to SC id
        member              = self.call_sc( requests.get, url_path = f'member', body = None, cache_file = f'cache/00-member.json' )
        self.url_slug       = member['workspace2']['url_slug']
        self.scid_from_ptid = self._make_scid_from_ptid()

    @backoff.on_exception( backoff.expo, Exception, max_tries = 5 )
    def call_sc( self, requests_fcn, url_path, body = None, cache_file = None ):

        # If cache exists, return its contents
        if cache_file and os.path.exists( cache_file ):
            with open( cache_file, 'r' ) as f: return json.load(f)

        # Make the API call and populate the cache
        resp = requests_fcn( url = self.throttler.throttle(f'{self.uri_base}/{url_path}'), headers = self.headers, json = body or {} )
        assert resp.status_code in { 200, 201 }, f'FAILED: {resp.text}'
        if cache_file:
            with open( cache_file, 'w' ) as f: json.dump( resp.json(), f )
        return resp.json()

    def _make_scid_from_ptid( self ):

        def gen_id_mappings( type, requests_fcn, url_path, body ):
            j = self.call_sc( requests_fcn, url_path = url_path, body = body, cache_file = f'cache/00-{type}.json' )
            for d in j: yield d.get('id',''), d.get('external_id','')

        ge = gen_id_mappings( 'epic',  requests.get,  f'epics',          {}                                           )
        gs = gen_id_mappings( 'story', requests.post, f'stories/search', { 'created_at_end': '2999-12-31T00:00:00Z' } ) # SC API seems to require at least one filter

        return {
            'epic'  : { ptid: scid for scid, ptid in ge },
            'story' : { ptid: scid for scid, ptid in gs },
        }

    def gen_story_or_epic_meta( self, want_cache: bool ):

        def gen_meta( type_plural, requests_fcn, url_path, body ):
            j = self.call_sc( requests_fcn, url_path = url_path, body = body, cache_file = f'cache/00-{type_plural}.json' if want_cache else '' )
            for d in j: yield ShortcutStoryMeta(
                type_single    = { 'epics': 'epic', 'stories': 'story'} .get(type_plural,''),
                type_plural    = type_plural,
                scid           = d.get( 'id',              '' ),
                name           = d.get( 'name',            '' ),
                owner_scids    = d.get( 'owner_ids',       [] ),
                follower_scids = d.get( 'follower_ids',    [] ),
                requester_scid = d.get( 'requested_by_id', '' ),
            )
        yield from gen_meta( 'epics',   requests.get,  f'epics',          {}                                           )
        yield from gen_meta( 'stories', requests.post, f'stories/search', { 'created_at_end': '2999-12-31T00:00:00Z' } ) # SC API seems to require at least one filter

    def gen_users( self ):

        j = self.call_sc( requests.get, 'members' )
        for d in j: yield ShortcutUser(
            scid   = get_path( d, ('id',),                     ''),
            email  = get_path( d, ('profile','email_address'), ''),
            name   = get_path( d, ('profile','name'),          ''),
        )    

if __name__ == '__main__':

    sm = ShortcutMetadata()
    print( list(sm.gen_users()) )
    print( list(sm.gen_story_or_epic_meta( want_cache = False )) )
    print( list(sm._make_scid_from_ptid()) )
