#################################
##### Name: Sam Stern
##### Uniqname: sternsam
#################################

from bs4 import BeautifulSoup
import requests
import json
import sqlite3
import time
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

BASE_URL = 'https://www.rottentomatoes.com/top'
COURSES_PATH = '/Desktop/507/final_project'
CACHE_FILE_NAME = 'fp_cache.json'

CACHE_DICT = {}
headers = {'User-Agent': 'UMSI 507 Course Project - Python Web Scraping','From': 'sternsams@umich.edu','Course-Info': 'https://www.si.umich.edu/programs/courses/507'}

ratings_dict = {
    1: "G", 2: "PG", 3: "PG-13", 4: "R", 5: "No Rating"
}

class Movie:
    '''a movie

    Instance Attributes
    -------------------
    name: string
        the title of the movie
    
    rating: string
        the rating of the movie

    tomatometer: int
        the percentage of reviews are 'fresh' from critic

    audience_score: int
        the percentage of audience viewers to liked the movie

    '''
    def __init__(self, name, rating, tomatometer, audience_score):
        self.name = name
        self.tomatometer = tomatometer
        self.audience_score = audience_score

        if rating == "G": self.rating=1
        elif rating == "PG": self.rating = 2
        elif rating == "PG-13": self.rating = 3
        elif rating == "R": self.rating = 4
        else: self.rating = 5

    def info(self):
        return(f"{self.name}: Tomatometer: {self.tomatometer}% | Audience Score: {self.audience_score}%")

def load_cache(cache_file):
    '''Load cache from cache file for api pull
    
    Parameters
    ---------
    None
    
    Returns
    -------
    dict
        cache if it exists, empty cache otherwise.
    '''

    try:
        cache_file = open(cache_file, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):

    
    '''Save webscraping cache in file named under var CACHE_FILE_NAME
    
    Parameters
    ---------
    cache: dictionary
        json dictionary to save in file
    
    Returns
    -------
    Nothing
    '''

    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    '''Check if cache exists, otherwises fetch data
    
    Parameters
    ---------
    url: string
        The URL for the website
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from either the cache or the fetch
    '''
    
    if (url in cache.keys()): # the url is our unique key
        # print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

def build_genre_url_dict(base_url):
    ''' Make a dictionary that maps genre name to genre page url from "https://www.rottentomatoes.com"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a genre name and value is the url
        e.g. {'black panther':'https://www.rottentomatoes.com/m/black_panther_2018', ...}
    '''

    responseDetail = make_url_request_using_cache(base_url, CACHE_DICT)

    #EDIT BELOW!!!!!
    soup = BeautifulSoup(responseDetail, 'html.parser')
    genre_list = soup.find('ul', class_='genrelist')
    genre_list = genre_list.find_all('li')

    genre_links = {}

    for item in genre_list:
        link = item.find('a').get('href')
        name = item.text.strip()
        genre_links[name.lower()] = 'https://www.rottentomatoes.com'+link

    return genre_links

def get_movie_instance(movie_url):
    '''Make an instance from a movie page URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a movie page in rottentomatoes.com
    
    Returns
    -------
    instance
        Movie instance
    '''
    #caching site url
    responseDetail = make_url_request_using_cache(movie_url, CACHE_DICT)
    soup = BeautifulSoup(responseDetail, 'html.parser')
    try:
        name = soup.find_all("h1", class_="scoreboard__title")[0].text.strip()
        name = str(name.title())
    except:
        name = 'no name'

    try:
        junk = soup.find_all(class_="scoreboard")[0]
        junk = str(junk)
        junk2 = junk.split('rating="')
        junk3 = junk2[1].split('"')
        rating = junk3[0]
    except:
        rating = 'no rating'

    try:
        junk = soup.find_all(class_="scoreboard")[0]
        junk = str(junk)
        junk2 = junk.split('tomatometerscore="')
        junk3 = junk2[1].split('"')
        tomatometer = int(junk3[0])   
    except:
        tomatometer = 0
        
    try:
        junk = soup.find_all(class_="scoreboard")[0]
        junk = str(junk)
        junk2 = junk.split('audiencescore="')
        junk3 = junk2[1].split('"')
        audience_score = int(junk3[0])    
    except:
        audience_score = 0

    return Movie(name, rating, tomatometer, audience_score)

