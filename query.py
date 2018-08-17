# Simple extended boolean search engine: query module
# Hussein Suleman
# 14 April 2016
# Extended by Kouame Kouassi
# 08 August 2018

import re
import math
import sys
import os
from math import log
from thesaurus import Word

import porter

import parameters

# check parameter for collection name
if len(sys.argv)<3:
   print ("Syntax: query.py <collection> <query>")
   exit(0)
 
# construct collection and query
collection = sys.argv[1]
query = ''
arg_index = 2
while arg_index < len(sys.argv):
   query += sys.argv[arg_index] + ' '
   arg_index += 1

# clean query
if parameters.case_folding:
   query = query.lower ()
query = re.sub (r'[^ a-zA-Z0-9]', ' ', query)
query = re.sub (r'\s+', ' ', query)
query_words = query.split (' ')

print "before", query_words, "\n"
if parameters.thesaurus:
    synonyms = []
    for term in query_words:
        if term != "":
            word = Word(term)
            synonyms += word.synonyms()
	    if term in synonyms:
	       synonyms.remove(term)
    query_words += synonyms
print "After", query_words, "\n"
# create accumulators and other data structures
accum = {}
filenames = []
p = porter.PorterStemmer ()

# get N
f = open (collection+"_index_N", "r")
N = eval (f.read ())
f.close ()

# get document lengths/titles
titles = {}
f = open (collection+"_index_len", "r")
lengths = f.readlines ()
f.close ()

# get index for each term and calculate similarities using accumulators
for term in query_words:
    if term != '':
        if parameters.stemming:
            term = p.stem (term, 0, len(term)-1)
        if not os.path.isfile (collection+"_index/"+term):
            continue
        print term
        f = open (collection+"_index/"+term, "r")
        lines = f.readlines ()
        idf = 1
        if parameters.use_idf:
           df = len(lines)
           idf = 1/df
           if parameters.log_idf:
              idf = math.log (1 + N/df)
        for line in lines:
            mo = re.match (r'([0-9]+)\:([0-9\.]+)', line)
            if mo:
                file_id = mo.group(1)
                tf = float (mo.group(2))
                if not file_id in accum:
                    accum[file_id] = 0
                if parameters.log_tf:
                    tf = (1 + math.log (tf))
                accum[file_id] += (tf * idf)
        f.close()

# parse lengths data and divide by |N| and get titles
for l in lengths:
   mo = re.match (r'([0-9]+)\:([0-9\.]+)\:(.+)', l)
   if mo:
      document_id = mo.group (1)
      length = eval (mo.group (2))
      title = mo.group (3)
      if document_id in accum:
         if parameters.normalization:
            accum[document_id] = accum[document_id] / length
         titles[document_id] = title

# print top ten results
result = sorted (accum, key=accum.__getitem__, reverse=True)
num_result_returned = min(len (result), 10)
for i in range (num_result_returned):
   print ("{0:10.8f} {1:5} {2}".format (accum[result[i]], result[i], titles[result[i]]))


#load relevance judgements
if parameters.query1:
    filename = 'testbed/relevance.1'
elif parameters.query2:
    filename = 'testbed/relevance.2'
elif parameters.query3:
    filename = filename = 'testbed/relevance.3'
else:
    exit(0)
relevance = []
with open(filename) as f:
    for line in f:
        relevance.append(eval(line))

counter = 0.0
ave_precision = 0.0
DCG = 0.0
rels = []
for i in range(num_result_returned):
    result_id = eval(result[i])
    rel = relevance[result_id - 1]
    rels.append(rel)
    DCG += rel/log(i + 2, 2)
    if rel > 0:
        counter += 1.0
    ave_precision += counter/(i + 1)
total_relevant_docs = len(relevance) - relevance.count(0)
recall = counter/total_relevant_docs
precision = counter/num_result_returned
AP = ave_precision/num_result_returned
rels = sorted(rels, reverse=True)
IDCG = 0.0
for i in range(len(rels)):
    IDCG += rels[i]/log(i + 2, 2) 
NDCG = DCG/IDCG

print "Number of relevant docs: ", total_relevant_docs
print "Recall: ", recall
print "Precision: ", precision
print "AP: ", AP
print "DCG ", DCG
print "IDCG: ", IDCG
print "NDCG: ", NDCG
