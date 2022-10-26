from django.urls import include, re_path
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from quality_control.admin import admin_site
admin.autodiscover()

urlpatterns = [
                   re_path(r'^admin/', admin.site.urls),
                   re_path(r'^admin2/', admin_site.urls),
                   re_path('', include('videoclases.urls')),
                   re_path(r'^api/', include('quality_control.urls')),
                   #re_path('accounts/', include('django.contrib.auth.urls')),
            ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
