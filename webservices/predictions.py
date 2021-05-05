#test commit
__author__ = 'vamsi'
from flask import Flask, make_response, request
import io
import csv
import os
import glob
from flask.wrappers import Response
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from datetime import datetime
import pandas as pd
import pickle
#import boto3
#from s3fs.core import S3FileSystem

app = Flask(__name__)

def create_ml_frame(pred_commits, ext):
    pred_commits = pred_commits[pred_commits['file_ext'] == ext]

    pred_commits['total_changed'] = pred_commits['number_lines_added'] + pred_commits['number_lines_removed']
    pred_commits['feature_total_changed'] = (pred_commits['total_changed'] ** 0.7)

    pred_commits['n_functions_add_del'] = abs(
        pred_commits['number_functions_before'] - pred_commits['number_functions_after'])
    pred_commits['feature_add_del_functions'] = (pred_commits['n_functions_add_del'] ** 1.3) * (
            pred_commits['total_changed'] ** 0.5)

    pred_commits['feature_changed_functions'] = (pred_commits['number_functions_edited'] ** 1.1) * (
            pred_commits['total_changed'] ** 0.5)

    pred_commits['feature_dmm_size'] = pred_commits['dmm_unit_size'] * (
            ((pred_commits['n_functions_add_del'] ** 1.3) * (pred_commits['total_changed'] ** 0.3)) +
            ((pred_commits['number_functions_edited'] ** 1.1) * (pred_commits['total_changed'] ** 0.3)))
    pred_commits['feature_dmm_unit_complexity'] = pred_commits['dmm_unit_complexity'] * (
            ((pred_commits['n_functions_add_del'] ** 1.3) * (pred_commits['total_changed'] ** 0.3)) +
            ((pred_commits['number_functions_edited'] ** 1.1) * (pred_commits['total_changed'] ** 0.3)))
    pred_commits['feature_dmm_unit_interfacing'] = pred_commits['dmm_unit_interfacing'] * (
            ((pred_commits['n_functions_add_del'] ** 1.3) * (pred_commits['total_changed'] ** 0.3)) +
            ((pred_commits['number_functions_edited'] ** 1.1) * (pred_commits['total_changed'] ** 0.3)))

    pred_ml_commits = pred_commits[
        ['hash', 'Author_encrypted', 'Committer_encrypted', 'Email_encrypted', 'committed_date',
         'feature_total_changed',
         'feature_add_del_functions', 'feature_changed_functions',
         'feature_dmm_unit_complexity',
         'feature_dmm_size', 'feature_dmm_unit_interfacing']]

    # Resetting the frame's index. It is required to retain the integrity of the frame
    pred_ml_commits = pred_ml_commits.reset_index().drop(columns='index')

    # Author/text column needs to be dropped before converting the all the fields into numeric types
    pred_ml_commits_na = pred_ml_commits.drop(columns= \
                                                  ['hash', 'Author_encrypted', 'Committer_encrypted', 'Email_encrypted',
                                                   'committed_date'])

    # Converting the fields to numeric types, filling the NaNs with zeros
    pred_ml_commits_numeric = pred_ml_commits_na.apply(pd.to_numeric, errors='coerce').fillna(0)

    return pred_ml_commits_numeric, pred_commits



# @app.route('/')
# def form():
#     return """
#         <html>
#             <body>
#                 <h1>Transform a file demo</h1>
#
#                 <form action="/predict" method="post" enctype="multipart/form-data">
#                     <input type="file" name="data_file" />
#                     <input type="submit" />
#                 </form>
#             </body>
#         </html>
#     """

