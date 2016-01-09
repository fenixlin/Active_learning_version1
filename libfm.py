import subprocess

class LibFM(object):
    
    def __init__(self, data_dir="./"):
        self.data_dir = data_dir

    def run(self, task, train_file, test_file, pred_file, method="mcmc", iter_num=100):
        subprocess.call(self.data_dir + "libFM -task " + task \
            + " -train " + train_file + " -test " + test_file \
            + " -method " + method + " -iter " + str(iter_num) \
            + " -out " + pred_file, shell=True)
