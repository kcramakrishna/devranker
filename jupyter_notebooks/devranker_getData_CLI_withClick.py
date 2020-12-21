import os
import git
import sys
from git import Repo
import concurrent.futures
import elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Search,Q
import queue
from enum import Enum
import elasticsearch
from elasticsearch_dsl import Search,Q
from elasticsearch import helpers
import pandas as pd
from pydriller import RepositoryMining
import multiprocessing as mp
from datetime import datetime
import elasticsearch
import pathlib
import re
from pathlib import Path



def _CustomLogs(msg1, msg2):
    print('\n\n' ,msg1, '::\n', msg2)


_CustomLogs('JUST STARTED', '')
# Flag to find buggy commits.
# Finding buggy commits entails using 'git blame' extensively. This takes a LOT of time.
# We have not yet fine tuned the logic to find 'buggy' commits. We should disable this to save time.
# Default is 'False'.
# For now, do not set this to 'True'.
findBuggyFlag = False

# Define a DEBUG flag with values from '0' to '5'. Default is '0' which is OFF.
# Use this cautiously - we are not validating for this

DEBUG = 0


_CustomLogs('RECEIVED PARAMETERS', sys.argv)
gitUrl = sys.argv[1]
outputFileName = sys.argv[2]

_CustomLogs('gitUrl', gitUrl)
_CustomLogs('outputFileName', outputFileName)

def create_components(git_url,esurl,localdir):
    # if no url supplied for Elastic, assume the localhost
    if esurl =='':
        try:
            es = elasticsearch.Elasticsearch(['http://localhost:9200/'], maxsize=500, block=False)
        except:
            print('Elasticsearch not running at localhost:9200')
            sys.exit(1)
    else:
        try:
            es = elasticsearch.Elasticsearch([esurl], maxsize=500, block=False)
        except:
            print('Elasticsearch not running at the given URL. For default localhost, do not provide the argument')
            sys.exit(1)
        
    # Get the default commit index name
    es_index_raw = str.split(git_url,'/')[-1].split('.')[0]+'_'+'index'
    
    # Get the default blame index name
    es_blame_index_raw = str.split(git_url,'/')[-1].split('.')[0]+'_'+'blame'+'_'+'index'
    es_index = es_index_raw.lower()
    es_blame_index = es_blame_index_raw.lower()
        
    # If local Repo path is not supplied, create default path in '/tmp'
    if localdir == '':
        if sys.platform == 'linux' or 'darwin':
            local_dir ='/tmp/'+str.split(git_url,'/')[-1].split('.')[0]
            clone_dir = '/tmp'
        else:
            local_dir ='C:\\Downloads'+str.split(git_url,'/')[-1].split('.')[0]
            clone_dir = 'C:\\Downloads'
    else:
        local_dir = localdir+'/'+str.split(git_url,'/')[-1].split('.')[0]
        clone_dir = localdir
    
    _CustomLogs('create_components() / localdir=', local_dir)
    # Check if the local Repo already exists
    if os.path.isdir(local_dir):
        # Load the local Repo
        try:
            repo = git.Repo(local_dir)
        # Get the latest commit object in the local Repo
            local_commit = repo.commit()
        except:
            print('No valid Repo found at the location. \
                    If unsure, remove the directory and try without local dir argument')
            sys.exit(1)
                       # latest local commit
        
        # Get the latest commit object in the remote Repo
        remote = git.remote.Remote(repo, 'origin')      # remote repo
        info = remote.fetch()[0]                        # fetch changes
        remote_commit = info.commit
        
        # If latest commit in local and remote differ then refresh the local Repo
        if (local_commit.hexsha == remote_commit.hexsha ):
            print('No changes in the Repo...')
        else:
            repo = git.Repo(local_dir)
            o = repo.remotes.origin
            o.pull()
            # Analyse and store additional commit data
            store_commit_data(local_dir,es,es_index,es_blame_index,local_commit.hexsha,remote_commit.hexsha )
    else:
        # If no local Repo exists, clone the Repo
        try:
            if sys.platform == 'linux' or 'darwin':
                git.Git(clone_dir).clone(git_url)
            else:
                git.Git('C:\\Downloads').clone(git_url)
        except:
            print('Not able to clone the Repo. \nIf there is a non Git directory with the same name, delete it and then try')
            _CustomLogs('EXCEPTION', sys.exc_info())
            sys.exit(1)
        
        # Delete the elastic indices, if exist
        es.indices.delete(index=es_index, ignore=[400, 404])
        es.indices.delete(index=es_blame_index, ignore=[400, 404])
        
        # Create new elastic indices
        es.indices.create(es_index)
        es.indices.create(es_blame_index)
        
        # Call the function to store the necessary commit data
        store_commit_data(local_dir,es,es_index,es_blame_index,'None','None')

    return es,es_index,es_blame_index

