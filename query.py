
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

tmp_affected_populations = ""
tmp_other_information = ""
tmp_causes = ""
tmp_treatment = ""
disease_type = "All Disease"

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
    global tmp_disease_type

    global tmp_affected_populations

    global tmp_causes
    global tmp_other_information


    global inform

    inform = ""
    if type(page) is not int:
        page = int(page.encode('utf-8'))

    if request.method == 'POST':

        symptoms_query = request.form['query']

        affected_populations_query = request.form['affected_populations']

        causes_query = request.form['causes']

        other_information_query = request.form['other_information']

        disease_type = request.form['disease_type']


        # update global variable template date
        tmp_symptoms = symptoms_query

        tmp_disease_type = disease_type

        tmp_affected_populations = affected_populations_query
        # tmp_country = country_query
        tmp_causes = causes_query
        tmp_other_information = other_information_query

    else:

        disease_type = tmp_disease_type

        symptoms_query = tmp_symptoms

        affected_populations_query = tmp_affected_populations

        causes_query = tmp_causes

        other_information_query = tmp_other_information

    # store query values to display in search box while browsing
    shows = {}

    shows['disease_type'] = disease_type

    shows['symptoms'] = symptoms_query

    shows['affected_populations'] = affected_populations_query

    shows['causes'] = causes_query
    shows['other_information'] = other_information_query


    # search
    mDisease = Disease()
    s = mDisease.search()

    # search for matching text query
    if len(symptoms_query) > 0:
        str_text_query = ""
        phrase_text_query = []
        beg = 0

        q = None
        # select the phrases surrounded by "
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

        # if text_search(str_text_query, phrase_text_query, q) is False and disease_type == "Conjunctive":
        #     disease_type = "Disjunctive"
        #     inform = " The text query has no match result, showing the result of disjunctive search"
        #     print inform

        # remaining query except for phrase surrounded by "
        if len(str_text_query) > 0:
            q = Q("match", symptoms = str_text_query) | Q('match', name = str_text_query)

        # print "phrases:" + str(phrase_text_query)
        for phrase in phrase_text_query:
            # meaning no remaining query except phrase
            if q == None:
                q = Q("match_phrase", symptoms = phrase) | Q("match_phrase", name = phrase)
            else:
                q |= Q("match_phrase", symptoms = phrase) | Q("match_phrase", name = phrase)

        s = s.query(q)

    if disease_type == "Common Disease":
        s = s.query("match", disease_type="Common Disease")
    elif disease_type == "Rare Disease":
        s = s.query("match", disease_type="Rare Disease")

    if len(affected_populations_query) > 0:
        s = s.query('match', affected_populations=affected_populations_query)


    if len(causes_query) > 0:
        s = s.query('match', causes=causes_query)
    if len(other_information_query) > 0:
        s = s.query('multi_match', query=other_information_query, type='cross_fields', fields=['introduction', 'diagnosis'], operator='and')

    # highlight
    s = s.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    s = s.highlight('symptoms', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('name', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('causes', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('affected_populations', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('treatment', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('diagnosis', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('disease_type', fragment_size=999999999, number_of_fragments=1)

    # extract data for current page
    start = 0 + (page-1)*10
    end = 10 + (page-1)*10

    # execute search
    response = s[start:end].execute()

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

            if 'affected_populations' in hit.meta.highlight:
                result['affected_populations'] = hit.meta.highlight.affected_populations[0]
            else:
                result['affected_populations'] = hit.affected_populations

            if 'treatment' in hit.meta.highlight:

                result['treatment'] = hit.meta.highlight.treatment[0]
            else:

                result['treatment'] = hit.treatment

            if 'causes' in hit.meta.highlight:
                result['causes'] = hit.meta.highlight.causes[0]
            else:
                result['causes'] = hit.causes

            if 'diagnosis' in hit.meta.highlight:
                result['diagnosis'] = hit.meta.highlight.diagnosis[0]
            else:
                result['diagnosis'] = hit.diagnosis

        else:
            result['name'] = hit.name
            result['symptoms'] = hit.symptoms
            result['affected_populations'] = hit.affected_populations
            result['causes'] = hit.causes
            result['treatment'] = hit.treatment
            result['diagnosis'] = hit.diagnosis
            result['introduction'] = hit.introduction


        result['_id'] = hit._id
        resultList[hit.meta.id] = result
        result['disease_type'] = hit.disease_type

    gresults = resultList

    # get the number of results
    result_num = response.hits.total

    print "other info:" + shows['other_information']

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
    diseasePopu = disease['affected_populations']
    diseaseDiag = disease['diagnosis']
    diseaseType = disease['disease_type']


    diseaseId = disease['_id']
    similarDisease = get_similar_docs(diseaseId)

    for term in disease:
        if type(disease[term]) is AttrList:
            s = "\n"
            for item in disease[term]:
                s += item + ",\n "
            disease[term] = s

    return render_template('page_targetArticle.html', disease=disease, name=diseaseName, intro=diseaseIntro,
                           symp=diseaseSymp, similar_dis_num=similar_dis_num, causes=diseaseCauses, treat=diseaseTreat,
                           popu=diseasePopu, diag=diseaseDiag,similarDiseaseDict=similarDisease, diseaseType = diseaseType)


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
        result['diagnosis'] = hit.diagnosis
        result['affected_populations'] = hit.affected_populations
        result['causes'] = hit.causes
        result['treatment'] = hit.treatment
        result['_id'] = hit._id
        result['disease_type'] = hit.disease_type
        resultList[hit.meta.id] = result

    g_similar_results = resultList
    similar_dis_num = len(resultList)
    return resultList

# click similar disease to get document
@app.route("/similar_documents/<res>", methods=['GET'])
def similar_documents(res):
    global g_similar_results
    disease = g_similar_results[res.encode('utf-8')]
    diseaseName = disease['name']
    diseaseIntro = disease['introduction']
    diseaseSymp = disease['symptoms']
    diseaseCauses = disease['causes']
    diseaseTreat = disease['treatment']
    diseasePopu = disease['affected_populations']
    diseaseDiag = disease['diagnosis']
    diseaseType = disease['disease_type']


    diseaseId = disease['_id']
    similarDisease = get_similar_docs(diseaseId)

    for term in disease:
        if type(disease[term]) is AttrList:
            s = "\n"
            for item in disease[term]:
                s += item + ",\n "
            disease[term] = s

    return render_template('page_targetArticle.html', disease=disease, name=diseaseName, intro=diseaseIntro, symp=diseaseSymp,
                           similar_dis_num = similar_dis_num,causes=diseaseCauses, treat=diseaseTreat, popu = diseasePopu,
                           diag = diseaseDiag, similarDiseaseDict = similarDisease,diseaseType = diseaseType)


# def text_search(str_text_query,phrase_text_query,q):
#     mDisease = Disease()
#     s = mDisease.search()
#     if len(str_text_query) > 0:
#         # print "str_text_query=" + str_text_query
#         if disease_type == "Conjunctive":
#             q = Q('multi_match', query = str_text_query, type='cross_fields', fields=['name', 'symptoms'], operator='and')
#         else :
#             q = Q("match", name = str_text_query) | Q('match', symptoms = str_text_query)
#
#     # print "phrases:" + str(phrase_text_query)
#     for phrase in phrase_text_query:
#         # print "phrase=" + phrase
#         if q is None:
#             q = Q("match_phrase", name = phrase) | Q("match_phrase", symptoms = phrase)
#         else:
#             q |= Q("match_phrase", name = phrase) | Q("match_phrase", symptoms = phrase)
#
#     start = 0
#     end = 10
#     s = s.query(q)
#
#     # execute search
#     response = s[start:end].execute()
#     if response.hits.total == 0:
#         # print "response is 0"
#         return False
#     else: return True


if __name__ == "__main__":
    app.run()

