import PySimpleGUI as sg
import os
import sys
import git
from pydriller import RepositoryMining
import multiprocessing as mp
import pathlib
import pandas
import json
import logging
import more_itertools

# TODO: RAVI-> Check whether it needed or not?
logging.basicConfig(level=logging.DEBUG)

# Widths of Starting, Middle & Last Widgets
width_1 = 40
width_2 = 40
width_3 = 9

# Heights of Starting, Middle & Last Widgets
height_1 = 1
height_2 = 1
height_3 = 1

# Height of Vertical Bars which are representing STEPs
v_height_1 = 10
v_height_2 = 10
v_height_3 = 10

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
DevrankerDir = ''
gitDirectory = ''
DestDirectory = ''

total_commits_count = 0

# Sub Layouts(Step1, Step2, Step3 & Step4) will be added to 'layout_main'
layout_step_1 = [
    [sg.Text('Select the Location of Cloned Repo', text_color='black', background_color='white',
             size=(width_1, height_1)),
     sg.Input(gitDirectory, key='_i_GitDirectory', enable_events=True, text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.FolderBrowse('Browse', target='_i_GitDirectory', pad=None, font=('MS Sans Serif', 10, 'bold'),
                     button_color=('red', 'white'), key='_fb_browse', size=(width_3, height_3))],

    [sg.Text('Select Destination Directory *', background_color='white', text_color='black', border_width=2,
             size=(width_1, height_1)),
     sg.Input(DestDirectory, key='_i_DestDirectory', enable_events=True, text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.FolderBrowse('Browse', target='_i_DestDirectory', pad=None, font=('MS Sans Serif', 10, 'bold'),
                     button_color=('red', 'white'), key='_fb_browse', size=(width_3, height_3))],

    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     sg.Button('Start Mining', key='_i_StartMining', font=('MS Sans Serif',
                                                           10, 'bold'), button_color=('blue', 'white'),
               size=(width_3, height_3)),
     sg.Button('Live Log', key='_i_LiveLog', font=('MS Sans Serif', 10, 'bold'), button_color=('orange', 'white'),
               size=(width_3, height_3))],

    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     sg.ProgressBar(100, orientation='h', size=(20, 8), key='_pb'),
     sg.Text('', background_color='white', key='_t_ProgressValue', font=('MS Sans Serif', 10, 'bold'),
             text_color='black', size=(width_3, height_3))]
]

