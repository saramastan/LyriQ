from datetime import datetime
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User

class SessionModel(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
  fallback_id = models.TextField(null=True, blank=True)
  max_lives = models.FloatField(null=False, blank=False, default=0)
  curr_lives = models.FloatField(null=False, blank=False, default=0)
  max_hints = models.FloatField(null=False, blank=False, default=0)
  curr_hints = models.FloatField(null=False, blank=False, default=0)
  hint_stage = models.FloatField(null=False, blank=False, default=0)
  max_tries = models.FloatField(null=False, blank=False, default=0)
  curr_tries = models.FloatField(null=False, blank=False, default=0)
  score = models.FloatField(null=False, blank=False, default=0)
  artist = models.TextField(null=False, blank=False, default="")
  all_songs = ArrayField(models.TextField(null=False, blank=False, default=""))
  difficulty_name = models.TextField(null=False, blank=False, default="") #'Easy', 'Medium', 'Hard', 'Custom'
  point_multiplier = models.FloatField(null=False, blank=False, default=0)
  min_lyric_words = models.FloatField(null=False, blank=False, default=0)
  max_lyric_words = models.FloatField(null=False, blank=False, default=0)
  min_decoy_words = models.FloatField(null=False, blank=False, default=0)
  max_decoy_words = models.FloatField(null=False, blank=False, default=0)
  answer_words = ArrayField(models.TextField(null=False, blank=False, default=""))
  puzzle_words = ArrayField(models.TextField(null=False, blank=False, default=""))
  bottom_words = ArrayField(models.TextField(null=False, blank=False, default=""))
  dropbox_words = ArrayField(models.TextField(null=False, blank=False, default=""))
  prev_guess = models.TextField(null=False, blank=False, default="")
  song_title = models.TextField(null=False, blank=False, default="")
  song_album = models.TextField(null=False, blank=False, default="")
  lyric_index_start = models.IntegerField(null=False, blank=False, default=0)
  lyric_index_end = models.IntegerField(null=False, blank=False, default=0)

  hint_before = models.TextField(blank=True, null=True)
  hint_after = models.TextField(blank=True, null=True)


class HighscoreModel(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  highscore = models.FloatField(null=False, blank=False, default=0)
  artist = models.TextField(null=False, blank=False, default="")
  difficulty = models.TextField(null=False, blank=False, default="") #'Easy', 'Medium', 'Hard', 'Custom'

        
class ArtistModel(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class SongModel(models.Model):
    artist = models.ForeignKey(ArtistModel, on_delete=models.CASCADE, related_name="songs")
    title = models.CharField(max_length=200)
    lyrics = models.TextField()

    class Meta:
        unique_together = ('artist', 'title')

    def __str__(self):
        return f"{self.artist.name} - {self.title}"
