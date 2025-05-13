import  requests
from    ShortcutMetadata        import ShortcutMetadata, ShortcutStoryMeta, ShortcutUser

user_email_lose = 'user-to-lose@example.com'
user_email_gain = 'user-to-gain@example.com'

def transform_item( sm: ShortcutMetadata, item: ShortcutStoryMeta, user_lose: ShortcutUser, user_gain: ShortcutUser ):

    # Compute new scids
    def transform_scid( scid: str ):
        return user_gain.scid if scid == user_lose.scid else scid
    owner_scids    = list(map( transform_scid, item.owner_scids    ))
    follower_scids = list(map( transform_scid, item.follower_scids ))
    requester_scid = transform_scid( item.requester_scid )

    # Compute body of call to PUT
    body = ( {}
        | ( {} if requester_scid      == item.requester_scid      else { 'requested_by_id' : requester_scid } )
        | ( {} if set(owner_scids)    == set(item.owner_scids)    else { 'owner_ids'       : owner_scids    } )
        | ( {} if set(follower_scids) == set(item.follower_scids) else { 'follower_ids'    : follower_scids } )
    )

    # Decide whether to proceed with an API call
    if not body: return
    if 'y' != input( f'Edit https://app.shortcut.com/{sm.url_slug}/{item.type_single}/{item.scid} ({item.name}) (y/N): ' ): return

    # Modify the story or epic
    resp_json = sm.call_sc( requests.put, f'{item.type_plural}/{item.scid}', body = body )
    print( f'Edited https://app.shortcut.com/{sm.url_slug}/{item.type_single}/{item.scid} ({item.name})' )

def main():

    # Get a dictionary from user email to user
    sm = ShortcutMetadata()
    userd = {
        user.email : user
        for user in sm.gen_users()
    }

    # Look up the user records and print them
    user_lose = userd.get( user_email_lose, None ); assert user_lose, f'No user with email {user_email_lose}'
    user_gain = userd.get( user_email_gain, None ); assert user_gain, f'No user with email {user_email_gain}'

    # Offer to change user_lose to user_gain in each story and epic
    print( f'Each edit will change {user_lose.name} ({user_lose.email}) to {user_gain.name} ({user_gain.email}) in a story or epic.' )
    for item in sm.gen_story_or_epic_meta( want_cache = False ):
        transform_item( sm, item, user_lose, user_gain )

main()
