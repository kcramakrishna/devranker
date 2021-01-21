import PySimpleGUI as sg
import os
import git
import sys
from git import Repo
import concurrent.futures
import elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Search, Q
import queue
from enum import Enum
import elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch import helpers
import pandas as pd
from pydriller import RepositoryMining
import multiprocessing as mp
from datetime import datetime
import elasticsearch
import pathlib
import re
from pathlib import Path
import subprocess


####################################################
# WIDTHs of Starting, Middle & Last Widgets
width_1 = 40
width_2 = 40
width_3 = 9

# HEIGHTs of Starting, Middle & Last Widgets
height_1 = 1
height_2 = 1
height_3 = 1

# Height of Vertical Bars which are representing STEPs
v_height_1 = 20
v_height_2 = 15
v_height_3 = 10
####################################################

# Flag to find buggy commits.
# Finding buggy commits entails using 'git blame' extensively. This takes a LOT of time.
# We have not yet fine tuned the logic to find 'buggy' commits. We should disable this to save time.
# Default is 'False'.
# For now, do not set this to 'True'.
findBuggyFlag = False

# Define a DEBUG flag with values from '0' to '5'. Default is '0' which is OFF.
# Use this cautiously - we are not validating for this
DEBUG = 0

# Initializing Variables
outputFileDirectory = ''
gitDirectory = ''
outputFileLocation = ''
# Constant value which will be added to 'outputFileDirectory'
# outputFileName = '/elasticray.git.csv'
outputFileName = ''

####################################################
# Variables for 'PySimpleGui'
dateStart = ''
dateEnd = ''
####################################################


def liveLogs(msg1, msg2):
    print('\n\n*****************')
    print(msg1, '::\n', msg2)
    print('*****************')


# Reading Values from 'devrankerClientConfig.txt' File
# reader = open('devrankerClientConfig.txt', 'r')
# Lines = reader.readlines()
# reader.close()

# liveLogs('Reading File ..... ', '')
# lineNo = 0

# for line in Lines:
#     lineNo += 1

#     print('Line No ', lineNo, '=>', line)

#     if '=' in line:
#         value = line.split('=')[1]
#         value = value.strip()
#         if 'findBuggyFlag' in line:
#             findBuggyFlag = value
#         elif 'DEBUG' in line:
#             DEBUG = int(value)
#         # elif 'outputFileDirectory' in line:
#         #     outputFileDirectory = value
#         elif 'gitUrl' in line:
#           #  global gitUrl
#             gitUrl = value
# liveLogs('gitUrl', gitUrl)
# liveLogs('outputFileDirectory', outputFileDirectory)
# liveLogs('DEBUG', DEBUG)
# liveLogs('typeof debug', type(DEBUG))
# liveLogs('findBuggyFlag', findBuggyFlag)

####################################################
# Sub LAYOUTs(Step1, Step2, Step3 & Step4) Preparation for Main Layout


layout_step_1 = [
    [sg.Text('Select the Location of Cloned Repo', text_color='black', background_color='white', size=(width_1, height_1)),
     sg.Input(gitDirectory, key='_i_GitDirectory', enable_events=True, text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.FolderBrowse('Browse', target='_i_GitDirectory', pad=None, font=('MS Sans Serif', 10, 'bold'), button_color=('red', 'white'), key='_fb_browse', size=(width_3, height_3))],


    [sg.Text('Select Destination Directory *', background_color='white', text_color='black', border_width=2, size=(width_1, height_1)),
     sg.Input(outputFileDirectory, key='_i_DestDirectory', enable_events=True, text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.FolderBrowse('Browse', target='_i_DestDirectory', pad=None, font=('MS Sans Serif', 10, 'bold'), button_color=('red', 'white'), key='_fb_browse', size=(width_3, height_3))],

    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     sg.Button('Start Mining', key='_i_StartMining', font=('MS Sans Serif',
                                                           10, 'bold'), button_color=('blue', 'white'), size=(width_3, height_3)),
     sg.Button('Live Log', key='_i_LiveLog', font=('MS Sans Serif', 10, 'bold'), button_color=('orange', 'white'), size=(width_3, height_3))],

    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     sg.ProgressBar(100, orientation='h', size=(20, 8), key='_pb'),
     sg.Text('', background_color='white', key='_t_ProgressValue', font=('MS Sans Serif', 10, 'bold'), text_color='black', size=(width_3, height_3))]
]


