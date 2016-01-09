__author__ = 'fenixlin'

import os
import cPickle
import random
import numpy as np
import scipy.sparse as sp
from parser import MLParser

class Database(object):

    def __init__(self, dataFormat, user_num, item_num, ratingfile, itemfile=None, userfile=None, home_dir="./"):
        if dataFormat=="movielens":
            self.parser = MLParser(ratingfile, itemfile, userfile)
        elif dataFormat=="amazon":
            self.parser = AmazonParser(ratingfile, itemfile, userfile)
        else:
            raise ValueError("Valid dataFormat: movielens, amazon")
            
        # nums must be explicitly assigned, since we won't get it from recovered data directly 
        self.USER_NUM = user_num
        self.ITEM_NUM = item_num
        
        self.home_dir = home_dir
        if not os.path.exists(self.home_dir):
            os.makedirs(self.home_dir)
        self.itemfile = itemfile
        self.ratingfile = ratingfile
        self.userfile = userfile

        # holding all underlying data
        self.rating_list = []
        self.attribute_list = []

        # holding substitutable training and testing data
        self.train_matrix = None
        self.train_item_id_of_col = None
        self.test_matrix = None
        self.test_item_id_of_col = None

    def load_data(self, sort_data=True, dump_file='dumpable.data'):
        try:
            self._recover_dumpable_data(self.home_dir+dump_file)
        except:
            self.parser.load_raw_data()
            self.attribute_list = self.parser.extract_attr_list()
            self.rating_list = self.parser.extract_rating_list(sort_data)
            #XXX: seems not necessary to dump
            #self._dump_rating_list(self.home_dir+dump_file)

    def make_train_test_matrix(self, train_test_ratio = 0.8):
        #XXX: merge into load_data()?
        self.train_matrix, self.train_item_id_of_col, _ = \
            self._extract_rating_matrix( \
            self._filtered_rating_list(0, int(self.ITEM_NUM*train_test_ratio)))
        self.test_matrix, self.test_item_id_of_col, _ = \
            self._extract_rating_matrix( \
            self._filtered_rating_list(int(self.ITEM_NUM*train_test_ratio)+1, self.ITEM_NUM-1))

    def dump_libfm_data(self, train_file=None, test_file=None, add_negative=False, binary=False, shuffle=True, omit_item=True):
        # output libfm format data from rating matrix
        # [rating item attribute] if omit_item==False, [rating attribute] if omit_item==True
        if add_negative:
            #XXX: do not actually addAllUsers and just output it to save time?
            train_matrix = self._add_neg_to_matrix(self.train_matrix.copy())
            test_matrix = self._add_neg_to_matrix(self.test_matrix.copy(), addAllUsers=True)
        else:
            train_matrix = self.train_matrix
            test_matrix = self.test_matrix

        if train_file!=None:
            self._dump_matrix_to_libfm_file(self.home_dir+train_file, train_matrix, self.train_item_id_of_col, binary, shuffle, omit_item)
        if test_file!=None:
            self._dump_matrix_to_libfm_file(self.home_dir+test_file, test_matrix, self.test_item_id_of_col, binary, shuffle, omit_item)

    def load_prediction_list(self, pred_file, task, threshold=0.5):
        #TODO: merge accuracy and regression error calculation inside.
        if task!='c' and task!='r':
            raise ValueError("task should be r(regression) or c(classification)")
        f = open(self.home_dir+pred_file,'r')
        row, col = self.test_matrix.nonzero()
        result = []
        for i in range(len(row)):
            pred = f.readline().strip()
            if task=='c':
                pred = pred>threshold
            result.append([row[i]. col[i]. pred])
        f.close()
        return result

    def _recover_dumpable_data(self, filename):
        f = open(filename, mode='rb')
        self.rating_list = cPickle.load(f)
        f.close()

    def _dump_rating_list(self, filename):
        #XXX: seems not necessary
        f = open(filename, 'wb')
        cPickle.dump(self.rating_list, f, protocol=2)
        f.close()

    def _add_neg_to_matrix(self, matrix, addAllUsers=False):
        #assign neg rating to -1 just for storing, output in file will be 0
        height, width = matrix.get_shape()
        count = 0
        if addAllUsers:
            for i in range(height):
                for j in range(width):
                    if matrix[i, j] == 0:
                        count += 1
                        matrix[i, j] = -1
                        if count%20000==0:
                            print count,"negative rating added..."
        else:
            target = matrix.nnz
            while count < target:
                i = random.randint(0, height-1)
                j = random.randint(0, width-1)
                if matrix[i, j] == 0:
                    count += 1
                    matrix[i, j] = -1
                if count%20000==0:
                    print count,"negative rating added..."
        print count,"negative rating added in total."
        return matrix

    def _dump_matrix_to_libfm_file(self, filename, matrix, item_id_of_col, binary, shuffle=True, omit_item=False):
        row, col = matrix.nonzero()
        height, width = matrix.get_shape()
        index = range(len(row))
        if shuffle:
            random.shuffle(index)
        count = 0
        libfm_file = open(filename, 'w')
        for i in index:
            x = row[i]
            y = col[i]
            rating = matrix[x,y]
            #assign neg rating to -1 just for storing, output in file will be 0
            if rating < 0:
                rating = 0
            if binary and rating>0:
                rating = 1
            libfm_file.write(str(rating)+' '+str(x)+':1')
            filled_num = height 
            if not omit_item:
                libfm_file.write(' '+str(y+filled_num)+':1')
                filled_num += width
            for attribute_pos in self.attribute_list[item_id_of_col[y]]:
                libfm_file.write(' '+str(filled_num+attribute_pos)+':1')
            libfm_file.write('\n')
            count += 1
            if count%20000==0:
                print filename,count,'lines written...'
        libfm_file.close()
        print filename,count,'lines written in total.'

    def _filtered_rating_list(self, head_item_count, tail_item_count):
        item_num_of_id = dict()
        for values in self.rating_list:
            itemID = values[1]
            if not item_num_of_id.has_key(itemID):
                item_num_of_id[itemID] = len(item_num_of_id)
            item_num = item_num_of_id[itemID]
            if item_num>=head_item_count and item_num<=tail_item_count:
                yield values

    def _extract_rating_matrix(self, rating_list):
        # XXX: make it to utils?
        # get specific rating matrix from given rating list(one rating per line)
        col_num_of_item = [-1 for i in range(self.ITEM_NUM)] # we may not have all items, so compression is needed
        item_id_of_col = []
        rating_matrix = np.zeros([self.USER_NUM, self.ITEM_NUM])
        item_count = -1
        for values in rating_list:
            userID = values[0]
            itemID = values[1]
            if col_num_of_item[itemID] < 0:
                item_count += 1
                col_num_of_item[itemID] = item_count
                item_id_of_col.append(itemID)
            rating = values[2]
            rating_matrix[userID, col_num_of_item[itemID]] = rating
        rating_matrix = sp.coo_matrix(rating_matrix[:, :item_count]).tolil() # item_count may not reach max_item_num
        print 'rating matrix is {0}*{1}'.format(self.USER_NUM, item_count)
        return rating_matrix, item_id_of_col, col_num_of_item

