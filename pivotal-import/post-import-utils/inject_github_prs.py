import backoff
from   datetime                 import datetime
from   itertools                import islice
import os
import requests
from   throttlex                import Throttler
import tzlocal

from   PivotalExport            import PivotalExport, PivotalPullRequest
from   ShortcutMetadata         import ShortcutMetadata


token        = os.getenv('GITHUB_API_TOKEN')
throttler_m  = Throttler( max_req =  79, period =   60 ) # See https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#about-secondary-rate-limits
throttler_h  = Throttler( max_req = 499, period = 3600 ) # See https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#about-secondary-rate-limits

def check_ratelimits():

    resp = requests.get(
        url     = f'https://api.github.com/rate_limit',
        headers = {
            'Authorization' : f'token {token}',
            'Accept'        : 'application/vnd.github.v3+json',
        },
    )
    print( resp.text )

@backoff.on_exception( backoff.expo, Exception, max_tries = 5 )
def write_comment_to_pr( pr: PivotalPullRequest, story_url: str ):

    url  = throttler_h.throttle( throttler_m.throttle( f'https://api.github.com/repos/{pr.repo_owner}/{pr.repo_name}/issues/{pr.pr_num}/comments' ) )
    resp = requests.post(
        url     = url,
        headers = {
            'Authorization' : f'token {token}',
            'Accept'        : 'application/vnd.github.v3+json',
        },
        json    = { 'body': story_url }
    )
    if resp.status_code not in { 200, 201 }:
        ratelimit_reset_unix = resp.headers.get( 'X-RateLimit-Reset', None )
        ratelimit_reset_human = datetime.fromtimestamp(int(ratelimit_reset_unix),tzlocal.get_localzone()).strftime('%Y-%m-%d %H:%M:%S %Z') if ratelimit_reset_unix else None
        print( f'Write FAILED while linking {pr.repo_name} PR {pr.pr_num} to story {story_url}. Aborting the rest of the run.' )
        print( f'Request: POST {url}' )
        print( f'Response was {resp.status_code} with informative headers: {resp.headers}' )
        if ratelimit_reset_human: print( f'The headers do not say much explicitly about secondary rate limits, but they do say you could try again at {ratelimit_reset_human}' )
        print()
        print( f'See https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#exceeding-the-rate-limit' )
        print( f'To make the next run skip re-processing some PRs, edit the islice start and stop parameters.' )
        print( f"That's optional since the script is mostly idempotent; see README.md." )
        exit(1)


    return resp

def main():

    # Check rate rate limits
    # check_ratelimits()
    # exit(0)

    # Read extracts from the Pivotal export data and from Shortcut (metadata only)
    pe  = PivotalExport( '../data/pivotal_export.csv' )
    sm  = ShortcutMetadata()

    # Report the total number of entries to write
    prs = list( pe.gen_pullrequests() )
    prn = len( prs )

    # For each entry, write a single comment to the appropriate PR, containing only the link to the story
    for i, pr in islice( enumerate(prs), 912, None ): # latter two params are start and stop; unfortunately they can't be named

        # Skip any entry that's for an epic or for a story that's missing from the ID mapping.
        if pr.item_type == 'epic': continue
        story_ptid = pr.item_id
        story_scid = sm.scid_from_ptid['story'].get( story_ptid, None )
        if not story_scid: continue

        # Write the Shortcut story URL to a PR comment. The Shortcut-GitHub integration does the rest.
        story_url  = f'https://app.shortcut.com/{sm.url_slug}/story/{story_scid}'
        write_comment_to_pr( pr, story_url )
        print( f'{i} of {prn}: Wrote {pr.repo_name} PR {pr.pr_num} to {story_url}' )

main()