def process_blame(commit, q_blamelist,eachline, local_dir, repo, npath):
    blamelist = []
    repo_blame = repo.blame(commit.hash,npath,eachline)
    
    # Git Blame of a line can produce multiple records with each record representing a past modification
    for blame_record in repo_blame:
        # Git Blame produces duplicate records (Don't know why).
        # Attempt to ignore duplicated by comparting the current record with the previous record
        # Also Git Blame produces record of the same commit hash, which can be ignored
        if str(commit.hash) !=str(blame_record[0]): #and (str(blame_record[0]) != prev_record):
            # Building Blame tuple for each Blame record
            blame_doc = {'orig_hash':commit.hash,'blame_hash':str(blame_record[0]),
                                            'file':npath}
            # Loading blame data into the list
            blamelist.append(blame_doc)
    
    # Put the blamelist into the queue.
    q_blamelist.put(blamelist)

    # Function to processes each commit


def process_commit(commit, repo, es, es_index, es_blame_index, local_dir):

    # Creating empty lists for carrying commit data
    doclist = []
    blamelist = []
    
    # Create queues for commit data and blame data
    q_blamelist = queue.Queue()
    
    for mod in commit.modifications:
        commit_data = {'hash':commit.hash,'Author':commit.author.name,'Email':commit.author.email,
                       'message':commit.msg,'authored_date':commit.author_date,
                       'Committer':commit.committer.name,'committed_date':commit.committer_date,
                       'number_of_branches':len(commit.branches), 'in_main_branch':commit.in_main_branch,
                       'merge_commit?':commit.merge,
                       'number_of_mod_files':len(commit.modifications),
                       'file_name':mod.filename,
                       'file_change_type_name':mod.change_type.name,
                       'file_change_type_value':mod.change_type.value,
                       'file_old_path':mod.old_path, 'file_new_path':mod.new_path,
                       'number_functions_before': len(mod.methods_before),
                       'number_functions_after': len(mod.methods),
                       'number_functions_edited': len(mod.changed_methods), #Existing methods changed.
                       'number_lines_added':mod.added,'number_lines_removed': mod.removed,
                       'file_number_loc':mod.nloc, 'language_supported': mod.language_supported,
                       # Can we get number of lines which are comments?
                       #   Else,We may not need the below variable 'size'.
                       'file_size': 0 if mod.source_code is None else len(mod.source_code.splitlines()),
                       'dmm_unit_size':commit.dmm_unit_size,
                       'dmm_unit_complexity':commit.dmm_unit_complexity,
                       'dmm_unit_interfacing':commit.dmm_unit_interfacing,
                       'file_complexity': mod.complexity,
                       'tokens':mod.token_count # We need to get exact details.
                      }
        
        # We actually need to identify and save file extension here but for now,
        #         we are doing this in 'get_latest_commits' below. We should move that code here.
        
        
        # loading each commit tuple into the list
        doclist.append(commit_data)
        
        if (findBuggyFlag == True):
            # Each modification object contains diff_parsed tag with "added" and "deleted" properties.
            alines = mod.diff_parsed['added']
            
            # "added" property is a tuple list with line number and actual line text.
            # List of text lines is extracted
            addedlines = [x[1] if len(alines)>0 else 'None' for x in alines ]
                    
            # Each modification object contains diff_parsed tag with "added" and "deleted" properties.
            blines = mod.diff_parsed['deleted']
            # "deleted" property is a tuple list with line number and actual line text.
            # List of text lines is extracted
            deletedlines = [x[1] if len(blines)>0 else 'None' for x in blines]
            
            no_of_mod_files = len(commit.modifications)
            lines_added = mod.added
            count = 0

            # Absolute path of the file in the cloned repo.
            # This is required to validate that the file has not been deleted in the subsequent commits
            newfilepath = local_dir+'/'+str(mod.new_path)

            # For bug fix commits, retrieving the blame data.
            # Using Regex on Commit messages to identify bug fix commits
            # Have lightweight threads process each modification(mod)
            # Remember that each modification is a single line in the commit and we can have many
            # Since most of the work is I/O bound, processors should be mostly idle,
            #       we can load up with a LOT of threads - set he max threads to 200
            if len(re.findall(r"\bbug\b|\bBug\b|\bFix\b|\bfix\b",commit.msg))>0 \
                    and os.path.isfile(newfilepath) \
                    and no_of_mod_files <15 and lines_added < 1000:
                with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
                    futures = [executor.submit(process_blame, commit, q_blamelist,eachline, \
                                               local_dir, repo, newfilepath) \
                                               for eachline in addedlines]

            # Wait for all threads to complete
            executor.shutdown(wait=True)
     
    # Changed the method to assert the empty queue
    while not q_blamelist.empty():
        blamelist.append(q_blamelist.get())

    
    # Each thread produces a list of tuples (in this case list of one tuple)
    # When data from queue is appended to a list, it produces list of lists instead of list of tuples
    # It is required to flatten the list of lists into list of tuples.
    # Bulkloading to elastic won't work otherwise
    blamelist = [item for sublist in blamelist for item in sublist]
    
    # using elasticsearch.py's helper tools to bulk load into elasticsearch's commit index
    helpers.bulk(es,doclist,index=es_index,doc_type ='commit_data',request_timeout = 2000)
    
    # Since Git Blame produces duplicate data, getting only unique records
    #blamelist_fil = [i for n, i in enumerate(blamelist) if i not in blamelist[n + 1:]]
    blame_df = pd.DataFrame(blamelist)
    blame_df_clean = blame_df.drop_duplicates()

    blamelist_fil = []
    
    df_iter = blame_df_clean.iterrows()
    for index, document in df_iter:
        blamelist_fil.append(document.to_dict())

    # using elasticsearch.py's helper tools to bulk load into elasticsearch's blame index
    helpers.bulk(es,blamelist_fil,index=es_blame_index,doc_type ='blame',request_timeout = 2000)

    # delete our lists
    del doclist
    del blamelist
    del blamelist_fil




