from django.shortcuts import render

def page_response(request):
  return render(request, 'home.html')