@app.route('/predict', methods=["POST"])
def predict():
    # https://flask.palletsprojects.com/en/1.1.x/api/?highlight=files#flask.Request.files
    # https://werkzeug.palletsprojects.com/en/1.0.x/datastructures/#werkzeug.datastructures.FileStorage
    if 'anonymised_file' in request.files:
        f = request.files['anonymised_file']
        # We need to get the name of the uploaded file - the output file name depends on this.
        # This line is not work. Need to figure out why
        target_repo_raw_data_filename = f.filename
        print(f.filename)
    else:
        return "No file"
    # The files can be large ~ MBs. We might add code in client to compress before uploading.
    #       We then need to decompress here.
    # We probably need account mgmt. and authentication/tokens to prevent misuse
    #stream = io.StringIO(f.stream.read().decode("UTF8"), newline=None)



    # Need to have code to validate input file or we risk our program crashing
    # Could be a good exercise for Samit or Atulya

    # What are we doing here ?
    #stream.seek(0)
    #csv_input = stream.read()
    #print(type(csv_input))

    #target_repo_commits = pd.read_csv(io.StringIO(csv_input),sep =',')
    target_repo_commits = pd.read_csv(f)
    target_repo_file_exts = target_repo_commits['file_ext'].unique()

    # Scaling the data
    scaler = MinMaxScaler()
    
     # Folder having the GMM pickle files
    gmm_models_folder = '/home/kc/Projects/data_files/sav_files/gmm_sav/'

    # Get the file names of saved GMM models. Get the file_ext from the file names
    a = glob.glob(gmm_models_folder + '*cpu*.sav')
    gmm_model_files = [os.path.basename(f) for f in a]
    file_ext_models = [x.split('_')[0] for x in gmm_model_files]

    # Folder having xgboost models
    xgboost_models_folder = '/home/kc/Projects/data_files/sav_files/xgboost_sav/'

    # Apparently it is a bad idea to append to DataFrames.
    # https://stackoverflow.com/questions/13784192/creating-an-empty-pandas-dataframe-then-filling-it
    # Create empty list to store dataframes for file extensions
    list_of_dfs = []

    for file_ext in target_repo_file_exts:

        # Prepare the features from raw data
        target_repo_data_frame_numeric, target_repo_data_frame_all_coloumns = create_ml_frame(target_repo_commits,
                                                                                              file_ext)
        # Ensure that we have models for this file extension
        if file_ext in file_ext_models:
            xgboost_model_file = xgboost_models_folder + file_ext + '_cpu_xgboost_model.sav'
            xboost_model = pickle.load(open(xgboost_model_file, 'rb'))

            # Use the xgboost model to predict the cluster
            predicted_clusters = xboost_model.predict(target_repo_data_frame_numeric)
            target_repo_data_frame_all_coloumns['predicted_cluster'] = predicted_clusters

            # Now use the GMM pickled models to calculate the probability of the mod belonging to predicted cluster
            # First get the relevant GMM pickle file for this file type/extension
            gmm_model_file = gmm_models_folder + file_ext + '_cpu_gmm_model_pickle.sav'
            mix = pickle.load(open(gmm_model_file, 'rb'))

            # Scale the data for GMM processing
            data_scaled = scaler.fit_transform(target_repo_data_frame_numeric)

            # Put this in a pandas frame
            cluster_frame = pd.DataFrame(data_scaled)

            # Get the 'real world' value of the centroids. We need these to calculate the 'score' of each mod.
            gmm_centroids = mix.means_
            real_centroids = scaler.inverse_transform(gmm_centroids)

            # Write these to dataframe
            real_centroids_dataFrame = pd.DataFrame(real_centroids, columns=['feature_total_changed',
                                                                             'feature_add_del_functions',
                                                                             'feature_changed_functions',
                                                                             'feature_dmm_unit_complexity',
                                                                             'feature_dmm_size',
                                                                             'feature_dmm_unit_interfacing'])

            # Add a column for summing all coloumns (https://github.com/kcramakrishna/cg/issues/10)
            # This is basically assigning a 'real world value' to each centroid i.e. cluster
            real_centroids_dataFrame['Sum_centroids'] = real_centroids_dataFrame.sum(axis=1)
            real_centroids_dataFrame['original_cluster_labels'] = real_centroids_dataFrame.index

            # Now we need to map the cluster labels to the 'sum of centroids' for that cluster
            centroid_map = {}
            for i in range(real_centroids_dataFrame.shape[0]):
                centroid_map[real_centroids_dataFrame['original_cluster_labels'].values[i]] = real_centroids_dataFrame['Sum_centroids'].values[i]

            # Initialise a coloumn for holding the probabilities of the prediction
            probability_for_labels = np.zeros((len(predicted_clusters), 1))

            # xgboost Gave the prediction, From GMM, get the probability of this prediction
            # Need to understand the below lines in more depth
            member_probs = mix.predict_proba(cluster_frame)
            for i in range(len(predicted_clusters)):
                probability_for_labels[i] = member_probs[i, predicted_clusters[i]]

            # Add the probabilities coloumn to the data Frame
            target_repo_data_frame_all_coloumns['probablities'] = probability_for_labels

            # Look up the Sum of Centroids for each cluster for each mod and add it to the row.
            target_repo_data_frame_all_coloumns['sum_centroid'] = np.arange(0.0,target_repo_data_frame_all_coloumns.shape[0], 1.0)

            for i in range(target_repo_data_frame_all_coloumns.shape[0]):
                target_repo_data_frame_all_coloumns['sum_centroid'].values[i] = centroid_map[target_repo_data_frame_all_coloumns['predicted_cluster'].values[i]]

            # Finally calculate the score for each mod in the target repo
            target_repo_data_frame_all_coloumns['mod_score'] = target_repo_data_frame_all_coloumns['sum_centroid'] * target_repo_data_frame_all_coloumns['probablities']

            # Append this dataframe to list_of_dfs
            list_of_dfs.append(target_repo_data_frame_all_coloumns)
        else:
            target_repo_data_frame_all_coloumns['predicted_cluster'] = 'No Model found'
            target_repo_data_frame_all_coloumns['sum_centroid'] = 0
            target_repo_data_frame_all_coloumns['probablities'] = 0
            target_repo_data_frame_all_coloumns['mod_score'] = 0
            # Append this dataframe to list_of_dfs
            list_of_dfs.append(target_repo_data_frame_all_coloumns)

    # Create a dataframe from list of dataframes
    predictions_dataframe = pd.concat(list_of_dfs, ignore_index=True)

    # Create the name for compressed download file
    # target_repo_raw_data_file is not being set properly. Need to figure out why
    predictions_file = 'cpu_scores_' + f.filename #target_repo_raw_data_file #+ 'zip'
    # We need to dump all the data into this file as csv
    #predictions_file = predictions_dataframe.to_csv(index=False, compression='zip')
    predictions_dataframe.to_csv(predictions_file, index=False)

    # Consider compressing the file before download. We will need to decompress in client too.
    # https://www.w3schools.com/python/ref_requests_response.asp
    # https://www.fullstackpython.com/flask-helpers-make-response-examples.html
    # We need to send filename along with the file contents. We need to figure out how.
    # response = make_response(predictions_file)
    # response.headers["Content-Disposition"] = "attachment"
    # return response
   
    # TODO: KC - It was added by Ravi. Need Code Review?
    try:
        # Reading File Data
        with open(os.path.join(os.getcwd(), predictions_file), 'rb') as f:
             data = f.readlines()
    except Exception as e:
        os.abort(400, e)

    return Response(data, headers={
        'Content-Type': 'application/csv',
        'Content-Disposition': 'attachment; filename=%s;' % predictions_file
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
