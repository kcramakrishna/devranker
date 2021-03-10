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
import pickle
import hashlib


# logging.basicConfig(level=logging.DEBUG)


# Initializing Variables
total_commits_count = 0
dict_callback = {"status": True, "msg": ""}
dict_callback_start_mining = {"status": True, "msg": "", "tc": 0, "cc": 0}


# Methods related to 'DevRanker'
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


# def store_commit_data(get_git_directory_path, get_devranker_dir, get_output_file_path):
def store_commit_data(git_directory_path, devranker_dir, output_file_path):
    # Why 'set_start_method("spawn")'?
    # Because getting Multiple windows unnecessarily and window became unresponsive after Mining is done
    # Ref: https://pythonspeed.com/articles/python-multiprocessing/

    mp.set_start_method("spawn")

    # Creating empty lists for carrying commit data
    doclist = []
    # Using list to update progress bar because it's thread-safe
    completed_commits = []

    # Create Multithreading pool to use full CPU
    # Ref: https://pythonspeed.com/articles/python-multiprocessing/
    pool = mp.Pool(mp.cpu_count())

    # If the Repo has just been cloned, the program will traverse the whole Repo
    # https://dzone.com/articles/shared-counter-python%E2%80%99s
    commits = RepositoryMining(git_directory_path).traverse_commits()
    # TODO: RAVI -> Move this into SETTERS/GETTERS
    global total_commits_count
    # 'more_itertools' used here to find commits count as 'commits' is Iterable
    # Note: ilen(commits) consumes the iterable 'commits'
    total_commits_count = more_itertools.ilen(commits)

    [pool.apply_async(process_commit(commit, doclist, completed_commits)) for commit in
     RepositoryMining(git_directory_path).traverse_commits()]
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
    df.to_csv(output_file_path)

    # Remove the temp file
    os.remove(temp_file)
    # display_data_file_location_path()
    # Inform user that mining is complete

    dict_callback_start_mining["msg"] = "Done"
    dict_callback_start_mining["tc"] = 0
    dict_callback_start_mining["cc"] = 0
    print(json.dumps(dict_callback_start_mining))


def anonymize(output_file_path, email_hash_dict_file_path, anonymized_file_path):
    target_repo_commits = pandas.read_csv(output_file_path)

    for i in range(len(target_repo_commits)):
        # Encrypt Author
        clear_text = target_repo_commits.loc[i, 'Author']
        hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
        target_repo_commits.loc[i, 'Author_encrypted'] = hashed

        # Encrypt Email
        clear_text = target_repo_commits.loc[i, 'Email']
        hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
        target_repo_commits.loc[i, 'Email_encrypted'] = hashed
        # if DEBUG >= 1:
        #     print('hash, email: ', hashed, clear_text)

        # Encrypt Committer
        clear_text = target_repo_commits.loc[i, 'Committer']
        hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
        target_repo_commits.loc[i, 'Committer_encrypted'] = hashed

        # Encrypt file_name
        clear_text = target_repo_commits.loc[i, 'file_name']
        hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
        target_repo_commits.loc[i, 'file_name_encrypted'] = hashed

        # Encrypt file_old_path
        clear_text = target_repo_commits.loc[i, 'file_old_path']
        hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
        target_repo_commits.loc[i, 'file_old_path_encrypted'] = hashed

        # Encrypt file_new_path
        clear_text = target_repo_commits.loc[i, 'file_new_path']
        hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
        target_repo_commits.loc[i, 'file_new_path_encrypted'] = hashed

    # Create a dictionary for email-ids. We need this later to decrypt the predictions file.
    # We can ignore the other encrypted fileds for now.
    email_hash_dict = {}
    for author_email in target_repo_commits['Email'].unique().tolist():
        # First hash the email
        hashed_email = hashlib.sha256(str(author_email).encode()).hexdigest()
        # Now add the hash and corresponding email to dictionary
        email_hash_dict[hashed_email] = author_email

    # Pickle this dictionary and write to file for future use
    email_hash_dict_file = email_hash_dict_file_path
    email_hash_dict_file_handler = open(email_hash_dict_file, 'wb')
    pickle.dump(email_hash_dict, email_hash_dict_file_handler)
    email_hash_dict_file_handler.close()

    # Drop the clear text columns 
    target_repo_commits.drop(columns=['Author', 'Email', 'Committer', 'file_name', 'file_old_path', 'file_new_path'],
                             inplace=True)

    # Write it out to the file. This is the file that is to be uploaded for scoring and prediction.
    target_repo_commits.to_csv(anonymized_file_path)
   
    print("Done")
    # sg.popup('Anonymize is done.', '\n\nAnonymize File location:\n' + anonymized_file_path,
    #          '\n\nAnonymize File Dictionary location:\n' + email_hash_dict_file_path)