layout_step_2 = [

    # Data File Location
    [sg.Text('Data file location at', text_color='black', background_color='white', size=(width_1, height_1)),
     sg.Input(key='_i_DFL', background_color='white',
              disabled=True, text_color='black', size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_DFL', size=(width_3, height_3))],

    # 'Encrypt' Button
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Encrypt', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_Encrypt', size=(width_3, height_3))],

    # Anonymised File
    [sg.Text('Anonymised File Located at', background_color='white', text_color='black', border_width=2,
             size=(width_1, height_1)),
     sg.Input(key='_i_AFL', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_AFL', size=(width_3, height_3))],

    # Anonymised Dictionary
    [sg.Text('Anonymisation Dictionary Located at', background_color='white', text_color='black', border_width=2,
             size=(width_1, height_1)),
     sg.Input(key='_i_ADL', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_ADL', size=(width_3, height_3))],

    # 'Get Predictions' Button
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Get Predictions', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_GetPredictions', size=(width_3, height_3))],
]

layout_step_3 = [
    [sg.Text('Anonymisation Predictions File', background_color='white', text_color='black', border_width=2,
             size=(width_1, height_1)),
     sg.Input(key='_i_APF', text_color='black',
              disabled=True, size=(width_2, height_2)),
     sg.Button('Inspect', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('orange', 'white'), key='_b_Inspect_APF', size=(width_3, height_3))],

    # 'Decrypt' Button
    [sg.Text('', background_color='white', text_color='black', size=(width_1, height_1)),
     # sg.Text('', background_color='white', text_color='black', size=(width_2-width_3, height_2-height_3)),
     sg.Button('Decrypt', pad=None, font=('MS Sans Serif', 10, 'bold'),
               button_color=('blue', 'white'), key='_b_Decrypt', size=(width_3, height_3))],
]

layout_step_4 = [
    [sg.Text('De-Anonymisation Predictions File', background_color='white', text_color='black', border_width=2,
             size=(width_1, height_1)),
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

# Main layout going to be added to 'window'
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


#  METHODS RELATED TO  'PySimpleGui'
def update_progress_bar(completed_commits):
    # lock.acquire()

    len_completed_commits = len(completed_commits)

    logging.info('PROCESS / COMMITS COUNTs:: ' + str(len_completed_commits) + ' / ' + str(total_commits_count))

    progressBar.update_bar(len_completed_commits, total_commits_count)
    progressBarText.update(str(len_completed_commits) + ' / ' + str(total_commits_count))

    if len(completed_commits) == total_commits_count:
        progressBarText.update(visible=False)
        progressBar.update_bar(0, 0)
    else:
        progressBarText.update(visible=True)

    # lock.release()


def process_commit(commit, doc_list, completed_commits):
    for mod in commit.modifications:
        # Create a field 'file_ext' which is the file 'type'
        # https://www.geeksforgeeks.org/how-to-get-file-extension-in-python/
        # 'pathlib.Path' gives extension 'None' for all '.' files i.e. .bashrc etc.
        #     it also gives an exception in some cases. We need to handle that too.
        file_ext = pathlib.Path(mod.filename).suffix or 'NoExt'

        mod_data = {'hash': commit.hash, 'Author': commit.author.name, 'Email': commit.author.email,
                    'message': commit.msg, 'authored_date': commit.author_date,
                    'Committer': commit.committer.name, 'committed_date': commit.committer_date,
                    'number_of_branches': len(commit.branches), 'in_main_branch': commit.in_main_branch,
                    'merge_commit?': commit.merge,
                    'number_of_mod_files': len(commit.modifications),
                    'file_name': mod.filename,
                    'file_ext': file_ext,
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
        # List appending is threadsafe: https://stackoverflow.com/a/18568017
        doc_list.append(mod_data)

    completed_commits.append(commit.hash)
    update_progress_bar(completed_commits)


def store_commit_data(git_directory, devranker_dir, output_file_name):
    # Creating empty lists for carrying commit data
    doclist = []
    # To update progress bar, using list here because it's thread-safe
    completed_commits = []

    # Create Multithreading pool to use full CPU
    # Ref: https://pythonspeed.com/articles/python-multiprocessing/
    pool = mp.Pool(mp.cpu_count())

    # If the Repo has just been cloned, the program will traverse the whole Repo
    # kc - progress bar needs to use the commit number from here or from 'process_commit'
    # https://dzone.com/articles/shared-counter-python%E2%80%99s

    commits = RepositoryMining(git_directory).traverse_commits()

    global total_commits_count
    # 'more_itertools' used here to find commits count as 'commits' is Iterable
    total_commits_count = more_itertools.ilen(commits)

    [pool.apply_async(process_commit(commit, doclist, completed_commits)) for commit in
     RepositoryMining(git_directory).traverse_commits()]
    # Close Multiprocessing pool
    pool.close()
    pool.join()

    # We have data in json format but we need output as csv.
    # There are many approaches to doing this including using dictionaries and stuff.
    # But the easiest way is to write json to file using json.dump and using pandas to read json file.
    # Write data to temp file since pandas.read_json expects file. We can probably optimise without having to
    #     create a new file.
    temp_file = os.path.join(devranker_dir, 'mod_data.json')
    with open(temp_file, 'w') as temp_out_file:
        # json.dump cannot handle python datetime object. We should convert this object to 'str'
        # https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
        # https://code-maven.com/serialize-datetime-object-as-json-in-python
        json.dump(doclist, temp_out_file, default=str)

    # Use pandas to read json and write to csv.
    df = pandas.read_json(temp_file)
    df.to_csv(output_file_name)

    # Remove the temp file
    os.remove(temp_file)

    # Inform user that mining is complete
    sg.popup('Mining is done and File location is \n' + output_file_name)


def validate_directories():
    if gitDirectory == '':
        sg.popup('Please Select Git Directory')
    elif DestDirectory == '':
        sg.popup('Please Select Output Directory')
    else:
        try:
            repo = git.Repo(gitDirectory)
            return True
        except:
            print('exc @ validate_directories', sys.exc_info())
            sg.popup('Invalid Git Directory, Please choose valid Git Directory')
            return False


def start_gui_Window():
    global progressBar
    global progressBarText
    global inputDestDir
    global dataFileLocation

    global gitDirectory
    global DestDirectory

    window = sg.Window('Dev Ranker', layout_main, background_color='white', finalize=True)
    progressBar = window['_pb']
    progressBarText = window['_t_ProgressValue']
    inputDestDir = window['_i_DestDirectory']
    dataFileLocation = window['_i_DFL']

    while True:
        event, values = window.Read()
        print(event, values)

        # STEP-1 Related
        if event in (None, 'Exit'):
            break

        elif event == '_i_GitDirectory':
            gitDirectory = values['_i_GitDirectory']
            logging.info('_i_GitDirectory', gitDirectory)
            # Verify if this is a gitRepo right here.
            try:
                repo = git.Repo(gitDirectory)
            except:
                print('exc after GitDirectory Button clicked ', sys.exc_info())
                sg.popup('Invalid Git Directory, Please choose valid Git Directory')
                # kc Need to clear gitDirectory
                continue

        elif event == '_i_StartMining':
            if validate_directories():
                # https://docs.python.org/3/library/os.path.html
                devranker_dir = os.path.join(DestDirectory, 'Devranker')
                if not os.path.exists(devranker_dir):
                    os.mkdir(devranker_dir)
                    sg.popup('Created working Directory: ', devranker_dir)

                # Create a filename from repo name. This is just the name. This is still not a file.
                repo_name = os.path.basename(gitDirectory)
                temp_file_name = repo_name + '.git.csv'
                output_file_name = os.path.join(devranker_dir, temp_file_name)
                # logging.info("OutputFilename", str(output_file_name))
            else:
                # Need to clear gitDirectory and DestDir here or at respective places.
                continue
            try:
                store_commit_data(gitDirectory, devranker_dir, output_file_name)
            except:
                logging.info("store_commit failed", '0')
                continue

        elif event == '_i_LiveLog':
            # update_progress_bar(100)
            sg.popup('Live Log Clicked')

        elif event == '_i_DestDirectory':
            DestDirectory = values['_i_DestDirectory']
            # dataFileLocation.update(outputFileLocation)
            # liveLogs(devranker_dir, values['_i_DestDirectory'])

        # STEP2 Related
        elif event == '_b_Inspect_DFL':
            sg.popup('Inspect DFL')
            # logging.debug('clicked _Inspect_DFL ')

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

    window.close


if __name__ == '__main__':
    # We should call this 'mp.set_start_method("spawn")' here only even though 'mp' used
    # in 'store_commit_data()' only, because when pressing 'Start Mining' button 2nd time
    # (Mostly after mining is done) 'mp.set_start_method("spawn")' throwing exception

    # Why 'set_start_method("spawn")'?
    # Because getting Multiple windows unnecessarily and window became unresponsive after Mining is done
    # Ref: https://pythonspeed.com/articles/python-multiprocessing/

    mp.set_start_method("spawn")

    # Calling window and initializing required widgets
    start_gui_Window()
