import re
import networkx as nx
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import collections
from imdb_helper_functions import url_to_soup_converter, get_name


def get_actors_by_movie_soup(cast_page_soup, num_of_actors_limit=None):
    try:
        my_soup = cast_page_soup.find_all('table',attrs={'class': 'cast_list'})[0].find_all('a',{'href': re.compile(r'/name/*')}) #Get actors
    except:
        return [] #In rare cases it can fail, if nothing can be found, therefore an empty list ist returned

    my_list = []

    url_base="https://imdb.com" #Base URL without www, because there are two variants possible and it is easier to replace www by "", than adding www.

    for actor in my_soup:
        if not actor.img:
            my_list.append((actor.contents[0].strip(),url_base+actor.attrs['href']))

        if len(my_list)==num_of_actors_limit:
            return my_list

    return my_list


def get_movies_by_actor_soup(actor_page_soup, num_of_movies_limit=None):
    try:
        my_soup = actor_page_soup.find("div",attrs={"class": "filmo-category-section"}).find_all('a',{'href': re.compile(r'/title/\w+/')}) #Get movies
    except:
        return [] #In rare cases it can fail, if nothing can be found, therefore an empty list ist returned

    my_list = []

    url_base="https://imdb.com" #Base URL without www, because there are two variants possible and it is easier to replace www by "", than adding www.


    for title in my_soup:
        try:
            if title.find_parent("b").next_sibling == "\n": #All exceptions realease date > Today, Post-production, Short movies or whatever have not \n, only full released movies have "\n"
                my_list.append((title.contents[0],url_base+title.attrs['href']))
        except:
            pass

        if len(my_list)==num_of_movies_limit:
            return my_list

    return my_list


def get_movie_distance(actor_start_url, actor_end_url,num_of_actors_limit=None, num_of_movies_limit=None):

    #Sanitize URLS, so that they work for "www" inside and without "www" inside
    actor_start_url = (actor_start_url[0],actor_start_url[1].replace(r"www.",""))
    actor_end_url = (actor_end_url[0],actor_end_url[1].replace(r"www.",""))

    try:
        dic = ""
        with open(r'dict_actors.txt','r') as f: #read from dict, if no dict exists, it will fail and be skipped
            for i in f.readlines():
                dic+=i #string
        dict_actors = eval(dic) # this is orignal dict with instace dict
    except:
        dict_actors = dict()
    
    try:
        dic = ""
        with open(r'dict_movies.txt','r') as f: #read from dict, if no dict exists, it will fail and be skipped
            for i in f.readlines():
                dic+=i #string
        dict_movies = eval(dic) # this is orignal dict with instace dict
    except:
        dict_movies = dict()

    movies = list()
    actors = list()

    # Loop 1
    if actor_start_url in dict_actors:
        movies = dict_actors.get(actor_start_url).copy() #Without copy(), there is a pointer on movies
        # print("read from dict")
    else:
        dict_actors[actor_start_url]= get_movies_by_actor_soup(url_to_soup_converter(actor_start_url[1]),num_of_movies_limit=num_of_movies_limit) #Use already implemented function
        movies = dict_actors.get(actor_start_url).copy() #Without copy(), there is a pointer on movies
        # print("dict entry added")

        with open('dict_actors.txt',"w") as f: #Write actors to dict, if it doesn't exist create new file dict_actors.txt
            f.write(str(dict_actors))
            # print("write to dict")
    
    for movie in movies:
        if movie in dict_movies:
            add_actors = dict_movies.get(movie)
            # print("read from dict")
        else:
            add_actors = get_actors_by_movie_soup(url_to_soup_converter(movie[1]+"fullcredits"),num_of_actors_limit=num_of_actors_limit) #Use already implemented function
            dict_movies[movie] = add_actors
            # print("dict entry added")

        actors += add_actors
        
    with open('dict_movies.txt',"w") as f: #Write movies to dict, if it doesn't exist create new file dict_movies.txt
        f.write(str(dict_movies))
        # print("write to dict")
        
    current_distance = 1 #Start with 1, it cannot be 0

    if actor_end_url in actors: #Check if there is a connection
        return current_distance #Success, Found connection
    else:
        current_distance += 1 #Otherwise Loop
        # print("Loop")
    
    # Loop 2 & 3
    while current_distance <= 3: #Maximum 3 Loops, Limitation according to instruction to prevent endless loop

        for actor in actors:
            if actor in dict_actors:
                add_movies = dict_actors.get(actor)
                # print("read movies from actor")
            else:
                add_movies = get_movies_by_actor_soup(url_to_soup_converter(actor[1]),num_of_movies_limit=num_of_movies_limit) #Use already implemented function
                dict_actors[actor] = add_movies
                # print("add movies to actor")
                
            movies += add_movies

        with open('dict_actors.txt',"w") as f:
            f.write(str(dict_actors))
            # print("write to dict")
            
        movies = list(set(movies)) # make list of movies unique

        for movie in movies:
            if movie in dict_movies:
                add_actors = dict_movies.get(movie)
                # print("read actor from dict")
            else:
                add_actors = get_actors_by_movie_soup(url_to_soup_converter(movie[1]+"fullcredits"),num_of_actors_limit=num_of_actors_limit) #Use already implemented function
                dict_movies[movie] = add_actors
                # print("dict actors to movie")

            actors += add_actors
        
        with open('dict_movies.txt',"w") as f:
            f.write(str(dict_movies))
            # print("write to dict")

        actors = set(actors) # make list of actors unique

        if actor_end_url in actors: #Check if there is a connection
            return current_distance #Success, Found connection
        else:
            actors = list(actors) # make list of actors unique
            current_distance += 1 #Otherwise Loop
            # print("Loop")

    return None
            
    

