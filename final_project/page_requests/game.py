import random
from django.shortcuts import render, redirect
from django.http import JsonResponse

from page_requests.models import HighscoreModel, SessionModel
from .forms import ArtistForm
from .api.genius_api import (
    get_song_hints,
    get_random_song_by_artist,
    get_lyrics,
    get_all_songs_and_artist,
    get_snippet_pair
)
import re, uuid

def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("🀄"," ")
    # text = re.sub(r"[^a-z0-9'\s]", " ", text)
    # text = re.sub(r"\s+", " ", text)
    return text.strip()  # <-- FIX: actually return stripped text

def _reset_run(ps: SessionModel):
    """Reset the current run without destroying the SessionModel."""
    difficulty = ps.difficulty_name
    if difficulty == "Custom":

        ps.curr_lives = ps.max_lives
        ps.curr_hints = ps.max_hints
        ps.curr_tries = ps.max_tries
    else:
        stats = DIFFICULTY_STATS.get(ps.difficulty_name, DIFFICULTY_STATS["Easy"])
        ps.curr_lives = stats.get("max_lives", 3)
        ps.curr_hints = stats.get("max_hints", 3)
        ps.curr_tries = stats.get("max_tries", 3)
    
    ps.score = 0
    ps.hint_stage = 0
    
    ps.answer_words = []
    ps.puzzle_words = []
    ps.bottom_words = []
    ps.dropbox_words = []
    ps.prev_guess = ""
    
    ps.song_title = ""
    ps.song_album = ""
    ps.hint_before = None
    ps.hint_after = None
    
    ps.save()

BASE_POINTS = 1
DIFFICULTY_STATS = { "Easy":
                    {"min_lyric_words":6,
                     "max_lyric_words":10,
                     "min_decoy_words":0,
                     "max_decoy_words":0,
                     "max_lives":3,
                     "max_hints":5,
                     "max_tries":3,
                     "point_multiplier":1},

                     "Medium":
                    {"min_lyric_words":9,
                     "max_lyric_words":10,
                     "min_decoy_words":1,
                     "max_decoy_words":2,
                     "max_lives":3,
                     "max_hints":3,
                     "max_tries":2,
                     "point_multiplier":2},

                     "Hard":
                    {"min_lyric_words":12,
                     "max_lyric_words":30,
                     "min_decoy_words":0,
                     "max_decoy_words":3,
                     "max_lives":1,
                     "max_hints":3,
                     "max_tries":1,
                     "point_multiplier":5},
                     }

