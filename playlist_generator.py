import requests
import json
from bs4 import BeautifulSoup
import config

def get_synonyms(keyword):
    """
        Returns a list of synonyms for a given 'keyword' by
        webscraping Thesaurus.com
    """
    soup = get_syn_page(keyword)
    syns = extract_syn(soup)
    return syns

def get_syn_page(keyword):
    """
        (Helper function)
        Requests the appropriate page from thesaurus.com
        and parses it with BeautifulSoup.
        Returns the soup object.
    """
    formatted_keyword = '%20'.join(keyword.split())  # if more than 1 word, add %20 between
    print(f"keyword(s): {keyword}")
    
    thes_url = "https://www.thesaurus.com/browse/" + formatted_keyword
    print(f"url: {thes_url}")
    res = requests.get(thes_url)
    print(res)
    print()
    
    # page not found
    if res.status_code == 404:
        print(f"There was a problem getting the page for keyword(s): '{keyword}'.")
        return -1
    
    data = res.text
    soup = BeautifulSoup(data, 'lxml')
    return soup

def extract_syn(soup):
    """
        (Helper function)
        Returns a list of synonyms, given soup object.
    """
    syns = []
    if soup == -1:  # no page found for original keyword
        return -1
    
    main_div = (soup.find("div", {"id": "meanings"}))
    # get synonyms in the href attribute of <a> tag
    # formatted as, e.g., /browse/cheerful or /browse/flying%20high
    for a in main_div.find_all('a', href=True):
        if a.text: 
            tag = a['href']
            syn = tag.split('/')[-1]

            # convert all the hex numbers to ASCII
            hexs = []  # get all hex numbers in the string, including the '%'
            for i, e in enumerate(syn):
                if e == "%":
                    hexs.append(syn[i:i+3])
            for e in hexs:
                num = e[1:]
                bytes_obj = bytes.fromhex(num)  # convert hex to bytes object
                ascii_str = bytes_obj.decode('ASCII')  # convert bytes object to ASCII representation
                syn = syn.replace(e, ascii_str, 1)

            syns.append(syn)

    return syns

def get_songlist(word, n):
    """
        Returns a list of n song items with 'word' in the track and/or album title
        using Spotify API.
    """
    songlist = []  # each element is: [<song title>, <album>, <artist>, <duration>]


    CLIENT_ID = config.CLIENT_ID
    CLIENT_SECRET = config.CLIENT_SECRET  # can be reset whenever
    
    AUTH_URL = 'https://accounts.spotify.com/api/token'
    # POST
    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    # convert the response to JSON
    auth_response_data = auth_response.json()

    # save the access token
    access_token = auth_response_data['access_token']

    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    # base URL of all Spotify API endpoints
    BASE_URL = 'https://api.spotify.com/v1/'

    # NOTE for keyword matching:
    # Matching of search keywords is not case-sensitive
    # Unless surrounded by double quotation marks, keywords are matched in any order
        # For example: q=roadhouse&20blues matches both “Blues Roadhouse” and “Roadhouse of the Blues”
        #         q="roadhouse&20blues" matches “My Roadhouse Blues” but not “Roadhouse of the Blues”
    keyword = word
    qry = '"' + '%20'.join(keyword.split(" ")) + '"'  # format keyword correctly
    params = {
        'q': qry,
        'type': 'track',  # valid types are: album, artist, playlist, track, show, episode
        'limit': n  # default is 20
    }

    r = requests.get(BASE_URL + 'search/', 
                    headers=headers,
                    params=params)
    # error check to make sure status code is 200
    if r.status_code != 200:
        raise Exception("Error: status code is not 200 :(")

    data = r.json()
    # print(data)
    items = data['tracks']['items']

    for item in items:
        songitem = {}
        title = item['name']
        album = item['album']['name']
        artist = item['artists'][0]['name']
        embed_url = 'https://open.spotify.com/embed/track/' + item['id']
        
        import time
        duration_ms = item['duration_ms']  # in ms
        number_of_seconds = duration_ms / 1000
        duration = time.strftime("%M:%S", time.gmtime(number_of_seconds))  # in s

        # print("******************************")
        # print(f"{title} -- {artist} ")
        # print(f"ALBUM: {album}")
        # print(f"{duration} min(s)")
        # print()

        songlist.append([word, title, album, artist, duration, embed_url])
    
    if songlist == []:  # no songs found
        return -1

    return songlist

def get_playlist(syns, n):
    """
        Returns final playlist of length n
        by shuffling synonym list, syns, when this function is called.
    """
    n = int(n)
    import random
    random.shuffle(syns)
    print("*******************************")
    print(syns)

    playlist = []
    # add one song from each syn to playlist
    for syn in syns:
        if len(playlist) == n:
            break
        song = get_songlist(syn, 1)
        print(song)
        playlist += song

    # if still not enough songs in playlist (ran out of syns), 
    # fill the rest of playlist with songs that have the keyword
    if len(playlist) < n:
        rem = n - len(playlist)
        rem_songlist = get_songlist(keyword, rem)
        playlist += rem_songlist

    return playlist
