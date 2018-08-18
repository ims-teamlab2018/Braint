"""
Models are partially based on code provided by Jeremy Barnes (https://github.com/jbarnesspain/sota_sentiment).
"""

from keras.models import Sequential, Model
from keras.layers import LSTM, Dropout, Dense, Embedding, Bidirectional, Conv1D, MaxPooling1D, Flatten, Input, SpatialDropout1D, Concatenate

import sys

sys.path.append('../')

from utils.attention import Attention

class LSTM_Model(object):
    def __init__(self, vocab_size, embedding_dim, output_dim, weights=None, params=None):
        self.input_dim = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_dim = self.embedding_dim
        self.output_dim = output_dim
        self.weights = weights
        self.parse_params(params)
        self.model = self.create_LSTM()

    def parse_params(self, params=None):
        if 'attention' in params:
            self.attention = params['attention']
        else:
            self.attention = False
        if 'max_len' in params:
            self.max_sequence_len = params['max_len']
        else:
            self.max_sequence_len = None
        if 'dropout' in params:
            self.dropout = params['dropout']
        else:
            self.dropout = .5
        if 'trainable_embeddings' in params:
            self.trainable = params['trainable_embeddings']
        else:
            self.trainable = True
        if 'optimizer' in params:
            self.optimizer = params['optimizer']
        else:
            self.optimizer = 'adam'
        if 'loss' in params:
            self.loss = params['loss']
        else:
            self.loss = 'categorical_crossentropy'

    def create_LSTM(self):
        if self.attention:
            # Define the model
            inp = Input(shape=(self.max_sequence_len,))
            if self.weights is not None:
                emb = Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        weights=[self.weights],
                        input_length=self.max_sequence_len,
                        trainable=True)(inp)
            else:
                emb = Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        input_length=self.max_sequence_len,
                        trainable=True)(inp)
            x = SpatialDropout1D(self.dropout)(emb)
            x = LSTM(self.lstm_dim, return_sequences=True)(x)
            x, attention = Attention()(x)
            x = SpatialDropout1D(self.dropout)(x)
            x = Dense(self.output_dim, activation="sigmoid")(x)
            model = Model(inputs=inp, outputs=x)
            model.compile(loss=self.loss,
              optimizer=self.optimizer,
              metrics=['accuracy'])
            self.attention_model = Model(inputs=inp, outputs=attention)
            return model
        else:
            model = Sequential()
            if self.weights is not None:
                model.add(Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        weights=[self.weights],
                        input_length=self.max_sequence_len,
                        trainable=True))
            else:
                model.add(Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        input_length=self.max_sequence_len,
                        trainable=True))
            model.add(Dropout(self.dropout))
            model.add(LSTM(self.lstm_dim))
            model.add(Dropout(self.dropout))
            model.add(Dense(self.output_dim, activation='softmax'))
            model.compile(optimizer=self.optimizer, loss=self.loss,
                  metrics=['accuracy'])
            return model

