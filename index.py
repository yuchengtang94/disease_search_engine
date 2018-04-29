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
    with open('disease_data.json') as data_file:
        diseases = json.load(data_file)
        size = len(diseases)
    
    # Action series for bulk loading
    actions = [
        {
            "_index": "test_rare_disease_index",
            "_type": "disease",
            "_id": mid,
            "disease_type":diseases[str(mid)]['disease_type'],
            "name":diseases[str(mid)]['name'],
            "introduction":diseases[str(mid)]['introduction'],
            "symptoms":diseases[str(mid)]['symptoms'],
            "causes":diseases[str(mid)]['causes'],
            "treatment":diseases[str(mid)]['treatment'],
            "diagnosis":diseases[str(mid)]['diagnosis'],
            "affected_populations":diseases[str(mid)]['affected_populations'],

             #diseases[str(mid)]['runtime'] # You would like to convert runtime to integer (in minutes)
            # --- Add more fields here ---

        }
        for mid in range(1, size+1)
    ]
    
    helpers.bulk(es, actions) 


def main():
    start_time = time.time()
    buildIndex()
    print("=== Built index in %s seconds ===" % (time.time() - start_time))
        
if __name__ == '__main__':
    main()