def page_response(request):
    form = ArtistForm()
    print(f"Request User: {request.user}")

    action = request.POST.get("action") if request.method == "POST" else None

    # GET SESSION_ID
    session = request.session
    print(f"session:{session}")
    if 'session_id' not in session:
        session_id = uuid.uuid4().hex
        session["session_id"] = session_id
        print(f"new session_id: {session_id}")
    else:
        session_id = session["session_id"]
        print(f"old session_id: {session_id}")
    session["blob"] = uuid.uuid4().hex  # don't delete this -Joey

    persistent_session = None

    if request.method == "POST":
        # START GAME ACTIONS
        if action == "start_game":
            form = ArtistForm(request.POST)
            if form.is_valid():
                artist_name = form.cleaned_data['artist']
                (all_songs, artist) = get_all_songs_and_artist(artist_name)
                if all_songs:
                    if request.user.is_authenticated:
                        persistent_session_filter = SessionModel.objects.all().filter(user=request.user)
                    else:
                        persistent_session_filter = SessionModel.objects.all().filter(fallback_id=session_id)
                    if persistent_session_filter.count() != 0:
                        persistent_session_filter.delete()

                    difficulty_name = request.POST.get("difficulty", "Easy")

                    if difficulty_name == "Custom":
                        try:
                            max_tries = int(request.POST.get("max_tries", 3))
                        except Exception: 
                            max_tries = 3
                        try:
                            max_lives = int(request.POST.get("max_lives", 3))
                        except Exception:
                            max_lives = 3
                        try:
                            max_hints = int(request.POST.get("max_hints", 3))
                        except Exception:
                            max_hints = 3

                        word_length = request.POST.get("word_length", "Medium")
                        decoys = request.POST.get("decoys", "Few")

                        if word_length == "Small":
                            min_lyric_words = 3
                            max_lyric_words = 6
                        elif word_length == "Large":
                            min_lyric_words = 10
                            max_lyric_words = 15
                        else: 
                            min_lyric_words = 6
                            max_lyric_words = 10

                        if decoys == "None":
                            min_decoy_words = 0
                            max_decoy_words = 0
                        elif decoys == "Some":
                            min_decoy_words = 2
                            max_decoy_words = 3
                        else:
                            min_decoy_words = 1
                            max_decoy_words = 2

                        DIFFICULTY_STAT = {
                            "min_lyric_words": min_lyric_words,
                            "max_lyric_words": max_lyric_words,
                            "min_decoy_words": min_decoy_words,
                            "max_decoy_words": max_decoy_words,
                            "max_lives": max_lives,
                            "max_hints": max_hints,
                            "max_tries": max_tries,
                            "point_multiplier": 1,

                        }
                    else:
                        DIFFICULTY_STAT = DIFFICULTY_STATS.get(difficulty_name, DIFFICULTY_STATS["Easy"])


                    persistent_session = SessionModel.objects.create(
                        user = request.user if request.user.is_authenticated else None,
                        fallback_id = session_id,
                        max_lives = DIFFICULTY_STAT.get("max_lives", 3),
                        curr_lives = DIFFICULTY_STAT.get("max_lives", 3),
                        max_hints = DIFFICULTY_STAT.get("max_hints", 3),
                        curr_hints = DIFFICULTY_STAT.get("max_hints", 3),
                        hint_stage = 0,
                        max_tries = DIFFICULTY_STAT.get("max_tries", 3),
                        curr_tries = DIFFICULTY_STAT.get("max_tries", 3),
                        score = 0,
                        artist = artist,
                        all_songs = all_songs,
                        difficulty_name = difficulty_name,
                        point_multiplier = DIFFICULTY_STAT.get("point_multiplier", 1),
                        min_lyric_words = DIFFICULTY_STAT.get("min_lyric_words", 10),
                        max_lyric_words = DIFFICULTY_STAT.get("max_lyric_words", 13),
                        min_decoy_words = DIFFICULTY_STAT.get("min_decoy_words", 2),
                        max_decoy_words = DIFFICULTY_STAT.get("max_decoy_words", 3),
                        answer_words = [],
                        puzzle_words = [],
                        bottom_words = [],
                        dropbox_words = [],
                        song_title = "",
                        song_album = "",
                        lyric_index_start = 0,
                        lyric_index_end = 0,
                        )
                else:
                    error_message = f"No songs found for {artist_name} [a]"
            else:
                error_message = "Please enter a valid artist name."
