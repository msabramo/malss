# -*- coding: utf-8 -*-

import os
import numpy as np
import multiprocessing
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from sklearn.cross_validation import StratifiedKFold, KFold
from sklearn.grid_search import GridSearchCV
from sklearn.learning_curve import learning_curve
from sklearn.svm import SVC, LinearSVC, SVR
from sklearn.metrics import classification_report, f1_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression, Ridge, SGDRegressor,\
    SGDClassifier
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from algorithm import Algorithm
from data import Data


class MALSS(object):
    def __init__(self, task, shuffle=True, standardize=True, scoring=None,
                 cv=5, n_jobs=-1, random_state=0, lang='en', verbose=True):
        """
        Initialize parameters.

        Parameters
        ----------
        task : string
            Specifies the task of the analysis. It must be one of
            'classification', 'regression'.
        shuffle : boolean, optional (default=True)
            Whether to shuffle the data.
        standardize : boolean, optional (default=True)
            Whether to sdandardize the data.
        scoring : string, callable or None, optional, default: None
            A string (see scikit-learn's model evaluation documentation) or
            a scorer callable object / function with
            signature scorer(estimator, X, y).
        cv : integer or cross-validation generator.
            If an integer is passed, it is the number of folds (default 3).
            K-fold cv (for regression task) or Stratified k-fold cv is
            used by default.
            Specific cross-validation objects can be passed, see
            sklearn.cross_validation module for the list of possible objects.
        n_jobs : integer, optional (default=1)
            The number of jobs to run in parallel. If -1, then the number of
            jobs is set to the number of cores - 1.
        random_state : int seed, RandomState instance, or None (default=0)
            The seed of the pseudo random number generator
        lang : string (default='en')
            Specifies the language in the report. It must be one of
            'en' (English), 'jp' (Japanese).
        verbos : bool, default: True
            Enable verbose output.
        """

        self.is_ready = False
        self.shuffle = shuffle
        self.standardize = standardize
        self.task = task
        self.cv = cv
        if n_jobs == -1:
            self.n_jobs = np.max([multiprocessing.cpu_count() - 1, 1])
        else:
            self.n_jobs = n_jobs
        self.random_state = random_state
        self.verbose = verbose
        if lang != 'en' and lang != 'jp':
            raise ValueError('lang:%s is no supported' % lang)
        self.lang = lang
        self.minimized_score = False
        if task == 'classification':
            self.scoring = 'f1' if scoring is None else scoring
        elif task == 'regression':
            self.scoring = 'mean_squared_error' if scoring is None else scoring
            if self.scoring == 'mean_squared_error' or\
               self.scoring == 'mean_absolute_error':
                self.minimized_score = True
        else:
            raise ValueError('task:%s is not supported' % task)

    def __choose_algorithm(self):
        algorithms = []
        if self.task == 'classification':
            if self.data.X.shape[0] * self.data.X.shape[1] <= 1e+06:
                if self.data.X.shape[0] ** 2 * self.data.X.shape[1] <= 1e+09:
                    algorithms.append(
                        Algorithm(
                            SVC(random_state=self.random_state),
                            [{'kernel': ['rbf'],
                              'C': [1, 10, 100, 1000],
                              'gamma': [1e-3, 1e-2, 1e-1, 1.0]}],
                            'Support Vector Machine (RBF Kernel)'))
                    algorithms.append(
                        Algorithm(
                            RandomForestClassifier(
                                random_state=self.random_state,
                                n_jobs=self.n_jobs),
                            [{'n_estimators': [10, 100, 1000],
                              'max_features': [0.3, 0.6, 0.9],
                              'max_depth': [3, 7, None]}],
                            'Random Forest'))
                algorithms.append(
                    Algorithm(
                        LinearSVC(random_state=self.random_state),
                        [{'C': [0.1, 1, 10, 100]}],
                        'Support Vector Machine (Linear Kernel)'))
                algorithms.append(
                    Algorithm(
                        LogisticRegression(random_state=self.random_state),
                        [{'penalty': ['l2', 'l1'],
                          'C': [0.1, 0.3, 1, 3, 10],
                          'class_weight': [None, 'auto']}],
                        'Logistic Regression'))
                algorithms.append(
                    Algorithm(
                        DecisionTreeClassifier(random_state=self.random_state),
                        [{'max_depth': [3, 5, 7, 9, 11]}],
                        'Decision Tree'))
                algorithms.append(
                    Algorithm(
                        KNeighborsClassifier(),
                        [{'n_neighbors': [2, 6, 10, 14, 18]}],
                        'k-Nearest Neighbors'))
            else:
                algorithms.append(
                    Algorithm(
                        SGDClassifier(
                            random_state=self.random_state,
                            n_jobs=self.n_jobs),
                        [{'loss': ['hinge', 'log'],
                          'penalty': ['l2', 'l1'],
                          'alpha': [1e-05, 3e-05, 1e-04, 3e-04, 1e-03],
                          'class_weight': [None, 'auto']}],
                        'SGD Classifier'))
        if self.task == 'regression':
            if self.data.X.shape[0] * self.data.X.shape[1] <= 1e+06:
                if self.data.X.shape[0] ** 2 * self.data.X.shape[1] <= 1e+09:
                    algorithms.append(
                        Algorithm(
                            SVR(random_state=self.random_state),
                            [{'kernel': ['rbf'],
                              'C': [1, 10, 100, 1000],
                              'gamma': [1e-3, 1e-2, 1e-1, 1.0]}],
                            'Support Vector Machine (RBF Kernel)'))
                    algorithms.append(
                        Algorithm(
                            RandomForestRegressor(
                                random_state=self.random_state,
                                n_jobs=self.n_jobs),
                            [{'n_estimators': [10, 100, 1000],
                              'max_features': [0.3, 0.6, 0.9],
                              'max_depth': [3, 7, None]}],
                            'Random Forest'))
                algorithms.append(
                    Algorithm(
                        Ridge(),
                        [{'alpha':
                            [0.01, 0.1, 1, 10, 100]}],
                        'Ridge Regression'))
                algorithms.append(
                    Algorithm(
                        DecisionTreeRegressor(random_state=self.random_state),
                        [{'max_depth': [3, 5, 7, 9, 11]}],
                        'Decision Tree'))
            else:
                algorithms.append(
                    Algorithm(
                        SGDRegressor(
                            random_state=self.random_state),
                        [{'penalty': ['l2', 'l1'],
                          'alpha': [1e-05, 3e-05, 1e-04, 3e-04, 1e-03]}],
                        'SGD Regressor'))
        return algorithms

    def add_algorithm(self, estimator, param_grid, name):
        """
        Add arbitrary scikit-learn-compatible algorithm.

        Parameters
        ----------
        estimator : object type that implements the “fit” and “predict” methods
            A object of that type is instantiated for each grid point.
        param_grid : dict or list of dictionaries
            Dictionary with parameters names (string) as keys and
            lists of parameter settings to try as values, or a list of
            such dictionaries, in which case the grids spanned by
            each dictionary in the list are explored.
            This enables searching over any sequence of parameter settings.
        name : string
            Algorithm name (used for report)
        """
        self.algorithms.append(Algorithm(estimator, param_grid, name))

    def remove_algorithm(self, index=-1):
        """
        Remove algorithm

        Parameters
        ----------
        index : int (default=-1)
            Remove an algorithm from list by index.
            By default, last algorithm is removed.
        """
        del self.algorithms[index]

    def get_algorithms(self):
        """
        Get algorithm names and grid parameters.

        Returns
        -------
        algorithms : list
            List of tupples(name, grid_params).
        """
        rtn = []
        for algorithm in self.algorithms:
            rtn.append((algorithm.name, algorithm.parameters))
        return rtn

    def fit(self, X, y, dname=None, algorithm_selection_only=False):
        """
        Tune parameters and search best algorithm

        Parameters
        ----------
        X : {numpy.ndarray, pandas.DataFrame}, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : {numpy.ndarray, pandas.Series}, shape = [n_samples]
            Target values (class labels in classification, real numbers in
            regression)
        dname : string (default=None)
            If not None, make a analysis report in this directory.
        algorithm_selection_only : boolean, optional (default=False)
            If True, only algorithm selection is executed.
            This option is needed for (get|add|remove)_algorithm(s) methods.

        Returns
        -------
        self : object
            Returns self.
        """
        self.data = Data(self.shuffle, self.standardize, self.random_state)
        self.data.fit_transform(X, y)

        if not self.is_ready:
            self.algorithms = self.__choose_algorithm()
        self.is_ready = True
        if algorithm_selection_only:
            return self

        if isinstance(self.cv, int):
            if self.task == 'classification':
                self.cv = StratifiedKFold(self.data.y, n_folds=self.cv,
                                          shuffle=self.shuffle,
                                          random_state=self.random_state)
            elif self.task == 'regression':
                self.cv = KFold(self.data.X.shape[0], n_folds=self.cv,
                                shuffle=self.shuffle,
                                random_state=self.random_state)

        self.__tune_parameters()
        if self.task == 'classification':
            self.__report_classification_result()

        if dname is not None:
            self.__make_report(dname)

        return self

    def predict(self, X):
        return self.algorithms[self.best_index].estimator.predict(
            self.data.transform(X))

    def __search_best_algorithm(self):
        self.best_score = float('-Inf')
        self.best_index = -1
        sign = 1.0
        if self.minimized_score:
            sign = -1.0
            self.best_score = float('Inf')
        for i in xrange(len(self.algorithms)):
            if sign * self.algorithms[i].best_score > sign * self.best_score:
                self.best_score = self.algorithms[i].best_score
                self.best_index = i
        self.algorithms[self.best_index].is_best_algorithm = True

    def __tune_parameters(self):
        for i in xrange(len(self.algorithms)):
            estimator = self.algorithms[i].estimator
            parameters = self.algorithms[i].parameters
            sc = f1score if self.scoring == 'f1' else self.scoring
            clf = GridSearchCV(
                estimator, parameters, cv=self.cv, scoring=sc,
                n_jobs=self.n_jobs)
            clf.fit(self.data.X, self.data.y)
            if self.minimized_score:
                clf.best_score_ *= -1.0
                for j in xrange(len(clf.grid_scores_)):
                    clf.grid_scores_[j] = (clf.grid_scores_[j][0],
                                           -1.0 * clf.grid_scores_[j][1],
                                           -1.0 * clf.grid_scores_[j][2])
            self.algorithms[i].estimator = clf.best_estimator_
            self.algorithms[i].best_score = clf.best_score_
            self.algorithms[i].best_params = clf.best_params_
            self.algorithms[i].grid_scores = clf.grid_scores_

        self.__search_best_algorithm()

    def __report_classification_result(self):
        for i in xrange(len(self.algorithms)):
            est = self.algorithms[i].estimator
            self.algorithms[i].classification_report =\
                classification_report(self.data.y, est.predict(self.data.X))

    def __plot_learning_curve(self, dname=None):
        for alg in self.algorithms:
            estimator = alg.estimator
            sc = f1score if self.scoring == 'f1' else self.scoring
            train_sizes, train_scores, test_scores = learning_curve(
                estimator,
                self.data.X,
                self.data.y,
                cv=self.cv,
                scoring=sc,
                n_jobs=self.n_jobs)
            if self.minimized_score:
                train_scores *= -1.0
                test_scores *= -1.0
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
                             test_scores_mean + test_scores_std,
                             alpha=0.1, color="g")
            plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
                     label="Training score")
            plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
                     label="Cross-validation score")
            if self.minimized_score:
                plt.legend(loc='upper right')
            else:
                plt.legend(loc="lower right")
            if dname is not None and not os.path.exists(dname):
                os.mkdir(dname)
            if dname is not None:
                plt.savefig('%s/learning_curve_%s.png' %
                            (dname, estimator.__class__.__name__),
                            bbox_inches='tight', dpi=75)
            else:
                plt.savefig('learning_curve_%s.png' %
                            estimator.__class__.__name__,
                            bbox_inches='tight', dpi=75)
            plt.close()

    def __make_report(self, dname='report'):
        if not os.path.exists(dname):
            os.mkdir(dname)

        self.__plot_learning_curve(dname)

        env = Environment(
            loader=FileSystemLoader(
                os.path.abspath(
                    os.path.dirname(__file__)) + '/template', encoding='utf8'))
        if self.lang == 'jp':
            tmpl = env.get_template('report_jp.html.tmp')
        else:
            tmpl = env.get_template('report.html.tmp')

        scoring_name = self.scoring if isinstance(self.scoring, str) else\
            self.scoring.func_name
        html = tmpl.render(algorithms=self.algorithms,
                           scoring=scoring_name,
                           task=self.task,
                           data=self.data,
                           verbose=self.verbose).encode('utf-8')
        fo = open(dname + '/report.html', 'w')
        fo.write(html)
        fo.close()

    def make_sample_code(self, fname='sample_code.py'):
        """
        Make a sample code

        Parameters
        ----------
        fname : string (default="sample_code.py")
            A string containing a path to a output file.
        """

        env = Environment(
            loader=FileSystemLoader(
                os.path.abspath(
                    os.path.dirname(__file__)) + '/template', encoding='utf8'))
        tmpl = env.get_template('sample_code.py.tmp')
        encoded = True if len(self.data.del_columns) > 0 else False
        html = tmpl.render(algorithm=self.algorithms[self.best_index],
                           encoded=encoded,
                           standardize=self.standardize).encode('utf-8')
        fo = open(fname, 'w')
        fo.write(html)
        fo.close()


def f1score(estimator, X, y):
    return f1_score(y, estimator.predict(X), average=None).mean()


if __name__ == "__main__":
    pass
