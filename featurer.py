from tokenizer import Tokenizer
#from corpus import Corpus
from math import log10
from operator import itemgetter
import docopt

class Featurer():
    """
    :Featurer:

    Extracts feature vectors from a corpus. Feature type can specified in the
    arguments (see under Options). Since the features are intended to be used
    by a Perceptron, we always add the additional feature "THETA" (value is 1).

    :Expected input:
        - corpus -- an instance of class Corpus
        - feature type -- type of features to be extracted
        - stopwords_perc -- (optional) how strict to be with stopwords, must be
        0 ≤ k ≤ corpus size. Default value is 10, which means that terms with a
        document frequency ≥ (corpus size / 10) are considered stopwords.

    :Output:
    Directly fed back into the corpus and tweets:
        - corpus.get_all_features() -- list of all feature labels in corpus
        - tweet.get_features() -- dict of features and values for each tweet

    :Usage:
        features = Featurer(corpus, feature_type, stopwords_perc)

    :Options:
        feature_types:
            -- binary
            -- count
            -- frequency
            -- tf-idf
            -- n-gram
    """

    def __init__(self, corp=None, type=None, stopwords_perc=10):

        self._types = ['binary', 'count', 'frequency', 'tf-idf', 'n-gram']

        """
        Greacefully exit if parameters are invalid
        """
        #if type not in self._types or not corp or not isinstance(corp, Corpus):
        if type not in self._types or not corp:
            raise ValueError('\nMissing or invalid 2 positional arguments:'
                '\'corpus\' and \'feature_type\'\n{}'.format(self.__doc__))

        self._corpus = corp                 # iterable collection of tweets
        self._size = 0                      # corpus size = nr of tweets
        self._term_idfs = {}                # dict with term-idf-score pairs
        self._stopwords = []                # terms with highest df-score
        self._threshold = stopwords_perc    # how strict to be with stopwords
        self._main()                        # start the fun


    def _main(self):
        """
        Main routine the performs some basic calculations before feature vectors
        are extracted:
        (1) counts collection size,
        (2) extracts list of all terms from colection (a.k.a. "feature names"),
        (3) sorts these terms according to df,
        (4) generates stopwords, i.e. words with highest df (by default this is
            df >= collection size / 10).
        """
        self._extract_idf()  # gets us size, terms, idf scores and stopwords


    def _extract_idf(self):
        """
        Extracts terms from corpus and adds them to self.__term_idfs. Calculates
        df score (=document frequency, i.e. number of tweets in which the term
        occurs). Words with highest df are dealt with as stopwords. Finally df's
        are converted to idf's (=inverted df, i.e. documents with low df get a
        higher score).
        """

        # Count corpus size, extract terms and count df for each term
        term_dfs = {}
        for tweet in self._corpus:
            self._size += 1
            terms = Tokenizer().get_terms(tweet.get_text())
            for term in terms:
                if term not in term_dfs:
                    term_dfs[term] = 1
                else:
                    term_dfs[term] += 1

        # Remove stopwords
        if (self._threshold != 0):
            threshold = self._size / self._threshold
            sorted_dfs = sorted(term_dfs.items(), key=itemgetter(1), reverse=True)
            for term_df in sorted_dfs:
                if term_df[1] < threshold:
                    break
                else:
                    self._stopwords.append(term_df[0])
                    del term_dfs[term_df[0]]

        #  Convert df's into idf's (inverted df)
        for term in term_dfs.keys():
            self._term_idfs[term] = log10(self._size / term_dfs[term])

        # Add the Theta as an additional element in the vectors
        self._term_idfs['THETA'] = 1

        # Add list of features to corpus
        self._corpus.set_all_feature_names(self._term_idfs.keys())


    def set_features(self):
        """
        Calculate features (a vector of tf-idf scores) for each tweet and send
        to its corresponding Tweet object.
        """
        for tweet in self._corpus:
            features = self._extract_tf_idf(tweet)
            tweet.set_features(features)


    def _extract_tf_idf(self, tweet):
        """
        For each term in tweet calculate tf, normalized by tweet size.
        Calculate tf-idf scores using pre-calculated idf-scores.
        """
        # Get count of each term in tweet
        term_tfs = {}
        tokens = Tokenizer().get_tokens(tweet.get_text())
        for token in tokens:
            if token in self._term_idfs.keys():
                if token in term_tfs:
                    term_tfs[token] += 1
                else:
                    term_tfs[token] = 1
        # Normalize by total number of tokens in tweet
        for term in term_tfs:
            term_tfs[term] /= len(tokens)
        # Calculate tf-idf scores by mutltiplying tf and idf
        tf_idfs = {}
        for term in term_tfs:
            tf_idfs[term] = term_tfs[term] * self._term_idfs[term]
        # Add Theta as an additional element in the vector
        # (Yes, this needs to be added in both idf and tf-idf dicts!)
        tf_idfs['THETA'] = 1

        return tf_idfs
