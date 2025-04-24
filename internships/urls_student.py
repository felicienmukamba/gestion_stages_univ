# gestion_stages_univ/internships/urls_student.py

from django.urls import path
from . import views # Importez vos vues définies dans internships/views.py

urlpatterns = [
    # Tableau de bord Étudiant
    # Cette vue affiche le résumé du stage de l'étudiant connecté
    path('tableau-de-bord/', views.tableau_de_bord_etudiant, name='tableau_de_bord_etudiant'),

    # --- Proposition de Stage ---
    # URL pour le formulaire de proposition d'entreprises par l'étudiant
    path('proposer-entreprises/', views.formulaire_proposition_etudiant, name='proposer_entreprises_etudiant'),

    # Ajoutez ici d'autres URLs spécifiques à l'étudiant si nécessaire
    # Par exemple : voir les détails de l'entreprise validée, voir le profil de l'encadreur affecté, etc.
]