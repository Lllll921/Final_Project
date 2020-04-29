from bs4 import BeautifulSoup
import requests
import time
import json
import sqlite3
import re
from selenium import webdriver
from flask import Flask, render_template,request
import plotly.graph_objs as go 

CACHE_FILE_NAME = 'cache.crawl'
FIRST_ENTER = 0

def insert_data_to_database(state_statistics):
    conn = sqlite3.connect("COVID-19.sqlite")
    cur = conn.cursor()
    drop_statistics = '''
        DROP TABLE IF EXISTS "Statistics";
    '''
    create_statistics = '''
    CREATE TABLE IF NOT EXISTS "Statistics" (
        "Location"	TEXT,
        "Total_Cases"	INTEGER,
        "New_Cases"	 INTEGER,
        "Total_Deaths"	INTEGER,
        "New_Deaths"	INTEGER,
        "Active_Cases"  INTEGER,
        "Total_Tests" INTEGER
    )
    '''
    cur.execute(drop_statistics)
    cur.execute(create_statistics)
    insert_instructors = '''
            INSERT INTO Statistics 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
    for statistics in state_statistics:
        cur.execute(insert_instructors, statistics)
    conn.commit()


def insert_testing_data_into_database(testing_statistics):
    conn = sqlite3.connect("COVID-19.sqlite")
    cur = conn.cursor()
    drop_statistics = '''
        DROP TABLE IF EXISTS "Testing_Statistics";
    '''
    create_statistics = '''
    CREATE TABLE IF NOT EXISTS "Testing_Statistics" (
        "Location"	TEXT,
        "Total_Cases/M_pop"	INTEGER,
        "Deaths/M_pop"	INTEGER,
        "Tests/M_pop"    INTEGER,
        "Fatality"       INTEGER
    )
    '''
    cur.execute(drop_statistics)
    cur.execute(create_statistics)
    insert_instructors = '''
            INSERT INTO Testing_Statistics 
            VALUES (?, ?, ?, ?, ?)
        '''
    for testing in testing_statistics:
       cur.execute(insert_instructors, testing)

    conn.commit()

def get_news():
    CACHE_DICT = load_cache()
    #browser=webdriver.Chrome()
    base_url = "https://news.1point3acres.com/"
    #browser.get(base_url)
    response = make_url_request_using_cache(base_url, CACHE_DICT)
    soup = BeautifulSoup(response, "html.parser")
    news = soup.find(id = "news")
    news_list = news.find_all(class_ = "jsx-2729180582 new")
    total_list = []
        
    for i in news_list:
        date = i.find(class_ = "jsx-2729180582 relative").text
        title = i.find(class_ = "jsx-2729180582 title")
        news_url = title['href']
        title = title.text[6:]
        text_list = i.find_all(class_ = "jsx-2729180582")
        main_text = text_list[len(text_list)-1].text
        news_tuple = (date, title, news_url, main_text)
        total_list.append(news_tuple)
    return total_list
    

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        browser=webdriver.Chrome()
        response =  browser.get(url)
        cache[url] = browser.page_source
        save_cache(cache)
        return cache[url]

def get_statistics():
    location_list = []
    confirmed_list = []
    new_cases_list = []
    death_list = []
    new_death_list = []
    active_cases_list = []
    total_tests_list = []
    state_statistics = []
    ratio_statistics = []

    base_url = "https://www.worldometers.info/coronavirus/country/us/"

    browser=webdriver.Chrome()
    browser.get(base_url)
    time.sleep(1)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    table = soup.find(class_ = "table table-bordered table-hover table-responsive usa_table_countries dataTable no-footer")

    rows = table.find_all(attrs={"class": re.compile(r"odd|even" )})
    for i in rows:
        stats = i.find_all('td')
        for j in range(0,10):
            if(j == 0):
                state_name = stats[j].text
                state_name = state_name.replace('\n','')
                state_name = state_name.rstrip()
                #print("Locations: " + state_name)
                location_list.append(state_name)
            if(j == 1):
                state_confirmed = stats[j].text
                state_confirmed = state_confirmed.replace(',', '')
                #print("Total Cases: " + state_confirmed)
                confirmed_list.append(state_confirmed)
            if(j == 2):
                state_new_confirmed = stats[j].text.replace('\n','')
                state_new_confirmed = state_new_confirmed.replace(',','')
                state_new_confirmed = state_new_confirmed.replace('+','')
                state_new_confirmed = state_new_confirmed.replace(' ','')
                if(state_new_confirmed == ""):
                    state_new_confirmed = 0
                new_cases_list.append(state_new_confirmed)
            if(j == 3):
                state_death = stats[j].text
                state_death = state_death.replace(',', '')
                #print("Total Deaths: " + state_death)
                death_list.append(state_death)
            if(j == 4):
                state_new_death = stats[j].text.replace(',','')
                state_new_death = state_new_death.replace('+','')
                state_new_death = state_new_death.replace(' ','')
                if(state_new_death == ""):
                    state_new_death = 0
                new_death_list.append(state_new_death)
            if(j == 5):
                state_active = stats[j].text.replace('\n','')
                state_active = state_active.replace(',','')
                #print("Active Cases: " + state_active)
                active_cases_list.append(state_active)    
            if(j == 6):
                total_1M_pop = stats[j].text.replace(',','')
            if(j == 7):
                deaths_1M_pop = stats[j].text.replace(',','')
            if(j == 8):
                state_total_test = stats[j].text.replace('\n','')
                state_total_test = state_total_test.replace(',','')
                #print("Total Tests: " + state_total_test)
                total_tests_list.append(state_total_test)
            if(j == 9):
                tests_1M_pop = stats[j].text.replace(',','')
            else:   
                continue
            fatality = round(int(state_death)/int(state_confirmed), 2)
        
        global FIRST_ENTER
        FIRST_ENTER = 1
        state_statistics.append([state_name, state_confirmed, state_new_confirmed ,state_death, state_new_death, state_active, state_total_test])
        ratio_statistics.append([state_name, total_1M_pop, deaths_1M_pop, tests_1M_pop, fatality])
        insert_data_to_database(state_statistics)
        insert_testing_data_into_database(ratio_statistics)
        


def get_plot_result_from_DB(choice):
    conn = sqlite3.connect('COVID-19.sqlite')
    cur = conn.cursor()
    q = '''
        SELECT Location, {choice} FROM Statistics 
        ORDER BY {choice} DESC
    '''.format(choice = choice)
    results = cur.execute(q).fetchall()
    conn.close()
    return results

def get_result_from_DB(location):
    conn = sqlite3.connect('COVID-19.sqlite')
    cur = conn.cursor()
    q = '''
        SELECT t.Location, Total_Cases, New_Cases, Total_Deaths, New_Deaths, Active_Cases, [Total_Cases/M_pop], [Deaths/M_pop], Total_Tests, [Tests/M_pop], Fatality FROM Statistics AS s
        JOIN Testing_Statistics AS t
        ON s.Location = t.Location
        WHERE s.Location = "{name}"    
    '''.format(name = location)
    results = cur.execute(q).fetchall()
    conn.close()
    return results

def get_all_results_from_DB():
    conn = sqlite3.connect('COVID-19.sqlite')
    cur = conn.cursor()
    q = '''
    SELECT *
    FROM Statistics AS s
    JOIN Testing_Statistics AS t
    ON s.Location = t.Location
    '''
    results = cur.execute(q).fetchall()
    conn.close()
    return results


def show_statistic_plot(list1, list2):
    xvals = list1[1:11]

    yvals = list2[1:11]
    bar_data = go.Bar(x = xvals, y = yvals)
    basic_layout = go.Layout(title="COVID-19 Statistics")
    fig = go.Figure(data = bar_data, layout = basic_layout)
    fig.show()

def get_world_statistics():
    print("a")


app = Flask(__name__)


@app.route("/news")
def index():
    news_list = get_news()
    return render_template('news.html', news_list = news_list)


@app.route("/statistics", methods=['POST'])
def statistics():
    choice = request.form['info_choice']
    isPlot = request.form['isPlot']
    if(choice == 'Statistics'):
        if(isPlot == "Yes"):
            list1 = []
            list2 = []
            second_choice = request.form['dir']
            num = request.form['number']
            if(int(num) > 50 or int(num) < 0):
                num = 50
            results = get_plot_result_from_DB(second_choice)
            for i in results:
                list1.append(i[0])
                list2.append(i[1])
            xvals = list1[1:int(num)+1]
            yvals = list2[1:int(num)+1]
            bar_data = go.Bar(x = xvals, y = yvals)
            basic_layout = go.Layout(title="COVID-19 Statistics")
            fig = go.Figure(data = bar_data, layout = basic_layout)
            div = fig.to_html(full_html=False)
            print(type(div))
            return render_template("plot.html", plot_div=div)
        else:
            results = get_all_results_from_DB()
            return render_template("statistics.html", results = results)
    if(choice == 'States'):
        state = request.form['state']
        results = get_result_from_DB(state)
        return render_template("state_form.html", results = results)

    else:
        news_list = get_news()
        return render_template('news.html', news_list = news_list)

@app.route("/")
def homepage(): 
    if(FIRST_ENTER == 0):
        get_statistics()
    return render_template('homepage.html')

if __name__ == "__main__":
   
    app.run(debug=True)
    
    

            

        
        












    
    