#                return redirect("start")

        # GET THE PERSISTENT SESSION
        if request.user.is_authenticated:
            persistent_session_filter = SessionModel.objects.all().filter(user=request.user)
        else:
            persistent_session_filter = SessionModel.objects.all().filter(fallback_id=session_id)
        if persistent_session_filter.count() == 0:
            persistent_session = None
        else:
            persistent_session = persistent_session_filter.last()

        # Handle Retry from Game Over
        if action == "reset_game" and persistent_session is not None:
            _reset_run(persistent_session)
            action = "get_snippet"   # <-- deal a new round immediately

        # IF THE USER IS NOT PLAYING SEND THEM BACK
        if persistent_session is None:
            print("No persistent_session, redirecting to home [a]")
            return render(request, "home.html")

        # GENERATE SNIPPET
        if action == "get_snippet" or action == "start_game":
            all_songs = persistent_session.all_songs
            if all_songs is None:
                (all_songs, artist) = get_all_songs_and_artist(persistent_session.artist)
                if all_songs is None:
                    all_songs = [""]

            song_title = get_random_song_by_artist(all_songs)
            if song_title is None:
                song_title = ""
            persistent_session.song_title = song_title
            persistent_session.all_songs = all_songs
            persistent_session.save()

            if persistent_session.song_title != "":
                lyrics = get_lyrics(persistent_session.artist, persistent_session.song_title)
                if lyrics:
                    # get both answer (ordered) and puzzle (shuffled + decoys)
                    [ans_ordered, decoy_words, index_start, index_end] = get_snippet_pair(lyrics, int(persistent_session.min_lyric_words), decoy_count=random.randint(int(persistent_session.min_decoy_words), int(persistent_session.max_decoy_words)))
                    
                    print(f"ans_ordered:{ans_ordered}")
                    print(f"decoy_words:{decoy_words}")
                    puz_words = list(ans_ordered)
                    number_of_words = random.randint(int(persistent_session.min_lyric_words), int(persistent_session.max_lyric_words))
                    print(f"number_of_words:{number_of_words}")
                    while len(puz_words) > number_of_words:
                        i = random.randint(0, int(len(puz_words)) - 2)
                        if i < 0 or i+1 >= len(puz_words): break
                        new_word = f"{puz_words[i]} {puz_words[i+1]}"
                        del puz_words[i+1]
                        puz_words[i] = new_word
                    puz_words = list(puz_words) + list(decoy_words)
                    random.shuffle(puz_words)
                    print(f"puz_words:{puz_words}")

                    persistent_session.lyric_index_start = index_start
                    persistent_session.lyric_index_end = index_end
                    persistent_session.answer_words = ans_ordered
                    persistent_session.puzzle_words = puz_words
                    persistent_session.bottom_words = puz_words
                    persistent_session.dropbox_words = []
                    persistent_session.prev_guess = ""
                    persistent_session.curr_tries = persistent_session.max_tries
                    persistent_session.hint_stage = 0
                    persistent_session.save()
                    print(f"answer_words:{persistent_session.answer_words}")
                    print(f"puzzle_words:{persistent_session.puzzle_words}")
                else:
                    error_message = "Couldn't fetch lyrics for that song. Try another artist."
            else:
                error_message = f"No songs found for {persistent_session.artist} [b]"
        
            hint = get_song_hints(persistent_session.artist,
            persistent_session.song_title,
            persistent_session.difficulty_name,
            persistent_session.lyric_index_start, persistent_session.lyric_index_end) or {}

            album = None
            title = None
            
            if "auto" in hint:
                album = hint["auto"].get("album")
                title = hint["auto"].get("title")
            elif "hint" in hint:
                album = hint["hint"].get("album")
                title = hint["hint"].get("title")
            else:
                album = hint.get("album")
                title = hint.get("title")

            persistent_session.song_album = album or ""
            persistent_session.song_title = title or persistent_session.song_title
            persistent_session.save()
        

            if persistent_session.difficulty_name == "Easy":
                easy_hints = hint.get("hint") if isinstance(hint.get("hint"), list) else ["", ""]
                persistent_session.hint_before = easy_hints[0] if len(easy_hints) > 0 else ""
                persistent_session.hint_after = easy_hints[1] if len(easy_hints) > 1 else ""
                persistent_session.save()
                
            else:
                persistent_session.hint_before = ""
                persistent_session.hint_after = ""
                persistent_session.save()
    
    
        
            #GET HINT
        elif action == "get_hint":
            if persistent_session.curr_hints > 0:
                if persistent_session.hint_stage == 0:
                    persistent_session.curr_hints -= 1
                    persistent_session.hint_stage += 2
                    message = "Hint Revealed!"
                    print(f"hint is {persistent_session.hint_before} and {persistent_session.hint_after} ")
                    persistent_session.save()
