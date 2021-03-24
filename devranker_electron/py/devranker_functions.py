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
# https://github.com/nalepae/pandarallel
from pandarallel import pandarallel

# We have another way to parallelize pandas which we are not using here
# https://www.kdnuggets.com/2019/11/speed-up-pandas-4x.html

# Initializing Variables
total_commits_count = 0
dict_callback = {"status": True, "msg": ""}
dict_callback_start_mining = {"status": True, "msg": "", "tc": 0, "cc": 0}
# kc - pandarallel https://github.com/nalepae/pandarallel
pandarallel.initialize(verbose=0)

# Methods related to 'DevRanker'
def process_commit(commit, doc_list, completed_commits):
    for mod in commit.modifications:
        # Create a field 'file_ext' which is the file 'type'
        # https://www.geeksforgeeks.org/how-to-get-file-extension-in-python/
        # 'pathlib.Path' gives extension 'None' for all '.' files i.e. .bashrc etc.
        #     it also gives an exception in some cases. We need to handle that too.
        file_ext_suffix = pathlib.Path(mod.filename).suffix or '.NoExt'
        file_ext = file_ext_suffix.split('.')[1]

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


def hash_encrypt(clear_text):
    hashed = hashlib.sha256(str(clear_text).encode()).hexdigest()
    return hashed


def hash_decrypt_lookup(key, dictionary):
    return dictionary.get(key)


def anonymize(output_file_path, email_hash_dict_file_path, anonymized_file_path):
    target_repo_commits = pandas.read_csv(output_file_path)

    # Realised that calculating hash on normal CPU'is is quite expensive and slow.
    # For now, we are encrypting only email id.

    # Create a dictionary for hashed email-ids. Hashing only once to improve performance.
    # We need this later to decrypt the predictions file.
    # We can ignore the other encrypted fields for now.
    email_hash_dict = {}
    # creating a temporary reverse dictionary to optimise for speed/time. We will use the below.
    reverse_email_hash_dict = {}
    for author_email in target_repo_commits['Email'].unique().tolist():
        # First hash the email
        hashed_email = hash_encrypt(author_email)
        # Now add the hash and corresponding email to dictionary
        email_hash_dict[hashed_email] = author_email
        # Now populate the reverse dict
        reverse_email_hash_dict[author_email] = hashed_email

    # Pickle this dictionary and write to file for future use
    # We don't need to pickle the reverse dictionary
    email_hash_dict_file = email_hash_dict_file_path
    email_hash_dict_file_handler = open(email_hash_dict_file, 'wb')
    pickle.dump(email_hash_dict, email_hash_dict_file_handler)
    email_hash_dict_file_handler.close()

    # Encrypt email
    # Logic should be to look up the hashed email from dictionary and add it to the pandas dataframe.
    # https://stackoverflow.com/questions/20250771/remap-values-in-pandas-column-with-a-dict
    target_repo_commits['Email_encrypted'] = \
        target_repo_commits['Email'].parallel_map(reverse_email_hash_dict)

    # We will need to create dictionary at some point if we need to display original string.
    target_repo_commits['Author_encrypted'] = \
        target_repo_commits.parallel_apply(lambda x: hash_encrypt(x['Author']), axis=1)

    # We will need to create dictionary at some point if we need to display original string.
    target_repo_commits['Committer_encrypted'] = \
        target_repo_commits.parallel_apply(lambda x: hash_encrypt(x['Committer']), axis=1)

    # We will need to create dictionary at some point if we need to display original string.
    target_repo_commits['file_name_encrypted'] = \
        target_repo_commits.parallel_apply(lambda x: hash_encrypt(x['file_name']), axis=1)

    # We will need to create dictionary at some point if we need to display original string.
    target_repo_commits['file_old_path_encrypted'] = \
        target_repo_commits.parallel_apply(lambda x: hash_encrypt(x['file_old_path']), axis=1)

    # We will need to create dictionary at some point if we need to display original string.
    target_repo_commits['file_new_path_encrypted'] = \
        target_repo_commits.parallel_apply(lambda x: hash_encrypt(x['file_new_path']), axis=1)

    # Drop the clear text columns
    target_repo_commits.drop(columns=['Author', 'Email', 'Committer', 'file_name', 'file_old_path', 'file_new_path'],
                             inplace=True)

    # Write it out to the file. This is the file that is to be uploaded for scoring and prediction.
    target_repo_commits.to_csv(anonymized_file_path)

    print("Done: ", anonymized_file_path)

def de_anonymize(anonymized_predictions_file_path, email_hash_dict_file_path, dev_predictions_file_path):

    anonymized_predictions_data = pandas.read_csv(anonymized_predictions_file_path, low_memory=False)
    # Read saved dictionary file and recreate the dictionary
    email_hash_dict_file_handler = open(email_hash_dict_file_path, 'rb')
    email_hash_dict = pickle.load(email_hash_dict_file_handler)
    predictions_data = anonymized_predictions_data.copy()

    # Iterate through each row to put back the emails
    # https://stackoverflow.com/questions/20250771/remap-values-in-pandas-column-with-a-dict
    predictions_data['Email'] = predictions_data['Email_encrypted'].parallel_map(email_hash_dict)

    predictions_data.to_csv(dev_predictions_file_path)
    print('De-anon - Done: ', dev_predictions_file_path)


def update_progress_bar(completed_commits):
    len_completed_commits = len(completed_commits)
    # print(len_completed_commits, total_commits_count)
    dict_callback_start_mining["msg"] = "Progress"
    dict_callback_start_mining["tc"] = total_commits_count
    dict_callback_start_mining["cc"] = len_completed_commits
    print(json.dumps(dict_callback_start_mining))
    sys.stdout.flush()


def get_csv_data(dev_predictions_file_path):
    csv_data = pandas.read_csv(dev_predictions_file_path, low_memory=False)

    Emails = csv_data['Email'].unique()
    dates = csv_data['committed_date'].unique()
    dicttables = {}

    for extE in Emails:
        dicttables[extE] = {}
        for extd in dates:
            dicttables[extE][extd] = 0
    # fixed issue while reading modscore, so kept int() to convert into int before serializing into Json
    # Ref: https://www.javaprogramto.com/2019/11/python-typeerror-integer-json-not-serializable.html            
    for j in range(csv_data.shape[0]):
        dicttables[csv_data['Email'][j]][csv_data['committed_date']
                                         [j]] += int(csv_data['mod_score'][j])  
    print(json.dumps(dicttables))


if __name__ == '__main__':

    method_name = sys.argv[1]

    if(sys.argv[1] == 'check_git_dir'):
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
        get_csv_data(sys.argv[2])
