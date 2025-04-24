# gestion_stages_univ/internships/urls_faculty.py

from django.urls import path
from . import views # Importez vos vues ici

urlpatterns = [
    # Tableau de bord Facultaire
    path('tableau-de-bord/', views.tableau_de_bord_facultaire, name='tableau_de_bord_facultaire'),

    # --- Gestion des Enseignants ---
    path('enseignants/', views.liste_enseignants_facultaire, name='liste_enseignants_facultaire'),
    path('enseignants/ajouter/', views.enseignant_form_modal, name='ajouter_enseignant_modal'),
    path('enseignants/modifier/<int:pk>/', views.enseignant_form_modal, name='modifier_enseignant_modal'),
    path('enseignants/supprimer/<int:pk>/', views.enseignant_delete_modal, name='supprimer_enseignant_modal'),

    # --- Gestion des Étudiants ---
    # URLs pour la gestion des Étudiants (avec modales)
    path('etudiants/', views.liste_etudiants_facultaire, name='liste_etudiants_facultaire'),
    path('etudiants/ajouter/', views.etudiant_form_modal, name='ajouter_etudiant_modal'),
    path('etudiants/modifier/<int:pk>/', views.etudiant_form_modal, name='modifier_etudiant_modal'),
    path('etudiants/supprimer/<int:pk>/', views.etudiant_delete_modal, name='supprimer_etudiant_modal'),

    # --- Gestion des Entreprises ---
    path('entreprises/', views.liste_entreprises_facultaire, name='liste_entreprises_facultaire'),
    path('entreprises/ajouter/', views.entreprise_form_modal, name='ajouter_entreprise_modal'),
    path('entreprises/modifier/<int:pk>/', views.entreprise_form_modal, name='modifier_entreprise_modal'),
    path('entreprises/supprimer/<int:pk>/', views.entreprise_delete_modal, name='supprimer_entreprise_modal'),

    # --- Gestion des Stages ---
    # Ajouter ici plus tard les URLs pour les stages (visualisation, validation, affectation)...
    path('proposer-entreprises/', views.formulaire_proposition_etudiant, name='proposer_entreprises_etudiant'),

    path('stages/', views.liste_stages_facultaire, name='liste_stages_facultaire'), # Vue pour lister tous les stages
    path('stages/valider-affecter/<int:pk>/', views.valider_affecter_stage_modal, name='valider_affecter_stage_modal'), # Modale pour validation/affectation

    # Vue listant les stages que cet enseignant encadre (peut être le tableau de bord lui-même ou une page séparée)
    path('stages-encadres/', views.liste_stages_encadres, name='liste_stages_encadres'),
    # URL pour le formulaire de notation de l'étudiant via modale
    path('noter-etudiant/<int:pk>/', views.formulaire_notation_modal, name='noter_etudiant_modal'),

    # --- Rapports ---
    path('rapport-affectations-pdf/', views.generate_student_supervisor_pdf_report, name='rapport_affectations_pdf'),

]