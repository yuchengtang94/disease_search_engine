
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


# cyc add
tmp_introduction = ""

tmp_causes = ""
tmp_treatment = ""

text_select = "Conjunctive"

inform = ""

gresults = {}

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
    # cyc add
    global tmp_introduction

    global tmp_causes
    global tmp_treatment

    global inform

    inform = ""
    if type(page) is not int:
        page = int(page.encode('utf-8'))
    # if the method of request is post, store query in local global variables
    # if the method of request is get, extract query contents from global variables
    if request.method == 'POST':
        symptoms_query = request.form['query']
        # star_query = request.form['starring']
        # mintime_query = request.form['mintime']

        # cyc add
        introduction_query = request.form['introduction']
        # country_query = request.form['country']
        causes_query = request.form['causes']
        treatment_query = request.form['treatment']
        # time_query = request.form['time']
        # categories_query = request.form['categories']
        text_select = request.form['freetext_select']
        print text_select
        #
        # if len(mintime_query) is 0:
        #     mintime = 0
        # else:
        #     mintime = int(mintime_query)
        # maxtime_query = request.form['maxtime']
        # if len(maxtime_query) is 0:
        #     maxtime = 99999
        # else:
        #     maxtime = int(maxtime_query)

        # update global variable template date
        tmp_symptoms = symptoms_query

        # tmp_star = star_query
        #
        # tmp_min = mintime
        # tmp_max = maxtime

        # cyc add
        tmp_introduction = introduction_query
        # tmp_country = country_query
        tmp_causes = causes_query
        tmp_treatment = treatment_query
        # tmp_time = time_query
        # tmp_categories = categories_query


    else:
        symptoms_query = tmp_symptoms
        # star_query = tmp_star

        # cyc add
        introduction_query = tmp_introduction
        # country_query = tmp_country
        causes_query = tmp_causes
        treatment_query = tmp_treatment
        # time_query = tmp_time
        # categories_query = tmp_categories

        # mintime = tmp_min
        # if tmp_min > 0:
        #     mintime_query = tmp_min
        # else:
        #     mintime_query = ""
        # maxtime = tmp_max
        # if tmp_max < 99999:
        #     maxtime_query = tmp_max
        # else:
        #     maxtime_query = ""

    # store query values to display in search box while browsing
    shows = {}
    shows['symptoms'] = symptoms_query

    # show_star = ""
    # if len(star_query) > 0:
    #     star_query = star_query.split(",")
    #     for star in star_query:
    #         show_star += star + ","
    #     show_star = show_star[:len(show_star) - 1]
    #
    # shows['star'] = show_star
    # shows['maxtime'] = maxtime_query
    # shows['mintime'] = mintime_query

    # cyc add
    shows['introduction'] = introduction_query
    # shows['country'] = country_query
    shows['causes'] = causes_query
    shows['treatment'] = treatment_query
    # shows['time'] = time_query
    # shows['categories'] = categories_query

    # search
    # cyc add
    mDisease = Disease()
    s = mDisease.search()

    # print "runtime" + str(mintime) + " " + str(maxtime)
    # # search for tuntime
    # s = search.query('range', runtime={'gte':mintime, 'lte':maxtime})



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

            # s = s.query(q1)
            # s = s.query('multi_match', query=str_text_query, type='cross_fields', fields=['title', 'text'], operator='and')

        print "phrases:" + str(phrase_text_query)
        for phrase in phrase_text_query:
            print "phrase=" + phrase
            if q == None:
                q = Q("match_phrase", symptoms = phrase) | Q("match_phrase", name = phrase)
            else:
                q |= Q("match_phrase", symptoms = phrase) | Q("match_phrase", name = phrase)

            # s = s.query('multi_match', query=phrase, type='cross_fields', fields=['title', 'text'], operator='and')
            # s = s.query('multi_match', query=phrase, type='cross_fields', fields=['title', 'text'], operator='and')
        s = s.query(q)


    # search for matching stars
    # You should support multiple values (list)
    # TODO: starring as list and by last first name
    # if len(star_query) > 0:
    #     for star in star_query:
    #         s = s.query('match', starring=star)

    # cyc add
    if len(introduction_query) > 0:
        s = s.query('match', introuduction=introduction_query)
    # if len(country_query) > 0:
    #     s = s.query('match', country=country_query)

    if len(causes_query) > 0:
        s = s.query('match', causes=causes_query)
    if len(treatment_query) > 0:
        s = s.query('match', treatment=treatment_query)
    # if len(time_query) > 0:
    #     int_time = int(time_query)
    #     s = s.query('match', time=int_time)
    # if len(categories_query) > 0:
    #     s = s.query('match', categories=categories_query)





    # highlight
    s = s.highlight_options(pre_tags='<mark>', post_tags='</mark>')
    s = s.highlight('symptoms', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('name', fragment_size=999999999, number_of_fragments=1)
    # cyc add
    # s = s.highlight('starring', fragment_size=999999999, number_of_fragments=1)
    # s = s.highlight('runtime', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('causes', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('introduction', fragment_size=999999999, number_of_fragments=1)
    # s = s.highlight('country', fragment_size=999999999, number_of_fragments=1)
    s = s.highlight('treatment', fragment_size=999999999, number_of_fragments=1)
    # s = s.highlight('categories', fragment_size=999999999, number_of_fragments=1)
    # s = s.highlight('time', fragment_size=999999999, number_of_fragments=1)

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
            print "highlight"
            if 'name' in hit.meta.highlight:
                result['name'] = hit.meta.highlight.name[0]
            else:
                result['name'] = hit.name
            if 'symptoms' in hit.meta.highlight:
                result['symptoms'] = hit.meta.highlight.symptoms[0]
            else:
                result['symptoms'] = hit.symptoms

            # cyc add
            # if 'starring' in hit.meta.highlight:
            #     result['starring'] = hit.meta.highlight.starring[0]
            # else:
            #     result['starring'] = hit.starring
            if 'introduction' in hit.meta.highlight:
                result['introduction'] = hit.meta.highlight.introduction[0]
            else:
                result['introduction'] = hit.introduction
            # if 'country' in hit.meta.highlight:
            #     result['country'] = hit.meta.highlight.country[0]
            # else:
            #     result['country'] = hit.country
            if 'treatment' in hit.meta.highlight:
                print "treatment highlight"
                result['treatment'] = hit.meta.highlight.treatment[0]
            else:
                print "treatment highlight no"
                result['treatment'] = hit.treatment
            # if 'time' in hit.meta.highlight:
            #     result['time'] = hit.meta.highlight.time[0]
            # else:
            #     result['time'] = hit.time
            # if 'runtime' in hit.meta.highlight:
            #     result['runtime'] = hit.meta.highlight.runtime[0]
            # else:
            #     result['runtime'] = hit.runtime
            # if 'categories' in hit.meta.highlight:
            #     result['categories'] = hit.meta.highlight.categories[0]
            # else:
            #     result['categories'] = hit.categories
            if 'causes' in hit.meta.highlight:
                result['causes'] = hit.meta.highlight.causes[0]
            else:
                result['causes'] = hit.causes

        else:
            result['name'] = hit.name
            result['symptoms'] = hit.symptoms
            # cyc add
            # result['starring'] = hit.starring
            result['introduction'] = hit.introduction
            # result['country'] = hit.country
            result['causes'] = hit.causes
            result['treatment'] = hit.treatment
            # result['time'] = hit.time
            # result['categories'] = hit.categories
            # result['runtime'] = hit.runtime


        resultList[hit.meta.id] = result


    # resultList = OrderedDict(sorted(resultList.iteritems(), key=lambda x: x[1]['score'],reverse=True))
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
        # if len(star_query) > 0:
        #     print str(star_query)
        #     print str(len(star_query))

            # message.append('Cannot find star: '+str(star_query))
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
    for term in disease:
        if type(disease[term]) is AttrList:
            s = "\n"
            for item in disease[term]:
                s += item + ",\n "
            disease[term] = s


    mDisease = Disease()

    # disease['runtime'] = str(filmdic['runtime']) + " min"
    return render_template('page_targetArticle.html', disease=disease, name=diseaseName, intro=diseaseIntro, symp=diseaseSymp,
                           causes=diseaseCauses, treat=diseaseTreat)


def text_search(str_text_query,phrase_text_query,q):
    mDisease = Disease()
    s = mDisease.search()
    if len(str_text_query) > 0:
        print "str_text_query=" + str_text_query
        if text_select == "Conjunctive":
            q = Q('multi_match', query = str_text_query, type='cross_fields', fields=['name', 'symptoms'], operator='and')
        else :
            q = Q("match", name = str_text_query) | Q('match', symptoms = str_text_query)

            # s = s.query(q1)
            # s = s.query('multi_match', query=str_text_query, type='cross_fields', fields=['title', 'text'], operator='and')

    print "phrases:" + str(phrase_text_query)
    for phrase in phrase_text_query:
        print "phrase=" + phrase
        if q is None:
            q = Q("match_phrase", name = phrase) | Q("match_phrase", symptoms = phrase)
        else:
            q |= Q("match_phrase", name = phrase) | Q("match_phrase", symptoms = phrase)

        # s = s.query('multi_match', query=phrase, type='cross_fields', fields=['title', 'text'], operator='and')
        # s = s.query('multi_match', query=phrase, type='cross_fields', fields=['title', 'text'], operator='and')

    start = 0
    end = 10
    s = s.query(q)
    q = None
    # execute search
    response = s[start:end].execute()
    if response.hits.total == 0:
        print "response is 0"
        return False
    else: return True


if __name__ == "__main__":
    app.run()

