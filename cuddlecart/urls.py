from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView

from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy

urlpatterns = [
    path('admin/', RedirectView.as_view(url='/admin/overview/', permanent=False)),
    path('django-admin/', admin.site.urls),  # Django's built-in admin (superuser tools)

    # Global Password Reset routes (prevents NoReverseMatch from Django's default auth templates)
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='shop/password_reset.html',
        email_template_name='shop/password_reset_email.html',
        subject_template_name='shop/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='shop/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='shop/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='shop/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('', include('shop.urls')),          # CuddleCart app (customer + custom admin dashboard)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
