# gestion_stages_univ/internships/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse_lazy, reverse 
from django.db import transaction # Utile pour les opérations impliquant plusieurs modèles
from django.template.loader import render_to_string # Pour rendre les templates partiels
from django.utils.decorators import method_decorator # Pour appliquer des décorateurs aux vues basées sur les classes
from django.views.generic import ListView # Utilisé pour les vues de liste

# Importations pour l'authentification et les formulaires
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm # Importez d'autres formulaires si utilisés directement

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

# Importations pour les modèles
from .models import (
    User, Faculty, Department, Promotion, Teacher, Student, Company, Internship
)
from .forms import (
    TeacherForm, CompanyForm, StudentForm, StudentProposalForm, 
    InternshipValidationForm, InternshipGradingForm # Importer le nouveau formulaire
)

# Importations pour le PDF
import io
from django.http import FileResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

# --- Fonctions de test pour les rôles (déjà définies) ---
def est_facultaire_test(user):
    return user.is_authenticated and user.est_facultaire

def est_enseignant_test(user):
    return user.is_authenticated and user.est_enseignant

def est_etudiant_test(user):
    return user.is_authenticated and user.est_etudiant

# --- Vues des Tableaux de Bord (déjà ébauchées) ---

@login_required # L'utilisateur doit être connecté pour accéder à cette vue
def home_dashboard(request):
    """
    Vue qui redirige l'utilisateur connecté vers son tableau de bord spécifique en fonction de son rôle.
    Si l'utilisateur n'a pas de rôle spécifique, le rediriger vers la page de connexion ou une page d'erreur.
    """
    if request.user.est_facultaire:
        return redirect(reverse('tableau_de_bord_facultaire'))
    elif request.user.est_enseignant:
        return redirect(reverse('tableau_de_bord_enseignant'))
    elif request.user.est_etudiant:
        return redirect(reverse('tableau_de_bord_etudiant'))
    else:
        # Si l'utilisateur est connecté mais n'a aucun des rôles spécifiques
        # Vous pouvez soit le déconnecter, soit l'envoyer vers une page indiquant un rôle manquant.
        messages.warning(request, "Votre compte n'a pas de rôle spécifique (Facultaire, Enseignant, Étudiant).")
        return redirect(reverse('logout')) # Ou reverse('login') ou une autre URL



@login_required
@user_passes_test(est_facultaire_test)
def tableau_de_bord_facultaire(request):
    statistiques = {
        'total_etudiants': Student.objects.count(),
        'total_enseignants': Teacher.objects.count(),
        'total_entreprises': Company.objects.count(),
        'propositions_soumises': Internship.objects.filter(statut='PROPOSITION_SOUMISE').count(),
        'stages_affectes': Internship.objects.filter(statut='ENCADREUR_AFFECTE').count(),
        'stages_termines': Internship.objects.filter(statut='TERMINE').count(),
    }
    return render(request, 'internships/faculty_dashboard.html', {'statistiques': statistiques})

@login_required
@user_passes_test(est_enseignant_test)
def tableau_de_bord_enseignant(request):
    try:
        enseignant = request.user.teacher
        stages_encadres = Internship.objects.filter(encadreur=enseignant).select_related('etudiant', 'entreprise_selectionnee')
        return render(request, 'internships/teacher_dashboard.html', {'stages_encadres': stages_encadres})
    except Teacher.DoesNotExist:
         return HttpResponse("Votre profil d'enseignant est incomplet ou incorrectement lié.", status=400)

@login_required
@user_passes_test(est_etudiant_test)
def tableau_de_bord_etudiant(request):
    try:
        etudiant = request.user.student
        try:
            mon_stage = etudiant.stage
        except Internship.DoesNotExist:
            mon_stage = None
        return render(request, 'internships/student_dashboard.html', {'etudiant': etudiant, 'mon_stage': mon_stage})
    except Student.DoesNotExist:
         return HttpResponse("Votre profil d'étudiant est incomplet ou incorrectement lié.", status=400)


# --- Vues pour la Gestion des Enseignants (par le Facultaire - déjà définies) ---

@login_required
@user_passes_test(est_facultaire_test)
def liste_enseignants_facultaire(request):
    enseignants = Teacher.objects.all().select_related('departement')
    return render(request, 'internships/faculty_teacher_list.html', {'enseignants': enseignants})

