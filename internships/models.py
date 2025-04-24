# gestion_stages_univ/internships/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _ # Utile si vous envisagez la traduction
# Optionnel: importer des champs de localisation si nécessaire
# from django_Maps import fields as map_fields


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé étendant AbstractUser pour ajouter des rôles spécifiques.
    """
    # Ajouter des rôles/drapeaux personnalisés
    # Ces champs booléens indiqueront le rôle principal de l'utilisateur
    est_facultaire = models.BooleanField(_("est facultaire"), default=False)
    est_enseignant = models.BooleanField(_("est enseignant"), default=False) # Indique si l'utilisateur est un enseignant et peut être un encadreur
    est_etudiant = models.BooleanField(_("est etudiant"), default=False)

    # Ajouter d'autres champs communs si nécessaire, par exemple un numéro de téléphone commun
    # telephone = models.CharField(max_length=20, blank=True, null=True)


    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")
        # Optionnel: ajouter des contraintes si un utilisateur ne peut avoir qu'un seul rôle principal
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(est_facultaire=True, est_enseignant=False, est_etudiant=False) |
                    Q(est_facultaire=False, est_enseignant=True, est_etudiant=False) |
                    Q(est_facultaire=False, est_enseignant=False, est_etudiant=True) |
                    Q(est_facultaire=False, est_enseignant=False, est_etudiant=False) # Permettre un utilisateur sans rôle spécifique au début
                ),
                name='%(app_label)s_user_has_one_role'
            )
        ]


    def __str__(self):
        """
        Retourne le nom d'utilisateur pour la représentation en chaîne de caractères.
        """
        return self.username

    # Ajoutez des propriétés ou méthodes utiles ici, par exemple pour obtenir le profil lié
    @property
    def is_faculty_user(self):
        return self.is_authenticated and self.est_facultaire

    @property
    def is_teacher_user(self):
        return self.is_authenticated and self.est_enseignant

    @property
    def is_student_user(self):
        return self.is_authenticated and self.est_etudiant


class Faculty(models.Model):
    """
    Représente une faculté au sein de l'université.
    """
    nom = models.CharField(_("nom"), max_length=100)
    code = models.CharField(_("code"), max_length=10, unique=True, help_text=_("Code court unique pour la faculté (ex: ST, EG)")) # Ex: "ST", "EG"

    class Meta:
        verbose_name = _("faculté")
        verbose_name_plural = _("facultés")

    def __str__(self):
        return self.nom

class Department(models.Model):
    """
    Représente un département au sein d'une faculté.
    """
    faculte = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departements', verbose_name=_("faculté"))
    nom = models.CharField(_("nom"), max_length=100)
    code = models.CharField(_("code"), max_length=10, unique=True, help_text=_("Code court unique pour le département (ex: INFO, GEST)")) # Ex: "INFO", "GEST"

    class Meta:
         verbose_name = _("département")
         verbose_name_plural = _("départements")

    def __str__(self):
        return f"{self.nom} ({self.faculte.nom})"

class Promotion(models.Model):
    """
    Représente une promotion spécifique au sein d'un département pour une année académique.
    """
    departement = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='promotions', verbose_name=_("département"))
    nom = models.CharField(_("nom"), max_length=50, help_text=_("Nom de la promotion (ex: L1, L2, L3, M1, M2)")) # Ex: "L1", "L2", "L3", "M1", "M2"
    annee_academique = models.CharField(_("année académique"), max_length=9, help_text=_("Année académique (ex: 2024-2025)")) # Ex: "2024-2025"

    class Meta:
        verbose_name = _("promotion")
        verbose_name_plural = _("promotions")
        # S'assurer qu'un nom de promotion est unique par département et année académique
        unique_together = ('departement', 'nom', 'annee_academique')


    def __str__(self):
        return f"{self.nom} {self.annee_academique} ({self.departement.nom})"

class Teacher(models.Model):
    """
    Représente un enseignant, qui peut également servir d'encadreur de stage.
    """
    # Un enseignant est lié à un utilisateur. OneToOneField signifie une relation 1 pour 1.
    # primary_key=True fait de ce champ la clé primaire et évite de créer un champ 'id' séparé.
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher', verbose_name=_("utilisateur"))
    matricule = models.CharField(_("matricule"), max_length=50, unique=True)
    nom_complet = models.CharField(_("nom complet"), max_length=200)
    departement = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='enseignants', verbose_name=_("département"))

    class Meta:
        verbose_name = _("enseignant")
        verbose_name_plural = _("enseignants")

    def __str__(self):
        return self.nom_complet

class Student(models.Model):
    """
    Représente un étudiant.
    """
    # Un étudiant est lié à un utilisateur (relation 1 pour 1)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student', verbose_name=_("utilisateur"))
    # Le matricule sera généré selon le format AnnéeAcademique-IDEtudiant-CodeFac-NomPromotion
    matricule = models.CharField(_("matricule"), max_length=50, unique=True)
    nom_complet = models.CharField(_("nom complet"), max_length=200)
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True, related_name='etudiants', verbose_name=_("promotion"))
    # ID unique par année académique/promotion pour la génération du matricule
    id_inscription_annee = models.IntegerField(_("ID Inscription Année"), help_text=_("ID unique d'inscription pour cette année académique et promotion"))

    # Champs pour les propositions d'entreprise faites par l'étudiant
    entreprise_proposee_1 = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='proposee_par_etudiants_1', verbose_name=_("1ère entreprise proposée"))
    entreprise_proposee_2 = models.ForeignKey('Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='proposee_par_etudiants_2', verbose_name=_("2ème entreprise proposée"))


    class Meta:
        verbose_name = _("étudiant")
        verbose_name_plural = _("étudiants")
        # S'assurer que l'ID inscription est unique par année académique/promotion
        unique_together = ('promotion', 'id_inscription_annee')


    def __str__(self):
        return self.nom_complet

class Company(models.Model):
    """
    Représente une entreprise partenaire pour les stages.
    """
    nom = models.CharField(_("nom"), max_length=200)
    adresse = models.TextField(_("adresse"), blank=True)
    personne_contact = models.CharField(_("personne contact"), max_length=100, blank=True)
    email_contact = models.EmailField(_("email contact"), blank=True)
    telephone_contact = models.CharField(_("téléphone contact"), max_length=50, blank=True)

    class Meta:
        verbose_name = _("entreprise")
        verbose_name_plural = _("entreprises")

    def __str__(self):
        return self.nom

class Internship(models.Model):
    """
    Représente l'affectation d'un étudiant à un stage spécifique dans une entreprise,
    avec un encadreur et un suivi du statut et de la note.
    """
    # Relation 1 pour 1 avec l'étudiant. Chaque étudiant a un seul enregistrement de stage principal.
    etudiant = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='stage', verbose_name=_("étudiant"))
    # L'entreprise qui a été validée et où l'étudiant fera son stage
    entreprise_selectionnee = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='stages_attribues', verbose_name=_("entreprise sélectionnée"))
    # L'enseignant qui encadre l'étudiant pendant son stage
    encadreur = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='stages_encadres', verbose_name=_("encadreur"))

    # Suivi du statut du stage
    STATUT_CHOICES = [
        ('EN_ATTENTE_PROPOSITION', _('En attente de proposition')),
        ('PROPOSITION_SOUMISE', _('Proposition Soumise')),
        ('PROPOSITION_VALIDEE', _('Proposition Validée')), # Si une entreprise est validée, mais pas encore d'encadreur
        ('ENCADREUR_AFFECTE', _('Encadreur Affecté')),   # Si entreprise ET encadreur sont affectés
        ('EN_COURS', _('En Cours')),                 # Si le stage a démarré
        ('TERMINE', _('Terminé')),                  # Si le stage est terminé et potentiellement noté
        ('ANNULE', _('Annulé')),                    # Si le stage est annulé pour une raison
    ]
    statut = models.CharField(_("statut"), max_length=30, choices=STATUT_CHOICES, default='EN_ATTENTE_PROPOSITION')

    # Notation finale du stage
    note = models.IntegerField(_("note"), null=True, blank=True, help_text=_("Note sur 100")) # Sur 100

    # Dates importantes du processus
    date_proposition_soumise = models.DateTimeField(_("date proposition soumise"), null=True, blank=True)
    date_validation = models.DateTimeField(_("date validation"), null=True, blank=True, help_text=_("Date de validation de l'entreprise"))
    date_encadreur_affecte = models.DateTimeField(_("date encadreur affecté"), null=True, blank=True)
    date_debut = models.DateField(_("date début stage"), null=True, blank=True)
    date_fin = models.DateField(_("date fin stage"), null=True, blank=True)
    date_notation = models.DateTimeField(_("date notation"), null=True, blank=True)


    class Meta:
        verbose_name = _("stage")
        verbose_name_plural = _("stages")
        # Assurez-vous qu'un étudiant n'ait qu'un seul enregistrement de stage (géré par OneToOneField)


    def __str__(self):
        return f"Stage de {self.etudiant.nom_complet}"

    # Ajoutez des propriétés ou méthodes utiles ici
    @property
    def is_validated(self):
        """Vrai si une entreprise a été sélectionnée."""
        return self.entreprise_selectionnee is not None

    @property
    def is_supervisor_assigned(self):
        """Vrai si un encadreur a été affecté."""
        return self.encadreur is not None

    @property
    def is_graded(self):
        """Vrai si une note a été attribuée."""
        return self.note is not None
