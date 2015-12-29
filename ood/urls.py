from django.contrib.auth import views as auth_views
from django.conf.urls import include, url
from django.contrib import admin

from ood import settings, views


urlpatterns = [
    url(r'^login/$', auth_views.login, {
        'extra_context': {
            'plus_id': settings.SOCIAL_AUTH_GOOGLE_PLUS_KEY,
        },
        'template_name': 'login.html'
    }, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^$', views.main, name='main'),
    url(r'^wakeup/([0-9]+)/$', views.wakeup, name='wakeup'),
    url(r'^shutdown/([0-9]+)/$', views.shutdown, name='shutdown'),
    url(r'^processing_start/([0-9]+)/$', views.processing_start,
        name='processing_start'),
    url(r'^processing_stop/([0-9]+)/$', views.processing_stop,
        name='processing_stop'),
    url(r'^admin/', include(admin.site.urls)),
]
