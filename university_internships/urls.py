# university_internships/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView # Pour la redirection de la page d'accueil
from django.contrib.auth import views as auth_views # Importer les vues d'auth intégrées
from internships import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('dashboard/', views.home_dashboard, name='home_dashboard'),


    # URLs d'authentification intégrées de Django
    path('comptes/connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('comptes/deconnexion/', auth_views.LogoutView.as_view(), name='logout'),

    # URLs de réinitialisation de mot de passe (assurez-vous de configurer l'envoi d'emails dans settings.py)
    path('comptes/reinitialiser-mdp/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('comptes/reinitialiser-mdp/fait/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('comptes/reinitialiser-mdp/confirmer/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('comptes/reinitialiser-mdp/complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

     # URLs de changement de mot de passe (après connexion)
    path('comptes/changer-mdp/',
         auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
         name='password_change'),
    path('comptes/changer-mdp/fait/',
         auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
         name='password_change_done'),


    # Inclure les URLs de votre application internships (vous les définirez plus tard)
    # Nous allons les structurer par rôle
    path('facultaire/', include('internships.urls_faculty')),
    path('enseignant/', include('internships.urls_teacher')),
    path('etudiant/', include('internships.urls_student')),


    # Redirection de la racine vers la page de connexion ou le tableau de bord par défaut après connexion
    path('', RedirectView.as_view(pattern_name='login'), name='home'), # Redirige la racine vers la connexion

    # Ajoutez ici d'autres URLs si nécessaire
]