#                    if persistent_session.difficulty_name == "Easy":
#                        hint_data = get_song_hints(
#                            persistent_session.artist,
#                            persistent_session.song_title,
#                            persistent_session.difficulty_name,
#                            persistent_session.lyric_index
#                        ) or {}
#                        easy_hints = hint_data.get("hint") if isinstance(hint_data.get("hint"), list) else ["", ""]
#                        persistent_session.hint_before = easy_hints[0] if len(easy_hints) > 0 else ""
#                        persistent_session.hint_after = easy_hints[1] if len(easy_hints) > 1 else ""
#                    persistent_session.save()
#                        message = "Hint Revealed!"
#                    else:
#                        hint_data = get_song_hints(
#                        persistent_session.artist,
#                        persistent_session.song_title,
#                        persistent_session.difficulty_name,
#                        persistent_session.lyric_index
#                        ) or {}
#                        if "hint" in hint_data:
#                            persistent_session.song_album = hint_data["hint"].get("album") or persistent_session.song_album
#                            persistent_session.song_title = hint_data["hint"].get("title") or persistent_session.song_title
#                            message = "Hint Revealed!"
#                    persistent_session.save()

                else:
                    error_message = "Hint already used."
            else:
                error_message = "No hints remaining."

        # SUBMIT GUESS
        elif action == "guess":
            target = _normalize(" ".join(persistent_session.answer_words))

            guess_text = request.POST.get("guess", "")
            won = _normalize(persistent_session.prev_guess) == target

            persistent_session.prev_guess = guess_text
            persistent_session.save()

            print(f'guess:{persistent_session.prev_guess}\ntarget:{target}')
            print(f'normalized guess:{_normalize(persistent_session.prev_guess)}')
            if _normalize(persistent_session.prev_guess) == target and target:
                # only count as correct if there is a non-empty target
                print("guess correct")
                if not won:
                    persistent_session.score += BASE_POINTS * persistent_session.point_multiplier * persistent_session.curr_tries
                is_correct = True
                persistent_session.save()
            else:
                print("guess incorrect")
                persistent_session.curr_tries -= 1

                if persistent_session.curr_tries == 0:
                    persistent_session.curr_lives -= 1

                if persistent_session.curr_lives == 0:
                    if request.user.is_authenticated and persistent_session.score > 0:
                        highscore_filter = HighscoreModel.objects.filter(
                            user=request.user,
                            artist=persistent_session.artist,
                            difficulty=persistent_session.difficulty_name
                        )
                        if highscore_filter.count() != 0:
                            highscore_model = highscore_filter.last()
                            if highscore_model is not None:
                                highscore = highscore_model.highscore
                                if highscore < persistent_session.score:
                                    highscore_model.highscore = persistent_session.score
                                    highscore_model.save()
                        else:
                            HighscoreModel.objects.create(
                                user=request.user,
                                artist=persistent_session.artist,
                                difficulty=persistent_session.difficulty_name,
                                highscore=persistent_session.score
                            )

                persistent_session.save()

                # End Game
        elif action == "end_game":
            if request.user.is_authenticated and persistent_session.score > 0:
                highscore_filter = HighscoreModel.objects.filter(
                    user=request.user,
                    artist=persistent_session.artist,
                    difficulty=persistent_session.difficulty_name
                )

                if highscore_filter.exists():
                    highscore_model = highscore_filter.last()
                    if highscore_model.highscore < persistent_session.score:
                        highscore_model.highscore = persistent_session.score
                        highscore_model.save()
                else:
                    HighscoreModel.objects.create(
                        user=request.user,
                        artist=persistent_session.artist,
                        difficulty=persistent_session.difficulty_name,
                        highscore=persistent_session.score
                    )
            persistent_session.curr_lives = 0
            persistent_session.curr_tries = 0
#            persistent_session.answer_words = []
            persistent_session.puzzle_words = []
            persistent_session.dropbox_words = []
            persistent_session.prev_guess = ""