def get_movies_for_genre(genre_url):
    '''Make a list of movie instances from a genre URL.
    
    Parameters
    ----------
    genre_url: string
        The URL for a genre in rottentomatoes.com
    
    Returns
    -------
    list
        a list of movie instances
    '''
    movie_instances = []

    responseDetail = make_url_request_using_cache(genre_url, CACHE_DICT)
    soup = BeautifulSoup(responseDetail, 'html.parser')
 
    table = soup.find('table', class_="table")
    movie_list = table.find_all('tr')

    for movie in movie_list[1:]:
        link = movie.find('a')['href']
        full_link = 'https://www.rottentomatoes.com' + link
        movie_inst = get_movie_instance(full_link)
        movie_instances.append(movie_inst)
    return movie_instances

def create_movie_table(conn):
    '''Creates movie table within the database
    
    Parameters
    ---------
    conn: SQLite connection
    
    Returns
    -------
    nothing
    '''
    cur = conn.cursor()

    drop_movies = '''
        DROP TABLE IF EXISTS "movies";
    '''
    create_movies = '''
        CREATE TABLE "movies" (
        "movie_id"	INTEGER NOT NULL UNIQUE,
        "name"	TEXT,
        "rating_id"	INTEGER,
        "tomatometer"	INTEGER,
        "audience_score"	INTEGER,
        PRIMARY KEY("movie_id" AUTOINCREMENT),
        FOREIGN KEY("rating_id") REFERENCES "ratings"("id")
    );'''



    cur.execute(drop_movies)
    cur.execute(create_movies)
    conn.commit()

def create_ratings_table(conn):
    '''Creates ratings table within the database
    
    Parameters
    ---------
    conn: SQLite connection
    
    Returns
    -------
    nothing
    '''
    
    cur = conn.cursor()
    drop_ratings = '''
        DROP TABLE IF EXISTS "ratings";
    '''
    create_ratings = '''
        CREATE TABLE "ratings" (
        "id"	INTEGER NOT NULL UNIQUE,
        "rating_name"	TEXT NOT NULL UNIQUE,
        PRIMARY KEY("id" AUTOINCREMENT)
    );'''

    cur.execute(drop_ratings)
    conn.commit()
    cur.execute(create_ratings)
    conn.commit()


    for key, val in ratings_dict.items():
        ratings_values = f'''
            INSERT INTO ratings(id, rating_name)
            VALUES({key}, "{val}");
        '''
        cur.execute(ratings_values)

    conn.commit()

def add_movie(conn, movie):
    '''adds movie instance to 'movie' table within the database.
    
    Parameters
    ---------
    conn: SQLite connection
    movie: Movie instance
    
    Returns
    -------
    nothing
    '''

    cur = conn.cursor()

    insert_movie = f'''
        INSERT INTO movies(name, rating_id, tomatometer, audience_score)
        VALUES("{movie.name}", {movie.rating}, {movie.tomatometer},{movie.audience_score})
    '''
    cur.execute(insert_movie)
    conn.commit()

