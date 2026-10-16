from django.urls import path
from . import views



urlpatterns = [
    path('',views.index,name='home'),
    path('index/', views.home, name='index'),
    path('academic',views.academic,name='academic'),
    path('admission',views.admission,name='admission'),
    path('campus',views.campuslife,name='campuslife'),
    path('student',views.student , name='studentcorner'),
    path('placements',views.placements , name='placements'),
    path('singup',views.singup,name='singup'),
    path('login',views.login,name='login'),
    path('logout',views.logout,name='logout'),
    path('about',views.about,name='about'),
    path('campus.html',views.campuslife,name='campuslife'),
    
    path('googled61072f71b08753c.html',views.verification, name='googled61072f71b08753c'),
]
