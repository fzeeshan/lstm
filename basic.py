#!/usr/bin/env python

import math
import numpy as np
import tensorflow as tf
from model import Model
from tensorflow.contrib.rnn import BasicLSTMCell
from tensorflow.contrib.rnn import MultiRNNCell
from tensorflow.contrib.layers import fully_connected # noqa

# lstm_units = 10
lstm_units = 1
lstm_cells = 1
lstm_timesteps = 100


class SinGen(object):
    def __init__(self, start=0.0, step=0.01, batchsize=10):
        self.start = start
        self.step = step
        self.batchsize = batchsize
        self.x = start

    def batch(self):
        '''
        batch

        Produce input and labels array shape (batchsize, 1)
        (for feeding into input tensor shape (None, batchsize, 1))
        '''
        xs = []
        for _ in range(self.batchsize):
            xs.append(self.x)
            self.x += self.step
        ys = [math.sin(x) for x in xs]
        outs = (self.batchsize, 1)
        return np.array(xs).reshape(outs), np.array(ys).reshape(outs)


class TSModel(Model):
    '''Basic timeseries tensorflow lstm model'''

    def __init__(self, timesteps, inputs=None):
        super().__init__()

        sn = self.name
        # If no input then build a placeholder expecing feed_dict
        if inputs is None:
            with tf.variable_scope(sn('input')):
                self.add(tf.placeholder(tf.float32, (None, timesteps, 1)))
        else:
            self.output = inputs

        with tf.variable_scope(sn('lstml_1')):
            cells = [BasicLSTMCell(num_units=lstm_units) for _ in range(lstm_cells)]
            multi_cell = MultiRNNCell(cells=cells)
            # What to do with state?
            outputs, state = tf.nn.dynamic_rnn(cell=multi_cell, inputs=self.output, time_major=False,
                                               dtype=tf.float32)
            self.add(outputs)

        # with tf.variable_scope(sn('linear_out')):
        #     self.add(fully_connected(inputs=self.output, num_outputs=1))


def main(_):
    m = TSModel(timesteps=lstm_timesteps)
    print(m)

    labels = tf.placeholder(tf.float32, [None, lstm_timesteps, 1], name='labels')
    loss = tf.losses.mean_squared_error(m.output, labels)
    opt = tf.train.AdamOptimizer(learning_rate=1e-4)
    global_step = tf.contrib.framework.get_or_create_global_step()
    train_opt = opt.minimize(loss, global_step=global_step)

    hooks = [tf.train.StopAtStepHook(last_step=100000),
             tf.train.LoggingTensorHook(tensors={'step': global_step, 'loss': loss}, every_n_iter=1),
             ]

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.log_device_placement = True

    with tf.train.SingularMonitoredSession(hooks=hooks, config=config) as sess:
        g = SinGen(batchsize=lstm_timesteps)
        while not sess.should_stop():
            x, y = g.batch()
            x = x.reshape((1, ) + x.shape)
            y = y.reshape((1, ) + y.shape)
            res = sess.run([loss, train_opt], feed_dict={m.input: x, labels: y})
            print(res[0], res[1])


if __name__ == '__main__':
    tf.app.run()