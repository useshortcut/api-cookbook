from    boltons.dictutils   import OrderedMultiDict
import  csv
from    dataclasses         import dataclass
from    itertools           import islice
import  io
import  os
import  regex
import  requests

@dataclass
class PivotalBlocker:

    blockee_type : str
    blockee_id   : str
    blocker_id   : str
    is_resolved  : bool

@dataclass
class PivotalPullRequest:

    item_type    : str
    item_id      : str
    pr_path      : str
    pr_num       : str
    repo_name    : str
    repo_owner   : str

@dataclass
class PivotalGitBranch:

    item_type    : str
    item_id      : str
    git_branch   : str

@dataclass( frozen = True, eq = True ) # These settings make objects of this class hashable. We'll need that to let objects of this class be dict keys.
class PivotalItemLabelRec:

    item_type    : str
    item_id      : str
    item_name    : str
    labels       : tuple[str]

class PivotalExport:

    def __init__( self, csv_path ):
        '''
        Represents an extract of data from a Pivotal export
        '''

        # Get the CSV as a list of rows, each represented as an OMD
        self.csv_path = csv_path
        self.row_omds = list( self.gen_csv_row_as_omd() )

    def gen_csv_row_as_list_of_tuples( self ):

        with io.open( self.csv_path, 'r', encoding = 'utf-8' ) as f:
            reader  = csv.reader( f )
            headers = next( reader )
            for row in reader: yield list( zip(headers,row) )

    def gen_csv_row_as_omd( self ):

        for keyvals in self.gen_csv_row_as_list_of_tuples():
            yield OrderedMultiDict( (k,v) for k,v in keyvals )

    def gen_itemlabelrecs( self ):

        for row_omd in self.row_omds:
            yield PivotalItemLabelRec(
                item_type = row_omd['Type'],
                item_id   = row_omd['Id'],
                item_name = row_omd['Title'],
                labels    = tuple( regex.split( r',\s*', str(row_omd['Labels']) ) )
            )

    def gen_blockers( self ):

        for row_omd in self.row_omds:
            for blocker_string, blocker_state in zip( row_omd.getlist('Blocker'), row_omd.getlist('Blocker Status') ):
                if not regex.fullmatch( r'#\d+', blocker_string ): continue
                yield PivotalBlocker(
                    blockee_type = row_omd['Type'],
                    blockee_id   = row_omd['Id'],
                    blocker_id   = blocker_string[1:],
                    is_resolved  = ( blocker_state == 'resolved' )
                )

    def gen_pullrequests( self ):

        for row_omd in self.row_omds:
            for pr_path in row_omd.getlist('Pull Request'):
                # if not pr_path: continue
                m = regex.fullmatch( r'https://github.com/(?P<repo_owner>[^/]+)/(?P<repo_name>[^/]+)/pull/(?P<pr_num>\d+)', pr_path )
                if m: yield PivotalPullRequest(
                    item_type    = row_omd['Type'],
                    item_id      = row_omd['Id'],
                    pr_path      = pr_path,
                    pr_num       = m.group('pr_num'),
                    repo_name    = m.group('repo_name'),
                    repo_owner   = m.group('repo_owner'),
                )

    def gen_gitbranches( self ):

        for row_omd in self.row_omds:
            for git_branch in row_omd.getlist('Git Branch'):
                if not git_branch: continue
                yield PivotalGitBranch(
                    item_type    = row_omd['Type'],
                    item_id      = row_omd['Id'],
                    git_branch   = git_branch,
                )

if __name__ == '__main__':

    pe = PivotalExport( '../data/pivotal_export.csv' )
    for pb in islice( pe.gen_blockers()     , 20 ): print( f'{pb=}' )
    for pr in islice( pe.gen_pullrequests() , 20 ): print( f'{pr=}' )
    for gb in islice( pe.gen_gitbranches()  , 20 ): print( f'{gb=}' )
    for lr in pe.gen_itemlabelrecs():
        if len(lr.labels) > 1: print( f'{lr=}' )