layout_step_2 = [

    # DATA FILE LOCATION AT
    [sg.Text('Data file location at', text_color='black', background_color='white', size=(width_1, height_1)),
     sg.Input(key='_i_DFL', background_color='white',
              disabled=True, text_color='black', size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_DFL', size=(width_3, height_3))],


    # ENCRYPT BUTTON
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Encrypt', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_Encrypt', size=(width_3, height_3))],


    # ANONYMISED FILE
    [sg.Text('Anonymised File Located at', background_color='white', text_color='black', border_width=2, size=(width_1, height_1)),
     sg.Input(key='_i_AFL', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_AFL', size=(width_3, height_3))],


    # ANONYMISED DICTIONARY
    [sg.Text('Anonymisation Dictionary Located at', background_color='white', text_color='black', border_width=2, size=(width_1, height_1)),
     sg.Input(key='_i_ADL', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_ADL', size=(width_3, height_3))],


    # GET PREDICTIONS BUTTON
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Get Predictions', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_GetPredictions', size=(width_3, height_3))],
]


layout_step_3 = [
    [sg.Text('Anonymisation Predictions File', background_color='white', text_color='black', border_width=2, size=(width_1, height_1)),
     sg.Input(key='_i_APF', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_APF', size=(width_3, height_3))],


    # GET PREDICTIONS BUTTON
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Decrypt', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_Decrypt', size=(width_3, height_3))],
]


layout_step_4 = [
    [sg.Text('De-Anonymisation Predictions File', background_color='white', text_color='black', border_width=2, size=(width_1, height_1)),
     sg.Input(key='_i_DAPF', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspects_DAPF', size=(width_3, height_3))],


    # GET PREDICTIONS BUTTON
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Show Charts', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_Showcharts', size=(width_3, height_3))],
]


####################################################
# MAIN LAYOUT WHICH IS GOING TO BE ADDED TO 'WINDOW'
layout_main = [
    # STEP 1
    [sg.Text('STEP 1', text_color='blue', background_color='white')],
    [sg.Text('', background_color='red', size=(2, v_height_1)),
     sg.Column(layout_step_1, background_color='white')],

    # STEP 2
    [sg.Text('STEP 2', text_color='blue', background_color='white')],
    [sg.Text('', background_color='blue', size=(2, v_height_2)),
     sg.Column(layout_step_2, background_color='white')],

    # STEP 3
    [sg.Text('STEP 3', text_color='blue', background_color='white')],
    [sg.Text('', background_color='blue', size=(2, v_height_3)),
     sg.Column(layout_step_3, background_color='white')],

    # STEP 4
    [sg.Text('STEP 4', text_color='blue', background_color='white')],
    [sg.Text('', background_color='blue', size=(2, v_height_3)),
     sg.Column(layout_step_4, background_color='white')],
]

####################################################
#######  METHODS RELATED TO  'PySimpleGui'  ########
####################################################


def updateProgressBar(value):
    # progressBar.update_bar(value)
    # progressBarText.update(str(value) + " % ")
    pass
    # if value == 100:
    # progressBarText.update(visible = False)
    # else:
    # progressBarText.update(visible = True)


####################################################
#########  METHODS RELATED TO  DEVRANKER  ##########
####################################################
# TODO: RAVI -> ADD VALIDATION FOR ALL VARIABLES
# Reading devrankerClientConfig.txt file data


def process_commit(commit, outputfile_fullpath ,repo):

    # Creating empty lists for carrying commit data
    doclist = []

    # Create queues for commit data and blame data
    q_blamelist = queue.Queue()

    for mod in commit.modifications:
        commit_data = {'hash': commit.hash, 'Author': commit.author.name, 'Email': commit.author.email,
                       'message': commit.msg, 'authored_date': commit.author_date,
                       'Committer': commit.committer.name, 'committed_date': commit.committer_date,
                       'number_of_branches': len(commit.branches), 'in_main_branch': commit.in_main_branch,
                       'merge_commit?': commit.merge,
                       'number_of_mod_files': len(commit.modifications),
                       'file_name': mod.filename,
                       'file_change_type_name': mod.change_type.name,
                       'file_change_type_value': mod.change_type.value,
                       'file_old_path': mod.old_path, 'file_new_path': mod.new_path,
                       'number_functions_before': len(mod.methods_before),
                       'number_functions_after': len(mod.methods),
                       # Existing methods changed.
                       'number_functions_edited': len(mod.changed_methods),
                       'number_lines_added': mod.added, 'number_lines_removed': mod.removed,
                       'file_number_loc': mod.nloc, 'language_supported': mod.language_supported,
                       # Can we get number of lines which are comments?
                       #   Else,We may not need the below variable 'size'.
                       'file_size': 0 if mod.source_code is None else len(mod.source_code.splitlines()),
                       'dmm_unit_size': commit.dmm_unit_size,
                       'dmm_unit_complexity': commit.dmm_unit_complexity,
                       'dmm_unit_interfacing': commit.dmm_unit_interfacing,
                       'file_complexity': mod.complexity,
                       # We need to get exact details.
                       'tokens': mod.token_count
                       }

        # loading each commit tuple into the list
        doclist.append(commit_data)
    
    # Append 'doclist' to 'outputfile_fullpath'
    # delete our lists
    del doclist
    del blamelist
    del blamelist_fil


def store_commit_data(local_dir, es, es_index, es_blame_index, local_commit, remote_commit):

    if DEBUG >= 1:
        store_start = datetime.now()
        print('starting store_commit', store_start)

    repo = Repo(local_dir)

    # Create Multithreading pool to use full CPU
    pool = mp.Pool(mp.cpu_count())

    # If the Repo has just been cloned, the program will traverse the whole Repo
    if(local_commit == 'None'):
        [pool.apply_async(process_commit(commit, repo, es, es_index, es_blame_index, local_dir)) for commit in
         RepositoryMining(local_dir).traverse_commits()]

    else:
        [pool.apply_async(process_commit(commit, repo, es, es_index, es_blame_index, local_dir)) for commit in
         RepositoryMining(local_dir, from_commit=local_commit, to_commit=remote_commit).traverse_commits()]

    # Close Multiprocessing pool
    pool.close()
    pool.join()
    if DEBUG >= 1:
        store_end = datetime.now()
        print('exiting store_commit', store_end)
        print('time taken by store_commit', (store_end - store_start))

    # Very important to explicitly refresh the Elastic indices as they are not automatically done.
    es.indices.refresh([es_blame_index, es_index])



def create_components(repoName, repo):
    # if no url supplied for Elastic, assume the localhost
    # if esurl == '':
    try:
        es = elasticsearch.Elasticsearch(['http://localhost:9200/'], maxsize=500, block=False)
    except:
        print('Elasticsearch not running at localhost:9200')
        sys.exit(1)
   
    # Get the default commit index name
    es_index_raw = repoName +'_'+'index'

    # Get the default blame index name
    es_blame_index_raw = repoName +'_'+'blame'+'_'+'index'
    es_index = es_index_raw.lower()
    es_blame_index = es_blame_index_raw.lower()

  
    try:
        # Get the latest commit object in the local Repo
        local_commit = repo.commit()
    except:
        print('No valid Repo found at the location. If unsure, remove the directory and try without local dir argument')
        sys.exit(1)
            # latest local commit

        # Get the latest commit object in the remote Repo
    remote = git.remote.Remote(repo, 'origin')      # remote repo
    info = remote.fetch()[0]                        # fetch changes
    remote_commit = info.commit

        # If latest commit in local and remote differ then refresh the local Repo
    # if (local_commit.hexsha == remote_commit.hexsha):
    #      print('No changes in the Repo...')
    # else:
    #     repo = git.Repo(gitDirectory)
    #     o = repo.remotes.origin
    #     o.pull()
         # Analyse and store additional commit data
    liveLogs("local_commit", local_commit.hexsha)
    liveLogs("remote_commit", remote_commit.hexsha)
    
    store_commit_data(gitDirectory, es, es_index, es_blame_index, local_commit.hexsha, remote_commit.hexsha)
  
    return es, es_index, es_blame_index


def get_latest_commits(es_instance, commit_index, blame_index):
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
    # print(blame_frame.columns)
    if blame_count > 0:
        blame_frame['file'] = blame_frame['file'].apply(
            lambda x: x.split('/')[-1])
        # Adding a column to Blame frame indicating that the row represents a Buggy commit
        blame_frame['type'] = 'Buggy'
        # Combining Commit frmae with Blame frame.
        # An additional column called 'type' gets added to the Commit frame.
        comb_frame = pd.merge(commit_frame, blame_frame, how='left', left_on=['hash', 'file_name'],
                              right_on=['blame_hash', 'file'])
    else:
        # If the Blame frame is empty, no need to merge.
        comb_frame = commit_frame
        comb_frame['type'] = 'Clean'

    # When merging happnes and 'type' column gets added to the main Commit frame,
    # The rows that are not part of Blame frame are filled with 'Nan'.
    # Here, all the NaNs from 'type' column are replaced with 'Clean' label.
    # Effectively, Each commit file (one Commit can contain more than one file) is categorised as
    #                 either Buggy or Clean.
    comb_frame['type'] = comb_frame['type'].fillna('Clean')

    # Cleaning and retaining the required columns
    comb_frame_refined = comb_frame[['hash', 'Author', 'Email',
                                     'message', 'authored_date',
                                     'Committer', 'committed_date',
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
                                     'number_lines_added', 'number_lines_removed',
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
        apply(lambda x: pathlib.Path(str(x)).suffix).\
        apply(lambda x: re.split(r"[^a-zA-Z0-9\s\++\_\-]", x)[-1])

    # For files without any extension, mark 'file_ext' as "NoExt"
    comb_frame_refined.file_ext = comb_frame_refined.file_ext.replace(
        r'^\s*$', 'NoExt', regex=True)

    # Sorting the frame by committed date
    comb_frame_refined = comb_frame_refined.drop_duplicates(
    ).sort_values('committed_date', ascending=False)

    return comb_frame_refined


def validateDirectories():
    if(gitDirectory == ''):
         sg.popup('Please Select Git Directory')
    elif(outputFileDirectory == ''):
         sg.popup('Please Select Output Directory')
    else:
         try:
             repo = git.Repo(gitDirectory)

             arrSplitGitDirectory = str.split(gitDirectory, '/')
             global outputFileName
             outputFileName = arrSplitGitDirectory[len(arrSplitGitDirectory)-1]

             liveLogs("Repo Name", outputFileName)

             startMiningProcess(outputFileName, repo)
         except:
             liveLogs('exc 599', sys.exc_info())
             sg.popup('Invalid Git Directory, Please choose valid Git Directory')



def startMiningProcess(repoName, repo):
    liveLogs('startTheProcess()', '')
    # Extracting features from target repos for predictions
    # Processing data for Git Repo.
    try:
         p1 = create_components(repoName, repo)
         liveLogs('startMiningProcess/create_components() => p1', p1)
        
         p1_commits = get_latest_commits(p1[0], p1[1], p1[2])

         storeCommitDataInDevRankerDirectory(p1_commits)
        
    except:
         liveLogs("Exc Create Components", sys.exc_info())

   
def storeCommitDataInDevRankerDirectory(p1_commits):
     outputFileLocation = outputFileDirectory + "/DevRanker"
     # Checking for 'devRanker' Directory in Selected Directory
     if not os.path.exists(outputFileLocation):
            os.makedirs(outputFileLocation)
     outputFileLocation = outputFileLocation + outputFileName + '.git.csv'
     p1_commits.to_csv(outputFileLocation)         

     liveLogs('storeCommitDataInDevRankerDirectory => p1_commits()', p1_commits)
     sg.popup('Mining is done and File location is \n' + outputFileLocation )


window = sg.Window('Dev Ranker', layout_main,
                   background_color='white', finalize=True)
# event, values = window.Read()
progressBar = window['_pb']
progressBarText = window['_t_ProgressValue']
inputDestinationDir = window['_i_DestDirectory']
dataFileLocation = window['_i_DFL']


####################################################
######          HANDLING ALL EVENTS          #######
####################################################
while True:

    event, values = window.Read()
    print(event, values)

    # STEP1 Related
    if event in (None, 'Exit'):
        break

    elif event == '_i_GitDirectory':
        gitDirectory = values['_i_GitDirectory']
        liveLogs('_i_GitDirectory', gitDirectory)

    elif event == '_i_StartMining':
        validateDirectories()
        updateProgressBar(0)
        # startTheProcess()

    elif event == '_i_LiveLog':
        updateProgressBar(100)
        sg.popup('Live Log Clicked')

    elif event == '_i_DestDirectory':
        outputFileDirectory = values['_i_DestDirectory']
        # dataFileLocation.update(outputFileLocation)
        # liveLogs(outputFileDirectory, values['_i_DestDirectory'])

    # STEP2 Related
    elif event == '_b_Inspect_DFL':
        sg.popup('Inspect DFL')

    elif event == '_b_Inspect_AFL':
        sg.popup('Inspect AFL')

    elif event == '_b_Inspect_ADL':
        sg.popup('Inspect ADL')

    elif event == '_b_GetPredictions':
        sg.popup('Get Prections Clicked')

    elif event == '_b_Encrypt':
        sg.popup('Encrypt Clicked')

    # STEP3 Related
    elif event == '_b_Inspect_APF':
        sg.popup('Inspect APF')

    elif event == '_b_Decrypt':
        sg.popup('Decrypt Clicked')

    # STEP4 Related
    elif event == '_b_Inspects_DAPF':
        sg.popup('Inspect DAPF Clicked')

    elif event == '_b_Showcharts':
        sg.popup('Show Charts Clicked')

# WHEN PRESSED CLOSE
window.close()
