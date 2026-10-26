from django.urls import path
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PYQViewSet

 
router = DefaultRouter()
router.register(r'pyqs', PYQViewSet, basename='pyq')


urlpatterns = [
    path('api/', include(router.urls)),
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
    path('About',views.about,name='about'),
    path('campus.html',views.campuslife,name='campuslife'),
    
    path("pyqs/", views.pyq_page, name="pyq-page"),
    
    path('googled61072f71b08753c.html',views.verification, name='googled61072f71b08753c'),
    path('verify-student/', views.company_student_verification, name='company_student_verification'),
]
