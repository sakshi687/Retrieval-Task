#!/usr/bin/env python
# coding: utf-8

# Removing Named Entities

# Importing Corpus From Directory

# In[1]:


import pandas as pd
import os, glob
folder = "C:\\Users\\ASUS\\AILA Practice\\casedocs_idf"
os.chdir(folder)
files = glob.glob("*.txt") # Makes a list of all files in folder
corpus = []
corpus_dict = {}
for file1 in files:
    with open (file1, 'r') as f:
        document = f.read() # Reads document content into a string
        corpus.append(document)
        corpus_dict[file1] = document


# In[2]:


new_corpus = corpus.copy()


# In[3]:


del corpus[0]


# Identify named entities using spaCy library and remove them from corpus

# In[4]:


def remove_multiple_strings(cur_string, replace_list):
  for cur_word in replace_list:
    cur_string = cur_string.replace(cur_word, '', 1)
  return cur_string.lower()

import spacy
nlp = spacy.load('en_core_web_md')

for doc in new_corpus:
    i = new_corpus.index(doc)
    processed_doc = nlp(doc)
    entities = []
    for ent in processed_doc.ents:
        entities.append(ent.text)
    new_corpus[i] = remove_multiple_strings(doc, entities)


# Split the corpus into tokens and remove puntuations and stop words using spaCy

# In[5]:


tokenized_corpus = []
for text in new_corpus:
    doc2 = nlp(text)
    tokens_in_one_corpus = []
    for token in doc2:
        if not token.is_punct | token.is_space | token.is_stop :
            tokens_in_one_corpus.append(token.orth_ )
    tokenized_corpus.append(tokens_in_one_corpus)


# ------GENSIM GITHUB CODE START------

# In[6]:


import logging
import math
from six import iteritems
from six.moves import range
from functools import partial
from multiprocessing import Pool

PARAM_K1 = 1.5
PARAM_B = 0.75
EPSILON = 0.25

logger = logging.getLogger(__name__)


class BM25(object):
    """Implementation of Best Matching 25 ranking function.
    Attributes
    ----------
    corpus_size : int
        Size of corpus (number of documents).
    avgdl : float
        Average length of document in `corpus`.
    doc_freqs : list of dicts of int
        Dictionary with terms frequencies for each document in `corpus`. Words used as keys and frequencies as values.
    idf : dict
        Dictionary with inversed documents frequencies for whole `corpus`. Words used as keys and frequencies as values.
    doc_len : list of int
        List of document lengths.
    """

    def __init__(self, corpus, k1=PARAM_K1, b=PARAM_B, epsilon=EPSILON):
        """
        Parameters
        ----------
        corpus : list of list of str
            Given corpus.
        k1 : float
            Constant used for influencing the term frequency saturation. After saturation is reached, additional
            presence for the term adds a significantly less additional score. According to [1]_, experiments suggest
            that 1.2 < k1 < 2 yields reasonably good results, although the optimal value depends on factors such as
            the type of documents or queries.
        b : float
            Constant used for influencing the effects of different document lengths relative to average document length.
            When b is bigger, lengthier documents (compared to average) have more impact on its effect. According to
            [1]_, experiments suggest that 0.5 < b < 0.8 yields reasonably good results, although the optimal value
            depends on factors such as the type of documents or queries.
        epsilon : float
            Constant used as floor value for idf of a document in the corpus. When epsilon is positive, it restricts
            negative idf values. Negative idf implies that adding a very common term to a document penalize the overall
            score (with 'very common' meaning that it is present in more than half of the documents). That can be
            undesirable as it means that an identical document would score less than an almost identical one (by
            removing the referred term). Increasing epsilon above 0 raises the sense of how rare a word has to be (among
            different documents) to receive an extra score.
        """

        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        self.corpus_size = 0
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self._initialize(corpus)

    def _initialize(self, corpus):
        """Calculates frequencies of terms in documents and in corpus. Also computes inverse document frequencies."""
        nd = {}  # word -> number of documents with word
        num_doc = 0
        for document in corpus:
            self.corpus_size += 1
            self.doc_len.append(len(document))
            num_doc += len(document)

            frequencies = {}
            for word in document:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
            self.doc_freqs.append(frequencies)

            for word, freq in iteritems(frequencies):
                if word not in nd:
                    nd[word] = 0
                nd[word] += 1

        self.avgdl = float(num_doc) / self.corpus_size
        # collect idf sum to calculate an average idf for epsilon value
        idf_sum = 0
        # collect words with negative idf to set them a special epsilon value.
        # idf can be negative if word is contained in more than half of documents
        negative_idfs = []
        for word, freq in iteritems(nd):
            idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)
        self.average_idf = float(idf_sum) / len(self.idf)

        if self.average_idf < 0:
            logger.warning(
                'Average inverse document frequency is less than zero. Your corpus of {} documents'
                ' is either too small or it does not originate from natural text. BM25 may produce'
                ' unintuitive results.'.format(self.corpus_size)
            )

        eps = self.epsilon * self.average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_score(self, document, index):
        """Computes BM25 score of given `document` in relation to item of corpus selected by `index`.
        Parameters
        ----------
        document : list of str
            Document to be scored.
        index : int
            Index of document in corpus selected to score with `document`.
        Returns
        -------
        float
            BM25 score.
        """
        score = 0.0
        doc_freqs = self.doc_freqs[index]
        numerator_constant = self.k1 + 1
        denominator_constant = self.k1 * (1 - self.b + self.b * self.doc_len[index] / self.avgdl)
        for word in document:
            if word in doc_freqs:
                df = self.doc_freqs[index][word]
                idf = self.idf[word]
                score += (idf * df * numerator_constant) / (df + denominator_constant)
        return score

    def get_scores(self, document):
        """Computes and returns BM25 scores of given `document` in relation to
        every item in corpus.
        Parameters
        ----------
        document : list of str
            Document to be scored.
        Returns
        -------
        list of float
            BM25 scores.
        """
        scores = [self.get_score(document, index) for index in range(self.corpus_size)]
        return scores

    


# ---------GENSIM GITHUB CODE END--------

# Applying gensim BM25 to the corpus to obtain scores

# In[7]:


list = []
i=1
for i in range(len(corpus)):
    list.append(tokenized_corpus[i+1]) 
p1 = BM25(list)


# In[8]:


query = tokenized_corpus[0]
resultant_scores = p1.get_scores(query)


# Sorting Resultant Sscores In Descending Order

# In[9]:


import numpy as np
res_list = np.array(resultant_scores)
res_list


# In[10]:


top_n = np.argsort(res_list)[::-1]
result = [corpus[i] for i in top_n]


# In[11]:


scores = res_list[top_n]
scores


# Finding Filename Corresponding To Sscores

# In[12]:


output = []

for item in result:
    for filename, content in corpus_dict.items():
        if content == item:
            output.append(filename)


# In[13]:


new_output = []
sstring = '.txt'
for item in output:
    if item.endswith(sstring): 
        new_output.append(item[:-(len(sstring))])


# Writing To a File For TREC-EVAL Evaluation

# In[14]:


f = open("C:\\Users\\ASUS\\AILA Practice\\run-NER-bm25.txt","a")
for i in range(len(corpus)):
    f.write("AILA_Q28 Q0 {} {} {} Default\n".format(new_output[i], (i+1), scores[i]))
f.close()


# In[ ]:




