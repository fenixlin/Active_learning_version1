__author__ = 'fenixlin'
from db import Database
from libfm import LibFM

def sample_exp():
    # making data from origin format to libfm format
    db = Database('movielens', 718, 8928, 'ratings.csv', 'movies.attr')
    db.load_data()
    db.make_train_test_matrix()
    db.add_negative_data('train')
    db.add_negative_data('test',addAllUsers=True)
    db.dump_libfm_data('train_step1.libfm', 'test_step1.libfm')

    libfm = LibFM()
    # step 1: classification to predict interest
    libfm.run('c', 'train_step1.libfm', 'test_step1.libfm', 'pred.libfm')
    step1_pred_list = db.load_pred_list('pred.libfm', 'c')

    # step 2: regression to predict possible rating
    libfm.run('r', 'train_step1.libfm', 'test_step1.libfm', 'pred.libfm')
    step2_pred_list = db.load_pred_list('pred.libfm', 'r')

    # step 3: select users for active learning via matlab program
    # TODO: matlab program

if __name__ == '__main__':
    sample_exp()
