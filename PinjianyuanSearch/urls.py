"""PinjianyuanSearch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from Mysearch import views
from Mysearch.views import SearchSuggest, SearchView, Facet, Gaoji
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


# from django.contrib import admin


urlpatterns = [
    # url(r'^admin/', admin.site.urls),

    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^index.html$', TemplateView.as_view(template_name='index.html'), name='index'),
    # url(r'^index.html$', TemplateView.as_view(template_name='index.html'), name='index'),

    url(r'^suggest/$', SearchSuggest.as_view(), name="suggest"),
    url(r'^search/$', SearchView.as_view(), name="search"),
    #分面搜索
    url(r'^facet/$', Facet, name="facet"),
    path('facet_menu/', views.facet_menu, name="facet_menu"),
    #高级搜索
    url(r'^gaoji/$', Gaoji, name="gaoji"),
    path('base/', views.base, name="base"),

]

urlpatterns += staticfiles_urlpatterns()