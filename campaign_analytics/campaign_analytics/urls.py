"""
URL configuration for campaign_analytics project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import home, admin_dashboard, manager_dashboard, client_dashboard, unauthorized, predict_view, download_report, custom_logout, custom_login 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/manager/', manager_dashboard, name='manager_dashboard'),
    path('dashboard/client/', client_dashboard, name='client_dashboard'),
    path('predict/', predict_view, name='predict'),
    path('predict/download/', download_report, name='download_report'),
    path('unauthorized/', unauthorized, name='unauthorized'),
]