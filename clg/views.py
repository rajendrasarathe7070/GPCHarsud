from django.shortcuts import render , HttpResponse ,redirect
import requests
# Create your views here.
def home(request):
  return HttpResponse("hellow asdf")
    # return render(request,'index.html')