#            persistent_session.song_title = ""
#            persistent_session.song_album = ""
            persistent_session.hint_stage = 0
            
            persistent_session.save()

    else:  # IF THE USER GOT HERE BY REFRESHING OR BOOKMARK
        if request.user.is_authenticated:
            persistent_session_filter = SessionModel.objects.all().filter(user=request.user)
        else:
            persistent_session_filter = SessionModel.objects.all().filter(fallback_id=session_id)
        if persistent_session_filter.count() == 0:
            persistent_session = None
        else:
            persistent_session = persistent_session_filter.last()

    # RENDER PAGE
    if persistent_session is None:
        print("No persistent_session, redirecting to home [b]")
        return render(request, "home.html")

    guess_words = persistent_session.prev_guess.split("🀄")
    if guess_words.count("") != 0:
        guess_words.remove("")

    bw = request.POST.get("bottom", None)
    print(f"bottom_input:{bw}")
    if bw != None:
        bw = bw.split("🀄")
        if bw.count("") != 0:
            bw.remove("")
        persistent_session.bottom_words = bw
        persistent_session.save()

    dw = request.POST.get("guess", None)
    print(f"dropbox_input:{dw}")
    if dw != None:
        dw = dw.split("🀄")
        if dw.count("") != 0:
            dw.remove("")
        persistent_session.dropbox_words = dw
        persistent_session.save()

    # STICK WORDS TOGETHER
    if action == "guess":
        dropbox_words = []
        target = _normalize(" ".join(persistent_session.answer_words))
        target_copy = target

        # don't allow words to stick together if they are stuck together as bottom words
        for bottom_word in persistent_session.bottom_words:
            if bottom_word.count(" ") > 0:
                target_copy = target_copy.replace(bottom_word, " 🔡 ", 1)

        i = 0
        old_dropbox_word = ""
        new_dropbox_word = ""
        if len(guess_words) > 0:
            old_dropbox_word = guess_words[i]
            new_dropbox_word = guess_words[i]
        while i < len(guess_words):
            if _normalize(new_dropbox_word) in target_copy:
                old_dropbox_word = new_dropbox_word
                i += 1
                if i < len(guess_words):
                    new_dropbox_word += f' {guess_words[i]}'
                else:
                    dropbox_words.append(new_dropbox_word)
                    break
            else:
                dropbox_words.append(old_dropbox_word)
                if old_dropbox_word.count(" ") >= 1:
                    target_copy = target_copy.replace(_normalize(old_dropbox_word), " 🔡 ", 1)
                if old_dropbox_word == new_dropbox_word:
                    i += 1
                if i == len(guess_words) - 1:
                    dropbox_words.append(guess_words[i])
                    break
                elif i < len(guess_words):
                    old_dropbox_word = guess_words[i]
                    new_dropbox_word = guess_words[i]
                else:
                    old_dropbox_word = ""
                    new_dropbox_word = ""
        persistent_session.dropbox_words = dropbox_words
        persistent_session.save()

    # FINAL correctness flag (guarded so "" == "" won't trigger)
    target = _normalize(" ".join(persistent_session.answer_words))
    if 'is_correct' not in locals():
        is_correct = False
    if target and persistent_session.prev_guess:
        if _normalize(persistent_session.prev_guess) == target:
            is_correct = True

    highscore = 0
    if request.user.is_authenticated:
        highscore_filter = HighscoreModel.objects.filter(
            user=request.user,
            artist=persistent_session.artist,
            difficulty=persistent_session.difficulty_name
        )
        if highscore_filter.count() != 0:
            highscore_model = highscore_filter.last()
            if highscore_model is not None:
                highscore = highscore_model.highscore

    if 'message' not in locals():
        message = None
    if 'error_message' not in locals():
        error_message = None

    game_over = (persistent_session.curr_lives == 0)

    return render(request, "game.html", {
        "curr_hints": persistent_session.curr_hints,
        "hint_stage": int(persistent_session.hint_stage),
        "form": form,
        "song_title": persistent_session.song_title,
        "dropbox_words": persistent_session.dropbox_words,
        "bottom_words": persistent_session.bottom_words,
        "tries_left": persistent_session.curr_tries,
        "message": message,
        "error_message": error_message,
        "artist_name": persistent_session.artist,
        "album_name": persistent_session.song_album,
        "base_points" : BASE_POINTS,
        "mode_mult": persistent_session.point_multiplier,
        "tries_mult": persistent_session.curr_tries,
        "total_gained_points": BASE_POINTS * persistent_session.point_multiplier * persistent_session.curr_tries,
        "current_score": persistent_session.score,
        "lives_left": persistent_session.curr_lives,
        "is_correct": is_correct,
        "correct_lyric": _normalize(" ".join(persistent_session.answer_words)),
        "difficulty_name": persistent_session.difficulty_name,
        "highscore": highscore,
        "max_hints": int(persistent_session.max_hints),
        "max_lives": int(persistent_session.max_lives),
        "hints_filled": list(range(int(persistent_session.curr_hints))),
        "hints_empty":  list(range(max(0, int(persistent_session.max_hints) - int(persistent_session.curr_hints)))),
        "lives_filled": list(range(int(persistent_session.curr_lives))),
        "lives_empty":  list(range(max(0, int(persistent_session.max_lives) - int(persistent_session.curr_lives)))),

        "hint_before": persistent_session.hint_before,
        "hint_after": persistent_session.hint_after,
        "game_over": game_over
    })
