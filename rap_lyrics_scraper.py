import sys
from os.path import exists
import os.path
from os import makedirs
from datetime import datetime, timedelta
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

# DISCLAIMER: The use of scraped lyrics from azlyrics.com for any commercial purposes is strictly prohibited.
# I do not condone the use of my script for any commercial applications.
# This script was made purely for playing around with some Natural Language Processing on Rap Lyrics.
# All lyrics generated are solely owned by azlyrics.com


### TODO: Package project into a pip install worthy project, with the whole subdirectory structure and files. 

HEADER = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "referer": "https://www.google.com/",
}

ROOT_URL = "https://www.azlyrics.com"


def get_artist_page(artist_name):
    """Takes an artist name, each name seperated by a space, ex: Kendrick Lamar
    Returns the azlyrics.com page for that artist."""
    url = (
        ROOT_URL
        + "/"
        + artist_name.lower()[0]
        + "/"
        + artist_name.lower().replace(" ", "")
        + ".html"
    )
    return requests.get(url, headers=HEADER)


def get_song_urls(page):
    """Takes an artists page, returned by a get command, and parses all the song links, names, and album it is from.
    Returns album names, song names, and song urls as three seperate lists"""
    soup = BeautifulSoup(page.content, "html.parser")
    artist_div = soup.find(id="listAlbum")
    divs = artist_div.find_all("div")
    album_names = []
    song_names = []
    song_urls = []
    for div in divs:
        try:
            if div["class"][0] == "album":
                current_album = div.text
            elif div["class"][0] == "listalbum-item":
                album_names.append(current_album)
                song_names.append(div.text)
                song_urls.append(div.find("a")["href"])
            else:
                print("UNKNOWN TYPE:    " + div.text)
        except KeyError:
            pass
    return album_names, song_names, song_urls


def create_database(album_names, song_names, song_urls, artist_name):
    """Takes in the three lists returned by get_song_urls to create and return a dataframe containing those values."""
    song_url_df = pd.DataFrame(columns=["album_name", "song_name", "song_urls"])
    filename = artist_name.lower().replace(" ", "_") + ".csv"
    song_url_df["album_name"] = album_names
    song_url_df["song_name"] = song_names
    song_url_df["song_urls"] = song_urls
    song_url_df.to_csv(filename)
    return song_url_df


def get_lyrics(url):
    """Takes in a single url then finds and returns the section of the website containing the lyrics."""
    page = requests.get(url, headers=HEADER)
    soup = BeautifulSoup(page.content, "html.parser")
    lyrics = soup.find("div", {"class": "", "id": ""})
    return lyrics.decode_contents()


def save_lyrics(song_lyrics, song_url):
    """Takes in the song lyrics returned by get_lyrics along with the url for those lyrics to save the lyrics in a directory of the same path as the songs url. No return."""
    if song_url.startswith("h"):
        filepath = "." + song_url.replace(ROOT_URL, "")[:-5] + ".txt"
    else:
        filepath = song_url
    try:
        with open(filepath, "w+", encoding="utf-8") as file:
            file.write(song_lyrics)
    except FileNotFoundError:
        path, _ = os.path.split(filepath)
        makedirs(path)
        with open(filepath, "w+", encoding="utf-8") as file:
            file.write(song_lyrics)


def generate_corpus(song_urls):
    """Takes a list of song urls then loops through each, getting the lyrics and saving them. The function contains a time.sleep in order to appear less bot-like."""
    for url in song_urls:
        print(url + " lyrics are being extracted and saved")
        if ROOT_URL in url:
            save_lyrics(get_lyrics(url), url)
        else:
            song_url = ROOT_URL + url
            save_lyrics(get_lyrics(song_url), song_url)
        time.sleep(3)


if __name__ == "__main__":
    """Generates a corpus containing all of an artists lyrics, with the artists name being a command line argument wrapped in quotation marks.
    Note that it will only generate lyrics for the first 100 songs, then the user must open azlyrics.com and complete a single captcha before modifying the list slicing at line 125 to continue to the next 100 song lyrics.
    Failure to do so will result in being banned by the website for being a robot."""
    artist_name = sys.argv[1]
    filepath = artist_name.lower().replace(" ", "_") + ".csv"
    time_since_mod = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))
    if exists(filepath) and (time_since_mod < timedelta(days=365)):
        artist_dataframe = pd.read_csv(filepath)
    else:
        page = get_artist_page(artist_name)
        album_names, song_names, song_urls = get_song_urls(page)
        artist_dataframe = create_database(
            album_names, song_names, song_urls, artist_name
        )
    generate_corpus(list(artist_dataframe["song_urls"][0:100]))
