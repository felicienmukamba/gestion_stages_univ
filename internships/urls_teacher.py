# gestion_stages_univ/internships/urls_teacher.py

from django.urls import path
from . import views # Importez vos vues définies dans internships/views.py

urlpatterns = [
    # Tableau de bord Enseignant
    # Cette vue peut afficher un résumé ou rediriger vers la liste des stages encadrés
    path('tableau-de-bord/', views.tableau_de_bord_enseignant, name='tableau_de_bord_enseignant'),

    # --- Gestion des Stages Encadrés par cet Enseignant ---
    # Vue listant spécifiquement les stages où l'enseignant connecté est l'encadreur
    path('stages-encadres/', views.liste_stages_encadres, name='liste_stages_encadres'),
    # URL pour le formulaire de notation d'un étudiant via modale (identifié par l'ID du stage)
    path('noter-etudiant/<int:pk>/', views.formulaire_notation_modal, name='noter_etudiant_modal'),

    # Ajoutez ici d'autres URLs spécifiques à l'enseignant si nécessaire
    # Par exemple : voir le profil d'un étudiant, voir les détails d'une entreprise, etc.
]