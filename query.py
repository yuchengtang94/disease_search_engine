
import re
from flask import *
from index import Disease
from pprint import pprint
from elasticsearch_dsl import Q
from elasticsearch_dsl.utils import AttrList
from collections import OrderedDict

# TODO:  autocomplete, star last name

app = Flask(__name__)

# Initialize global variables for rendering page
tmp_symptoms = ""
tmp_name = ""

tmp_introduction = ""
tmp_causes = ""
tmp_treatment = ""
text_select = "Conjunctive"

inform = ""

gresults = {}
g_similar_results = {}

similar_dis_num = 0

@app.route("/")
def search():
    return render_template('page_query.html')

@app.route("/results", defaults={'page': 1}, methods=['GET','POST'])
@app.route("/results/<page>", methods=['GET','POST'])
def results(page):
    global tmp_symptoms
    global tmp_name

    global gresults
    global text_select

    global tmp_introduction

    global tmp_causes
    global tmp_treatment

    global inform

    inform = ""
    if type(page) is not int:
        page = int(page.encode('utf-8'))

    if request.method == 'POST':
        symptoms_query = request.form['query']

        introduction_query = request.form['introduction']

        causes_query = request.form['causes']
        treatment_query = request.form['treatment']

        text_select = request.form['freetext_select']
        # print text_select

        # update global variable template date
        tmp_symptoms = symptoms_query

        tmp_introduction = introduction_query
        # tmp_country = country_query
        tmp_causes = causes_query
        tmp_treatment = treatment_query

    else:
        symptoms_query = tmp_symptoms

        introduction_query = tmp_introduction

        causes_query = tmp_causes
        treatment_query = tmp_treatment

    # store query values to display in search box while browsing
    shows = {}
    shows['symptoms'] = symptoms_query

    shows['introduction'] = introduction_query

    shows['causes'] = causes_query
    shows['treatment'] = treatment_query

    # search
    mDisease = Disease()
    s = mDisease.search()

    # search for matching text query
    if len(symptoms_query) > 0:
        str_text_query = ""
        phrase_text_query = []
        beg = 0

        q = None
        while beg < len(symptoms_query):
            i = symptoms_query.find("\"",beg)
            # print "i =" + str(i)
            if i == -1:
                str_text_query += symptoms_query[beg:]
                # print str_text_query
                break

            str_text_query += symptoms_query[beg: i]
            beg = i + 1

            i = symptoms_query.find("\"",beg)
            if i == -1:
                i = len(symptoms_query)
            phrase_text_query.append(symptoms_query[beg: i])
            beg = i + 1

        if text_search(str_text_query, phrase_text_query, q) is False and text_select == "Conjunctive":
            text_select = "Disjunctive"
            inform = " The text query has no match result, showing the result of disjunctive search"
            print inform

        if len(str_text_query) > 0:
            print "str_text_query=" + str_text_query
            if text_select == "Conjunctive":
                q = Q('multi_match', query = str_text_query, type='cross_fields', fields=['symptoms', 'name'], operator='and')
            else :
                q = Q("match", symptoms = str_text_query) | Q('match', name = str_text_query)

        print "phrases:" + str(phrase_text_query)
        for phrase in phrase_text_query:
            print "phrase=" + phrase
            if q == None:
                q = Q("match_phrase", symptoms = phrase) | Q("match_phrase", name = phrase)
            else:
                q |= Q("match_phrase", symptoms = phrase) | Q("match_phrase", name = phrase)

        s = s.query(q)

    if len(introduction_query) > 0:
        s = s.query('match', introuduction=introduction_query)


    if len(causes_query) > 0:
        s = s.query('match', causes=causes_query)
    if len(treatment_query) > 0:
        s = s.query('match', treatment=treatment_query)

    # highlight
    s = s.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    s = s.highlight('symptoms', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('name', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('causes', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('introduction', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('treatment', fragment_size=999999999, number_of_fragments=1)

    # extract data for current page
    start = 0 + (page-1)*10
    end = 10 + (page-1)*10

    # execute search
    response = s[start:end].execute()

    hitscount = len(response.hits)

    # insert data into response
    resultList = {}
    for hit in response.hits:
        result={}
        result['score'] = hit.meta.score

        if 'highlight' in hit.meta:

            if 'name' in hit.meta.highlight:
                result['name'] = hit.meta.highlight.name[0]
            else:
                result['name'] = hit.name
            if 'symptoms' in hit.meta.highlight:
                result['symptoms'] = hit.meta.highlight.symptoms[0]
            else:
                result['symptoms'] = hit.symptoms

            if 'introduction' in hit.meta.highlight:
                result['introduction'] = hit.meta.highlight.introduction[0]
            else:
                result['introduction'] = hit.introduction

            if 'treatment' in hit.meta.highlight:

                result['treatment'] = hit.meta.highlight.treatment[0]
            else:

                result['treatment'] = hit.treatment

            if 'causes' in hit.meta.highlight:
                result['causes'] = hit.meta.highlight.causes[0]
            else:
                result['causes'] = hit.causes

        else:
            result['name'] = hit.name
            result['symptoms'] = hit.symptoms
            result['introduction'] = hit.introduction
            result['causes'] = hit.causes
            result['treatment'] = hit.treatment
        result['_id'] = hit._id
        resultList[hit.meta.id] = result

    gresults = resultList

    # get the number of results
    result_num = response.hits.total

    # if we find the results, extract title and text information from doc_data, else do nothing
    if result_num > 0:
        return render_template('page_SERP.html', results=resultList, res_num=result_num, page_num=page, queries=shows, message = inform)
    else:
        message = []
        if len(symptoms_query) > 0:
            message.append('Unknown search term: '+symptoms_query)

        inform = " Maybe you can try to modify your query."
        return render_template('page_SERP.html', results=message, res_num=result_num, page_num=page, queries=shows,
                               message = inform)


@app.route("/documents/<res>", methods=['GET'])
def documents(res):
    global gresults
    disease = gresults[res.encode('utf-8')]
    diseaseName = disease['name']
    diseaseIntro = disease['introduction']
    diseaseSymp = disease['symptoms']
    diseaseCauses = disease['causes']
    diseaseTreat = disease['treatment']


    diseaseId = disease['_id']
    similarDisease = get_similar_docs(diseaseId)

    for term in disease:
        if type(disease[term]) is AttrList:
            s = "\n"
            for item in disease[term]:
                s += item + ",\n "
            disease[term] = s

    return render_template('page_targetArticle.html', disease=disease, name=diseaseName, intro=diseaseIntro, symp=diseaseSymp,similar_dis_num = similar_dis_num,
                           causes=diseaseCauses, treat=diseaseTreat, similarDiseaseDict = similarDisease)


def get_similar_docs(diseaseId):
    global similar_dis_num
    global g_similar_results
    mDisease = Disease()
    s = mDisease.search()
    # more like this
    s = s.query('more_like_this', fields=['name', 'symptoms'],
                like={
                    "_index": "test_rare_disease_index",
                    "_type": "disease",
                    "_id": diseaseId}
                )
    response = s[0:5].execute()

    resultList = {}
    for hit in response.hits:
        result = {}
        result['score'] = hit.meta.score
        result['name'] = hit.name
        # print "similar disease hit.name = " + hit.name
        result['symptoms'] = hit.symptoms
        result['introduction'] = hit.introduction
        result['causes'] = hit.causes
        result['treatment'] = hit.treatment
        result['_id'] = hit._id
        resultList[hit.meta.id] = result

    g_similar_results = resultList
    similar_dis_num = len(resultList)
    return resultList

@app.route("/similar_documents/<res>", methods=['GET'])
def similar_documents(res):
    global g_similar_results
    disease = g_similar_results[res.encode('utf-8')]
    diseaseName = disease['name']
    diseaseIntro = disease['introduction']
    diseaseSymp = disease['symptoms']
    diseaseCauses = disease['causes']
    diseaseTreat = disease['treatment']

    diseaseId = disease['_id']
    similarDisease = get_similar_docs(diseaseId)

    for term in disease:
        if type(disease[term]) is AttrList:
            s = "\n"
            for item in disease[term]:
                s += item + ",\n "
            disease[term] = s

    return render_template('page_targetArticle.html', disease=disease, name=diseaseName, intro=diseaseIntro, symp=diseaseSymp,similar_dis_num = similar_dis_num,
                           causes=diseaseCauses, treat=diseaseTreat, similarDiseaseDict = similarDisease)


def text_search(str_text_query,phrase_text_query,q):
    mDisease = Disease()
    s = mDisease.search()
    if len(str_text_query) > 0:
        # print "str_text_query=" + str_text_query
        if text_select == "Conjunctive":
            q = Q('multi_match', query = str_text_query, type='cross_fields', fields=['name', 'symptoms'], operator='and')
        else :
            q = Q("match", name = str_text_query) | Q('match', symptoms = str_text_query)

    # print "phrases:" + str(phrase_text_query)
    for phrase in phrase_text_query:
        # print "phrase=" + phrase
        if q is None:
            q = Q("match_phrase", name = phrase) | Q("match_phrase", symptoms = phrase)
        else:
            q |= Q("match_phrase", name = phrase) | Q("match_phrase", symptoms = phrase)

    start = 0
    end = 10
    s = s.query(q)

    # execute search
    response = s[start:end].execute()
    if response.hits.total == 0:
        # print "response is 0"
        return False
    else: return True


if __name__ == "__main__":
    app.run()

