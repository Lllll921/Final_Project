from bs4 import BeautifulSoup
import requests
import time
import json
import sqlite3
from selenium import webdriver
from flask import Flask, render_template
import plotly.graph_objs as go 

CACHE_FILE_NAME = 'cache.crawl'

def insert_data_to_database(state_statistics):
    conn = sqlite3.connect("COVID-19.sqlite")
    cur = conn.cursor()
    drop_statistics = '''
        DROP TABLE IF EXISTS "Statistics";
    '''
    create_statistics = '''
    CREATE TABLE IF NOT EXISTS "Statistics" (
        "Location"	TEXT,
        "Cases"	INTEGER,
        "Deaths"	INTEGER,
        "Fatality"	INTEGER,
        "Recovered"	INTEGER
    )
    '''
    cur.execute(drop_statistics)
    cur.execute(create_statistics)
    insert_instructors = '''
            INSERT INTO Statistics 
            VALUES (?, ?, ?, ?, ?)
        '''
    cur.execute(insert_instructors, state_statistics)
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
        "Total Testing"	INTEGER,
        "Population"	INTEGER
    )
    '''
    cur.execute(drop_statistics)
    cur.execute(create_statistics)
    insert_instructors = '''
            INSERT INTO Testing_Statistics 
            VALUES (?, ?, ?)
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
    news_list = news.find_all(class_ = "jsx-2588237678 new")
    date_list = []
    title_list = []
    url_list = []
    main_text_list = []
        
    for i in news_list:
        date = i.find(class_ = "jsx-2588237678 relative").text
        title = i.find(class_ = "jsx-2588237678 title")
        news_url = title['href']
        title = title.text
        text_list = i.find_all(class_ = "jsx-2588237678")
        main_text = text_list[len(text_list)-1].text
        date_list.append(date)
        title_list.append(title)
        url_list.append(news_url)
        main_text_list.append(main_text)
        

        print(date)
        print(title)
        print(main_text)
        print(news_url)
        print("")


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
    browser=webdriver.Chrome()
    base_url = "https://coronavirus.1point3acres.com"
    browser.get(base_url)
    time.sleep(3)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    website = soup.find(class_ = "jsx-3623395659")
    table = website.find(class_ = "jsx-3301338917 state-table card")    #change
    #country_info = table.find(class_ = "jsx-2599469586 row country-row")
    state_detail = table.find_all(class_ = "jsx-3301338917 stat row")    #change
    location_list = []
    confirmed_list = []
    death_list = []
    fatality_list = []
    recovered_list = []

    for i in state_detail:
        state_info = i.find_all('span', class_ = "jsx-3301338917")    #change
        for j in range(0,5):
            if(j == 0):
                state_name = state_info[j].text
                location_list.append(state_name)
                #print("Location: ", state_name)
            if(j == 1):
                state_confirmed_change = state_info[j].find(class_ = "jsx-3323058653")
                if(state_confirmed_change == None):
                    state_confirmed_change = "+0"
                    state_confirmed = state_info[j].text
                else:
                    state_confirmed_change = state_confirmed_change.text
                    state_confirmed = state_info[j].text[len(state_confirmed_change):]
                confirmed_list.append(state_confirmed)
                state_confirmed = state_confirmed + "(" + state_confirmed_change + ")"
                #print("confirmed: ", state_confirmed)
            if(j == 2):
                state_death_change = state_info[j].find(class_ = "jsx-2274486433")
                if(state_death_change == None):
                    state_death_change = "+0"
                    state_death = state_info[j].text
                else:
                    state_death_change = state_death_change.text
                    state_death = state_info[j].text[len(state_death_change):]
                death_list.append(state_death)
                state_death = state_death + "(" +  state_death_change + ")"
                #print("Death: ", state_death)
            if(j == 3):
                state_fatality = state_info[j].text
                fatality_list.append(state_fatality)
                #print("Fatality rate: ", state_fatality)
            if(j == 4):
                state_recover_change = state_info[j].find(class_ = "jsx-2878027135")
                if(state_recover_change == None):
                    state_recover_change = "+0"
                    state_recover = state_info[j].text
                else:
                    state_recover_change = state_recover_change.text
                    state_recover = state_info[j].text[len(state_recover_change):]
                recovered_list.append(state_recover)
                state_recover = state_recover + "(" + state_recover_change + ")"
                #print("Recovered: ", state_recover)
                
                #     state_statistics = [state_name, state_confirmed, state_death, state_fatality, state_recover]
                #     insert_data_to_database(state_statistics)
    show_statistic_plot(location_list, confirmed_list)

def get_testing_statistic():
    browser=webdriver.Chrome()
    base_url = "https://coronavirus.1point3acres.com/en/test"
    browser.get(base_url)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    test_list = soup.find(class_ = "ant-table-tbody")
    testing_statistics = []
    for i in test_list:
        test_state_list = i.find_all('span', class_ = "jsx-3214873797")
        if len(test_state_list) != 0:
            state_name = test_state_list[0].text
            testing= test_state_list[2].text.split()
            testing_total = testing[0]
            population = testing[1]
            testing_statistics.append([state_name, testing_total, population])
    insert_testing_data_into_database(testing_statistics)

def show_statistic_plot(list1, list2):
    xvals = list1[0:10]

    yvals = list2[0:10]
    bar_data = go.Bar(x = xvals, y = yvals)
    #pie_data = go.Pie(labels = xvals, values = yvals)
    basic_layout = go.Layout(title="COVID-19 Statistics")
    fig = go.Figure(data = bar_data, layout = basic_layout)
    #fig = go.Figure(data = pie_data, layout = basic_layout)
    fig.show()

def get_world_statistics():
    print("a")

app = Flask(__name__)

@app.route("/")
def index():
    # return render_template('news.html', link_list = link_list)
    print("a")

if __name__ == "__main__": 

    get_news()
    
    #response = input("What kind of information you want to get: ").lower()

    #browser=webdriver.Chrome()
    #base_url = "https://coronavirus.1point3acres.com"
    #browser.get(base_url)
    #soup = BeautifulSoup(browser.page_source, "html.parser")
    #card = soup.find(class_ = "jsx-3875756938 card")
    #card_list = card.find_all('a', class_ = "jsx-3875756938")
    #card_name_list = card.find_all('span', class_ = "jsx-3875756938")
    #new_url = ""
    #for i in range(0, len(card_list)):
    #    information_choice = card_name_list[i].text.replace(' ', '')
    #    if(response == information_choice.lower()):
    #        if(card_list[i]['target'] == '_blank'):
    #            new_url = card_list[i]['href']
    #            break
    #        elif(card_list[i]['target'] == '_self'):
    #            new_url = base_url + card_list[i]['href']
    #            break

    #if(new_url == ""):
    #    print("We don't have such information")
    #else:
        

        







    #browser.get(new_url)。+
    #soup = BeautifulSoup(browser.page_source, "html.parser")
    #world_card = soup.find(class_ = "jsx-2132740580 country-table card")
    #world_data = world_card.find_all(class_ = "jsx-2132740580 row")
    #for i in world_data:
    #    #name_box = i.find('span', class_ = "jsx-2132740580 expandable-span")
    #    #if name_box != none:
    #    #    name = name_box.find('label', class_ = "jsx-2132740580").text
    #    statistic_box = i.find('span', class_ = "jsx-2132740580")
    #    for j in statistic_box:
    #        print(j)
    #        print("")


            

        
        












    
    






