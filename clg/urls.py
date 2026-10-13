"""
URL configuration for clg project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include
from clg import views
from two_factor.urls import urlpatterns as tf_urls
from django.conf import settings
from django.conf.urls.static import static




# admin.site.__class__ = OTPAdminSite
admin.site.site_header = "Govt. Polytechnic Collage Harsud "
# 1. Ek alag aur safe custom class banayein jo OTPAdminSite ko extend kare
 
urlpatterns = [
    
    path("admin/", admin.site.urls),
    # path('' ,views.home ,name="home"),
    path('', include(tf_urls)),
    path('',include('core.urls')),
    # path('admission/',include('core.urls'),name="admission"),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

