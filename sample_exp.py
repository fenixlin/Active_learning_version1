__author__ = 'fenixlin'
from db import Database
from libfm import LibFM

def sample_exp():
    # making data from origin format to libfm format
    db = Database('movielens', 718, 8928, 'ratings.csv', 'movies.attr')
    db.load_data()
    db.make_train_test_matrix()
    libfm = LibFM()

    # step 1: classification to predict interest
    db.dump_libfm_data('train_step1.libfm', 'test_step1.libfm', add_negative=True, binary=True)
    #libfm.run('c', 'train_step1.libfm', 'test_step1.libfm', 'pred.libfm')
    #step1_pred_list = db.load_pred_list('pred.libfm', 'c')

    # step 2: regression to predict possible rating
    db.dump_libfm_data('train_step2.libfm', 'test_step2.libfm', add_negative=False, binary=False)
    #libfm.run('r', 'train_step1.libfm', 'test_step1.libfm', 'pred.libfm')
    #step2_pred_list = db.load_pred_list('pred.libfm', 'r')

    # step 3: select users for active learning via matlab program
    # TODO: matlab program

if __name__ == '__main__':
    sample_exp()
