#!/usr/bin/env python
# coding: utf-8

# IMPROVED BM25 APPROACH: 
# relevance(q,d) = BM25(q',d) + BM25(q",d)

# Importing Corpus from directory

# In[1]:


import pandas as pd
import os, glob
folder = "C:\\Users\\ASUS\\AILA Practice\\casedocs"
os.chdir(folder)
files = glob.glob("*.txt") # Makes a list of all files in folder
corpus = []
corpus_dict = {}
for file1 in files:
    with open (file1, 'r') as f:
        document = f.read() # Reads document content into a string
        corpus.append(document)
        corpus_dict[file1] = document


# Removing punctuations and stemming using Porter Stemmer and creating tokenized_corpus

# In[2]:


new_corpus = corpus.copy()


# In[3]:


#Convert text to Lowercase
import nltk
def to_lower(text):
    return ' '.join([w.lower() for w in nltk.word_tokenize(text)])

for doc in new_corpus:
    i = new_corpus.index(doc)
    result = to_lower(doc)
    new_corpus[i] = result
    
#Remove Punctuations
from string import punctuation
def strip_punctuation(s):
    return ''.join(c for c in s if c not in punctuation)

for doc in new_corpus:
    i = new_corpus.index(doc)
    result = strip_punctuation(doc)
    new_corpus[i] = result

#Remove Numbers
for doc in new_corpus:
    i = new_corpus.index(doc)
    result = ''.join(c for c in doc if not c.isdigit())
    new_corpus[i] = result

#Remove Stop Words
import nltk
from nltk.corpus import stopwords
stopwords = stopwords.words('english')

tokenized_corpus = [nltk.word_tokenize(doc) for doc in new_corpus]

for doc in tokenized_corpus:
    i = tokenized_corpus.index(doc)
    result = [word for word in tokenized_corpus[i] if word not in stopwords]
    tokenized_corpus[i] = result
    
#Porter Stemmer for stemming
from nltk.stem import PorterStemmer

ps = PorterStemmer()
for docs in tokenized_corpus:
    i = tokenized_corpus.index(docs)
    for words in docs:
        j = tokenized_corpus[i].index(words)
        tokenized_corpus[i][j] = ps.stem(words)


# Using rank_bm25 library and running it against tokenized_corpus

# In[4]:


from rank_bm25 import BM25Okapi

bm25A = BM25Okapi(tokenized_corpus)


# q' = FINDING IDF VALUES FOR QUERY AND EXTRACTING TOP 50%

# START....

# importing casedocs_idf = casedocs + query

# In[5]:


import pandas as pd
import os, glob
folder_idf = "C:\\Users\\ASUS\\AILA Practice\\casedocs_idf"
os.chdir(folder_idf)
files_idf = glob.glob("*.txt") # Makes a list of all files in folder
corpus_idf = []
dict_idf={}
for file1 in files_idf:
    with open (file1, 'r') as f:
        document = f.read() # Reads document content into a string
        corpus_idf.append(document)
        dict_idf[file1] = document


# preprocessing it the same way

# In[6]:


#Convert text to Lowercase
import nltk
def to_lower(text):
    return ' '.join([w.lower() for w in nltk.word_tokenize(text)])

for doc in corpus_idf:
    i = corpus_idf.index(doc)
    result = to_lower(doc)
    corpus_idf[i] = result
    
#Remove Punctuations
from string import punctuation
def strip_punctuation(s):
    return ''.join(c for c in s if c not in punctuation)

for doc in corpus_idf:
    i = corpus_idf.index(doc)
    result = strip_punctuation(doc)
    corpus_idf[i] = result

#Remove Numbers
for doc in corpus_idf:
    i = corpus_idf.index(doc)
    result = ''.join(c for c in doc if not c.isdigit())
    corpus_idf[i] = result

#Remove Stop Words
import nltk
from nltk.corpus import stopwords
stopwords = stopwords.words('english')

tokenized_corpus_idf = [nltk.word_tokenize(doc) for doc in corpus_idf]

for doc in tokenized_corpus_idf:
    i = tokenized_corpus_idf.index(doc)
    result = [word for word in tokenized_corpus_idf[i] if word not in stopwords]
    tokenized_corpus_idf[i] = result
    
#Porter Stemmer for stemming
from nltk.stem import PorterStemmer

ps = PorterStemmer()
for docs in tokenized_corpus_idf:
    i = tokenized_corpus_idf.index(docs)
    for words in docs:
        j = tokenized_corpus_idf[i].index(words)
        tokenized_corpus_idf[i][j] = ps.stem(words)


# using tf-idf vectorizer

# In[7]:


from sklearn.feature_extraction.text import TfidfVectorizer 

def dummy_fun(doc):
    return doc

tfidf_vectorizer=TfidfVectorizer(
    use_idf=True,
    analyzer='word',
    tokenizer=dummy_fun,
    preprocessor=dummy_fun,
    token_pattern=None)

tfidf_vectorizer_vectors=tfidf_vectorizer.fit_transform(tokenized_corpus_idf)


# In[8]:


import numpy as np
# function to get unique values 
def unique(list1): 
    x = np.array(list1) 
    return np.unique(x)

list = unique(tokenized_corpus_idf[0])


# In[9]:


dict = {}

for words in list:
    if words in tfidf_vectorizer.get_feature_names():
        index = tfidf_vectorizer.get_feature_names().index(words)
        dict[words] = tfidf_vectorizer.idf_[index]
keys = np.fromiter(dict.keys(), dtype='<U7')
vals = np.fromiter(dict.values(), dtype=float)


# In[10]:


import math
feature_arr = np.array(keys)
tfidf_sort = np.argsort(vals).flatten()[::-1]

top = len(list)/2
m = math.ceil(top)
top_m = feature_arr[tfidf_sort][:m]
top_m


# END....

# Applying BM25

# In[11]:


doc_scores_A = bm25A.get_scores(top_m)
doc_scores_A


# q" = FINDING SCORES FOR q"

# In[12]:


from rank_bm25 import BM25Okapi

bm25B = BM25Okapi(tokenized_corpus)


# In[13]:


doc_scores_B = bm25B.get_scores(list)
doc_scores_B


# Adding Scores for q' and q" and obtain scores for all casedocs

# In[14]:


res_list = [doc_scores_A + doc_scores_B for i in range(len(doc_scores_A))]


# In[1]:


res_list = res_list[0]
res_list


# Retrieving top 10 documents for Precision@10 Calculation

# In[16]:


n = 10
top_n = np.argsort(res_list)[::-1][:n]
result = [corpus[i] for i in top_n]


# In[17]:


output = []

for item in result:
    for filename, content in corpus_dict.items():
        if content == item:
            output.append(filename)


# In[18]:


output


# In[19]:


new_output = []
sstring = '.txt'
for item in output:
    if item.endswith(sstring): 
        new_output.append(item[:-(len(sstring))])


# In[20]:


new_output


# TREC_EVAL GOLD STANDARD - PRECISION @ 10 CALCULATION

# In[21]:


with open('C:\\Users\\ASUS\\AILA Practice\\trec_goldstd_priorcases.txt') as f:
    irrelevant = [line.rstrip() for line in f]


# In[22]:


dict = {}

for line in irrelevant:
    key = line.partition(' Q0 ')[0]
    temp = line.partition(' Q0 ')[2]
    val = temp.partition(' 0')[0]
    dict.setdefault(key, [])
    dict[key].append(val)


# In[23]:


count_relevant = 0

for item in new_output:
    if item not in dict['AILA_Q50']:
        count_relevant = count_relevant + 1


# In[24]:


count_relevant


# In[ ]:




