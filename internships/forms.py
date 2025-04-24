# gestion_stages_univ/internships/forms.py

from django import forms
from .models import Teacher, Student, Company, Internship, Promotion, Department, Faculty, User
from django.forms.widgets import PasswordInput, NumberInput
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse_lazy # Importer reverse_lazy si utilisé ailleurs dans les formulaires

# --- Formulaire pour Enseignant ---
class TeacherForm(forms.ModelForm):
    # Ce champ est utilisé pour le mot de passe lors de la CREATION.
    # Lors de la MODIFICATION, il est optionnel et permet de changer le mot de passe.
    password_initial = forms.CharField(
        label="Mot de passe (pour l'utilisateur)",
        widget=PasswordInput,
        required=True, # Requis à la création
        help_text="Ce mot de passe sera attribué au compte utilisateur lié. L'enseignant devra le changer."
    )

    class Meta:
        model = Teacher
        fields = ['matricule', 'nom_complet', 'departement', 'password_initial']
        # Exclure 'user' car il est géré manuellement et est la PK

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        # Le champ matricule ne doit pas être modifiable après création car il devient le username
        if self.instance:
             self.fields['matricule'].disabled = False
             self.fields['password_initial'].required = False
             self.fields['password_initial'].help_text = "Laissez vide pour ne pas changer le mot de passe."

    def clean_matricule(self):
         # Validation personnalisée pour le matricule (username) lors de la CREATION
         matricule = self.cleaned_data.get('matricule')
         if not self.instance and matricule: # Seulement lors de la création
              if User.objects.filter(username=matricule).exists():
                  raise ValidationError(f"Un utilisateur avec le nom d'utilisateur '{matricule}' existe déjà.")
         return matricule


    def save(self, commit=True):
        # Cette méthode save() du formulaire gérera UNIQUEMENT la MODIFICATION d'un enseignant existant.
        # La CREATION d'un nouvel enseignant (et de son utilisateur) sera gérée dans la vue.

        if self.instance: # --- Logique de MODIFICATION d'un enseignant existant ---
             # Utiliser une transaction pour garantir que les opérations (User et Teacher) sont atomiques
             with transaction.atomic():
                 # Récupérer l'instance Teacher existante
                 teacher = self.instance
                 # Mettre à jour les champs non PK de l'instance à partir des données nettoyées du formulaire
                 teacher.nom_complet = self.cleaned_data['nom_complet']
                 teacher.departement = self.cleaned_data['departement']
                 # Le matricule n'est pas modifiable (désactivé dans __init__)

                 password = self.cleaned_data.get('password_initial')
                 # Vérifier si un mot de passe est fourni ET si l'enseignant a déjà un utilisateur lié
                 if password and hasattr(teacher, 'user') and teacher.user is not None:
                      teacher.user.set_password(password)
                      teacher.user.save() # Enregistrer l'utilisateur si le mot de passe a changé

                 # Si commit=True, sauvegarder l'instance Teacher après la potentielle mise à jour de l'utilisateur.
                 if commit:
                      teacher.save() # Enregistrer les modifications apportées à l'instance Teacher

             return teacher # Retourne l'instance Teacher modifiée

        else: # --- Logique de CREATION (sera gérée dans la vue, cette partie est simplifiée ici) ---
             # Si cette méthode save est appelée sans instance (création), elle ne fait rien d'autre que
             # retourner l'instance en mémoire avec les données du formulaire (sans l'utilisateur lié).
             # La vue doit intercepter la création et appeler objects.create() à la place.
             # On peut éventuellement retourner l'instance non sauvegardée si commit=False est utilisé dans la vue,
             # mais pour OneToOneField(primary_key=True), il est préférable de créer et sauvegarder en une seule étape dans la vue.
             # Pour éviter toute confusion, on peut même lever une erreur si save() est appelée en mode création.
             # Mais pour l'instant, contentons-nous de retourner l'instance non liée, la vue doit gérer la création.
             # Note: super().save(commit=False) ne fonctionnera pas correctement ici pour la création à cause de la PK.
             # On va donc simplement retourner None ou l'instance non liée si commit=False.
             # La meilleure pratique est que la vue gère la création entièrement.
             # Pour l'instant, on garde une structure qui ne lève pas d'erreur si commit=False est appelé,
             # même si la création finale doit se faire dans la vue.
             # On retourne l'instance en mémoire avec les données du formulaire, mais sans l'utilisateur lié.
             # La vue devra utiliser ces données pour appeler objects.create().
             # On peut simuler le comportement de super().save(commit=False) pour les autres champs.
             teacher = Teacher(
                 matricule=self.cleaned_data.get('matricule'),
                 nom_complet=self.cleaned_data.get('nom_complet'),
                 departement=self.cleaned_data.get('departement')
             )
             # L'utilisateur et la PK seront définis par la vue lors de l'appel à objects.create()

             if commit:
                  # Si commit=True est passé en mode création, cela indique une mauvaise utilisation.
                  # La création avec OneToOneField(primary_key=True) doit utiliser objects.create() dans la vue.
                  # On pourrait lever une erreur ici, mais pour être moins intrusif, on retourne l'instance non sauvegardée.
                  pass # La vue DOIT gérer la création avec objects.create()

             return teacher # Retourne l'instance en mémoire (non liée à l'utilisateur en DB)


