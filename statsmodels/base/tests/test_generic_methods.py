# -*- coding: utf-8 -*-
"""Tests that use cross-checks for generic methods

Should be easy to check consistency across models
Does not cover tsa

Initial cases copied from test_shrink_pickle

Created on Wed Oct 30 14:01:27 2013

Author: Josef Perktold
"""

import pickle
import numpy as np
import statsmodels.api as sm

from numpy.testing import assert_, assert_allclose
from numpy.testing.decorators import knownfailureif

from nose import SkipTest
import platform


iswin = platform.system() == 'Windows'
npversionless15 = np.__version__ < '1.5'
winoldnp = iswin & npversionless15



class CheckGenericMixin(object):

    def __init__(self):
        self.predict_kwds = {}

    @classmethod
    def setup_class(self):

        nobs = 500
        np.random.seed(987689)
        x = np.random.randn(nobs, 3)
        x = sm.add_constant(x)
        self.exog = x
        self.xf = 0.25 * np.ones((2, 4))

    def test_ttest_tvalues(self):
        # test that t_test has same results a params, bse, tvalues, ...
        res = self.results
        mat = np.eye(len(res.params))
        tt = res.t_test(mat)

        assert_allclose(tt.effect, res.params, rtol=1e-12)
        assert_allclose(tt.sd, res.bse, rtol=1e-10)
        assert_allclose(tt.tvalue, res.tvalues, rtol=1e-12)
        assert_allclose(tt.pvalue, res.pvalues, rtol=5e-10)
        assert_allclose(tt.conf_int(), res.conf_int(), rtol=1e-10)

        # test params table frame returned by t_test
        table_res = np.column_stack((res.params, res.bse, res.tvalues,
                                    res.pvalues, res.conf_int()))
        table1 = np.column_stack((tt.effect, tt.sd, tt.tvalue, tt.pvalue,
                                 tt.conf_int()))
        table2 = tt.summary_frame().values
        assert_allclose(table2, table_res, rtol=1e-12)

        # move this to test_attributes ?
        assert_(hasattr(res, 'use_t'))


    def test_ftest_pvalues(self):
        res = self.results
        use_t = res.use_t
        k_vars = len(res.params)
        # check default use_t
        pvals = [res.wald_test(np.eye(k_vars)[k], use_f=use_t).pvalue
                                                   for k in range(k_vars)]
        assert_allclose(pvals, res.pvalues, rtol=5e-10)

        # sutomatic use_f based on results class use_t
        pvals = [res.wald_test(np.eye(k_vars)[k]).pvalue
                                                   for k in range(k_vars)]
        assert_allclose(pvals, res.pvalues, rtol=5e-10)



    # TODO The following is not (yet) guaranteed across models
    #@knownfailureif(True)
    def test_fitted(self):
        # ignore wrapper for isinstance check
        from statsmodels.genmod.generalized_linear_model import GLMResults
        from statsmodels.discrete.discrete_model import DiscreteResults
        results = self.results._results
        if (isinstance(results, GLMResults) or
            isinstance(results, DiscreteResults)):
            raise SkipTest

        res = self.results
        fitted = res.fittedvalues
        assert_allclose(res.model.endog - fitted, res.resid, rtol=1e-12)
        assert_allclose(fitted, res.predict(), rtol=1e-12)


#########  subclasses for individual models, unchanged from test_shrink_pickle
# TODO: check if setup_class is faster than setup

class TestGenericOLS(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        x = self.exog
        np.random.seed(987689)
        y = x.sum(1) + np.random.randn(x.shape[0])
        self.results = sm.OLS(y, self.exog).fit()


class TestGenericWLS(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        x = self.exog
        np.random.seed(987689)
        y = x.sum(1) + np.random.randn(x.shape[0])
        self.results = sm.WLS(y, self.exog, weights=np.ones(len(y))).fit()


class TestGenericPoisson(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        x = self.exog
        np.random.seed(987689)
        y_count = np.random.poisson(np.exp(x.sum(1) - x.mean()))
        model = sm.Poisson(y_count, x)  #, exposure=np.ones(nobs), offset=np.zeros(nobs)) #bug with default
        # use start_params to converge faster
        start_params = np.array([0.75334818, 0.99425553, 1.00494724, 1.00247112])
        self.results = model.fit(start_params=start_params, method='bfgs',
                                 disp=0)

        #TODO: temporary, fixed in master
        self.predict_kwds = dict(exposure=1, offset=0)

class TestGenericNegativeBinomial(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        np.random.seed(987689)
        data = sm.datasets.randhie.load()
        exog = sm.add_constant(data.exog, prepend=False)
        mod = sm.NegativeBinomial(data.endog, data.exog)
        self.results = mod.fit(disp=0)

class TestGenericLogit(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        x = self.exog
        nobs = x.shape[0]
        np.random.seed(987689)
        y_bin = (np.random.rand(nobs) < 1.0 / (1 + np.exp(x.sum(1) - x.mean()))).astype(int)
        model = sm.Logit(y_bin, x)  #, exposure=np.ones(nobs), offset=np.zeros(nobs)) #bug with default
        # use start_params to converge faster
        start_params = np.array([-0.73403806, -1.00901514, -0.97754543, -0.95648212])
        self.results = model.fit(start_params=start_params, method='bfgs', disp=0)


class TestGenericRLM(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        x = self.exog
        np.random.seed(987689)
        y = x.sum(1) + np.random.randn(x.shape[0])
        self.results = sm.RLM(y, self.exog).fit()


class TestGenericGLM(CheckGenericMixin):

    def setup(self):
        #fit for each test, because results will be changed by test
        x = self.exog
        np.random.seed(987689)
        y = x.sum(1) + np.random.randn(x.shape[0])
        self.results = sm.GLM(y, self.exog).fit()

if __name__ == '__main__':
    pass
