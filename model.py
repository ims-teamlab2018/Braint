import pickle
import numpy as np
from keras.models import load_model, model_from_json
from keras.callbacks import ModelCheckpoint
from keras.preprocessing.sequence import pad_sequences

from utils.WordVecs import *

from architectures import LSTM_Model , BiLSTM_Model #, CNN
from corpus import Corpus
from tokenizer import Tokenizer

class Model(object):

    def __init__(self):
        self.__tokenizer = Tokenizer()

    def __tweet2idx(self, tweet, w2idx):
        return np.array([w2idx[token] if token in w2idx else w2idx['<UNK>'] for token in tweet])

    def __convert_format(self, corpus, classes, w2idx, max_len):
        dataset = []
        for tweet in corpus:
            dataset.append((tweet.get_text(), tweet.get_gold_label()))
        x_data, y_data = zip(*dataset)

        x_data = [self.__tokenizer.get_only_tokens(tweet) for tweet in x_data]
        y_data = [classes[label] for label in y_data]

        # class to one hot vector
        y_data = [np.eye(len(classes))[label] for label in y_data]
        # to np array
        x_data = np.array([self.__tweet2idx(tweet, w2idx) for tweet in x_data])
        y_data = np.array(y_data)
        # padding
        x_data = pad_sequences(x_data, max_len)
        return x_data, y_data

    def __create_vocab(self, corpus):
        vocab = {}
        for tweet in corpus:
            for token in self.__tokenizer.get_only_tokens(tweet.get_text()):
                if token in vocab:
                    vocab[token] += 1
                else:
                    vocab[token] = 1
        # add <unk> token to map unseen words to, use high nuber so that it does not get filtered out by min_count
        vocab['<UNK>'] = 100
        return vocab

    def __get_word_embeddings(self, vecs, vocab, min_count):
        # vecs : self.vocab_length, self.vector_size, self._matrix, self._w2idx, self._idx2w
        dim = vecs.vector_size
        embeddings = {}
        for word in vecs._w2idx.keys():
            embeddings[word] = vecs[word]
        # add random embeddings for words that occur in training data but not in the pretrained w2v embeddings
        for word in vocab:
            if word not in embeddings and vocab[word] >= min_count:
                embeddings[word] = np.random.uniform(-0.25, 0.25, dim)

        vocab_size = len(embeddings)
        word_idx_map = dict()
        W = np.zeros(shape=(vocab_size+1, dim), dtype='float32')
        W[0] = np.zeros(dim, dtype='float32')
        i = 1
        for word in embeddings:
            W[i] = embeddings[word]
            word_idx_map[word] = i
            i += 1  
        return embeddings, W, word_idx_map    
    
    def train(self, train_corpus, classes, architecture, params, num_epochs, max_len, embedding_file, file_type, min_count, save_dir, dev_corpus=None):
        params['max_len'] = max_len
        print('Creating vocab...')
        vocab = self.__create_vocab(train_corpus)
        print('vocab finished')
        # create wordvecs and W
        print('Loading embeddings...')

        # filter embedding file with vocab
        vecs = WordVecs(embedding_file, file_type, vocab)


        print('finished loading')
        print('Creating wordvecs, W and w2idx map...')
        embeddings, W, word_idx_map = self.__get_word_embeddings(vecs, vocab, min_count)
        print('wordvecs, W, w2idx map finished')
        # convert train corpus to xtrain, ytrain
        print('Converting train corpus...')
        x_train, y_train = self.__convert_format(train_corpus, classes, word_idx_map, max_len)
        # convert dev corpus to xdev, ydev
        if dev_corpus:
            print('Converting dev corpus...')
            x_dev, y_dev = self.__convert_format(dev_corpus, classes, word_idx_map, max_len)
        print('converting finished')

        # create nn
        output_dim = len(classes)
        vocab_size = len(embeddings)
        embedding_dim = vecs.vector_size
        print('Creating nn...')
        if architecture == 'LSTM':
            nn = LSTM_Model(vocab_size, embedding_dim, output_dim, W, params)
        elif architecture == 'BiLSTM':
            nn = BiLSTM_Model(vocab_size, embedding_dim, output_dim, W, params)
        elif architecture == 'CNN':
            nn = CNN_Model(vocab_size, embedding_dim, output_dim, W, params)
        else:
            return
        print('nn finished')
        
        #checkpointing
        filepath = save_dir + "weights-improvement-{epoch:02d}-{val_acc:.2f}.hdf5"
        checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True, mode='auto')
        # train
        if dev_corpus:
            hist = nn.model.fit(x_train, y_train, validation_data=[x_dev, y_dev], epochs=num_epochs, verbose=1, callbacks=[checkpoint])
        else:
            hist = nn.model.fit(x_train, y_train, validation_split=0.1, epochs=num_epochs, verbose=1, callbacks=[checkpoint])
        print(hist.history)

        print('Finished training ' + architecture)
        
        # serialize model architecture to JSON
        model_json = nn.model.to_json()
        with open(save_dir + "model.json", "w") as json_file:
            json_file.write(model_json)
        # serialize vocab, word to id mapping, max_len and classes
        pickle.dump(vocab, open(save_dir + "vocab.p", "wb"))
        pickle.dump(max_len, open(save_dir + "max_sequence_len.p", "wb"))
        pickle.dump(word_idx_map, open(save_dir + "word_idx_map.p", "wb"))
        pickle.dump(classes, open(save_dir + "classes.p", "wb" ))

    def test(self, save_dir, path_weights, test_corpus):   
        classes = pickle.load(open(save_dir + "classes.p", "rb"))
        inv_classes = {v: k for k, v in classes.items()}
        max_len = pickle.load(open(save_dir + "max_sequence_len.p", "rb"))
        word_idx_map = pickle.load(open(save_dir + "word_idx_map.p", "rb"))
        inv_word_idx_map = {v: k for k, v in word_idx_map.items()}
        # convert test data into input format
        x_test, y_test = self.__convert_format(test_corpus, classes, word_idx_map, max_len)
        # load model architecture
        json_file = open(save_dir + 'model.json', 'r')
        loaded_model = json_file.read()
        json_file.close()
        model = model_from_json(loaded_model)
        # load weights
        model.load_weights(path_weights)
        print("Loaded model from disk")
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

        # evaluate model & print accuracy
        score = model.evaluate(x_test, y_test, verbose=0)
        print("%s: %.2f%%" % (model.metrics_names[1], score[1]*100))

        # get predictions
        predictions = model.predict_classes(x_test, verbose=1)

        # write predictions to file
        with open(save_dir + 'predictions.csv', 'w') as out:
            for tweet, prediction in zip(x_test, predictions):
                tokens = [inv_word_idx_map[idx] if idx in inv_word_idx_map else '' for idx in tweet]
                text = " ".join(tokens)
                label = inv_classes[prediction]
                out.write(label + '\t' + text + '\n')
                     
        # write predictions in tweets of test corpus
        # order of predictions should be the same as oder of tweets in test_corpus
        for i in range(len(predictions)):
            test_corpus.get_ith(i).set_pred_label(inv_classes[predictions[i]])

        return test_corpus


""" 
# code to get attention weights for each input word
# code taken from:
# https://srome.github.io/Understanding-Attention-in-Neural-Networks-Mathematically/
# TODO: adapt so that it works with this model

def get_word_importances(text):
    lt = tokenizer.texts_to_sequences([text])
    x = pad_sequences(lt, maxlen=maxlen)
    p = model.predict(x)
    att = attention_model.predict(x)
    return p, [(reverse_token_map.get(word), importance) for word, importance in zip(x[0], att[0]) if word in reverse_token_map]
"""
        