import os
import random
import requests
import re
import lyricsgenius
from page_requests.models import SongModel, ArtistModel

GENIUS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
HEADERS = {"Authorization": f"Bearer {GENIUS_TOKEN}"}

genius = lyricsgenius.Genius(
    GENIUS_TOKEN,
    skip_non_songs=True,
    excluded_terms=["(Remix)", "(Live)", "(Acoustic)"],
    remove_section_headers=True,
    timeout=15
)

COMMON_WORDS = [
    "love", "baby", "time", "day", "night", "dream", "life", "death", "world",
    "light", "dark", "fire", "sky", "rain", "dance", "smile", "cry", "sweet", "eyes",
    "baby", "kiss", "cheek", "hand", "soul", "stay", "forever", "alone", "high", "low"
        ]

def get_all_songs_and_artist (artist_name):
    try:
        search_response = requests.get(
            "https://api.genius.com/search",
            params={"q": artist_name},
            headers=HEADERS
        )
        data = search_response.json()
        hits = (data.get("response") or {}).get("hits") or []

        if hits:
            actual_name = hits[0]["result"]["primary_artist"]["name"].strip()
        else:
            actual_name = artist_name.strip()
            
        existing_artist = ArtistModel.objects.filter(name__iexact=actual_name).first()
        if existing_artist and existing_artist.songs.exists():
            print(f"Using cached data for {existing_artist.name}")
            all_titles = [song.title for song in existing_artist.songs.all()]
            return (all_titles, existing_artist.name)

        artist = genius.search_artist(artist_name, max_songs=10, get_full_info=False)
        if not artist or not artist.songs:
            print(f"No songs found for {artist_name}")
            return (None, None)
        
        actual_name = artist.name.strip()
        artist_object, created = ArtistModel.objects.get_or_create(name=actual_name)
        
        songs_data = {}
        
        for song in artist.songs:
            title_lower = song.title.lower()
            blocked = ["live", "acoustic", "remix", "version", "demo", "instrumental", "concert" ]
            
            skip = False
            for word in blocked:
                if word in title_lower:
                    skip = True
                    print(f"Skipping: {song.title}")
                    break
            if skip:
                continue
                
            if song.title and song.lyrics:
                SongModel.objects.get_or_create(artist=artist_object, title=song.title.strip(), defaults={"lyrics": song.lyrics.strip()})
                
                songs_data[song.title] = song.lyrics
        
        all_titles = list(songs_data.keys())
        
        print(f"{len(all_titles)} songs for {artist_object.name}")
            
        return (all_titles, artist.name)

    except Exception as e:
        print(f"Error fetching songs for {artist_name}: {e}")
        return (None, None)

    
def get_random_song_by_artist(all_songs):
    try:
        random_song = random.choice(all_songs)
        return random_song
    except Exception as e:
        print(f"Error getting song: {e}")
        return None

    
def get_lyrics(artist, title):
    try:
        artist_object = ArtistModel.objects.filter(name=artist).first()
        if not artist_object:
            print(f"Artist not found: {artist}")
            return None
        
        song = SongModel.objects.filter(artist=artist_object, title=title).first()
        if song:
            print(f"Loaded lyrics from cache ({artist} - {title})")
            return song.lyrics
                
    except Exception as e:
        print(f"Error getting lyrics: {e}")
    return None
    
    
def get_decoy_words(count=3, length=5, lyric_line=None):
    decoys = random.sample(COMMON_WORDS, count)
    if lyric_line:
        words = re.findall(r"\b[a-zA-Z]{4,}\b", lyric_line.lower())
        if words:
            word = random.sample(words, min(2, len(words)))
            try:
                response = requests.get(f"https://api.datamuse.com/words?ml={word}&max={count}")
                if response.status_code == 200:
                    decoys = [w["word"] for w in response.json()]
            except Exception:
                pass
    return decoys[:count]


def get_related_words(word, max_results=3):
    try:
        response = requests.get(f"https://api.datamuse.com/words?ml={word}&max={max_results}")
        if response.status_code == 200:
            return [w["word"] for w in response.json()]
    except Exception:
        pass
    return []


#def get_random_line_snippet(lyrics, word_count=10):
#    lines = []
#    for line in lyrics.split("\n"):
#        stripped_line = line.strip()
#        if stripped_line != "":
#            lines.append(stripped_line)
#
#    if not lines:
#        all_words = lyrics.replace("\n", " ").split()
#        return all_words[:word_count]
#
#    valid_indices = []
#    for i in range(len(lines)):
#        line_words = lines[i].split()
#        if len(line_words) >= 3 and len(line_words) <= 16:
#            valid_indices.append(i)
#
#    if not valid_indices:
#        for i in range(len(lines)):
#            valid_indices.append(i)
#
#    start_index = random.choice(valid_indices)
#
#    words = []
#    current_index = start_index
#    while len(words) < word_count and current_index < len(lines):
#        current_line_words = lines[current_index].split()
#        for word in current_line_words:
#            words.append(word)
#        current_index += 1
#    if len(words) > 16:
#        words = words[:word_count]
#
#    decoy_words = get_decoy_words(count=3, lyric_line=" ".join(words))
#
#    all_words = words + decoy_words
#
#    random.shuffle(all_words)
#
#    return all_words