def plot_user_input(vis, movie_amount, movie_rating):
    '''Plots the plotly visualizations depending on the user input
    
    Parameters
    ---------
    vis: number corresponding to the type of visualization
    movie_amount: Amount to limit the query results
    movie_rating: Movie ratings to filter the query results 
    
    Returns
    -------
    nothing
    '''

    #HISTOGRAM
    if vis == 1:
        query = f'''
            SELECT movies.tomatometer, movies.audience_score
            FROM movies JOIN ratings on movies.rating_id=ratings.id
            WHERE ratings.rating_name == "{movie_rating}"
            LIMIT {int(movie_amount)};
        '''
        cur.execute(query)
        tomato_scores = []
        audience_scores = []
        for row in cur:
            tomato_scores.append(row[0])
            audience_scores.append(row[1])

        fig = px.histogram(x=tomato_scores, labels = {'x': "Tomatometer Scores (%)", 'y': 'Count'})
        fig.show()
        fig = px.histogram(x=audience_scores, labels = {'x': "Audience Scores (%)", 'y': 'Count'})
        fig.show()

        fig = go.Figure()
        fig.add_trace(go.Histogram(x=tomato_scores, name = 'Tomatometer Scores (%)'))
        fig.add_trace(go.Histogram(x=audience_scores, name = 'Audience Scores (%)'))

        # The two histograms are drawn on top of another
        fig.update_layout(barmode='stack')
        fig.show()


    #Bar Chart
    if vis == 2:
        query = f'''
            SELECT movies.name, movies.tomatometer, movies.audience_score
            FROM movies JOIN ratings on movies.rating_id=ratings.id
            WHERE ratings.rating_name == "{movie_rating}"
            LIMIT {int(movie_amount)};
        '''
        cur.execute(query)
        scores = {'Title': [], 'Tomatometer (%)': [], 'Audience Score (%)': []}
        for row in cur:
            scores['Title'].append(row[0])
            scores['Tomatometer (%)'].append(row[1])
            scores['Audience Score (%)'].append(row[2])

        df = pd.DataFrame(data=scores)
        fig = px.bar(df, x = 'Title', y = 'Tomatometer (%)') 
        fig.show()
        fig = px.bar(df, x = 'Title', y = 'Audience Score (%)') 
        fig.show()
        fig = go.Figure(data=[
            go.Bar(name='Tomatometer', x=df['Title'], y=df['Tomatometer (%)']),
            go.Bar(name='Audience Score', x=df['Title'], y=df['Audience Score (%)'])
        ])
        # Change the bar mode
        fig.update_layout(barmode='group')
        fig.show()



if __name__ == "__main__":
    CACHE_DICT = load_cache(CACHE_FILE_NAME)
    genre_urls = build_genre_url_dict(BASE_URL)

    i = 1
    print(f"Top 100 Movie Lists")
    print("-----------------------------------------")
    for key, val in genre_urls.items():
        print(f"{i}: {key.title()}")
        i += 1
    print("-----------------------------------------")

    genre_choice = input("Please input the number of the Top 100 list you are interested in: ")

    keys_list = list(genre_urls.keys())
    value_list = list(genre_urls.values())

    genre_link = value_list[int(genre_choice)-1]

    movie_instances = get_movies_for_genre(genre_link)

    conn = sqlite3.connect("movies_rt.sqlite")
    create_movie_table(conn)
    create_ratings_table(conn)
    cur = conn.cursor()
    i=0
    for movie in movie_instances:
        add_movie(conn, movie)

    while True:
        vis = input('Which visualization would you like to see for these movies? Please 1 for histogram or 2 for bar chart: ')
        vis = int(vis)
        if vis == 1 or vis == 2:
            break
        else:
            print("Please enter a valid number.\n")
            continue
    
    while True:
        movie_amount = input("How many movies would you like to see in your visualization? (1-100): ")

        if movie_amount.isnumeric() and (int(movie_amount) > 0 and int(movie_amount)< 101):
            movie_amount = int(movie_amount)
            break
        else:
            print("Please enter a valid number.\n")
            continue

    while True:
        movie_rating = input("Which movie rating would you like to filter by? (OPTIONS: G, PG, PG-13, R): ")
        if movie_rating in ratings_dict.values():
            break
        else:
            print("Please enter a valid rating.\n")
            continue

    plot_user_input(vis, movie_amount, movie_rating)

    conn.close()