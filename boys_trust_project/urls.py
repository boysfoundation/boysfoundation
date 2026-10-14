from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve
from portfolio import views
from django.urls import path, include
from django.views.generic.base import RedirectView  # <--- Make sure this line is present

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/logo.png')),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('portfolio/project/<int:pk>/', views.project_detail, name='project_detail'),
    path('donate/', views.donate, name='donate'),
    path('blood-donation/', views.blood_support, name='blood_support'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('payment-handler/', views.payment_handler, name='payment_handler'),
    path('contact/', views.contact, name='contact'),

    # Explicitly serve static and media files on production (Render)
    re_path(
        r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}
    ),
    re_path(
        r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}
    ),
]