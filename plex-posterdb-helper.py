import requests
import sys
import os.path
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from plexapi.server import PlexServer

def plex_setup():
    if os.path.exists("config.json"):
        try:
            config = json.load(open("config.json"))
            base_url = config["base_url"]
            token = config["token"]
            tv_library = config["tv_library"]
            movie_library = config["movie_library"]    
        except:
            sys.exit("Error with config.json file. Please consult the readme.md.") 
        
        plex = PlexServer(base_url, token)
        tv = plex.library.section('TV Shows')
        movies = plex.library.section('Movies')
        return tv, movies
    else:
        sys.exit("No config.json file found. Please consult the readme.md.") 
      

def cook_soup(url):  
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        sys.exit(f"Failed to retrieve the page. Status code: {response.status_code}")
        

def scrape_posters(url):
    movieposters = []
    showposters = []
    
    if ("theposterdb.com" in url) and ("set" in url):
        soup = cook_soup(url)
    else:
        sys.exit("Poster set not found. Check the link you are inputting.")
    
    # find the poster grid
    poster_div = soup.find('div', class_='row d-flex flex-wrap m-0 w-100 mx-n1 mt-n1')

    # find all poster divs
    posters = poster_div.find_all('div', class_='col-6 col-lg-2 p-1')

    # loop through the poster divs
    for poster in posters:
        # get if poster is for a show or movie
        media_type = poster.find('a', class_="text-white", attrs={'data-toggle': 'tooltip', 'data-placement': 'top'})['title']
        # get high resolution poster image
        overlay_div = poster.find('div', class_='overlay')
        poster_id = overlay_div.get('data-poster-id')
        poster_url = "https://theposterdb.com/api/assets/" + poster_id
        # get metadata
        title_p = poster.find('p', class_='p-0 mb-1 text-break').string

        if media_type == "Show":
            title = title_p.split(" (")[0]                   
            if " - " in title_p:
                split_season = title_p.split(" - ")[1]
            else:
                split_season = "Cover"
            
            showposter = {}
            showposter["title"] = title
            showposter["url"] = poster_url
            showposter["season"] = split_season
            showposters.append(showposter)

        if media_type == "Movie":
            splitstring = title_p.split(" (")
            title = splitstring[0]
            year = splitstring[1].split(")")[0]
            movieposter = {}
            movieposter["title"] = title
            movieposter["url"] = poster_url
            movieposter["year"] = int(year)
            movieposters.append(movieposter)
    
    return movieposters, showposters

  
def set_posters(url, tv, movies):
    movieposters, showposters = scrape_posters(url)
    for movie in movieposters:
        try:
            plex_movie = movies.get(movie["title"], year=movie["year"])
            plex_movie.uploadPoster(movie["url"])
            print(f'Uploaded art for {movie["title"]}.')
        except:
            print(f"{movie['title']} not found in Plex library.")

    for show in showposters:
        # loop through show seasons
        try:
            tv_show = tv.get(show["title"])
            if show["season"] == "Cover":
                try:
                    tv_show.uploadPoster(url=show['url'])
                    print(f"Uploading cover art for {show['title']}.")
                except:
                    print(f"{show['title']} not found, skipping.")
            elif show["season"] == "Special":
                try:
                    specials_season = tv_show.season("Specials")
                    specials_season.uploadPoster(url=show['url'])
                    print(f"Uploading cover art for {show['title']} - Specials.")
                except:
                    print(f"{show['title']} - {show['season']} not found, skipping.")
            else:
                try:
                    season = tv_show.season(show["season"])
                    season.uploadPoster(url=show['url'])
                    print(f"Uploading cover art for {show['title']} - Season {show['season']}.")
                except:
                    print(f"{show['title']} - Season {show['season']} not found, skipping.")
        except:
            if show["season"] == "Cover":
                print(f"{show['title']} not found, skipping.")
            elif show["season"] == "Special":
                print(f"Uploading cover art for {show['title']} - Specials.")
            else:
                print(f"{show['title']} - {show['season']} not found, skipping.")


if __name__ == "__main__":
    tv, movies = plex_setup()
    
    while True:
        user_input = input("Enter theposterdb set url (type 'stop' to end): ")
        
        if user_input.lower() == 'stop':
            print("Stopping...")
            break

        set_posters(user_input, tv, movies)