# --- Formulaire pour Entreprise ---
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['nom', 'adresse', 'personne_contact', 'email_contact', 'telephone_contact']

    def save(self, commit=True):
        return super().save(commit=commit)

# --- Formulaire pour Étudiant ---
class StudentForm(forms.ModelForm):
    # Ce champ est utilisé pour le mot de passe lors de la CREATION.
    # Lors de la MODIFICATION, il est optionnel et permet de changer le mot de passe.
    password_initial = forms.CharField(
        label="Mot de passe (pour l'utilisateur)",
        widget=PasswordInput,
        required=True, # Requis à la création
        help_text="Ce mot de passe sera attribué au compte utilisateur lié. L'étudiant devra le changer."
    )

    class Meta:
        model = Student
        fields = ['nom_complet', 'promotion', 'id_inscription_annee', 'password_initial']
        # Exclure 'matricule' et 'user' car gérés automatiquement et 'user' est la PK

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        # Les champs matricule et id_inscription_annee ne doivent pas être modifiables après création
        if self.instance:
             # self.fields['matricule'].disabled = True # Le matricule n'est pas dans les fields
             # id_inscription_annee ne doit pas être modifiable après création
             self.fields['id_inscription_annee'].disabled = True
             self.fields['password_initial'].required = False
             self.fields['password_initial'].help_text = "Laissez vide pour ne pas changer le mot de passe."

    # La validation clean_id_inscription_annee est toujours utile pour la création
    def clean_id_inscription_annee(self):
        id_inscription = self.cleaned_data.get('id_inscription_annee')
        promotion = self.cleaned_data.get('promotion')

        if id_inscription is not None and promotion:
            # Vérifier l'unicité par promotion et année académique
            query = Student.objects.filter(
                id_inscription_annee=id_inscription,
                promotion__annee_academique=promotion.annee_academique
            )
            if self.instance:
                query = query.exclude(pk=self.instance.pk)

            if query.exists():
                raise ValidationError(f"Un étudiant avec l'ID inscription {id_inscription} existe déjà pour la promotion {promotion.nom} de l'année {promotion.annee_academique}.")

        return id_inscription

    def save(self, commit=True):
        # Cette méthode save() du formulaire gérera UNIQUEMENT la MODIFICATION d'un étudiant existant.
        # La CREATION d'un nouvel étudiant (et de son utilisateur et stage initial) sera gérée dans la vue.

        if self.instance: # --- Logique de MODIFICATION d'un étudiant existant ---
             # Utiliser une transaction pour assurer l'atomicité des opérations User/Student
             with transaction.atomic():
                 # Récupérer l'instance Student existante
                 student = self.instance
                 # Mettre à jour les champs non PK de l'instance à partir des données nettoyées du formulaire
                 student.nom_complet = self.cleaned_data['nom_complet']
                 student.promotion = self.cleaned_data['promotion']
                 # id_inscription_annee n'est pas modifiable (désactivé dans __init__)

                 password = self.cleaned_data.get('password_initial')
                 # Vérifier si un mot de passe est fourni ET si l'étudiant a déjà un utilisateur lié
                 if password and hasattr(student, 'user') and student.user is not None:
                      student.user.set_password(password)
                      student.user.save() # Enregistrer l'utilisateur si le mot de passe a changé

                 # Si commit=True, sauvegarder l'instance Student après la potentielle mise à jour de l'utilisateur.
                 if commit:
                      student.save() # Enregistrer les modifications (nom_complet, promotion, id_inscription_annee)

             return student # Retourne l'instance Student modifiée

        else: # --- Logique de CREATION (sera gérée dans la vue, cette partie est simplifiée ici) ---
             # Similaire à TeacherForm.save() en mode création, cette branche ne fait rien de plus
             # que de retourner une instance Student en mémoire avec les données du formulaire,
             # mais sans l'utilisateur lié ni la PK définie.
             # La vue DOIT gérer la création complète avec objects.create().
             student = Student(
                 nom_complet=self.cleaned_data.get('nom_complet'),
                 promotion=self.cleaned_data.get('promotion'),
                 id_inscription_annee=self.cleaned_data.get('id_inscription_annee')
             )
             # Le matricule, l'utilisateur et la PK seront définis par la vue lors de l'appel à objects.create().
             # L'instance Internship initiale sera également créée par la vue.

             if commit:
                  # Si commit=True est passé en mode création, cela indique une mauvaise utilisation.
                  pass # La vue DOIT gérer la création avec objects.create()

             return student # Retourne l'instance en mémoire (non liée à l'utilisateur en DB)


