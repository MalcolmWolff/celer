# Author: Mathurin Massias <mathurin.massias@gmail.com>
#         Alexandre Gramfort <alexandre.gramfort@inria.fr>
#         Joseph Salmon <joseph.salmon@telecom-paristech.fr>
# License: BSD 3 clause

import numpy as np

from scipy import sparse
from functools import partial
from sklearn.linear_model import LassoCV

from celer import celer_path


def build_dataset(n_samples=50, n_features=200, n_informative_features=10,
                  n_targets=1, sparse_X=False):
    """
    build an ill-posed linear regression problem with many noisy features and
    comparatively few samples
    """
    random_state = np.random.RandomState(0)
    if n_targets > 1:
        w = random_state.randn(n_features, n_targets)
    else:
        w = random_state.randn(n_features)
    w[n_informative_features:] = 0.0
    if sparse_X:
        X = sparse.random(n_samples, n_features, density=0.5, format='csc',
                          random_state=random_state)
        X_test = sparse.random(n_samples, n_features, density=0.5,
                               format='csc', random_state=random_state)
    else:
        X = random_state.randn(n_samples, n_features)
        X_test = random_state.randn(n_samples, n_features)
    y = X.dot(w)
    y_test = X_test.dot(w)
    return X, y, X_test, y_test


def test_celer_path_dense():
    """Test Lasso path computation on dense data."""
    X, y, _, _ = build_dataset(n_samples=50, n_features=50, n_targets=1)

    alpha_max = np.max(np.abs(X.T.dot(y)))
    n_alphas = 10
    alphas = alpha_max * np.logspace(0, -2, n_alphas)

    tol = 1e-6
    alphas, coefs, gaps, thetas = celer_path(X, y, alphas=alphas, tol=tol,
                                             return_thetas=True, verbose=False,
                                             verbose_inner=False)
    np.testing.assert_array_less(gaps, tol)


def test_celer_path_sparse():
    """Test Lasso path computation on sparse data."""
    X, y, _, _ = build_dataset(n_samples=50, n_features=50, n_targets=1,
                               sparse_X=True)
    alpha_max = np.max(np.abs(X.T.dot(y)))
    n_alphas = 10
    alphas = alpha_max * np.logspace(0, -2, n_alphas)

    tol = 1e-6
    alphas, coefs, gaps, thetas = celer_path(X, y, alphas=alphas, tol=tol,
                                             return_thetas=True, verbose=False,
                                             verbose_inner=False)
    np.testing.assert_array_less(gaps, tol)


def test_LassoCV_compatibility():
    """Test that our estimator is pluggable into sklearn's LassoCV."""
    X, y, _, _ = build_dataset(n_samples=50, n_features=50, n_targets=1)
    clf = LassoCV(eps=1e-2)
    clf.path = partial(celer_path, verbose=0, verbose_inner=0)
    clf.fit(X, y)

    clf2 = LassoCV(eps=1e-2)
    clf2.fit(X, y)

    np.testing.assert_allclose(clf.coef_, clf2.coef_)