def get_snippet_pair(lyrics: str, word_count: int = 6 , decoy_count: int = 3):
    print(f"word_count:{word_count}, decoy_count:{decoy_count}")
    lines = [ln.strip() for ln in lyrics.split("\n")]
    
    if not lines:
        lines = [lyrics.strip()]
    
    index = random.randint(0, len(lines) - 1)
    
    chosen_line = lines[index]
    
    cleaned_line = re.sub(r"\([^)]*\)", " ", chosen_line.lower())
    normalized_line = re.sub(r"[^\w\s'’]", " ", cleaned_line)
    normalized_line = re.sub(r"\s+", " ", normalized_line).strip()
    
    words = normalized_line.split()
    
    next_index = index + 1
    while len(words) < word_count:
        if next_index < len(lines):
            next_line = re.sub(r"\([^)]*\)", " ", lines[next_index].lower())
            next_line = re.sub(r"[^\w\s'’]", " ", next_line)
            next_line = re.sub(r"\s+", " ", next_line).strip()
            words += next_line.split()
            next_index += 1
        else:
            index = random.randint(0, len(lines) - 1)
    
            chosen_line = lines[index]
    
            cleaned_line = re.sub(r"\([^)]*\)", " ", chosen_line.lower())
            normalized_line = re.sub(r"[^\w\s'’]", " ", cleaned_line)
            normalized_line = re.sub(r"\s+", " ", normalized_line).strip()
            
            words = normalized_line.split()
            next_index = index + 1
            
        
#    if len(words) > word_count + 3:
#        start_index = random.randint(0, len(words) - word_count)
#        words = words[start_index:start_index + word_count]
        
    print(f"words:{words}")
    
    try:
        decoys = get_decoy_words(count=decoy_count, lyric_line=normalized_line)
    except NameError:
        decoys = []
        
    # puzzle_words = list(words) + list(decoys)
    # random.shuffle(puzzle_words)
    return [words, decoys, index, next_index-1]


def get_song_hints(artist_name: str, song_title: str, difficulty: str, index_start: int, index_end: int):
    auto = ""
    hint = ""
  
    try:

        r = requests.get("https://api.genius.com/search", params={"q": f"{song_title} {artist_name}"}, headers=HEADERS)
        hits = (r.json().get("response") or {}).get("hits") or []
        if not hits:
            return {"title": song_title, "album": None}
        song_id = hits[0]["result"]["id"]
        d = requests.get(f"https://api.genius.com/songs/{song_id}", headers=HEADERS)

        s = (d.json().get("response") or {}).get("song") or {}

        album = (s.get("album") or {}).get("name")

        title = s.get("title") or song_title

        album = re.sub(r"[:\(\[\{].*?[\)\]\}]", "", album or "").strip()
        title = re.sub(r"[:\(\[\{].*?[\)\]\}]", "", title or "").strip()
        if difficulty == "Easy":
            auto = {"title": title, "album": album}
            hint = ["", ""]
            
            lyrics = get_lyrics(artist_name, song_title)
            
            lines = [ln.strip() for ln in lyrics.split("\n") if len(ln.strip().split()) >= 3]
            if not lines:
                lines = [lyrics.strip()]
        
            if index_start - 1 >= 0:
                line_before = lines[index_start-1]

                cleaned_line_before = re.sub(r"\([^)]*\)", " ", line_before.lower())
                
                normalized_line_before = re.sub(r"[^\w\s'’]", " ", cleaned_line_before)
                normalized_line_before = re.sub(r"\s+", " ", normalized_line_before).strip()
                hint[0] = normalized_line_before

                
            if index_end + 1 < len(lines):
                line_after = lines[index_end+1]
                cleaned_line_after = re.sub(r"\([^)]*\)", " ", line_after.lower())
                normalized_line_after = re.sub(r"[^\w\s'’]", " ", cleaned_line_after)
                normalized_line_after = re.sub(r"\s+", " ", normalized_line_after).strip()
                hint[1] = normalized_line_after
            return {"auto": auto, "hint": hint}

        else:
            print("title and album")
            hint = {"title": title, "album": album}
            return {"hint": hint}
    except Exception:
        return {"title": song_title, "album": None}
