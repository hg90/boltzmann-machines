import numpy as np
import tensorflow as tf


class BaseLayer(object):
    """Helper class that encapsulates one layer of stochastic units in RBM/DBM."""
    def __init__(self, n_units, tf_dtype=tf.float32):
        self.n_units = n_units
        self.tf_dtype = tf_dtype

    def init(self, random_seed=None):
        """Randomly initialize states according to their distribution."""
        raise NotImplementedError

    def activation(self, x, b):
        """Compute activation of states according to the distribution.

        Parameters
        ----------
        x - total input received (incl. bias)
        b - bias
        """
        raise NotImplementedError

    def make_rand(self, batch_size, rng):
        """Generate random data that will be passed to feed_dict."""
        pass

    def sample(self, rand_data, means):
        """Sample states of the units by combining output from 2 previous functions."""
        pass


class BernoulliLayer(BaseLayer):
    def __init__(self, **kwargs):
        super(BernoulliLayer, self).__init__(**kwargs)

    def init(self, random_seed=None):
        return tf.random_uniform((self.n_units,), minval=0., maxval=1.,
                                 dtype=self.tf_dtype, seed=random_seed, name='bernoulli_init')

    def activation(self, x, b):
        return tf.nn.sigmoid(x)

    def make_rand(self, batch_size, rng):
        return rng.rand(batch_size, self.n_units)

    def sample(self, rand_data, means):
        return tf.cast(tf.less(rand_data, means), dtype=self.tf_dtype)


class MultinomialLayer(BaseLayer):
    def __init__(self, **kwargs):
        super(MultinomialLayer, self).__init__(**kwargs)

    def init(self, random_seed=None):
        t = tf.random_uniform((self.n_units,), minval=0., maxval=1.,
                              dtype=self.tf_dtype, seed=random_seed)
        t /= tf.reduce_sum(t)
        return tf.identity(t, name='multinomial_init')

    def activation(self, x, b):
        return tf.nn.softmax(x)

    def make_rand(self, batch_size, rng):
        return rng.rand(batch_size, 1)

    def sample(self, rand_data, means):
        cumprobs = tf.cumsum(means, axis=-1)
        t = tf.to_int32(tf.greater_equal(cumprobs, rand_data))
        ind = tf.to_int32(tf.argmax(t, axis=-1))
        r = tf.to_int32(tf.range(tf.shape(ind)[0]))
        samples = tf.scatter_nd(tf.transpose([r, ind]),
                                tf.ones_like(r),
                                tf.to_int32(tf.shape(cumprobs)))
        return tf.cast(samples, dtype=self.tf_dtype)


class GaussianLayer(BaseLayer):
    def __init__(self, sigma, **kwargs):
        super(GaussianLayer, self).__init__(**kwargs)
        self.sigma = np.asarray(sigma)

    def init(self, random_seed=None):
        t = tf.random_normal((self.n_units,), dtype=self.tf_dtype, seed=random_seed)
        t = tf.multiply(t, self.sigma, name='gaussian_init')
        return t

    def activation(self, x, b):
        t = x * self.sigma + b * (1. - self.sigma)
        return t

    def make_rand(self, batch_size, rng):
        return rng.randn(batch_size, self.n_units)
