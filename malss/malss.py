# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from sklearn.utils import shuffle as sk_shuffle
from sklearn import cross_validation
from sklearn.grid_search import GridSearchCV
from sklearn.learning_curve import learning_curve
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from docutils.core import publish_cmdline
from sklearn.datasets import fetch_mldata

from algorithm import Algorithm


class MALSS(object):
    def __init__(self, X, y, task, shuffle=True, n_jobs=1):
        """
        Set the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : array, shape = [n_samples]
            Target values (class labels in classification, real numbers in regression)
        task : string
            Specifies the task of the analysis. It must be one of 'classification', 'regression'.
        shuffle : boolean, optional (default=True)
            Whether to shuffle the data.
        n_jobs : integer, optional (default=1)
            The number of jobs to run in parallel. If -1, then the number of jobs is set to the number of cores.
        """
        if task == 'classification':
            if shuffle:
                self.X, self.y = sk_shuffle(X, y, random_state=0)
            else:
                self.X = X
                self.y = y
            self.X = StandardScaler().fit_transform(self.X)
            self.task = task
            self.n_jobs = n_jobs
            self.algorithms = self.__choose_algorithm()
        elif task == 'regression':
            raise ValueError('task:%s is not implemented yet')
        else:
            raise ValueError('task:%s is not supported'%task)


    def __choose_algorithm(self):
        algorithms = []
        if self.task == 'classification':
            algorithms.append(Algorithm(SVC(random_state=0),
                [{'kernel': ['rbf'], 'C': [1, 10, 100, 1000],
                'gamma': [1e-4, 1e-3, 1e-2, 1e-1]}]))
        return algorithms
    
    
    def execute(self):
        self.__tune_parameters()
        self.__plot_learning_curve()
        self.__make_report()


    def __tune_parameters(self):
        if self.task == 'classification':
            sc = 'accuracy'
        elif self.task == 'regression':
            sc = 'r2'
        
        for i in xrange(len(self.algorithms)):
            estimator = self.algorithms[i].estimator
            parameters = self.algorithms[i].parameters
            cv = cross_validation.StratifiedShuffleSplit(self.y, test_size=0.2, random_state=0)
            clf = GridSearchCV(estimator, parameters, cv=cv, scoring=sc, n_jobs=self.n_jobs)
            clf.fit(self.X, self.y)
            self.algorithms[i].estimator = clf.best_estimator_


    def __plot_learning_curve(self):
        for alg in self.algorithms:
            estimator = alg.estimator
            cv = cross_validation.StratifiedShuffleSplit(self.y, test_size=0.2, random_state=0)
            train_sizes, train_scores, test_scores = learning_curve(
                estimator, self.X, self.y, cv=cv, n_jobs=self.n_jobs)
            train_scores_mean = np.mean(train_scores, axis=1)
            train_scores_std = np.std(train_scores, axis=1)
            test_scores_mean = np.mean(test_scores, axis=1)
            test_scores_std = np.std(test_scores, axis=1)

            plt.figure()
            plt.title(estimator.__class__.__name__)
            plt.xlabel("Training examples")
            plt.ylabel("Score")
            plt.grid()
        
            plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                             train_scores_mean + train_scores_std, alpha=0.1,
                             color="r")
            plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                             test_scores_mean + test_scores_std, alpha=0.1, color="g")
            plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
                     label="Training score")
            plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
                     label="Cross-validation score")
        
            plt.legend(loc="lower right")
            plt.savefig('learning_curve_%s.png'%estimator.__class__.__name__, bbox_inches='tight', dpi=75)
            plt.close()
    
    
    def __make_report(self):
        fo = open('report.rst', 'w')
        fo.write('.. image:: learning_curve_SVC.png')
        fo.close()
        publish_cmdline(writer_name='html', argv=['report.rst', 'report.html'])


def __make_data():
    import os
    
    if not os.path.exists('data/spam.txt'):
        if not os.path.exists('data'):
            os.mkdir('data')
        
        import urllib
        urllib.urlretrieve('http://mldata.org/repository/data/download/uci-20070111-spambase/', 'data/uci-20070111-spambase.arff')
        fi = open('data/uci-20070111-spambase.arff', 'r')
        fo = open('data/spam.txt', 'w')
        header = []
        for line in fi:
            if '@attribute' in line:
                header.append(line.rstrip().split(' ')[1])
            if '@data' in line:
                break
        for h in header:
            fo.write(h)
            if h == header[-1]:
                fo.write('\n')
            else:
                fo.write(',')
        for line in fi:
            line = line.rstrip()
            line = line[:-1]+'spam' if line[-1] == '1' else line[:-1]+'nonspam'
            fo.write(line+'\n')
        fi.close()
        fo.close()
        
        os.remove('data/uci-20070111-spambase.arff')

    data = pd.read_csv('./data/spam.txt', header=0)
    y = data['class']
    del data['class']
    
    return data, y


if __name__=="__main__":
    data, y = __make_data()
    cls = MALSS(data, y, 'classification', n_jobs=3)
    cls.execute()


