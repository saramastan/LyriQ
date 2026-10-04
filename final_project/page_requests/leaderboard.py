from django.shortcuts import render
from page_requests.models import HighscoreModel
from django.db.models import Max, Sum, Count
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def page_response(request):
    # Get filter parameters
    selected_artist = request.GET.get('artist', '')
    selected_difficulty = request.GET.get('difficulty', '')
    
    # Get all unique artists and difficulties for filters
    all_artists = HighscoreModel.objects.values_list('artist', flat=True).distinct().order_by('artist')
    all_difficulties = HighscoreModel.objects.values_list('difficulty', flat=True).distinct().order_by('difficulty')
    
    # Base queryset
    highscores = HighscoreModel.objects.select_related('user').all()
    
    # Apply filters
    if selected_artist:
        highscores = highscores.filter(artist=selected_artist)
    if selected_difficulty:
        highscores = highscores.filter(difficulty=selected_difficulty)
    
    # Get top scores (ordered by highscore descending)
    top_scores = highscores.order_by('-highscore')[:50]
    
    # Get user statistics
    user_stats = None
    if request.user.is_authenticated:
        user_highscores = HighscoreModel.objects.filter(user=request.user)
        if selected_artist:
            user_highscores = user_highscores.filter(artist=selected_artist)
        if selected_difficulty:
            user_highscores = user_highscores.filter(difficulty=selected_difficulty)
            
        user_stats = {
            'total_games': user_highscores.count(),
            'highest_score': user_highscores.aggregate(Max('highscore'))['highscore__max'] or 0,
            'total_points': user_highscores.aggregate(Sum('highscore'))['highscore__sum'] or 0,
        }
    
    context = {
        'top_scores': top_scores,
        'user_stats': user_stats,
        'all_artists': all_artists,
        'all_difficulties': all_difficulties,
        'selected_artist': selected_artist,
        'selected_difficulty': selected_difficulty,
    }
    
    return render(request, 'leaderboard.html', context)