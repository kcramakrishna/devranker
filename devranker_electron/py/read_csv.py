import sys
import pandas
import json


sys.path.append('/usr/lib/python3.9/site-packages')

def get_csv_data():
    print(json.dumps('dlkfdklfldjfldfj******'))
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

if __name__ == '__main__':
    # sys.argv index starting from 1, 0 is file name
    get_csv_data()
    #  print('Arguments from renderer.js are:', sys.argv) 