# Function to analyse all commits (and import to elastic)
def store_commit_data(local_dir,es,es_index,es_blame_index,local_commit,remote_commit):

    if DEBUG >= 1:
        store_start = datetime.now()
        print('starting store_commit', store_start)
    
    repo = Repo(local_dir)

    # Create Multithreading pool to use full CPU
    pool = mp.Pool(mp.cpu_count())
    
    # If the Repo has just been cloned, the program will traverse the whole Repo
    if(local_commit == 'None'):
        [pool.apply_async(process_commit(commit, repo, es,es_index,es_blame_index, local_dir)) for commit in \
         RepositoryMining(local_dir).traverse_commits()]
        
    else:
        [pool.apply_async(process_commit(commit, repo, es,es_index,es_blame_index, local_dir)) for commit in \
         RepositoryMining(local_dir,from_commit = local_commit, to_commit = remote_commit).traverse_commits()]

    # Close Multiprocessing pool
    pool.close()
    pool.join()
    if DEBUG >= 1:
        store_end = datetime.now()
        print('exiting store_commit', store_end)
        print('time taken by store_commit', (store_end - store_start))
    
    # Very important to explicitly refresh the Elastic indices as they are not automatically done.
    es.indices.refresh([es_blame_index,es_index])



   
def get_latest_commits(es_instance,commit_index,blame_index):
        # Assigning Elastic instance, Commit Elastic Index and Blame Elastic Index to variables
        es = es_instance
        es_ma_index = commit_index
        es_bl_index = blame_index
        # Using Elasticsearch DSL function to get the data of Commit index
        blame_es_data = Search(using=es, index=es_bl_index)
        # Loading data into a dictionary
        blame_dict = [hit.to_dict() for hit in blame_es_data.scan()]
        # Using Elasticsearch DSL function to get the data of Blame index
        commit_es_data = Search(using=es, index=es_ma_index)
        # Loading data into a dictionary
        commit_dict = [hit.to_dict() for hit in commit_es_data.scan()]
        # Creating pandas dataframe for commit data
        commit_frame = pd.DataFrame(commit_dict)
        # Creating pandas dataframe for blame data
        blame_frame = pd.DataFrame(blame_dict)
        # Getting the blame row count. If the frame is empty, it means all the records are clean
        blame_count = blame_frame.shape[0]
        #print(blame_frame.columns)
        if blame_count>0:
            blame_frame['file'] = blame_frame['file'].apply(lambda x:x.split('/')[-1])
            # Adding a column to Blame frame indicating that the row represents a Buggy commit
            blame_frame['type'] = 'Buggy'
            # Combining Commit frmae with Blame frame.
            # An additional column called 'type' gets added to the Commit frame.
            comb_frame = pd.merge(commit_frame,blame_frame,how='left', left_on = ['hash','file_name'], \
                                  right_on = ['blame_hash','file'])
        else:
            # If the Blame frame is empty, no need to merge.
            comb_frame=commit_frame
            comb_frame['type'] = 'Clean'
            
        # When merging happnes and 'type' column gets added to the main Commit frame,
        # The rows that are not part of Blame frame are filled with 'Nan'.
        # Here, all the NaNs from 'type' column are replaced with 'Clean' label.
        # Effectively, Each commit file (one Commit can contain more than one file) is categorised as
        #                 either Buggy or Clean.
        comb_frame['type'] = comb_frame['type'].fillna('Clean')
        
        # Cleaning and retaining the required columns
        comb_frame_refined = comb_frame[['hash','Author','Email',
                                           'message','authored_date',
                                           'Committer','committed_date',
                                           'number_of_branches', 'in_main_branch',
                                           'merge_commit?',
                                           'number_of_mod_files',
                                           'file_name',
                                           'file_change_type_name',
                                           'file_change_type_value',
                                           'file_old_path', 'file_new_path',
                                           'number_functions_before',
                                           'number_functions_after',
                                           'number_functions_edited',
                                           'number_lines_added','number_lines_removed',
                                           'file_number_loc', 'language_supported',
                                           'file_size',
                                           'dmm_unit_size',
                                           'dmm_unit_complexity',
                                           'dmm_unit_interfacing',
                                           'file_complexity',
                                           'tokens',
                                           'type'
                                        ]]
        
        # Create a coloumn 'file_ext' which is the file 'type'
        comb_frame_refined['file_ext'] = comb_frame_refined['file_new_path'].\
                                                    apply(lambda x:pathlib.Path(str(x)).suffix).\
                                                    apply(lambda x:re.split(r"[^a-zA-Z0-9\s\++\_\-]",x)[-1])

        # For files without any extension, mark 'file_ext' as "NoExt"
        comb_frame_refined.file_ext = comb_frame_refined.file_ext.replace(r'^\s*$', 'NoExt', regex=True)

        # Sorting the frame by committed date
        comb_frame_refined = comb_frame_refined.drop_duplicates().sort_values('committed_date', ascending=False)
        
        return comb_frame_refined


# Realised that git blame and most of our code is heavily constrained by disk speed.
#       We can create and use an in memory file system. In Linux we can use /tmp

#Set tmpfs if you have tmpfs. Else leave this as '/tmp' /tmp is usually in RAM
tmpfs = '/tmp'

if (tmpfs == ''):
    Home_address = str(Path.home())
else:
    #Set Home_address to the tmpfs
    Home_address = tmpfs

localdir = Home_address + '/cg_Repos'

_CustomLogs('LOCAL DIR' , localdir)

_CustomLogs('create_components()', '')
# Extracting features from target repos for predictions
# Processing data for Git Repo.
p1 = create_components(gitUrl,'',localdir)
_CustomLogs('create_components()=>p1', p1)

_CustomLogs('get_latest_commits()', '')
# Getting the commit data as pandas frames

try:
    p1_commits = get_latest_commits(p1[0],p1[1],p1[2])
    p1_commits.to_csv(outputFileName)
    _CustomLogs('get_latest_commits()', p1_commits)
except:
    _CustomLogs('EXCEPTION OCCURED @ get_latest_commits()', sys.exc_info()[0])

# Storing these to file on hard disk



    
