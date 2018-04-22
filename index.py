import json
import re
import time
import types

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Index, DocType, Text, Keyword, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import tokenizer, analyzer
from elasticsearch_dsl.query import MultiMatch, Match


# Connect to local host server
connections.create_connection(hosts=['127.0.0.1:9200'])

# Establish elasticsearch
es = Elasticsearch()

# Define analyzers
my_analyzer = analyzer('custom',
                       tokenizer='standard',
                       filter=['lowercase', 'stop','html_strip'])
# --- Add more analyzers here ---
title_analyzer = analyzer('custom',
                          tokenizer = ['standard','whitespace', 'lowercase'],
                          filter = '')
text_analyzer_norm = analyzer('custom',
                         tokenizer = ['standard', 'lowercase'],
                         filter = ['html_strip', 'stop','word_delimiter','porter_stem'])
starr_analyzer = analyzer('custom',
                          tokenizer = ['lowercase', 'whitespace'],
                          filter = ['html_strip'])
director_analyzer = analyzer('custom',
                          tokenizer = ['lowercase', 'whitespace'],
                          filter = 'html_strip')
location_analyzer = analyzer('custom',
                             tokenizer = ['lowercase', 'whitespace'],
                             filter = 'html_strip')
language_analyzer = analyzer('custom',
                             tokenizer = ['lowercase', 'whitespace'],
                             filter = 'html_strip')
category_analyzer = analyzer('custom',
                             tokenizer = ['standard','lowercase', 'whitespace'],
                             filter = ['html_strip', 'stop','word_delimiter'])
w_analyzer = analyzer('custom',
                      tokenizer = 'whitespace',
                      filter = ['lowercase', 'stop', 'stemmer'],
                      char_filter = ['html_strip'])

# Define document mapping
# You can use existed analyzers or use ones you define yourself as above
class Disease(DocType):

    def __init__(self, **kwargs):

        super(Disease, self).__init__(**kwargs)

        # --- disease here ---
        id = Text(analyzer=my_analyzer)
        name = Text(analyzer=my_analyzer)
        introduction = Text(analyzer=my_analyzer)
        symptoms = Text(analyzer=my_analyzer)
        causes = Text(analyzer=my_analyzer)
        treatment = Text(analyzer=my_analyzer)

    class Meta:
        index = 'test_rare_disease_index'
        doc_type = 'disease'

    def save(self, *args, **kwargs):
        return super(Disease, self).save(*args, **kwargs)

# Populate the index
def buildIndex():
    Disease_index = Index('test_rare_disease_index')
    if Disease_index.exists():
        Disease_index.delete()  # Overwrite any previous version
    Disease_index.doc_type(Disease) # Set doc_type to Movie
    Disease_index.create()
    
    # Open the json film corpus
    with open('final_rare_disease.json') as data_file:
        diseases = json.load(data_file)
        size = len(diseases)
    
    # Action series for bulk loading
    actions = [
        {
            "_index": "test_rare_disease_index",
            "_type": "disease",
            "_id": mid,
            "name":diseases[str(mid)]['name'],
            "introduction":diseases[str(mid)]['introduction'],
            "symptoms":diseases[str(mid)]['symptoms'],
            "causes":diseases[str(mid)]['causes'],
            "treatment":diseases[str(mid)]['treatment']

             #diseases[str(mid)]['runtime'] # You would like to convert runtime to integer (in minutes)
            # --- Add more fields here ---

        }
        for mid in range(1, size+1)
    ]
    
    helpers.bulk(es, actions) 

def convert_time(s):
    res = 0
    if isinstance(s, types.ListType):
        s = s[0]

    s = s.lower()
    s = re.sub(r"\s*", "",s)
    if s == "":
        return res
    if re.match(r"\d*h\d*m.*|"
                r"\d*hours*\d*minutes*.*|"
                r"\d*h\d*mins*.*"
                , s):

        i = 0
        while i < len(s) and (s[i].isdigit() or s[i] == '.'):
            i += 1
        hour = s[:i]

        while i < len(s) and not s[i].isdigit():
            i +=1
        j = i
        while j < len(s) and (s[j].isdigit() or s[j] == '.'):
            j +=1
        minute = s[i:j] or "0"
        try:

            res = int(60 * float(hour)) + int(float(minute))
        except:
            print "hour:" + hour + " min:" + minute
            # print "convertTime: convert int/float failed"
    elif re.match(r"\d*\.*\d*mins*.*|"
                  r"\d*minutes*.*"
            , s):

        j = 0
        while j < len(s) and (s[j].isdigit() or s[j] == '.'):
            j +=1
        minute = s[:j]
        try:
            res = int(float(minute))
        except:
            print "min:" + minute
            # print "convertTime: convert float failed"

    elif re.match(r"\d*\.*\d*h.*|"
                  r"\d*\.*\d*hours*.*"
            ,s):

        i = 0
        while i < len(s) and (s[i].isdigit() or s[i] == '.'):
            i += 1
        hour = s[:i]
        try:

            res = int(60 * float(hour))
        except:
            print "hour:" + hour
            # print "convertTime: convert int/float failed"
    else:

        print "convert runtime failed: " + "\"" + str(s) + "\""
    return res

def main():
    start_time = time.time()
    buildIndex()
    print("=== Built index in %s seconds ===" % (time.time() - start_time))
        
if __name__ == '__main__':
    main()