def get_movie_descriptions_by_actor_soup(actor_page_soup):
    movies = get_movies_by_actor_soup(actor_page_soup)
    dict_actor_mov_descr = dict()
    for movie in movies:
        try:
            movie_page = url_to_soup_converter(movie[1])
            movie_description = movie_page.find("span", attrs={'role':'presentation', 'data-testid':'plot-xl'}).contents[0]
            dict_actor_mov_descr[movie] = movie_description
        except:
            pass

    return dict_actor_mov_descr

"""
# Final Project Week 1
#Some header settings to get everything in english, with US IP
headers = {'Accept-Language': 'en',
           'X-FORWARDED-FOR': '2.21.184.0'}


# Reuqest Male actor
male_actor_page = 'https://www.imdb.com/name/nm0695435/'
male = requests.get(male_actor_page, headers=headers)

# Request Female actor
female_actor_page = 'https://www.imdb.com/name/nm0397171/'
female = requests.get(female_actor_page, headers=headers)

# Request Movie
movie_page = "https://www.imdb.com/title/tt0411008/fullcredits"
movie = requests.get(movie_page, headers=headers)

# Soup objects
male_soup = BeautifulSoup(male.text,features="html.parser")
female_soup = BeautifulSoup(female.text,features="html.parser")
movie_soup = BeautifulSoup(movie.text,features="html.parser")

# Get return values, list of values
male_movies = get_movies_by_actor_soup(male_soup,num_of_movies_limit=10)
female_movies = get_movies_by_actor_soup(female_soup,num_of_movies_limit=10)
movie = get_actors_by_movie_soup(movie_soup, num_of_actors_limit=10)

# Results week 10
print(*male_movies,sep = "\n")
print("\n")
print(*female_movies,sep = "\n")
print("\n")
print(*movie,sep = "\n")
"""

"""
# Final Project Week 2

# List of Tuples as start
best_paid_actors=[
    "https://www.imdb.com/name/nm0425005/", #Dwayne Johnson
    "https://www.imdb.com/name/nm0000375/", #Robert Downey Jr.
    "https://www.imdb.com/name/nm1165110/", #Chris Hemsworth
    "https://www.imdb.com/name/nm4289673/", #Akshay Kumar
    "https://www.imdb.com/name/nm0000329/", #Jackie Chan
    "https://www.imdb.com/name/nm0177896/", #Bradley Cooper
    "https://www.imdb.com/name/nm0001191/", #Adam Sandler
    "https://www.imdb.com/name/nm0424060/", #Scarlett Johansson
    "https://www.imdb.com/name/nm0005527/", #Sofía Vergara
    "https://www.imdb.com/name/nm0262635/" #Chris Evans
]


# Does dict_network already exist? If yes, take it from saved .txt-File
try:
    dic = ""
    with open(r'dict_network.txt','r') as f:
        for i in f.readlines():
            dic+=i #string
    dict_network = eval(dic) # this is orignal dict with instace dict
except:
    dict_network = dict()


for i in range(len(best_paid_actors)-1):
    for j in range(i+1,len(best_paid_actors)):
        
        actor_start = get_name(best_paid_actors[i])
        actor_end = get_name(best_paid_actors[j])
        edge = (actor_start,actor_end)
        distance = None

        if edge not in dict_network:
            distance = get_movie_distance(best_paid_actors[i], best_paid_actors[j],num_of_actors_limit=5, num_of_movies_limit=5)
            dict_network[edge] = distance
        else:
            distance = dict_network[edge]

        print(f'{actor_start} -- {distance} -- {actor_end}')

with open(r'dict_network.txt',"w") as f:
    f.write(str(dict_network))
"""

"""
# Final Project Week 3

# List of Tuples as start
best_paid_actors=[
    ("Dwayne Johnson","https://www.imdb.com/name/nm0425005/"), #Dwayne Johnson
    ("Robert Downey Jr.","https://www.imdb.com/name/nm0000375/"), #Robert Downey Jr.
    ("Chris Hemsworth","https://www.imdb.com/name/nm1165110/"), #Chris Hemsworth
    ("Akshay Kumar","https://www.imdb.com/name/nm4289673/"), #Akshay Kumar
    ("Jackie Chan","https://www.imdb.com/name/nm0000329/"), #Jackie Chan
    ("Bradley Cooper","https://www.imdb.com/name/nm0177896/"), #Bradley Cooper
    ("Adam Sandler","https://www.imdb.com/name/nm0001191/"), #Adam Sandler
    ("Scarlett Johansson","https://www.imdb.com/name/nm0424060/"), #Scarlett Johansson
    ("Sofía Vergara","https://www.imdb.com/name/nm0005527/"), #Sofía Vergara
    ("Chris Evans","https://www.imdb.com/name/nm0262635/") #Chris Evans
]

for actor in best_paid_actors:
    try:
        dic = ""
        with open(f'dict_{actor[0]}_mov_descr.txt','r') as f:
            for i in f.readlines():
                dic+=i #string
        dict_actor_mov_descr = eval(dic) # this is orignal dict with instace dict
    except:
        my_soup = url_to_soup_converter(actor[1])
        dict_actor_mov_descr = get_movie_descriptions_by_actor_soup(my_soup) #Dictionary of movie descriptions of an actor
        with open(f'dict_{actor[0]}_mov_descr.txt',"w") as f:
            f.write(str(dict_actor_mov_descr))

    unwanted_chars = ".,-_"

    words = []
    for raw_words in dict_actor_mov_descr.values():
        for raw_word in raw_words.split(" "):
            words.append(raw_word.strip(unwanted_chars))

    wordfreq = collections.Counter(words)

    print(wordfreq)
"""