# --- Formulaire pour la Proposition de l'Étudiant ---
class StudentProposalForm(forms.ModelForm):
    entreprise_proposee_1 = forms.ModelChoiceField(
        queryset=Company.objects.all().order_by('nom'),
        label="1ère entreprise proposée",
        empty_label="-- Sélectionnez une entreprise --"
    )
    entreprise_proposee_2 = forms.ModelChoiceField(
        queryset=Company.objects.all().order_by('nom'),
        label="2ème entreprise proposée (Optionnel)",
        required=False,
        empty_label="-- Sélectionnez une entreprise --"
    )

    class Meta:
        model = Student
        fields = ['entreprise_proposee_1', 'entreprise_proposee_2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
         cleaned_data = super().clean()
         entreprise_1 = cleaned_data.get('entreprise_proposee_1')
         entreprise_2 = cleaned_data.get('entreprise_proposee_2')
         if entreprise_1 and entreprise_2 and entreprise_1 == entreprise_2:
              raise ValidationError("La première et la deuxième proposition ne peuvent pas être la même entreprise.")
         return cleaned_data

    def save(self, commit=True):
        # Pour ce formulaire, on modifie une instance Student existante, pas de création de User/Student
        student_instance = super().save(commit=False); # Obtient l'instance Student à modifier

        entreprise_1 = self.cleaned_data.get('entreprise_proposee_1')
        entreprise_2 = self.cleaned_data.get('entreprise_proposee_2')

        student_instance.entreprise_proposee_1 = entreprise_1
        student_instance.entreprise_proposee_2 = entreprise_2

        if commit:
            with transaction.atomic():
                 student_instance.save() # Sauvegarde les propositions sur l'instance Student existante

                 # Trouver ou créer l'instance Internship liée à cet étudiant
                 internship_instance, created = Internship.objects.get_or_create(etudiant=student_instance)

                 # Mettre à jour le statut du stage si des propositions sont soumises
                 if internship_instance.statut in ['EN_ATTENTE_PROPOSITION', 'PROPOSITION_SOUMISE']:
                      if entreprise_1: # S'il y a au moins une proposition
                          internship_instance.statut = 'PROPOSITION_SOUMISE'
                          internship_instance.date_proposition_soumise = timezone.now()
                      else: # Si l'étudiant retire toutes ses propositions
                          internship_instance.statut = 'EN_ATTENTE_PROPOSITION'
                          internship_instance.date_proposition_soumise = None

                      internship_instance.save() # Sauvegarde les modifications sur l'instance Internship

        return student_instance # Retourne l'instance Student modifiée

# --- Formulaire pour la Validation et l'Affectation (Facultaire) ---
class InternshipValidationForm(forms.ModelForm):
     entreprise_selectionnee = forms.ModelChoiceField(
          queryset=Company.objects.none(),
          label="Entreprise Validée",
          empty_label="-- Sélectionner l'entreprise validée --",
          required=True
     )
     encadreur = forms.ModelChoiceField(
          queryset=Teacher.objects.all().order_by('nom_complet'),
          label="Encadreur Affecté",
          empty_label="-- Sélectionner un encadreur --",
          required=True
     )

     class Meta:
          model = Internship
          fields = ['entreprise_selectionnee', 'encadreur']

     def __init__(self, *args, **kwargs):
          internship_instance = kwargs.get('instance')
          super().__init__(*args, **kwargs)
          if internship_instance:
              # Filtrer le queryset des entreprises sélectionnables pour n'inclure que celles proposées par l'étudiant
              proposed_companies_ids = [
                  internship_instance.etudiant.entreprise_proposee_1_id,
                  internship_instance.etudiant.entreprise_proposee_2_id
              ]
              self.fields['entreprise_selectionnee'].queryset = Company.objects.filter(
                  id__in=[id for id in proposed_companies_ids if id is not None]
              )

     def clean(self):
          cleaned_data = super().clean()
          internship_instance = self.instance
          # Validation pour s'assurer que le statut du stage est approprié pour la validation/affectation
          if internship_instance and internship_instance.statut not in ['PROPOSITION_SOUMISE', 'PROPOSITION_VALIDEE', 'ENCADREUR_AFFECTE']:
               raise ValidationError("Ce stage n'est pas dans un état permettant la validation/affectation.")
          return cleaned_data

     def save(self, commit=True):
          # Surcharger la méthode save pour mettre à jour le statut et les dates
          internship = super().save(commit=False) # Met à jour entreprise_selectionnee et encadreur sur l'instance en mémoire

          # Mettre à jour le statut et les dates en fonction des changements
          if internship.entreprise_selectionnee and internship.encadreur:
               # Si une entreprise ET un encadreur sont sélectionnés
               if internship.statut == 'PROPOSITION_SOUMISE': # Si on passe de soumise à affectée
                    internship.statut = 'ENCADREUR_AFFECTE'
                    if not internship.date_validation: # Si la date de validation n'est pas encore définie
                         internship.date_validation = timezone.now() # Date de validation = date affectation
                    internship.date_encadreur_affecte = timezone.now()
               elif internship.statut == 'PROPOSITION_VALIDEE': # Si on passe de validée (sans encadreur) à affectée
                     internship.statut = 'ENCADREUR_AFFECTE'
                     internship.date_encadreur_affecte = timezone.now()
               # Si le statut est déjà ENCADREUR_AFFECTE ou EN_COURS, on ne change que la date d'affectation si l'encadreur a été modifié
               elif internship.statut in ['ENCADREUR_AFFECTE', 'EN_COURS']:
                    # Optionnel: vérifier si l'encadreur a réellement changé avant de mettre à jour la date
                    # if 'encadreur' in self.changed_data:
                    internship.date_encadreur_affecte = timezone.now()

          elif internship.entreprise_selectionnee and not internship.encadreur:
               # Si une entreprise est sélectionnée mais pas d'encadreur
               if internship.statut == 'PROPOSITION_SOUMISE': # Si on passe de soumise à validée
                    internship.statut = 'PROPOSITION_VALIDEE'
                    internship.date_validation = timezone.now()
                    # On ne change pas date_encadreur_affecte

          # Si l'entreprise sélectionnée ou l'encadreur sont retirés (cas moins fréquent via ce formulaire)
          # Vous pourriez ajouter une logique pour gérer le retour à un statut antérieur si nécessaire.

          if commit:
               internship.save() # Sauvegarder l'instance Internship

          return internship

# --- Formulaire pour la Notation (Enseignant) ---
class InternshipGradingForm(forms.ModelForm):
    note = forms.IntegerField(
        label="Note du Stage (sur 100)",
        widget=NumberInput(attrs={'min': 0, 'max': 100}),
        required=True
    )

    class Meta:
        model = Internship
        fields = ['note']

    def clean_note(self):
        note = self.cleaned_data.get('note')
        if note is not None and (note < 0 or note > 100):
            raise ValidationError("La note doit être comprise entre 0 et 100.")
        return note

    def save(self, commit=True):
        # Surcharger la méthode save pour mettre à jour le statut et la date de notation
        internship = super().save(commit=False) # Met à jour le champ note

        # Mettre à jour le statut à 'TERMINE' si une note est attribuée et que le statut n'est pas déjà terminé
        if internship.note is not None and internship.statut != 'TERMINE':
             internship.statut = 'TERMINE' # Le stage est considéré comme terminé après notation

        # Mettre à jour la date de notation si une note est attribuée ou modifiée
        if internship.note is not None:
             internship.date_notation = timezone.now()

        if commit:
            internship.save() # Sauvegarder l'instance Internship

        return internship
