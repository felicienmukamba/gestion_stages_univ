# gestion_stages_univ/internships/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin # Pour personnaliser l'admin du modèle User
from .models import (
    User, Faculty, Department, Promotion, Teacher, Student, Company, Internship
)
from django.utils.translation import gettext_lazy as _ # Pour la traduction dans l'admin


# --- Personnalisation de l'interface d'administration ---

# Personnalisation du modèle User
class CustomUserAdmin(UserAdmin):
    """
    Personnalise l'affichage du modèle User dans l'interface d'administration.
    """
    # Ajouter les champs de rôle personnalisés aux fieldsets existants ou en créer de nouveaux
    fieldsets = UserAdmin.fieldsets + (
        (_('Rôles Spécifiques'), {'fields': ('est_facultaire', 'est_enseignant', 'est_etudiant')}),
        # Ajoutez ici d'autres fieldsets si vous ajoutez des champs au modèle User
    )
    # Ajouter les champs de rôle à la liste d'affichage
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'est_facultaire', 'est_enseignant', 'est_etudiant')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'est_facultaire', 'est_enseignant', 'est_etudiant')
    search_fields = ('username', 'email', 'first_name', 'last_name') # Ajouter la recherche

# Enregistrer le modèle User avec sa personnalisation
admin.site.register(User, CustomUserAdmin)


# Personnalisation pour les autres modèles
class FacultyAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Faculty.
    """
    list_display = ('nom', 'code')
    search_fields = ('nom', 'code')

admin.site.register(Faculty, FacultyAdmin)


class DepartmentAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Department.
    """
    list_display = ('nom', 'code', 'faculte')
    list_filter = ('faculte',) # Ajouter un filtre par faculté
    search_fields = ('nom', 'code', 'faculte__nom') # Rechercher dans le nom du département et de la faculté

admin.site.register(Department, DepartmentAdmin)


class PromotionAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Promotion.
    """
    list_display = ('nom', 'annee_academique', 'departement', 'departement__faculte') # Afficher la faculté via le département
    list_filter = ('annee_academique', 'departement__faculte', 'departement') # Filtrer par année, faculté et département
    search_fields = ('nom', 'annee_academique', 'departement__nom', 'departement__faculte__nom') # Rechercher

    # Afficher la faculté dans list_display en utilisant une fonction
    def departement__faculte(self, obj):
        return obj.departement.faculte.nom
    departement__faculte.short_description = _("Faculté") # Nom de la colonne


admin.site.register(Promotion, PromotionAdmin)


class TeacherAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Teacher.
    """
    # Afficher des champs du User lié et du Département
    list_display = ('matricule', 'nom_complet', 'departement', 'user__username', 'user__email')
    list_filter = ('departement__faculte', 'departement') # Filtrer par faculté et département
    search_fields = ('matricule', 'nom_complet', 'user__username', 'user__email', 'departement__nom', 'departement__faculte__nom') # Rechercher

    # Afficher des champs du User lié en utilisant des fonctions
    def user__username(self, obj):
        return obj.user.username
    user__username.short_description = _("Nom d'utilisateur")

    def user__email(self, obj):
        return obj.user.email
    user__email.short_description = _("Email Utilisateur")

    # Pour les ForeignKeys/OneToOneFields avec beaucoup d'objets, raw_id_fields est plus performant
    # raw_id_fields = ('user', 'departement') # Utile si vous avez des milliers d'utilisateurs ou départements

admin.site.register(Teacher, TeacherAdmin)


class StudentAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Student.
    """
    # Afficher des champs pertinents, y compris de la Promotion et des Propositions
    list_display = ('matricule', 'nom_complet', 'promotion', 'promotion__departement', 'promotion__departement__faculte', 'id_inscription_annee', 'entreprise_proposee_1', 'entreprise_proposee_2')
    list_filter = ('promotion__annee_academique', 'promotion__departement__faculte', 'promotion__departement', 'promotion') # Filtrer par année, faculté, département, promotion
    search_fields = ('matricule', 'nom_complet', 'user__username', 'promotion__nom', 'promotion__annee_academique', 'promotion__departement__nom', 'promotion__departement__faculte__nom') # Rechercher

    # Afficher les champs de la Promotion et de la Faculté/Département
    def promotion__departement(self, obj):
        return obj.promotion.departement.nom if obj.promotion else '-'
    promotion__departement.short_description = _("Département")

    def promotion__departement__faculte(self, obj):
         return obj.promotion.departement.faculte.nom if obj.promotion and obj.promotion.departement else '-'
    promotion__departement__faculte.short_description = _("Faculté")

    # Afficher le nom des entreprises proposées
    def entreprise_proposee_1(self, obj):
        return obj.entreprise_proposee_1.nom if obj.entreprise_proposee_1 else '-'
    entreprise_proposee_1.short_description = _("Prop. 1")

    def entreprise_proposee_2(self, obj):
        return obj.entreprise_proposee_2.nom if obj.entreprise_proposee_2 else '-'
    entreprise_proposee_2.short_description = _("Prop. 2")


    # raw_id_fields = ('user', 'promotion', 'entreprise_proposee_1', 'entreprise_proposee_2') # Utile si beaucoup d'objets


admin.site.register(Student, StudentAdmin)


class CompanyAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Company.
    """
    list_display = ('nom', 'personne_contact', 'email_contact', 'telephone_contact')
    search_fields = ('nom', 'personne_contact', 'email_contact', 'telephone_contact', 'adresse') # Rechercher
    # list_filter = ('ville', 'pays') # Si vous ajoutez des champs de localisation

admin.site.register(Company, CompanyAdmin)


class InternshipAdmin(admin.ModelAdmin):
    """
    Personnalise l'affichage du modèle Internship.
    """
    # Afficher les champs pertinents du stage, de l'étudiant, de l'entreprise et de l'encadreur
    list_display = (
        'etudiant', 'statut', 'entreprise_selectionnee', 'encadreur', 'note',
        'etudiant__promotion__annee_academique', 'etudiant__promotion__departement', 'etudiant__promotion', # Infos étudiant
        'date_proposition_soumise', 'date_validation', 'date_encadreur_affecte', 'date_notation' # Dates
    )
    list_filter = (
        'statut', 'etudiant__promotion__annee_academique', 'etudiant__promotion__departement__faculte', # Filtres principaux
        'etudiant__promotion__departement', 'etudiant__promotion', 'entreprise_selectionnee', 'encadreur' # Filtres secondaires
    )
    search_fields = (
        'etudiant__nom_complet', 'etudiant__matricule', 'entreprise_selectionnee__nom',
        'encadreur__nom_complet', 'statut' # Rechercher
    )
    ordering = ('-etudiant__promotion__annee_academique', 'etudiant__promotion__nom', 'statut', 'etudiant__nom_complet') # Tri par défaut

    # Utiliser raw_id_fields pour les relations qui peuvent avoir beaucoup d'objets
    # raw_id_fields = ('etudiant', 'entreprise_selectionnee', 'encadreur') # Très utile si beaucoup d'étudiants/entreprises/enseignants

    # Rendre certains champs en lecture seule si le statut avance
    # def get_readonly_fields(self, request, obj=None):
    #     if obj and obj.statut != 'EN_ATTENTE_PROPOSITION': # Ex: Une fois proposé, ne pas modifier l'étudiant lié
    #          return self.readonly_fields + ('etudiant',)
    #     return self.readonly_fields

    # Afficher des champs de l'étudiant lié dans la liste
    def etudiant__promotion__annee_academique(self, obj):
        return obj.etudiant.promotion.annee_academique if obj.etudiant and obj.etudiant.promotion else '-'
    etudiant__promotion__annee_academique.short_description = _("Année")

    def etudiant__promotion__departement(self, obj):
         return obj.etudiant.promotion.departement.nom if obj.etudiant and obj.etudiant.promotion and obj.etudiant.promotion.departement else '-'
    etudiant__promotion__departement.short_description = _("Département")

    def etudiant__promotion(self, obj):
        return obj.etudiant.promotion.nom if obj.etudiant and obj.etudiant.promotion else '-'
    etudiant__promotion.short_description = _("Promotion")


admin.site.register(Internship, InternshipAdmin)