class BiLSTM_Model(object):

    def __init__(self, vocab_size, embedding_dim, output_dim, weights=None, params=None):
        self.input_dim = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_dim = self.embedding_dim
        self.output_dim = output_dim
        self.weights = weights
        self.parse_params(params)
        self.model = self.create_BiLSTM()

    def parse_params(self, params=None):
        if 'attention' in params:
            self.attention = params['attention']
        else:
            self.attention = False
        if 'max_len' in params:
            self.max_sequence_len = params['max_len']
        else:
            self.max_sequence_len = None
        if 'dropout' in params:
            self.dropout = params['dropout']
        else:
            self.dropout = .5
        if 'trainable_embeddings' in params:
            self.trainable = params['trainable_embeddings']
        else:
            self.trainable = True
        if 'optimizer' in params:
            self.optimizer = params['optimizer']
        else:
            self.optimizer = 'adam'
        if 'loss' in params:
            self.loss = params['loss']
        else:
            self.loss = 'categorical_crossentropy'

    def create_BiLSTM(self):
        if self.attention:
            inp = Input(shape=(self.max_sequence_len,))
            if self.weights is not None:
                emb = Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        weights=[self.weights],
                        input_length=self.max_sequence_len,
                        trainable=True)(inp)
            else:
                emb = Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        input_length=self.max_sequence_len,
                        trainable=True)(inp)
            x = SpatialDropout1D(self.dropout)(emb)
            x = Bidirectional(LSTM(self.lstm_dim, return_sequences=True))(x)
            x, attention = Attention()(x)
            x = SpatialDropout1D(self.dropout)(x)
            x = Dense(self.output_dim, activation="sigmoid")(x)
            model = Model(inputs=inp, outputs=x)
            model.compile(loss=self.loss,
              optimizer=self.optimizer,
              metrics=['accuracy'])
            self.attention_model = Model(inputs=inp, outputs=attention)
            return model
        else:
            model = Sequential()
            if self.weights is not None:
                model.add(Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        weights=[self.weights],
                        input_length=self.max_sequence_len,
                        trainable=True))
            else:
                model.add(Embedding(self.input_dim + 1,
                        self.embedding_dim,
                        input_length=self.max_sequence_len,
                        trainable=True))
            model.add(Dropout(self.dropout))
            model.add(Bidirectional(LSTM(self.lstm_dim)))
            model.add(Dropout(self.dropout))
            model.add(Dense(self.output_dim, activation='softmax'))
            model.compile(optimizer=self.optimizer, loss=self.loss,
                  metrics=['accuracy'])
            return model

class CNN_Model(object):

    def __init__(self, vocab_size, embedding_dim, output_dim, weights=None, params=None):
        self.input_dim = vocab_size
        self.embedding_dim = embedding_dim
        self.weights = weights
        self.dim = embedding_dim
        self.output_dim = output_dim
        self.parse_params(params)
        self.model = self.create_cnn()

    def parse_params(self, params=None):
        if 'filter_sizes' in params:
            self.filter_sizes = params['filter_sizes']
        else:
            self.filter_sizes = (2,3,4)
        if 'num_filters' in params:
            self.num_filters = params['num_filters']
        else:
            self.num_filters = 3
        if 'attention' in params:
            self.attention = params['attention']
        else:
            self.attention = False
        if 'max_len' in params:
            self.max_sequence_len = params['max_len']
        else:
            self.max_sequence_len = 60
        if 'dropout' in params:
            self.dropout = params['dropout']
        else:
            self.dropout = .5
        if 'trainable_embeddings' in params:
            self.trainable = params['trainable_embeddings']
        else:
            self.trainable = True
        if 'optimizer' in params:
            self.optimizer = params['optimizer']
        else:
            self.optimizer = 'adam'
        if 'loss' in params:
            self.loss = params['loss']
        else:
            self.loss = 'categorical_crossentropy'
           
    def create_cnn(self):
        # Convolutional model
        graph_in = Input(shape=(self.max_sequence_len, self.embedding_dim))
        convs = []
        for fsz in self.filter_sizes:
            conv = Conv1D(filters=self.num_filters,
                    kernel_size=fsz,
                    padding='valid',
                    activation='relu',
                    strides=1)(graph_in)
            pool = MaxPooling1D(pool_size=2)(conv)
            flatten = Flatten()(pool)
            convs.append(flatten)
    
        #out = Merge(mode='concat')(convs)
        out = Concatenate()(convs)
        graph = Model(inputs=graph_in, outputs=out)

        # Full model
        model = Sequential()
        if self.weights is not None:
            model.add(Embedding(self.input_dim + 1,
                            self.embedding_dim,
                            weights=[self.weights],
                            input_length=self.max_sequence_len,
                            trainable=True))
        else:
            model.add(Embedding(self.input_dim + 1,
                            self.embedding_dim,
                            input_length=self.max_sequence_len,
                            trainable=True))
        model.add(Dropout(self.dropout))
        model.add(graph)
        model.add(Dense(self.dim, activation='relu'))
        model.add(Dropout(self.dropout))
        model.add(Dense(self.output_dim, activation='softmax'))

        model.compile(optimizer=self.optimizer, loss=self.loss,
                    metrics=['accuracy'])
        return model