def de_anonymize(anonymized_predictions_file_path, email_hash_dict_file_path, dev_predictions_file_path):
    try:
        # Read the file to be decrypted
        print(1, anonymized_predictions_file_path,  email_hash_dict_file_path, dev_predictions_file_path)
        anonymized_predictions_data = pandas.read_csv(anonymized_predictions_file_path)
        # Read saved dictionary file and recreate the dictionary
        email_hash_dict_file_handler = open(email_hash_dict_file_path, 'rb')
        print(2, email_hash_dict_file_handler)
        email_hash_dict = pickle.load(email_hash_dict_file_handler)
        print(3, email_hash_dict)
        predictions_data = anonymized_predictions_data.copy()
        print(4, predictions_data)

        # Iterate through each row to put back the emails
        for i in range(len(predictions_data)):
            hashed_email = anonymized_predictions_data.loc[i, 'Email_encrypted']
            predictions_data.loc[i, 'Email'] = email_hash_dict.get(hashed_email)
            predictions_data.to_csv(dev_predictions_file_path)

        dict_callback["status"] = True
        dict_callback["msg"] = "De Anonymization is Completed"
        print(json.dumps(dict_callback))

    except:
        # print(sys.exc_info())
        dict_callback["status"] = False
        dict_callback["msg"] = sys.exc_info()[0]
        print(json.dumps(dict_callback))

    # print('De Anonymizing is done and File location is', dev_predictions_file_path)


def update_progress_bar(completed_commits):
    len_completed_commits = len(completed_commits)
    # print(len_completed_commits, total_commits_count)
    dict_callback_start_mining["msg"] = "Progress"
    dict_callback_start_mining["tc"] = total_commits_count
    dict_callback_start_mining["cc"] = len_completed_commits
    print(json.dumps(dict_callback_start_mining))
    sys.stdout.flush()

def get_csv_data():
    csv_data = pandas.read_csv('/Users/rknowsys/Desktop/Devranker/dev_scores_elasticray.git.csv')

    Emails = csv_data['Email'].unique()
    dates = csv_data['committed_date'].unique()
    dicttables = {}

    for extE in Emails:
        dicttables[extE] = {}
        for extd in dates:
            dicttables[extE][extd] = 0
    for j in range(csv_data.shape[0]):
        dicttables[csv_data['Email'][j]][csv_data['committed_date'][j]] += csv_data['mod_score'][j]
    print(json.dumps(dicttables))

# def start_gui_Window(event):
    # while True:
    #     if event == '_i_GitDirectory':
    #         path = values['_i_GitDirectory']
    #         logging.info('_i_GitDirectory', path)
    #         # Verify if this is a gitRepo right here.
    #         try:
    #             repo = git.Repo(path)
    #             set_git_directory_path(path)
    #         except:
    #             sg.popup(
    #                 'Invalid Git Directory, Please choose valid Git Directory')
    #             # kc Need to clear gitDirectory
    #             continue

    #     elif event == '_i_StartMining':
    #         if validate_directories():
    #             set_devranker_dir()
    #             set_output_file_path()
    #         else:
    #             # Need to clear gitDirectory and DestDir here or at respective places.
    #             continue
    #         try:
    #             store_commit_data()
    #         except:
    #             continue

    #     elif event == '_i_DestDirectory':
    #         set_dest_directory_path(values['_i_DestDirectory'])

    #     elif event == '_b_Encrypt':
    #         anonymize()

    #     elif event == '_b_Decrypt':
    #         de_anonymize()

if __name__ == '__main__':
    # Calling window and initializing required widgets
    # dict_callback = {"status": True, "msg": ""}
    # print(sys.argv)
    method_name = sys.argv[1]

    if(sys.argv[1] == 'check_git_dir'):
        # print("aaaaaa")
        # Verify if this is a gitRepo right here.
        try:
            git.Repo(sys.argv[2])

            dict_callback["status"] = True
            dict_callback["msg"] = 'Its a Valid Git Directory'
            print(json.dumps(dict_callback))
        except:
            dict_callback["status"] = False
            dict_callback["msg"] = 'Invalid Git Directory, Please choose valid Git Directory'
            print(json.dumps(dict_callback))

    elif(sys.argv[1] == 'start_mining'):
        try:
            store_commit_data(sys.argv[2], sys.argv[3], sys.argv[4])
        except:
            dict_callback_start_mining["msg"] = sys.exc_info()
            print(json.dumps(dict_callback_start_mining))

    elif(method_name == 'anonymize'):
        anonymize(sys.argv[2], sys.argv[3], sys.argv[4])

    elif(method_name == 'de_anonymize'):
        de_anonymize(sys.argv[2], sys.argv[3], sys.argv[4])

    elif(method_name == 'get_csv_data'):
        get_csv_data()