@login_required
@user_passes_test(est_facultaire_test)
def enseignant_form_modal(request, pk=None):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if pk:
        enseignant = get_object_or_404(Teacher, pk=pk)
        form = TeacherForm(request.POST or None, instance=enseignant)
    else:
        enseignant = None
        form = TeacherForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            with transaction.atomic():
                 teacher_instance = form.save()
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Enseignant enregistré avec succès.'})
            else:
                return redirect('liste_enseignants_facultaire')
        else:
            if is_ajax:
                html = render_to_string('internships/partials/form_enseignant.html', {'form': form}, request=request)
                return HttpResponseBadRequest(html)
            else:
                 return render(request, 'internships/faculty_teacher_form_page.html', {'form': form, 'enseignant': enseignant})
    if is_ajax:
        html = render_to_string('internships/partials/form_enseignant.html', {'form': form}, request=request)
        return HttpResponse(html)
    else:
         return render(request, 'internships/faculty_teacher_form_page.html', {'form': form, 'enseignant': enseignant})

@login_required
@user_passes_test(est_facultaire_test)
def enseignant_delete_modal(request, pk):
    enseignant = get_object_or_404(Teacher, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        with transaction.atomic():
             enseignant.delete() # Supprime l'enseignant et l'utilisateur lié grâce à CASCADE
        if is_ajax:
            return JsonResponse({'success': True, 'message': 'Enseignant supprimé avec succès.'})
        else:
            return redirect('liste_enseignants_facultaire')

    if is_ajax:
        html = render_to_string('internships/partials/confirm_delete_enseignant.html', {'enseignant': enseignant}, request=request)
        return HttpResponse(html)
    else:
        return render(request, 'internships/faculty_teacher_confirm_delete.html', {'enseignant': enseignant})


# --- Vues pour la Gestion des Entreprises (par le Facultaire - déjà définies) ---

@login_required
@user_passes_test(est_facultaire_test)
def liste_entreprises_facultaire(request):
    entreprises = Company.objects.all()
    return render(request, 'internships/faculty_company_list.html', {'entreprises': entreprises})

@login_required
@user_passes_test(est_facultaire_test)
def entreprise_form_modal(request, pk=None):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if pk:
        entreprise = get_object_or_404(Company, pk=pk)
        form = CompanyForm(request.POST or None, instance=entreprise)
    else:
        entreprise = None
        form = CompanyForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Entreprise enregistrée avec succès.'})
            else:
                return redirect('liste_entreprises_facultaire')
        else:
            if is_ajax:
                html = render_to_string('internships/partials/form_entreprise.html', {'form': form}, request=request)
                return HttpResponseBadRequest(html)
            else:
                 return render(request, 'internships/faculty_company_form_page.html', {'form': form, 'entreprise': entreprise})
    if is_ajax:
        html = render_to_string('internships/partials/form_entreprise.html', {'form': form}, request=request)
        return HttpResponse(html)
    else:
         return render(request, 'internships/faculty_company_form_page.html', {'form': form, 'entreprise': entreprise})


@login_required
@user_passes_test(est_facultaire_test)
def entreprise_delete_modal(request, pk):
    entreprise = get_object_or_404(Company, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        entreprise.delete()
        if is_ajax:
            return JsonResponse({'success': True, 'message': 'Entreprise supprimée avec succès.'})
        else:
            return redirect('liste_entreprises_facultaire')

    if is_ajax:
        html = render_to_string('internships/partials/confirm_delete_entreprise.html', {'entreprise': entreprise}, request=request)
        return HttpResponse(html)
    else:
        return render(request, 'internships/faculty_company_confirm_delete.html', {'entreprise': entreprise})


# --- Nouvelles Vues pour la Gestion des Étudiants (par le Facultaire) ---

@login_required
@user_passes_test(est_facultaire_test)
def liste_etudiants_facultaire(request):
    # Vue listant tous les étudiants
    # Utiliser select_related pour charger la promotion, le département et la faculté en une requête
    etudiants = Student.objects.all().select_related('promotion', 'promotion__departement', 'promotion__departement__faculte')
    return render(request, 'internships/faculty_student_list.html', {'etudiants': etudiants})

@login_required
@user_passes_test(est_facultaire_test)
def etudiant_form_modal(request, pk=None):
    # Vue utilisée pour l'ajout (pk=None) et la modification (pk=int) d'un étudiant via modale
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if pk: # Modification
        etudiant = get_object_or_404(Student, pk=pk)
        form = StudentForm(request.POST or None, instance=etudiant)
    else: # Ajout
        etudiant = None
        form = StudentForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # La logique de création/mise à jour de l'utilisateur et la génération du matricule
            # sont gérées dans la méthode save() du StudentForm grâce à transaction.atomic() à l'intérieur
            student_instance = form.save() # form.save() retourne l'instance Student

            if is_ajax:
                # Si c'est une requête AJAX, retourner une réponse JSON de succès
                return JsonResponse({'success': True, 'message': 'Étudiant enregistré avec succès.'})
            else:
                # Sinon (accès direct), rediriger vers la liste
                return redirect('liste_etudiants_facultaire')
        else:
            # Le formulaire n'est pas valide
            if is_ajax:
                # Si c'est AJAX, rendre le formulaire avec les erreurs et le retourner
                html = render_to_string('internships/partials/form_etudiant.html', {'form': form}, request=request)
                # Retourner une réponse BadRequest (400) avec le HTML du formulaire et les erreurs
                return HttpResponseBadRequest(html)
            else:
                # Sinon, afficher le formulaire avec les erreurs sur une page complète
                 return render(request, 'internships/faculty_student_form_page.html', {'form': form, 'etudiant': etudiant})


    # Requête GET (pour afficher le formulaire initial)
    if is_ajax:
        # Si c'est AJAX, rendre uniquement la partie formulaire pour la modale
        html = render_to_string('internships/partials/form_etudiant.html', {'form': form}, request=request)
        return HttpResponse(html) # Retourner le HTML
    else:
        # Sinon (accès direct), afficher le formulaire sur une page complète
         return render(request, 'internships/faculty_student_form_page.html', {'form': form, 'etudiant': etudiant})


@login_required
@user_passes_test(est_facultaire_test)
def etudiant_delete_modal(request, pk):
    # Vue pour la suppression d'un étudiant via modale
    etudiant = get_object_or_404(Student, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        with transaction.atomic():
             # Supprime l'étudiant et l'utilisateur lié grâce à CASCADE
             # Supprime également l'objet Internship lié grâce à OneToOneField et CASCADE
             etudiant.delete()
        if is_ajax:
            return JsonResponse({'success': True, 'message': 'Étudiant supprimé avec succès.'})
        else:
            return redirect('liste_etudiants_facultaire')

    # Requête GET pour afficher la confirmation de suppression dans la modale
    if is_ajax:
        html = render_to_string('internships/partials/confirm_delete_etudiant.html', {'etudiant': etudiant}, request=request)
        return HttpResponse(html)
    else:
        # Optionnel: page de suppression complète si non AJAX
        return render(request, 'internships/faculty_student_confirm_delete.html', {'etudiant': etudiant})


# --- Ajoutez ici les autres vues plus tard (Stages: propositions, validation, affectation, notation) ---

# --- Vue de génération PDF (déjà définie) ---
@login_required
@user_passes_test(est_facultaire_test)
def generate_student_supervisor_pdf_report(request):
    stages = Internship.objects.select_related(
        'etudiant', 'etudiant__promotion', 'etudiant__promotion__departement',
        'entreprise_selectionnee', 'encadreur'
    ).filter(statut='ENCADREUR_AFFECTE').order_by(
        'etudiant__promotion__annee_academique', 'etudiant__promotion__nom', 'etudiant__nom_complet'
    )

    template_path = 'internships/reports/liste_etudiants_encadreurs.html'
    template = get_template(template_path)
    html = template.render({'stages': stages, 'date_rapport': timezone.now()})

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF. ' + str(pisa_status.err), status=500)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'rapport_affectations_stages_{timezone.now().strftime("%Y%m%d")}.pdf')



@login_required
@user_passes_test(est_etudiant_test) # Seuls les étudiants peuvent proposer
def formulaire_proposition_etudiant(request):
    try:
        etudiant = request.user.student # Récupérer l'instance Student de l'utilisateur connecté
    except Student.DoesNotExist:
        # Gérer le cas où l'utilisateur est marqué comme étudiant mais n'a pas de profil Student
        messages.error(request, "Votre profil étudiant est introuvable.")
        return redirect('logout') # Ou rediriger vers une page d'erreur

    # Optionnel: Vérifier si l'étudiant a déjà un stage dans un état avancé
    # Si le stage est déjà validé ou affecté, ne pas autoriser une nouvelle proposition?
    # Cela dépend des règles métier. Ici, on autorise la modification de la proposition
    # tant que le stage n'est pas validé/affecté.
    # try:
    #     mon_stage = etudiant.stage
    #     if mon_stage.statut in ['PROPOSITION_VALIDEE', 'ENCADREUR_AFFECTE', 'EN_COURS', 'TERMINE']:
    #         messages.warning(request, f"Vous avez déjà un stage {mon_stage.get_statut_display()}. Vous ne pouvez pas soumettre de nouvelle proposition.")
    #         return redirect('tableau_de_bord_etudiant') # Rediriger vers son tableau de bord
    # except Internship.DoesNotExist:
    #     pass # Pas encore de stage, c'est bon

    if request.method == 'POST':
        # Initialiser le formulaire avec les données POST et l'instance Student de l'étudiant connecté
        form = StudentProposalForm(request.POST, instance=etudiant)
        if form.is_valid():
            # La méthode save() du formulaire gère la mise à jour de Student et la création/mise à jour de Internship
            try:
                form.save()
                messages.success(request, "Vos propositions de stage ont été enregistrées et soumises.")
                return redirect('tableau_de_bord_etudiant') # Rediriger vers le tableau de bord étudiant
            except ValidationError as e:
                 # Gérer les erreurs de validation personnalisées de la méthode save (ex: même entreprise proposée)
                 messages.error(request, f"Erreur lors de l'enregistrement : {e.message}")
            except Exception as e:
                 # Gérer d'autres erreurs potentielles lors de la sauvegarde transactionnelle
                 messages.error(request, f"Une erreur inattendue est survenue : {e}")
                 # Re-afficher le formulaire avec les données soumises
                 return render(request, 'internships/student_proposal_form.html', {'form': form})

    else: # Méthode GET
        # Initialiser le formulaire avec l'instance Student pour pré-remplir les champs s'il a déjà proposé
        form = StudentProposalForm(instance=etudiant)

    # Afficher le formulaire
    return render(request, 'internships/student_proposal_form.html', {'form': form})


# --- Vues pour la Gestion des Stages (par le Facultaire: validation, affectation) ---
# Ajouter ici plus tard...
# def liste_stages_facultaire(request): ...
# def valider_affecter_stage(request, pk): ...


# --- Vue de génération PDF (déjà définie) ---
@login_required
@user_passes_test(est_facultaire_test)
def generate_student_supervisor_pdf_report(request):
    stages = Internship.objects.select_related(
        'etudiant', 'etudiant__promotion', 'etudiant__promotion__departement',
        'entreprise_selectionnee', 'encadreur'
    ).filter(statut='ENCADREUR_AFFECTE').order_by(
        'etudiant__promotion__annee_academique', 'etudiant__promotion__nom', 'etudiant__nom_complet'
    )

    template_path = 'internships/reports/liste_etudiants_encadreurs.html'
    template = get_template(template_path)
    html = template.render({'stages': stages, 'date_rapport': timezone.now()})

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF. ' + str(pisa_status.err), status=500)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'rapport_affectations_stages_{timezone.now().strftime("%Y%m%d")}.pdf')




@login_required
@user_passes_test(est_facultaire_test)
def liste_stages_facultaire(request):
    # Vue listant tous les stages avec les infos pertinentes
    # Utiliser select_related pour charger les objets liés en une requête
    stages = Internship.objects.all().select_related(
        'etudiant',
        'etudiant__promotion',
        'etudiant__promotion__departement',
        'entreprise_selectionnee',
        'encadreur'
    ).order_by( # Trier pour une meilleure visualisation
        'etudiant__promotion__annee_academique',
        'etudiant__promotion__nom',
        'statut', # Grouper par statut
        'etudiant__nom_complet'
    )
    return render(request, 'internships/faculty_internship_list.html', {'stages': stages})

@login_required
@user_passes_test(est_facultaire_test)
def valider_affecter_stage_modal(request, pk):
    # Vue utilisée pour valider l'entreprise et affecter l'encadreur via modale
    internship = get_object_or_404(Internship, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # Optionnel: Ajouter une validation ici si le statut n'est pas "PROPOSITION_SOUMISE" ou "ENCADREUR_AFFECTE"
    # if internship.statut not in ['PROPOSITION_SOUMISE', 'PROPOSITION_VALIDEE', 'ENCADREUR_AFFECTE']:
    #     if is_ajax:
    #         return JsonResponse({'success': False, 'message': "Le statut de ce stage ne permet pas la validation/affectation."}, status=400)
    #     else:
    #         messages.error(request, "Le statut de ce stage ne permet pas la validation/affectation.")
    #         return redirect('liste_stages_facultaire')


    if request.method == 'POST':
        # Initialiser le formulaire avec les données POST et l'instance Internship
        # Note: Passer l'instance est crucial pour filtrer les entreprises dans le formulaire
        form = InternshipValidationForm(request.POST, instance=internship)
        if form.is_valid():
            # La méthode save() du formulaire gère la mise à jour du statut et des dates
            form.save()

            # Optionnel: Ajouter un message flash
            messages.success(request, f"Stage de {internship.etudiant.nom_complet} validé et encadreur affecté avec succès.")

            if is_ajax:
                # Si c'est une requête AJAX, retourner une réponse JSON de succès
                return JsonResponse({'success': True, 'message': 'Validation et affectation enregistrées.'})
            else:
                # Sinon (accès direct), rediriger vers la liste des stages
                return redirect('liste_stages_facultaire')
        else:
            # Le formulaire n'est pas valide
            if is_ajax:
                # Si c'est AJAX, rendre le formulaire avec les erreurs et le retourner
                html = render_to_string('internships/partials/form_validation_affectation.html', {'form': form, 'internship': internship}, request=request)
                # Retourner une réponse BadRequest (400) avec le HTML du formulaire et les erreurs
                return HttpResponseBadRequest(html)
            else:
                # Sinon, afficher le formulaire avec les erreurs sur une page complète (moins probable pour une modale)
                 return render(request, 'internships/faculty_internship_validation_page.html', {'form': form, 'internship': internship})


    else: # Méthode GET (pour afficher le formulaire initial dans la modale)
        # Initialiser le formulaire avec l'instance Internship pour pré-remplir si déjà validé
         # Note: Passer l'instance est crucial pour filtrer les entreprises dans le formulaire
        form = InternshipValidationForm(instance=internship)

    # Rendre le template partiel pour la modale
    if is_ajax:
        html = render_to_string('internships/partials/form_validation_affectation.html', {'form': form, 'internship': internship}, request=request)
        return HttpResponse(html)
    else:
         # Rendre une page complète si non AJAX (moins probable)
         return render(request, 'internships/faculty_internship_validation_page.html', {'form': form, 'internship': internship})


# --- Vues pour la Notation par l'Enseignant ---
# Ajouter ici plus tard...
# def liste_stages_encadres(request): ... (déjà ébauché)
# def formulaire_notation_modal(request, pk): ...

# --- Vue de génération PDF (déjà définie) ---
@login_required
@user_passes_test(est_facultaire_test)
def generate_student_supervisor_pdf_report(request):
    stages = Internship.objects.select_related(
        'etudiant', 'etudiant__promotion', 'etudiant__promotion__departement',
        'entreprise_selectionnee', 'encadreur'
    ).filter(statut='ENCADREUR_AFFECTE').order_by(
        'etudiant__promotion__annee_academique', 'etudiant__promotion__nom', 'etudiant__nom_complet'
    )

    template_path = 'internships/reports/liste_etudiants_encadreurs.html'
    template = get_template(template_path)
    html = template.render({'stages': stages, 'date_rapport': timezone.now()})

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF. ' + str(pisa_status.err), status=500)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'rapport_affectations_stages_{timezone.now().strftime("%Y%m%d")}.pdf')




@login_required
@user_passes_test(est_enseignant_test) # Seuls les enseignants peuvent accéder à cette liste
def liste_stages_encadres(request):
    # Vue listant les stages où l'enseignant connecté est l'encadreur
    try:
        enseignant = request.user.teacher # Récupérer le profil enseignant de l'utilisateur connecté
    except Teacher.DoesNotExist:
         messages.error(request, "Votre profil d'enseignant est introuvable ou incorrectement lié.")
         return redirect('logout') # Rediriger ou afficher une erreur appropriée

    # Filtrer les stages où cet enseignant est l'encadreur
    # On peut filtrer les stages selon le statut si on veut (ex: 'ENCADREUR_AFFECTE' ou 'EN_COURS')
    stages_a_noter = Internship.objects.filter(encadreur=enseignant).select_related('etudiant', 'entreprise_selectionnee').order_by('statut', 'etudiant__nom_complet') # Ordonner pour clarté

    return render(request, 'internships/teacher_internship_list.html', {'stages_a_noter': stages_a_noter})


@login_required
@user_passes_test(est_enseignant_test) # Seuls les enseignants peuvent noter
def formulaire_notation_modal(request, pk):
    # Vue pour gérer le formulaire de notation via modale
    internship = get_object_or_404(Internship, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # --- Vérification de l'autorisation ---
    # S'assurer que l'enseignant connecté est bien l'encadreur de ce stage
    try:
        enseignant_connecte = request.user.teacher
        if internship.encadreur != enseignant_connecte:
            # L'utilisateur n'est pas l'encadreur de ce stage, refuser l'accès
            if is_ajax:
                 return JsonResponse({'success': False, 'message': "Vous n'êtes pas autorisé à noter ce stage."}, status=HttpResponseForbidden.status_code) # Statut 403 Forbidden
            else:
                 messages.error(request, "Vous n'êtes pas autorisé à noter ce stage.")
                 return redirect('liste_stages_encadres') # Rediriger vers sa liste de stages
    except Teacher.DoesNotExist:
        # L'utilisateur connecté n'a pas de profil Teacher (ne devrait pas arriver avec user_passes_test, mais sécurité supplémentaire)
        if is_ajax:
             return JsonResponse({'success': False, 'message': "Votre profil enseignant est introuvable."}, status=HttpResponseForbidden.status_code)
        else:
             messages.error(request, "Votre profil enseignant est introuvable.")
             return redirect('logout')


    # Optionnel: Vérifier le statut du stage si on veut limiter la notation à certains statuts (ex: 'ENCADREUR_AFFECTE' ou 'EN_COURS')
    # if internship.statut not in ['ENCADREUR_AFFECTE', 'EN_COURS', 'TERMINE']: # On peut modifier la note si déjà Terminé ?
    #     if is_ajax:
    #         return JsonResponse({'success': False, 'message': "Ce stage n'est pas dans un état permettant la notation."}, status=400)
    #     else:
    #         messages.warning(request, "Ce stage n'est pas dans un état permettant la notation.")
    #         return redirect('liste_stages_encadres')


    if request.method == 'POST':
        # Initialiser le formulaire avec les données POST et l'instance Internship
        form = InternshipGradingForm(request.POST, instance=internship)
        if form.is_valid():
            # La méthode save() du formulaire gère la mise à jour de la note, du statut et de la date de notation
            form.save()

            messages.success(request, f"La note pour {internship.etudiant.nom_complet} a été enregistrée.")

            if is_ajax:
                # Si c'est une requête AJAX, retourner une réponse JSON de succès
                return JsonResponse({'success': True, 'message': 'Note enregistrée avec succès.'})
            else:
                # Sinon (accès direct), rediriger vers la liste des stages encadrés
                return redirect('liste_stages_encadres')
        else:
            # Le formulaire n'est pas valide
            if is_ajax:
                # Si c'est AJAX, rendre le formulaire avec les erreurs et le retourner
                html = render_to_string('internships/partials/form_notation.html', {'form': form, 'internship': internship}, request=request)
                # Retourner une réponse BadRequest (400) avec le HTML du formulaire et les erreurs
                return HttpResponseBadRequest(html)
            else:
                # Sinon, afficher le formulaire avec les erreurs sur une page complète (moins probable)
                 return render(request, 'internships/teacher_grading_page.html', {'form': form, 'internship': internship})


    else: # Méthode GET (pour afficher le formulaire initial dans la modale)
        # Initialiser le formulaire avec l'instance Internship pour pré-remplir si une note existe déjà
        form = InternshipGradingForm(instance=internship)

    # Rendre le template partiel pour la modale
    if is_ajax:
        html = render_to_string('internships/partials/form_notation.html', {'form': form, 'internship': internship}, request=request)
        return HttpResponse(html)
    else:
         # Rendre une page complète si non AJAX (moins probable)
         return render(request, 'internships/teacher_grading_page.html', {'form': form, 'internship': internship})

# --- Vue de génération PDF (déjà définie) ---
@login_required
@user_passes_test(est_facultaire_test)
def generate_student_supervisor_pdf_report(request):
    stages = Internship.objects.select_related(
        'etudiant', 'etudiant__promotion', 'etudiant__promotion__departement',
        'entreprise_selectionnee', 'encadreur'
    ).filter(statut='ENCADREUR_AFFECTE').order_by(
        'etudiant__promotion__annee_academique', 'etudiant__promotion__nom', 'etudiant__nom_complet'
    )

    template_path = 'internships/reports/liste_etudiants_encadreurs.html'
    template = get_template(template_path)
    html = template.render({'stages': stages, 'date_rapport': timezone.now()})

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF. ' + str(pisa_status.err), status=500)

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'rapport_affectations_stages_{timezone.now().strftime("%Y%m%d")}.pdf')