from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.db.models import Q

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST

from django.db import transaction, IntegrityError
from django.db.models.deletion import ProtectedError, RestrictedError
from django.utils import timezone

from .models import (
    Utilisateur,
    UniteOrganisationnelle,
    Processus,
    Document,
    VersionDocument,
    Audit,
    NonConformite,
    ActionCorrective,
    Historique,
)

from .forms import (
    UtilisateurForm,
    UtilisateurModificationForm,
    UniteOrganisationnelleForm,
    ProcessusForm,
    DocumentForm,
    VersionDocumentForm,
    AuditForm,
    NonConformiteForm,
    ActionCorrectiveForm,
)
from functools import wraps


# ==========================================================
# ADMINISTRATEUR : DOCUMENTS EN LECTURE SEULE
# ==========================================================

def interdire_admin_documents(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        profil = getattr(
            request.user,
            'profil_smq',
            None
        )

        if profil is not None and profil.role == 'ADMIN':

            messages.error(
                request,
                "L'administrateur dispose uniquement "
                "d'un accès en consultation aux documents."
            )

            return redirect('liste_documents')

        return view_func(request, *args, **kwargs)

    return wrapper

# ==========================================================
# VÉRIFICATION DU RÔLE ADMINISTRATEUR
# ==========================================================

def est_administrateur(request):

    try:
        profil = request.user.profil_smq

        return profil.role == 'ADMIN'

    except Utilisateur.DoesNotExist:
        return False


# ==========================================================
# CONNEXION
# ==========================================================

def connexion(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('dashboard')

        return render(
            request,
            'smq/login.html',
            {
                'erreur':
                'Nom utilisateur ou mot de passe incorrect.'
            }
        )

    return render(
        request,
        'smq/login.html'
    )


# ==========================================================
# TABLEAU DE BORD
# ==========================================================
@login_required
def dashboard(request):

    # =====================================================
    # KPI PRINCIPAUX
    # =====================================================

    nombre_processus = Processus.objects.count()
    nombre_documents = Document.objects.count()
    nombre_audits = Audit.objects.count()
    nombre_non_conformites = NonConformite.objects.count()
    nombre_actions_correctives = ActionCorrective.objects.count()


    # =====================================================
    # DOCUMENTS PAR STATUT
    # =====================================================

    documents_brouillon = Document.objects.filter(
        statut='BROUILLON'
    ).count()

    documents_validation = Document.objects.filter(
        statut='EN_VALIDATION'
    ).count()

    documents_valides = Document.objects.filter(
        statut='VALIDE'
    ).count()

    documents_publies = Document.objects.filter(
        statut='PUBLIE'
    ).count()


    # =====================================================
    # POURCENTAGES DOCUMENTS
    # =====================================================

    def pourcentage(valeur, total):

        if total == 0:
            return 0

        return round(
            (valeur / total) * 100,
            1
        )


    documents_brouillon_pct = pourcentage(
        documents_brouillon,
        nombre_documents
    )

    documents_validation_pct = pourcentage(
        documents_validation,
        nombre_documents
    )

    documents_valides_pct = pourcentage(
        documents_valides,
        nombre_documents
    )

    documents_publies_pct = pourcentage(
        documents_publies,
        nombre_documents
    )


    # =====================================================
    # NON-CONFORMITÉS PAR ÉTAT
    # =====================================================

    nc_ouvertes = NonConformite.objects.filter(
        statut='OUVERTE'
    ).count()

    nc_en_cours = NonConformite.objects.filter(
        statut='EN_COURS'
    ).count()

    nc_resolues = NonConformite.objects.filter(
        statut='RESOLUE'
    ).count()

    nc_cloturees = NonConformite.objects.filter(
        statut='CLOTUREE'
    ).count()


    # =====================================================
    # POURCENTAGES POUR LE GRAPHIQUE CIRCULAIRE
    # =====================================================

    nc_ouvertes_pct = pourcentage(
        nc_ouvertes,
        nombre_non_conformites
    )

    nc_en_cours_pct = pourcentage(
        nc_en_cours,
        nombre_non_conformites
    )

    nc_resolues_pct = pourcentage(
        nc_resolues,
        nombre_non_conformites
    )

    # Valeurs cumulées nécessaires pour le donut CSS

    nc_cumul_en_cours = (
        nc_ouvertes_pct +
        nc_en_cours_pct
    )

    nc_cumul_resolues = (
        nc_cumul_en_cours +
        nc_resolues_pct
    )


    # =====================================================
    # CONTEXTE
    # =====================================================







    context = {

        # KPI

        'nombre_processus': nombre_processus,
        'nombre_documents': nombre_documents,
        'nombre_audits': nombre_audits,
        'nombre_non_conformites': nombre_non_conformites,
        'nombre_actions_correctives': nombre_actions_correctives,

        # Documents

        'documents_brouillon': documents_brouillon,
        'documents_validation': documents_validation,
        'documents_valides': documents_valides,
        'documents_publies': documents_publies,

        'documents_brouillon_pct': documents_brouillon_pct,
        'documents_validation_pct': documents_validation_pct,
        'documents_valides_pct': documents_valides_pct,
        'documents_publies_pct': documents_publies_pct,

        # Non-conformités

        'nc_ouvertes': nc_ouvertes,
        'nc_en_cours': nc_en_cours,
        'nc_resolues': nc_resolues,
        'nc_cloturees': nc_cloturees,

        'nc_ouvertes_pct': nc_ouvertes_pct,
        'nc_cumul_en_cours': nc_cumul_en_cours,
        'nc_cumul_resolues': nc_cumul_resolues,
    }

    return render(
        request,
        'smq/dashboard.html',
        context
    )

















# ==========================================================
# DÉCONNEXION
# ==========================================================


@login_required
@require_POST
def deconnexion(request):

    logout(request)

    messages.success(
        request,
        "Vous avez été déconnecté avec succès."
    )

    return redirect('login')

# ==========================================================
# CRÉER UN UTILISATEUR
# ==========================================================
@login_required
def creer_utilisateur(request):

    # Vérifier que l'utilisateur est administrateur
    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de créer un utilisateur."
        )

        return redirect('dashboard')

    if request.method == 'POST':

        form = UtilisateurForm(request.POST)

        if form.is_valid():

            # Récupérer les informations
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Toutes les opérations à l'intérieur de ce bloc
            # sont exécutées dans une seule transaction
            with transaction.atomic():

                # Créer le compte Django
                compte = User.objects.create_user(
                    username=username,
                    email=form.cleaned_data['email'],
                    password=password
                )

                # Préparer le profil SMQ
                utilisateur = form.save(
                    commit=False
                )

                # Relier le profil SMQ au compte Django
                utilisateur.user = compte

                # Enregistrer le profil SMQ
                utilisateur.save()

                # Enregistrer l'opération dans l'historique
                enregistrer_historique(
                    request,
                    f"Création de l'utilisateur : "
                    f"{utilisateur.prenom} {utilisateur.nom}"
                )

            # Message de confirmation
            messages.success(
                request,
                "Utilisateur créé avec succès."
            )

            return redirect(
                'liste_utilisateurs'
            )

    else:

        form = UtilisateurForm()

    return render(
        request,
        'smq/creer_utilisateur.html',
        {
            'form': form
        }
    )

# ==========================================================
# LISTE DES UTILISATEURS
# ==========================================================

@login_required
def liste_utilisateurs(request):

    # Seul l'administrateur peut voir cette page
    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "d'accéder à la gestion des utilisateurs."
        )

        return redirect('dashboard')

    utilisateurs = Utilisateur.objects.all().order_by(
        'nom',
        'prenom'
    )

    contexte = {
        'utilisateurs': utilisateurs
    }

    return render(
        request,
        'smq/liste_utilisateurs.html',
        contexte
    )



# ==========================================================
# MODIFIER UN UTILISATEUR — ADMIN UNIQUEMENT
# ==========================================================

@login_required
def modifier_utilisateur(request, utilisateur_id):

    if not est_administrateur(request):
        messages.error(
            request,
            "Vous n'avez pas l'autorisation de modifier un utilisateur."
        )
        return redirect('dashboard')

    utilisateur = get_object_or_404(
        Utilisateur.objects.select_related('user'),
        pk=utilisateur_id
    )

    if request.method == 'POST':

        form = UtilisateurModificationForm(
            request.POST,
            instance=utilisateur
        )

        if form.is_valid():

            nouveau_role = form.cleaned_data.get(
                'role',
                utilisateur.role
            )

            # Empêcher l'administrateur de retirer
            # son propre rôle ADMIN.
            if (
                utilisateur.user_id == request.user.pk
                and nouveau_role != 'ADMIN'
            ):

                form.add_error(
                    'role',
                    "Vous ne pouvez pas retirer votre propre rôle Administrateur."
                )

            else:

                nouveau_password = form.cleaned_data.get('password')

                try:
                    with transaction.atomic():

                        profil = form.save(commit=False)

                        compte = profil.user

                        if compte is not None:

                            compte.username = form.cleaned_data['username']

                            compte.email = form.cleaned_data['email']

                            if nouveau_password:
                                compte.set_password(nouveau_password)

                            compte.save()

                        profil.save()

                        enregistrer_historique(
                            request,
                            f"Modification de l'utilisateur : "
                            f"{profil.prenom} {profil.nom}"
                        )

                except IntegrityError:

                    form.add_error(
                        None,
                        "Modification impossible : "
                        "le nom d'utilisateur existe déjà."
                    )

                else:

                    # Maintenir la session si l'administrateur
                    # modifie son propre mot de passe.
                    if (
                        nouveau_password
                        and compte is not None
                        and compte.pk == request.user.pk
                    ):

                        update_session_auth_hash(
                            request,
                            compte
                        )

                    messages.success(
                        request,
                        "Utilisateur modifié avec succès."
                    )

                    return redirect('liste_utilisateurs')

    else:

        form = UtilisateurModificationForm(
            instance=utilisateur,
            initial={
                'username': (
                    utilisateur.user.username
                    if utilisateur.user
                    else ''
                )
            }
        )

    return render(
        request,
        'smq/modifier_utilisateur.html',
        {
            'form': form,
            'utilisateur': utilisateur
        }
    )


# ==========================================================
# ACTIVER / DÉSACTIVER UN UTILISATEUR
# ADMIN UNIQUEMENT
# ==========================================================

@login_required
@require_POST
def changer_statut_utilisateur(request, utilisateur_id):

    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de modifier "
            "le statut d'un utilisateur."
        )

        return redirect('dashboard')

    with transaction.atomic():

        # Ne pas utiliser select_related('user') ici :
        # la relation peut être NULL et PostgreSQL
        # refuse alors select_for_update().
        utilisateur = get_object_or_404(
            Utilisateur.objects.select_for_update(),
            pk=utilisateur_id
        )

        # Empêcher la modification de son propre statut.
        if utilisateur.user_id == request.user.pk:

            messages.error(
                request,
                "Vous ne pouvez pas modifier "
                "le statut de votre propre compte."
            )

            return redirect('liste_utilisateurs')

        # Inverser le statut.
        nouveau_statut = not utilisateur.actif

        utilisateur.actif = nouveau_statut

        utilisateur.save(
            update_fields=['actif']
        )

        # Synchroniser avec le compte Django.
        if utilisateur.user_id is not None:

            User.objects.filter(
                pk=utilisateur.user_id
            ).update(
                is_active=nouveau_statut
            )

        # Historique.
        action = (
            'Activation'
            if nouveau_statut
            else 'Désactivation'
        )

        enregistrer_historique(
            request,
            f"{action} de l'utilisateur : "
            f"{utilisateur.prenom} {utilisateur.nom}"
        )

    if nouveau_statut:

        messages.success(
            request,
            "Utilisateur activé avec succès."
        )

    else:

        messages.success(
            request,
            "Utilisateur désactivé avec succès."
        )

    return redirect('liste_utilisateurs')


# ==========================================================
# SUPPRIMER UN UTILISATEUR
# ADMIN UNIQUEMENT
# ==========================================================

@login_required
@require_POST
def supprimer_utilisateur(request, utilisateur_id):

    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de supprimer un utilisateur."
        )

        return redirect('dashboard')

    try:

        with transaction.atomic():

            utilisateur = get_object_or_404(
                Utilisateur.objects.select_for_update(),
                pk=utilisateur_id
            )

            # Interdire la suppression de son propre compte.
            if utilisateur.user_id == request.user.pk:

                messages.error(
                    request,
                    "Vous ne pouvez pas supprimer votre propre compte."
                )

                return redirect('liste_utilisateurs')

            compte = None

            if utilisateur.user_id is not None:

                compte = User.objects.get(
                    pk=utilisateur.user_id
                )

            # Protéger les superutilisateurs Django.
            if compte is not None and compte.is_superuser:

                messages.error(
                    request,
                    "Un superutilisateur Django ne peut pas "
                    "être supprimé depuis cette interface."
                )

                return redirect('liste_utilisateurs')

            # La suppression nécessite une désactivation préalable.
            if (
                utilisateur.actif
                or (
                    compte is not None
                    and compte.is_active
                )
            ):

                messages.error(
                    request,
                    "Désactivez d'abord cet utilisateur "
                    "avant de le supprimer."
                )

                return redirect('liste_utilisateurs')

            # Vérifier toutes les relations avec le profil SMQ.
            # On préserve notamment les documents, processus,
            # audits, actions correctives et historiques.
            dependances = []

            for relation in Utilisateur._meta.related_objects:

                if not (
                    relation.one_to_many
                    or relation.one_to_one
                ):
                    continue

                modele = relation.related_model
                champ = relation.field.name

                if modele._base_manager.filter(
                    **{champ: utilisateur}
                ).exists():

                    dependances.append(
                        str(modele._meta.verbose_name_plural)
                    )

            # Vérifier également les relations avec auth.User.
            if compte is not None:

                for relation in User._meta.related_objects:

                    if not (
                        relation.one_to_many
                        or relation.one_to_one
                    ):
                        continue

                    # Le profil SMQ est supprimé avec le compte.
                    if (
                        relation.related_model is Utilisateur
                        and relation.field.name == 'user'
                    ):
                        continue

                    modele = relation.related_model
                    champ = relation.field.name

                    if modele._base_manager.filter(
                        **{champ: compte}
                    ).exists():

                        dependances.append(
                            str(modele._meta.verbose_name_plural)
                        )

            if dependances:

                elements = ', '.join(
                    sorted(set(dependances))[:4]
                )

                messages.error(
                    request,
                    "Suppression impossible : cet utilisateur "
                    f"possède des données associées ({elements}). "
                    "Conservez son compte désactivé "
                    "pour préserver la traçabilité."
                )

                return redirect('liste_utilisateurs')

            nom_complet = (
                f"{utilisateur.prenom} {utilisateur.nom}"
            )

            # Supprimer le compte Django et son profil SMQ.
            if compte is not None:

                compte.delete()

            else:

                utilisateur.delete()

            # Enregistrer l'opération.
            enregistrer_historique(
                request,
                f"Suppression de l'utilisateur : {nom_complet}"
            )

    except (
        ProtectedError,
        RestrictedError,
        IntegrityError
    ):

        messages.error(
            request,
            "Suppression impossible : cet utilisateur "
            "possède encore des données associées."
        )

        return redirect('liste_utilisateurs')

    messages.success(
        request,
        f"L'utilisateur « {nom_complet} » "
        "a été supprimé avec succès."
    )

    return redirect('liste_utilisateurs')








# ==========================================================
# LISTE DES UNITÉS ORGANISATIONNELLES
# ==========================================================

@login_required
def liste_unites(request):

    # Afficher toutes les unités, actives ou inactives,
    # avec leur unité parente.

    unites = (
        UniteOrganisationnelle.objects
        .select_related('parent')
        .order_by('nom')
    )

    return render(
        request,
        'smq/liste_unites.html',
        {
            'unites': unites
        }
    )


# ==========================================================
# CRÉER UNE UNITÉ ORGANISATIONNELLE
# ADMIN UNIQUEMENT
# ==========================================================

@login_required
def creer_unite(request):

    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de créer une unité organisationnelle."
        )

        return redirect('dashboard')

    if request.method == 'POST':

        form = UniteOrganisationnelleForm(
            request.POST
        )

        if form.is_valid():

            unite = form.save()

            enregistrer_historique(
                request,
                f"Création de l'unité organisationnelle : "
                f"{unite.nom}"
            )

            messages.success(
                request,
                "Unité organisationnelle créée avec succès."
            )

            return redirect('liste_unites')

    else:

        form = UniteOrganisationnelleForm()

    return render(
        request,
        'smq/creer_unite.html',
        {
            'form': form
        }
    )


# ==========================================================
# MODIFIER UNE UNITÉ ORGANISATIONNELLE
# ADMIN UNIQUEMENT
# ==========================================================

@login_required
def modifier_unite(request, unite_id):

    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de modifier une unité organisationnelle."
        )

        return redirect('dashboard')

    unite = get_object_or_404(
        UniteOrganisationnelle,
        id=unite_id
    )

    if request.method == 'POST':

        form = UniteOrganisationnelleForm(
            request.POST,
            instance=unite
        )

        if form.is_valid():

            unite = form.save()

            enregistrer_historique(
                request,
                f"Modification de l'unité organisationnelle : "
                f"{unite.nom}"
            )

            messages.success(
                request,
                "Unité organisationnelle modifiée avec succès."
            )

            return redirect('liste_unites')

    else:

        form = UniteOrganisationnelleForm(
            instance=unite
        )

    return render(
        request,
        'smq/modifier_unite.html',
        {
            'form': form,
            'unite': unite
        }
    )


# ==========================================================
# SUPPRIMER UNE UNITÉ ORGANISATIONNELLE
# ADMIN UNIQUEMENT
# ==========================================================

@login_required
@require_POST
def supprimer_unite(request, unite_id):

    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de supprimer une unité."
        )

        return redirect('liste_unites')

    try:

        with transaction.atomic():

            unite = get_object_or_404(
                UniteOrganisationnelle.objects.select_for_update(),
                pk=unite_id
            )

            # Vérifier les éléments associés
            # pour éviter leur suppression en cascade.

            dependances = []

            if unite.utilisateurs.exists():
                dependances.append('utilisateurs')

            if unite.processus.exists():
                dependances.append('processus')

            if unite.audits.exists():
                dependances.append('audits')

            if unite.sous_unites.exists():
                dependances.append('sous-unités')

            # Refuser la suppression si l'unité est utilisée.

            if dependances:

                messages.error(
                    request,
                    "Suppression impossible : cette unité possède "
                    "des éléments associés ("
                    + ', '.join(dependances)
                    + "). Réaffectez-les ou désactivez l'unité."
                )

                return redirect('liste_unites')

            nom_unite = unite.nom

            unite.delete()

            enregistrer_historique(
                request,
                f"Suppression de l'unité organisationnelle : "
                f"{nom_unite}"
            )

    except (
        ProtectedError,
        RestrictedError,
        IntegrityError
    ):

        messages.error(
            request,
            "Cette unité ne peut pas être supprimée "
            "car elle est encore utilisée dans le système."
        )

        return redirect('liste_unites')

    messages.success(
        request,
        f"L'unité « {nom_unite} » "
        "a été supprimée avec succès."
    )

    return redirect('liste_unites')


# ==========================================================
# ACTIVER / DÉSACTIVER UNE UNITÉ ORGANISATIONNELLE
# ADMIN UNIQUEMENT
# ==========================================================


@login_required
@require_POST
def changer_statut_unite(request, unite_id):
    """
    Activer ou désactiver une unité organisationnelle
    sans supprimer ses données associées.
    """

    # Vérification des droits administrateur
    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de modifier "
            "le statut d'une unité."
        )

        return redirect('liste_unites')

    # Transaction pour sécuriser la modification
    with transaction.atomic():

        # CORRECTION :
        # Ne pas utiliser select_related('parent')
        # avec select_for_update() car parent est nullable.

        unite = get_object_or_404(
            UniteOrganisationnelle.objects.select_for_update(),
            pk=unite_id
        )

        # ==================================================
        # DÉSACTIVATION
        # ==================================================

        if unite.actif:

            # Vérifier les sous-unités actives
            if unite.sous_unites.filter(actif=True).exists():

                messages.error(
                    request,
                    "Désactivez d'abord les sous-unités actives "
                    "avant de désactiver cette unité."
                )

                return redirect('liste_unites')

            unite.actif = False

            action = 'Désactivation'

            confirmation = (
                f"L'unité « {unite.nom} » "
                "est maintenant inactive."
            )

        # ==================================================
        # ACTIVATION
        # ==================================================

        else:

            # Vérifier que l'unité parente est active
            if unite.parent_id:

                parent = unite.parent

                if not parent.actif:

                    messages.error(
                        request,
                        "Activez d'abord l'unité parente "
                        "avant de réactiver cette unité."
                    )

                    return redirect('liste_unites')

            unite.actif = True

            action = 'Activation'

            confirmation = (
                f"L'unité « {unite.nom} » "
                "est maintenant active."
            )

        # ==================================================
        # ENREGISTREMENT
        # ==================================================

        unite.save(update_fields=['actif'])

        # Historique des opérations
        enregistrer_historique(
            request,
            f"{action} de l'unité organisationnelle : "
            f"{unite.nom}"
        )

    # Message de confirmation
    messages.success(
        request,
        confirmation
    )

    return redirect('liste_unites')



# ==========================================================
# LISTE DES PROCESSUS
# ==========================================================


@login_required
def liste_processus(request):

    processus = (
        Processus.objects
        .select_related('unite', 'pilote')
        .all()
        .order_by('nom')
    )

    unites = (
        UniteOrganisationnelle.objects
        .all()
        .order_by('nom')
    )

    contexte = {
        'processus': processus,
        'unites': unites,
    }

    return render(
        request,
        'smq/liste_processus.html',
        contexte
    )

# ==========================================================
# CRÉER UN PROCESSUS
# ==========================================================
# ==========================================================
# CRÉER UN PROCESSUS
# ==========================================================

@login_required
def creer_processus(request):

    profil = getattr(request.user, 'profil_smq', None)

    # Seul le responsable qualité peut créer un processus
    if profil is None or profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de créer un processus."
        )

        return redirect('liste_processus')

    if request.method == 'POST':

        form = ProcessusForm(request.POST)

        if form.is_valid():

            processus = form.save()

            enregistrer_historique(
                request,
                f"Création du processus : {processus.nom}"
            )

            messages.success(
                request,
                "Processus créé avec succès."
            )

            return redirect('liste_processus')

    else:

        form = ProcessusForm()

    return render(
        request,
        'smq/creer_processus.html',
        {
            'form': form
        }
    )


# ==========================================================
# MODIFIER UN PROCESSUS
# ==========================================================

@login_required
def modifier_processus(request, processus_id):

    profil = getattr(request.user, 'profil_smq', None)

    # Seul le responsable qualité peut modifier un processus
    if profil is None or profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de modifier un processus."
        )

        return redirect('liste_processus')

    processus = get_object_or_404(
        Processus,
        id=processus_id
    )

    if request.method == 'POST':

        form = ProcessusForm(
            request.POST,
            instance=processus
        )

        if form.is_valid():

            processus = form.save()

            enregistrer_historique(
                request,
                f"Modification du processus : {processus.nom}"
            )

            messages.success(
                request,
                "Processus modifié avec succès."
            )

            return redirect('liste_processus')

    else:

        form = ProcessusForm(
            instance=processus
        )

    return render(
        request,
        'smq/modifier_processus.html',
        {
            'form': form,
            'processus': processus
        }
    )
# ==========================================================
# SUPPRIMER UN PROCESSUS — RESPONSABLE QUALITÉ UNIQUEMENT
# ==========================================================

@login_required
@require_POST
def supprimer_processus(request, processus_id):

    profil = getattr(request.user, 'profil_smq', None)

    # Seul le responsable qualité peut supprimer
    if profil is None or profil.role != 'RESP_QUALITE':
        messages.error(
            request,
            "Vous n'avez pas l'autorisation de supprimer un processus."
        )
        return redirect('liste_processus')

    try:
        with transaction.atomic():

            processus = get_object_or_404(
                Processus.objects.select_for_update(),
                pk=processus_id
            )

            # Empêcher la suppression si des documents existent
            if Document.objects.filter(processus=processus).exists():
                messages.error(
                    request,
                    "Suppression impossible : ce processus possède "
                    "des documents associés. Désactivez-le plutôt."
                )
                return redirect('liste_processus')

            # Vérifier les autres relations du processus
            dependances = []

            for relation in Processus._meta.related_objects:

                if relation.related_model is Document:
                    continue

                if not (
                    relation.one_to_many
                    or relation.one_to_one
                    or relation.many_to_many
                ):
                    continue

                modele = relation.related_model
                champ = relation.field.name

                if modele._base_manager.filter(
                    **{champ: processus}
                ).exists():
                    dependances.append(
                        str(modele._meta.verbose_name_plural)
                    )

            if dependances:
                messages.error(
                    request,
                    "Suppression impossible : ce processus possède "
                    "d'autres données associées. Désactivez-le plutôt."
                )
                return redirect('liste_processus')

            nom_processus = processus.nom

            processus.delete()

            # Historique
            enregistrer_historique(
                request,
                f"Suppression du processus : {nom_processus}"
            )

    except (ProtectedError, RestrictedError, IntegrityError):

        messages.error(
            request,
            "Suppression impossible : ce processus est encore "
            "utilisé dans le système."
        )
        return redirect('liste_processus')

    messages.success(
        request,
        f"Le processus « {nom_processus} » "
        "a été supprimé avec succès."
    )

    return redirect('liste_processus')

# ==========================================================
# ACTIVER / DÉSACTIVER UN PROCESSUS
# ==========================================================

@login_required
@require_POST
def changer_statut_processus(request, processus_id):

    profil = getattr(request.user, 'profil_smq', None)

    # Seul le responsable qualité peut changer le statut
    if profil is None or profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de modifier "
            "le statut d'un processus."
        )

        return redirect('liste_processus')

    processus = get_object_or_404(
        Processus,
        id=processus_id
    )

    # Inversion du statut
    processus.actif = not processus.actif

    processus.save(update_fields=['actif'])

    if processus.actif:

        enregistrer_historique(
            request,
            f"Activation du processus : {processus.nom}"
        )

        messages.success(
            request,
            "Processus activé avec succès."
        )

    else:

        enregistrer_historique(
            request,
            f"Désactivation du processus : {processus.nom}"
        )

        messages.success(
            request,
            "Processus désactivé avec succès."
        )

    return redirect('liste_processus')


# ==========================================================
# LISTE DES DOCUMENTS
# ==========================================================

@login_required
def liste_documents(request):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # REQUÊTE DE BASE
    # =====================================================

    documents = (
        Document.objects
        .select_related('processus', 'auteur')
    )


    # =====================================================
    # DOCUMENTS SELON LES RÔLES
    # =====================================================

    if profil.role in ['ADMIN', 'RESP_QUALITE']:

        # Administrateur et responsable qualité :
        # accès à tous les documents

        documents = documents.all()


    elif profil.role == 'PILOTE':

        # Le pilote peut voir :
        # 1. Les documents qu'il a créés
        # 2. Les documents de ses processus,
        #    même créés par un autre utilisateur

        documents = documents.filter(

            Q(auteur=profil) |
            Q(processus__pilote=profil)

        ).distinct()


    elif profil.role == 'CONTRIBUTEUR':

        # Le contributeur peut voir :
        # 1. Tous les documents publiés
        # 2. Tous les documents qu'il a créés,
        #    quel que soit leur statut
        #
        # Il ne peut pas voir les brouillons
        # ou documents en validation des autres.

        documents = documents.filter(

            Q(auteur=profil) |
            Q(statut='PUBLIE')

        ).distinct()


    else:

        # Autres rôles :
        # documents publiés uniquement

        return redirect('documents_publies')


    # =====================================================
    # TRI
    # =====================================================

    documents = documents.order_by(
        '-date_creation',
        '-id'
    )


    # =====================================================
    # DERNIÈRE VERSION DE CHAQUE DOCUMENT
    # =====================================================

    for document in documents:

        derniere_version = (
            VersionDocument.objects
            .filter(document=document)
            .order_by('-date_creation', '-id')
            .first()
        )

        document.derniere_version = derniere_version

        if derniere_version:

            document.derniere_date = (
                derniere_version.date_creation
            )

        else:

            document.derniere_date = (
                document.date_creation
            )


    # =====================================================
    # AFFICHAGE
    # =====================================================

    return render(
        request,
        'smq/liste_documents.html',
        {
            'documents': documents
        }
    )


@login_required
def creer_document(request):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # =====================================================
    # VÉRIFICATION DES DROITS
    # =====================================================

    # L'administrateur consulte les documents uniquement.
    if profil.role == 'ADMIN':

        messages.error(
            request,
            "L'administrateur ne peut pas créer de document."
        )

        return redirect('liste_documents')

    # Rôles autorisés à créer un document
    if profil.role not in [
        'RESP_QUALITE',
        'PILOTE',
        'CONTRIBUTEUR'
    ]:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de créer un document."
        )

        return redirect('documents_publies')

    # =====================================================
    # FORMULAIRE
    # =====================================================

    if request.method == 'POST':

        form = DocumentForm(request.POST)

    else:

        form = DocumentForm()

    # =====================================================
    # PROCESSUS AUTORISÉS SELON LE RÔLE
    # =====================================================

    if profil.role == 'RESP_QUALITE':

        processus_autorises = Processus.objects.filter(
            actif=True
        )

    elif profil.role == 'PILOTE':

        processus_autorises = Processus.objects.filter(
            pilote=profil,
            actif=True
        )

    else:  # CONTRIBUTEUR

        processus_autorises = Processus.objects.filter(
            unite=profil.unite,
            actif=True
        )

    form.fields['processus'].queryset = (
        processus_autorises.order_by('nom')
    )

    # =====================================================
    # ENREGISTREMENT
    # =====================================================

    if request.method == 'POST' and form.is_valid():

        document = form.save(commit=False)

        document.auteur = profil
        document.statut = 'BROUILLON'

        document.save()

        enregistrer_historique(
            request,
            f"Création du document : {document.titre}"
        )

        messages.success(
            request,
            "Document créé avec succès."
        )

        return redirect('liste_documents')

    # =====================================================
    # AFFICHAGE
    # =====================================================

    return render(
        request,
        'smq/creer_document.html',
        {
            'form': form
        }
    )




# ==========================================================
# MODIFIER UN DOCUMENT — RESPONSABLE QUALITÉ
# ==========================================================

@login_required
def modifier_document(request, document_id):

    profil = getattr(request.user, 'profil_smq', None)

    if profil is None:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    if profil.role != 'RESP_QUALITE':
        messages.error(
            request,
            "Seul le Responsable qualité peut modifier "
            "les informations d'un document."
        )
        return redirect('liste_documents')

    document = get_object_or_404(
        Document,
        pk=document_id
    )

    if document.statut != 'BROUILLON':
        messages.error(
            request,
            "Seul un document au statut Brouillon "
            "peut être modifié."
        )
        return redirect('liste_documents')

    form = DocumentForm(
        request.POST if request.method == 'POST' else None,
        instance=document
    )

    # Processus actifs + processus actuel du document
    form.fields['processus'].queryset = (
        Processus.objects
        .filter(
            Q(actif=True) |
            Q(pk=document.processus_id)
        )
        .distinct()
        .order_by('nom')
    )

    if request.method == 'POST' and form.is_valid():

        ancien_titre = document.titre

        document = form.save()

        enregistrer_historique(
            request,
            f"Modification du document : {ancien_titre} "
            f"→ {document.titre}"
        )

        messages.success(
            request,
            f"Les informations du document "
            f"« {document.titre} » ont été mises à jour."
        )

        return redirect('liste_documents')

    return render(
        request,
        'smq/modifier_document.html',
        {
            'form': form,
            'document': document
        }
    )

@login_required
@interdire_admin_documents
def ajouter_version_document(request, document_id):

    # =====================================================
    # RÉCUPÉRER LE DOCUMENT
    # =====================================================

    document = get_object_or_404(
        Document,
        id=document_id
    )

    # =====================================================
    # RÉCUPÉRER LE PROFIL SMQ
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # VÉRIFIER LE STATUT DU DOCUMENT
    # =====================================================
    #
    # Une version peut être ajoutée :
    #
    # 1. à un document BROUILLON
    #    → création de V1, V2, etc. avant publication
    #
    # 2. à un document PUBLIE
    #    → création d'une nouvelle révision
    #      tout en conservant la version publiée actuelle
    #
    # Les documents EN_VALIDATION ou VALIDE
    # ne peuvent pas recevoir une nouvelle version.
    # =====================================================

    if document.statut not in ['BROUILLON', 'PUBLIE']:

        messages.error(
            request,
            "Une nouvelle version ne peut être ajoutée "
            "qu'à un document en brouillon ou publié."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFIER LES PERMISSIONS
    # =====================================================

    # ADMIN et RESPONSABLE QUALITÉ :
    # peuvent ajouter une version à tous les documents.

    if profil.role == 'RESP_QUALITE':

        pass


    # PILOTE et CONTRIBUTEUR :
    # uniquement sur leurs propres documents.

    elif profil.role in ['PILOTE', 'CONTRIBUTEUR']:

        if document.auteur != profil:

            messages.error(
                request,
                "Vous ne pouvez ajouter une version "
                "qu'à vos propres documents."
            )

            return redirect(
                'liste_versions_document',
                document_id=document.id
            )


    # Autres rôles :
    # aucune création de version.

    else:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "d'ajouter une version à ce document."
        )

        return redirect('documents_publies')


    # =====================================================
    # EMPÊCHER PLUSIEURS RÉVISIONS EN MÊME TEMPS
    # =====================================================
    #
    # Exemple :
    #
    # V1 = PUBLIE
    # V2 = BROUILLON
    #
    # Dans ce cas, on ne doit pas pouvoir créer V3
    # tant que V2 n'a pas terminé son workflow.
    #
    # =====================================================

    if document.statut == 'PUBLIE':

        revision_existante = VersionDocument.objects.filter(
            document=document,
            statut__in=[
                'BROUILLON',
                'EN_VALIDATION',
                'VALIDE'
            ]
        ).exists()

        if revision_existante:

            messages.error(
                request,
                "Une nouvelle version de ce document "
                "est déjà en cours de préparation."
            )

            return redirect(
                'liste_versions_document',
                document_id=document.id
            )


    # =====================================================
    # CALCUL AUTOMATIQUE DU PROCHAIN NUMÉRO DE VERSION
    # =====================================================

    versions = VersionDocument.objects.filter(
        document=document
    )

    numero = 1

    prochaine_version = f"V{numero}"


    # Chercher le premier numéro V1, V2, V3...
    # qui n'existe pas encore.

    while versions.filter(
        numero_version__iexact=prochaine_version
    ).exists():

        numero += 1

        prochaine_version = f"V{numero}"


    # =====================================================
    # TRAITEMENT DU FORMULAIRE
    # =====================================================

    if request.method == 'POST':

        form = VersionDocumentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # Préparer la nouvelle version
            version = form.save(
                commit=False
            )

            # Associer la version au document
            version.document = document

            # Numéro automatique :
            # V1, V2, V3...
            version.numero_version = prochaine_version

            # Utilisateur ayant créé la version
            version.cree_par = profil

            # Toute nouvelle version commence
            # obligatoirement en brouillon
            version.statut = 'BROUILLON'

            # Enregistrement dans PostgreSQL
            version.save()


            # =================================================
            # HISTORIQUE
            # =================================================

            enregistrer_historique(
                request,
                f"Ajout de la version "
                f"{version.numero_version} "
                f"du document : {document.titre}"
            )


            # =================================================
            # MESSAGE DE CONFIRMATION
            # =================================================

            messages.success(
                request,
                f"Version {version.numero_version} "
                f"ajoutée avec succès."
            )


            # Retour vers la liste des versions
            return redirect(
                'liste_versions_document',
                document_id=document.id
            )


    # =====================================================
    # AFFICHAGE INITIAL DU FORMULAIRE
    # =====================================================

    else:

        form = VersionDocumentForm()


    # =====================================================
    # AFFICHAGE DE LA PAGE
    # =====================================================

    return render(
        request,
        'smq/ajouter_version_document.html',
        {
            'form': form,
            'document': document,
            'prochaine_version': prochaine_version,
        }
    )


@login_required
@require_POST
@interdire_admin_documents
def soumettre_version_document(request, version_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # RÉCUPÉRER LA VERSION
    # =====================================================

    version = get_object_or_404(
        VersionDocument,
        id=version_id
    )

    document = version.document


    # =====================================================
    # VÉRIFIER QU'IL S'AGIT D'UNE RÉVISION
    # D'UN DOCUMENT DÉJÀ PUBLIÉ
    # =====================================================

    if document.statut != 'PUBLIE':

        messages.error(
            request,
            "Cette action est réservée aux nouvelles versions "
            "d'un document déjà publié."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFIER LE STATUT DE LA VERSION
    # =====================================================

    if version.statut != 'BROUILLON':

        messages.error(
            request,
            "Seule une version en brouillon peut être "
            "soumise pour validation."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFIER LES PERMISSIONS
    # =====================================================

    if profil.role == 'RESP_QUALITE':

        pass

    elif profil.role in ['PILOTE', 'CONTRIBUTEUR']:

        if document.auteur != profil:

            messages.error(
                request,
                "Vous ne pouvez soumettre que les versions "
                "de vos propres documents."
            )

            return redirect(
                'liste_versions_document',
                document_id=document.id
            )

    else:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de soumettre cette version."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # PASSAGE EN VALIDATION
    # =====================================================

    version.statut = 'EN_VALIDATION'

    version.save(
        update_fields=['statut']
    )


    # =====================================================
    # HISTORIQUE
    # =====================================================

    enregistrer_historique(
        request,
        f"Soumission pour validation de la version "
        f"{version.numero_version} du document : "
        f"{document.titre}"
    )


    # =====================================================
    # MESSAGE
    # =====================================================

    messages.success(
        request,
        f"La version {version.numero_version} "
        f"a été soumise pour validation."
    )


    return redirect(
        'liste_versions_document',
        document_id=document.id
    )






@login_required
@require_POST
@interdire_admin_documents
def demander_modification_version_document(request, version_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # VÉRIFIER LES PERMISSIONS
    # =====================================================

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de demander une modification."
        )

        return redirect('documents_publies')


    # =====================================================
    # RÉCUPÉRER LA VERSION
    # =====================================================

    version = get_object_or_404(
        VersionDocument.objects.select_related('document'),
        id=version_id
    )

    document = version.document


    # =====================================================
    # VÉRIFIER LE DOCUMENT
    # =====================================================

    if document.statut != 'PUBLIE':

        messages.error(
            request,
            "Cette action est réservée aux nouvelles versions "
            "d'un document publié."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFIER LE STATUT DE LA VERSION
    # =====================================================

    if version.statut != 'EN_VALIDATION':

        messages.error(
            request,
            "Une modification ne peut être demandée "
            "que pour une version en cours de validation."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # RETOUR EN BROUILLON
    # =====================================================

    version.statut = 'BROUILLON'

    version.save(
        update_fields=['statut']
    )


    # =====================================================
    # HISTORIQUE
    # =====================================================

    enregistrer_historique(
        request,
        f"Demande de modification de la version "
        f"{version.numero_version} du document : "
        f"{document.titre}"
    )


    # =====================================================
    # MESSAGE
    # =====================================================

    messages.success(
        request,
        f"La version {version.numero_version} "
        f"a été renvoyée en brouillon pour modification."
    )


    return redirect(
        'liste_versions_document',
        document_id=document.id
    )
@login_required
@require_POST
@interdire_admin_documents
def valider_version_document(request, version_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # VÉRIFIER LES PERMISSIONS
    # =====================================================

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de valider cette version."
        )

        return redirect('documents_publies')


    # =====================================================
    # RÉCUPÉRER LA VERSION
    # =====================================================

    version = get_object_or_404(
        VersionDocument.objects.select_related('document'),
        id=version_id
    )

    document = version.document


    # =====================================================
    # VÉRIFIER LE DOCUMENT
    # =====================================================

    if document.statut != 'PUBLIE':

        messages.error(
            request,
            "Cette action est réservée aux nouvelles versions "
            "d'un document publié."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFIER LE STATUT DE LA VERSION
    # =====================================================

    if version.statut != 'EN_VALIDATION':

        messages.error(
            request,
            "Seule une version en cours de validation "
            "peut être validée."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VALIDATION DE LA VERSION
    # =====================================================

    version.statut = 'VALIDE'

    version.save(
        update_fields=['statut']
    )


    # =====================================================
    # HISTORIQUE
    # =====================================================

    enregistrer_historique(
        request,
        f"Validation de la version "
        f"{version.numero_version} du document : "
        f"{document.titre}"
    )


    # =====================================================
    # MESSAGE
    # =====================================================

    messages.success(
        request,
        f"La version {version.numero_version} "
        f"a été validée avec succès."
    )


    return redirect(
        'liste_versions_document',
        document_id=document.id
    )



@login_required
@interdire_admin_documents
def modifier_version_document(request, version_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # RÉCUPÉRER LA VERSION
    # =====================================================

    version = get_object_or_404(
        VersionDocument.objects.select_related('document'),
        id=version_id
    )

    document = version.document


    # =====================================================
    # SEULE UNE VERSION BROUILLON PEUT ÊTRE MODIFIÉE
    # =====================================================

    if version.statut != 'BROUILLON':

        messages.error(
            request,
            "Seule une version en brouillon peut être modifiée."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFICATION DES PERMISSIONS
    # =====================================================

    if profil.role == 'RESP_QUALITE':

        pass

    elif (
        profil.role in ['PILOTE', 'CONTRIBUTEUR']
        and document.auteur == profil
    ):

        pass

    else:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de modifier cette version."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # TRAITEMENT DU FORMULAIRE
    # =====================================================

    if request.method == 'POST':

        form = VersionDocumentForm(
            request.POST,
            request.FILES,
            instance=version
        )

        if form.is_valid():

            version_modifiee = form.save(commit=False)

            # Sécurité :
            # ces informations ne doivent jamais être modifiées
            # depuis le formulaire.

            version_modifiee.document = document
            version_modifiee.numero_version = version.numero_version
            version_modifiee.cree_par = version.cree_par
            version_modifiee.statut = 'BROUILLON'

            version_modifiee.save()


            # =================================================
            # HISTORIQUE
            # =================================================

            enregistrer_historique(
                request,
                f"Modification de la version "
                f"{version.numero_version} du document : "
                f"{document.titre}"
            )


            messages.success(
                request,
                f"La version {version.numero_version} "
                f"a été modifiée avec succès."
            )


            return redirect(
                'liste_versions_document',
                document_id=document.id
            )


    else:

        form = VersionDocumentForm(
            instance=version
        )


    return render(
        request,
        'smq/modifier_version_document.html',
        {
            'form': form,
            'document': document,
            'version': version,
        }
    )



@login_required
@require_POST
@interdire_admin_documents
def publier_version_document(request, version_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # VÉRIFIER LES PERMISSIONS
    # =====================================================

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de publier cette version."
        )

        return redirect('documents_publies')


    # =====================================================
    # RÉCUPÉRER LA VERSION
    # =====================================================

    version = get_object_or_404(
        VersionDocument.objects.select_related('document'),
        id=version_id
    )

    document = version.document


    # =====================================================
    # VÉRIFIER LE DOCUMENT
    # =====================================================

    if document.statut != 'PUBLIE':

        messages.error(
            request,
            "Cette action est réservée aux nouvelles versions "
            "d'un document déjà publié."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # VÉRIFIER LE STATUT DE LA VERSION
    # =====================================================

    if version.statut != 'VALIDE':

        messages.error(
            request,
            "Seule une version validée peut être publiée."
        )

        return redirect(
            'liste_versions_document',
            document_id=document.id
        )


    # =====================================================
    # PUBLICATION
    # =====================================================

    with transaction.atomic():

        # Toutes les anciennes versions publiées
        # deviennent archivées.

        VersionDocument.objects.filter(
            document=document,
            statut='PUBLIE'
        ).exclude(
            id=version.id
        ).update(
            statut='ARCHIVE'
        )


        # La nouvelle version devient la version officielle.

        version.statut = 'PUBLIE'

        version.save(
            update_fields=['statut']
        )


        # Le document reste publié.

        if document.statut != 'PUBLIE':

            document.statut = 'PUBLIE'

            document.save(
                update_fields=['statut']
            )


    # =====================================================
    # HISTORIQUE
    # =====================================================

    enregistrer_historique(
        request,
        f"Publication de la version "
        f"{version.numero_version} du document : "
        f"{document.titre}"
    )


    # =====================================================
    # MESSAGE
    # =====================================================

    messages.success(
        request,
        f"La version {version.numero_version} "
        f"a été publiée avec succès. "
        f"L'ancienne version publiée a été archivée."
    )


    return redirect(
        'liste_versions_document',
        document_id=document.id
    )




# ==========================================================
# LISTE DES VERSIONS D'UN DOCUMENT
# ==========================================================
@login_required
def liste_versions_document(request, document_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # =====================================================
    # DOCUMENT
    # =====================================================

    document = get_object_or_404(
        Document.objects.select_related(
            'processus',
            'auteur'
        ),
        id=document_id
    )

    # =====================================================
    # DROITS DE GESTION
    # =====================================================

    # Responsable qualité : gestion des documents
    # Pilote / Contributeur : gestion de leurs documents
    # Administrateur : lecture seule

    peut_gerer_document = (
        profil.role == 'RESP_QUALITE'
        or (
            profil.role in ['PILOTE', 'CONTRIBUTEUR']
            and document.auteur == profil
        )
    )

    peut_consulter_toutes_versions = (
        profil.role == 'ADMIN'
    )

    # =====================================================
    # DROITS DE CONSULTATION
    # =====================================================

    if not (
        peut_gerer_document
        or peut_consulter_toutes_versions
        or document.statut == 'PUBLIE'
    ):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de consulter ce document."
        )

        return redirect('documents_publies')

    # =====================================================
    # VERSIONS VISIBLES
    # =====================================================

    versions = VersionDocument.objects.filter(
        document=document
    )

    # ADMIN : toutes les versions
    # RESPONSABLE QUALITÉ : toutes les versions
    # AUTEUR : toutes les versions
    # AUTRES : versions publiées ou archivées

    if not (
        peut_gerer_document
        or peut_consulter_toutes_versions
    ):

        versions = versions.filter(
            statut__in=[
                'PUBLIE',
                'ARCHIVE'
            ]
        )

    versions = versions.order_by(
        '-date_creation',
        '-id'
    )

    # =====================================================
    # AJOUT D'UNE VERSION
    # =====================================================

    peut_ajouter_version = False

    if peut_gerer_document:

        # Document encore en brouillon

        if document.statut == 'BROUILLON':

            peut_ajouter_version = True

        # Document publié : nouvelle révision possible

        elif document.statut == 'PUBLIE':

            revision_existante = (
                VersionDocument.objects
                .filter(
                    document=document,
                    statut__in=[
                        'BROUILLON',
                        'EN_VALIDATION',
                        'VALIDE'
                    ]
                )
                .exists()
            )

            if not revision_existante:

                peut_ajouter_version = True

    # =====================================================
    # AFFICHAGE
    # =====================================================

    return render(
        request,
        'smq/liste_versions_document.html',
        {
            'document': document,
            'versions': versions,
            'peut_gerer_document': peut_gerer_document,
            'peut_consulter_toutes_versions': (
                peut_consulter_toutes_versions
            ),
            'peut_ajouter_version': peut_ajouter_version,
        }
    )






# ==========================================================
# SUPPRIMER UN DOCUMENT
# ==========================================================

@login_required
@require_POST
@interdire_admin_documents
def supprimer_document(request, document_id):

    # =====================================================
    # RÉCUPÉRER LE PROFIL SMQ
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # RÉCUPÉRER LE DOCUMENT
    # =====================================================

    document = get_object_or_404(
        Document,
        id=document_id
    )


    # =====================================================
    # VÉRIFIER LE STATUT
    # =====================================================

    if document.statut != 'BROUILLON':

        messages.error(
            request,
            "Seul un document en brouillon peut être supprimé."
        )

        return redirect('liste_documents')


    # =====================================================
    # VÉRIFIER LES PERMISSIONS
    # =====================================================

    if profil.role == 'RESP_QUALITE':

        pass

    elif profil.role in ['PILOTE', 'CONTRIBUTEUR']:

        if document.auteur != profil:

            messages.error(
                request,
                "Vous ne pouvez supprimer que vos propres documents."
            )

            return redirect('liste_documents')

    else:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de supprimer un document."
        )

        return redirect('documents_publies')


    # =====================================================
    # CONSERVER LE TITRE AVANT SUPPRESSION
    # =====================================================

    titre_document = document.titre


    # =====================================================
    # SUPPRIMER LES FICHIERS DES VERSIONS
    # =====================================================

    versions = VersionDocument.objects.filter(
        document=document
    )

    for version in versions:

        if version.fichier:

            version.fichier.delete(
                save=False
            )


    # =====================================================
    # SUPPRIMER LES VERSIONS
    # =====================================================

    versions.delete()


    # =====================================================
    # SUPPRIMER LE DOCUMENT
    # =====================================================

    document.delete()


    # =====================================================
    # HISTORIQUE
    # =====================================================

    enregistrer_historique(
        request,
        f"Suppression du document brouillon : {titre_document}"
    )


    # =====================================================
    # MESSAGE
    # =====================================================

    messages.success(
        request,
        f'Le document "{titre_document}" a été supprimé avec succès.'
    )


    return redirect('liste_documents')
# ==========================================================
# SOUMETTRE UN DOCUMENT POUR VALIDATION
# ==========================================================

@login_required
@require_POST
@interdire_admin_documents
def soumettre_document(request, document_id):

    # Récupérer le profil SMQ
    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # Récupérer le document
    document = get_object_or_404(
        Document,
        id=document_id
    )

    # ------------------------------------------------------
    # Vérifier les droits
    # ------------------------------------------------------

    # peuvent soumettre tous les documents
    if profil.role == 'RESP_QUALITE':
        pass

    # Pilote et contributeur :
    # uniquement leurs propres documents
    elif profil.role in ['PILOTE', 'CONTRIBUTEUR']:

        if document.auteur != profil:

            messages.error(
                request,
                "Vous ne pouvez soumettre que "
                "vos propres documents."
            )

            return redirect('liste_documents')

    # Autres rôles : interdit
    else:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de soumettre un document."
        )

        return redirect('documents_publies')

    # ------------------------------------------------------
    # Vérifier le statut
    # ------------------------------------------------------

    if document.statut != 'BROUILLON':

        messages.error(
            request,
            "Seul un document en brouillon "
            "peut être soumis pour validation."
        )

        return redirect('liste_documents')

    # ------------------------------------------------------
    # Vérifier qu'au moins une version existe
    # ------------------------------------------------------

    version_existe = VersionDocument.objects.filter(
        document=document
    ).exists()

    if not version_existe:

        messages.error(
            request,
            "Vous devez ajouter au moins une version "
            "avant de soumettre le document."
        )

        return redirect('liste_documents')

    # ------------------------------------------------------
    # Soumettre le document
    # ------------------------------------------------------

    document.statut = 'EN_VALIDATION'

    document.save()

    # Traçabilité
    enregistrer_historique(
        request,
        f"Soumission pour validation du document : "
        f"{document.titre}"
    )

    messages.success(
        request,
        "Le document a été soumis pour validation."
    )

    return redirect('liste_documents')


# ==========================================================
# VALIDER UN DOCUMENT
# ==========================================================
@login_required
@require_POST
@interdire_admin_documents
def valider_document(request, document_id):

    # Récupérer le profil SMQ de l'utilisateur connecté
    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('liste_documents')


    # Vérifier les droits
    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de valider un document."
        )

        return redirect('liste_documents')


    # Récupérer le document
    document = get_object_or_404(
        Document,
        id=document_id
    )


    # Vérifier que le document est bien en validation
    if document.statut != 'EN_VALIDATION':

        messages.error(
            request,
            "Seul un document en cours de validation peut être validé."
        )

        return redirect('liste_documents')


    # Changer le statut : En validation → Validé
    document.statut = 'VALIDE'

    # Enregistrement dans PostgreSQL
    document.save()

    # Enregistrement automatique dans l'historique
    enregistrer_historique(
        request,
        f'Validation du document : {document.titre}'
    )

    # Message de confirmation
    messages.success(
        request,
        "Le document a été validé avec succès."
    )

    return redirect('liste_documents')
















# ==========================================================
# PUBLIER UN DOCUMENT INITIAL
# ==========================================================

@login_required
@require_POST
@interdire_admin_documents
def publier_document(request, document_id):

    # =====================================================
    # PROFIL UTILISATEUR
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('liste_documents')


    # =====================================================
    # PERMISSIONS
    # =====================================================

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de publier un document."
        )

        return redirect('liste_documents')


    # =====================================================
    # DOCUMENT
    # =====================================================

    document = get_object_or_404(
        Document,
        id=document_id
    )


    # =====================================================
    # VÉRIFIER LE STATUT
    # =====================================================

    if document.statut != 'VALIDE':

        messages.error(
            request,
            "Seul un document validé peut être publié."
        )

        return redirect('liste_documents')


    # =====================================================
    # RÉCUPÉRER LA VERSION À PUBLIER
    # =====================================================

    version_a_publier = (
        VersionDocument.objects
        .filter(
            document=document
        )
        .order_by(
            '-date_creation',
            '-id'
        )
        .first()
    )


    if not version_a_publier:

        messages.error(
            request,
            "Ce document ne possède aucune version à publier."
        )

        return redirect('liste_documents')


    # =====================================================
    # PUBLICATION
    # =====================================================

    with transaction.atomic():

        # Toutes les anciennes versions deviennent archivées.
        # Cela garantit qu'une seule version sera publiée.

        VersionDocument.objects.filter(
            document=document
        ).exclude(
            id=version_a_publier.id
        ).update(
            statut='ARCHIVE'
        )


        # La version la plus récente devient officielle.

        version_a_publier.statut = 'PUBLIE'

        version_a_publier.save(
            update_fields=['statut']
        )


        # Le document devient publié.

        document.statut = 'PUBLIE'

        document.save(
            update_fields=['statut']
        )


    # =====================================================
    # HISTORIQUE
    # =====================================================

    enregistrer_historique(
        request,
        f"Publication du document : "
        f"{document.titre} - "
        f"version {version_a_publier.numero_version}"
    )


    # =====================================================
    # MESSAGE
    # =====================================================

    messages.success(
        request,
        f"Le document a été publié avec succès "
        f"avec la version "
        f"{version_a_publier.numero_version}."
    )


    return redirect('liste_documents')


# ==========================================================
# DOCUMENTS PUBLIÉS PAR DIRECTION
# ==========================================================

# ==========================================================
# DOCUMENTS PUBLIÉS PAR DIRECTION
# ==========================================================

@login_required
def documents_publies(request):

    # =====================================================
    # UNITÉS ORGANISATIONNELLES
    # =====================================================

    unites = UniteOrganisationnelle.objects.all().order_by(
        'nom'
    )


    # =====================================================
    # FILTRE PAR UNITÉ
    # =====================================================

    unite_id = request.GET.get('unite')


    # =====================================================
    # DOCUMENTS PUBLIÉS
    # =====================================================

    documents = (
        Document.objects
        .filter(
            statut='PUBLIE'
        )
        .select_related(
            'processus',
            'processus__unite'
        )
        .order_by(
            '-date_creation',
            '-id'
        )
    )


    # =====================================================
    # FILTRER PAR UNITÉ SI NÉCESSAIRE
    # =====================================================

    if unite_id:

        documents = documents.filter(
            processus__unite_id=unite_id
        )


    # =====================================================
    # VERSION ACTUELLEMENT PUBLIÉE
    # =====================================================

    for document in documents:

        version_publiee = (
            VersionDocument.objects
            .filter(
                document=document,
                statut='PUBLIE'
            )
            .order_by(
                '-date_creation',
                '-id'
            )
            .first()
        )


        # On conserve le nom "derniere_version"
        # pour ne pas avoir à modifier le template existant.

        document.derniere_version = version_publiee


        # Date affichée sur la page.

        if version_publiee:

            document.derniere_date = (
                version_publiee.date_creation
            )

        else:

            document.derniere_date = (
                document.date_creation
            )


    # =====================================================
    # AFFICHAGE
    # =====================================================

    return render(
        request,
        'smq/documents_publies.html',
        {
            'documents': documents,
            'unites': unites,
            'unite_selectionnee': unite_id,
        }
    )

# ==========================================================
# GESTION DES AUDITS
# ==========================================================
# ==========================================================
# LISTE DES AUDITS
# ==========================================================

@login_required
def liste_audits(request):

    # Récupérer le profil SMQ de l'utilisateur connecté
    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # Administrateur et responsable qualité :
    # accès à tous les audits
    if profil.role in ['ADMIN', 'RESP_QUALITE']:

        audits = Audit.objects.all().order_by(
            '-date_audit'
        )

    # Auditeur :
    # accès uniquement aux audits qui lui sont affectés
    elif profil.role == 'AUDITEUR':

        audits = Audit.objects.filter(
            auditeur=profil
        ).order_by('-date_audit')

    # Les autres rôles n'ont pas accès
    else:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de consulter les audits."
        )

        return redirect('dashboard')

    return render(
        request,
        'smq/liste_audits.html',
        {
            'audits': audits
        }
    )


@login_required
def creer_audit(request):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # Seul le responsable qualité peut créer un audit.
    # ADMIN : consultation uniquement.
    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de créer un audit."
        )

        return redirect('liste_audits')

    if request.method == 'POST':

        form = AuditForm(request.POST)

        if form.is_valid():

            audit = form.save(commit=False)
            audit.statut = 'PLANIFIE'
            audit.save()

            enregistrer_historique(
                request,
                f"Création de l'audit : "
                f"{audit.reference} - {audit.titre}"
            )

            messages.success(
                request,
                "Audit créé avec succès."
            )

            return redirect('liste_audits')

    else:
        form = AuditForm()

    return render(
        request,
        'smq/creer_audit.html',
        {
            'form': form
        }
    )


@login_required
def modifier_audit(request, audit_id):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # Seul le responsable qualité peut modifier un audit.
    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation de modifier un audit."
        )

        return redirect('liste_audits')

    audit = get_object_or_404(
        Audit,
        id=audit_id
    )

    # Modification autorisée uniquement si PLANIFIE.
    if audit.statut != 'PLANIFIE':

        messages.error(
            request,
            "Seul un audit planifié peut être modifié. "
            "Les audits en cours ou terminés "
            "ne peuvent plus être modifiés."
        )

        return redirect('liste_audits')

    if request.method == 'POST':

        form = AuditForm(
            request.POST,
            instance=audit
        )

        if form.is_valid():

            audit = form.save()

            enregistrer_historique(
                request,
                f"Modification de l'audit : "
                f"{audit.reference} - {audit.titre}"
            )

            messages.success(
                request,
                "Audit modifié avec succès."
            )

            return redirect('liste_audits')

    else:

        form = AuditForm(
            instance=audit
        )

    return render(
        request,
        'smq/modifier_audit.html',
        {
            'form': form,
            'audit': audit
        }
    )


# ==========================================================
# ANNULER UN AUDIT PLANIFIÉ 
# ==========================================================

@login_required
@require_POST
def annuler_audit(request, audit_id):
    """
    Permet au Responsable qualité d'annuler un audit planifié.
    L'audit est conservé pour assurer la traçabilité.
    """

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # Vérification du rôle
    if profil.role != 'RESP_QUALITE':
        messages.error(
            request,
            "Seul le Responsable qualité peut annuler un audit."
        )
        return redirect('liste_audits')

    # Récupération de l'audit
    audit = get_object_or_404(
        Audit,
        pk=audit_id
    )

    # Seuls les audits planifiés peuvent être annulés
    if audit.statut != 'PLANIFIE':
        messages.error(
            request,
            "Seul un audit planifié peut être annulé."
        )
        return redirect('liste_audits')

    # Annulation et historique
    with transaction.atomic():

        audit.statut = 'ANNULE'

        audit.save(
            update_fields=['statut']
        )

        enregistrer_historique(
            request,
            f"Annulation de l'audit : "
            f"{audit.reference} - {audit.titre}"
        )

    messages.success(
        request,
        f"L'audit « {audit.reference} » a été annulé."
    )

    return redirect('liste_audits')







# ==========================================================
# LISTE DES NON-CONFORMITÉS
# ==========================================================



@login_required
def liste_non_conformites(request):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    non_conformites = (
        NonConformite.objects
        .select_related('audit')
        .prefetch_related('actions_correctives')
    )

    if profil.role in ['ADMIN', 'RESP_QUALITE']:
        pass

    elif profil.role == 'AUDITEUR':
        non_conformites = non_conformites.filter(
            audit__auditeur=profil
        )

    else:
        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de consulter les non-conformités."
        )
        return redirect('dashboard')

    non_conformites = non_conformites.order_by('-id')

    for nc in non_conformites:

        nc.peut_cloturer = False
        nc.peut_reprendre = False

        actions = list(
            nc.actions_correctives.all()
        )

        # Responsable qualité :
        # reprendre uniquement s'il reste
        # une action non efficace non remplacée.

        if (
            profil.role == 'RESP_QUALITE'
            and nc.statut == 'RESOLUE'
        ):
            nc.peut_reprendre = (
                action_non_efficace_a_remplacer(
                    nc,
                    actions
                )
            )

        # Responsable qualité:
        # clôturer si toutes les actions finales
        # ont été vérifiées efficaces.

        if (
            profil.role == 'RESP_QUALITE'
            and nc.statut == 'RESOLUE'
            
        ):
            nc.peut_cloturer = (
                actions_pretes_pour_cloture(
                    nc,
                    actions
                )
            )

    return render(
        request,
        'smq/liste_non_conformites.html',
        {
            'non_conformites': non_conformites
        }
    )










@login_required
def creer_non_conformite(request):

    # Récupérer le profil SMQ de l'utilisateur connecté
    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # Vérifier le rôle
    if profil.role != 'AUDITEUR':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de créer une non-conformité."
        )

        return redirect('dashboard')

    # Si le formulaire est envoyé
    if request.method == 'POST':

        form = NonConformiteForm(request.POST)

        # Si l'utilisateur est auditeur,
        # il ne peut sélectionner que ses propres audits
        if profil.role == 'AUDITEUR':

            form.fields['audit'].queryset = Audit.objects.filter(
                auditeur=profil
            )

        if form.is_valid():

            # Création de la non-conformité avec le statut initial OUVERTE
            non_conformite = form.save(commit=False)
            non_conformite.statut = 'OUVERTE'
            non_conformite.save()

            # Enregistrement automatique dans l'historique
            enregistrer_historique(
                request,
                f"Création de la non-conformité : "
                f"{non_conformite.reference}"
            )

            messages.success(
                request,
                "Non-conformité créée avec succès."
            )

            return redirect('liste_non_conformites')

    else:

        form = NonConformiteForm()

        # Pour un auditeur :
        # afficher uniquement les audits qui lui sont affectés
        if profil.role == 'AUDITEUR':

            form.fields['audit'].queryset = Audit.objects.filter(
                auditeur=profil
            )

    return render(
        request,
        'smq/creer_non_conformite.html',
        {
            'form': form
        }
    )





@login_required
def modifier_non_conformite(request, nc_id):

   

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

   

    if profil.role != 'AUDITEUR':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de modifier une non-conformité."
        )

        return redirect('liste_non_conformites')

 

    non_conformite = get_object_or_404(
        NonConformite.objects.select_related('audit'),
        id=nc_id
    )

  

    # Une NC peut être modifiée uniquement
    # lorsqu'elle est OUVERTE ou EN_COURS.

    if non_conformite.statut not in ['OUVERTE', 'EN_COURS']:

        messages.error(
            request,
            "Cette non-conformité est résolue ou clôturée "
            "et ne peut plus être modifiée."
        )

        return redirect('liste_non_conformites')

    

    if profil.role == 'AUDITEUR':

        if (
            non_conformite.audit_id is None
            or non_conformite.audit.auditeur_id != profil.id
        ):

            messages.error(
                request,
                "Vous ne pouvez modifier que les "
                "non-conformités liées à vos propres audits."
            )

            return redirect('liste_non_conformites')

    
    if request.method == 'POST':

        form = NonConformiteForm(
            request.POST,
            instance=non_conformite
        )

        

        if profil.role == 'AUDITEUR':

            form.fields['audit'].queryset = Audit.objects.filter(
                auditeur=profil
            )

        

        if form.is_valid():

            # Conserver le statut actuel :
            # les changements de statut passent
            # uniquement par les fonctions dédiées.

            statut_initial = non_conformite.statut

            non_conformite_modifiee = form.save(
                commit=False
            )

            non_conformite_modifiee.statut = statut_initial

            non_conformite_modifiee.save()

            form.save_m2m()

            

            enregistrer_historique(
                request,
                f"Modification de la non-conformité : "
                f"{non_conformite_modifiee.reference}"
            )

          

            messages.success(
                request,
                "Non-conformité modifiée avec succès."
            )

            return redirect('liste_non_conformites')

    else:

       

        form = NonConformiteForm(
            instance=non_conformite
        )

        # Pour l'auditeur :
        # afficher uniquement ses audits.

        if profil.role == 'AUDITEUR':

            form.fields['audit'].queryset = Audit.objects.filter(
                auditeur=profil
            )

    

    return render(
        request,
        'smq/modifier_non_conformite.html',
        {
            'form': form,
            'non_conformite': non_conformite
        }
    )

# ==========================================================
# REPRENDRE LE TRAITEMENT D'UNE NON-CONFORMITÉ
# APRÈS UNE VÉRIFICATION NON EFFICACE
# ==========================================================

@login_required
@require_POST
def reprendre_traitement_non_conformite(request, nc_id):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    if profil.role != 'RESP_QUALITE':
        messages.error(
            request,
            "Seul le responsable qualité peut "
            "reprendre le traitement."
        )
        return redirect('liste_non_conformites')

    non_conformite = get_object_or_404(
        NonConformite.objects.select_related('audit'),
        id=nc_id
    )

    if non_conformite.statut != 'RESOLUE':
        messages.error(
            request,
            "Seule une non-conformité résolue "
            "peut être remise en traitement."
        )
        return redirect('liste_non_conformites')

    actions = list(
        ActionCorrective.objects.filter(
            non_conformite=non_conformite
        )
    )

    if not action_non_efficace_a_remplacer(
        non_conformite,
        actions
    ):
        messages.error(
            request,
            "Aucune action non efficace ne nécessite "
            "actuellement un remplacement."
        )
        return redirect('liste_non_conformites')

    non_conformite.statut = 'EN_COURS'
    non_conformite.save(
        update_fields=['statut']
    )

    enregistrer_historique(
        request,
        f"Reprise du traitement de la non-conformité "
        f"{non_conformite.reference} après "
        f"vérification d'une action non efficace."
    )

    messages.success(
        request,
        "Le traitement de la non-conformité "
        "a été repris avec succès."
    )

    return redirect('liste_non_conformites')



# ==========================================================
# GESTION DES ACTIONS CORRECTIVES
# ==========================================================

# ==========================================================
# LISTE DES ACTIONS CORRECTIVES
# AVEC TRAÇABILITÉ DES REMPLACEMENTS

# ==========================================================
# LISTE DES ACTIONS CORRECTIVES
# AVEC TRAÇABILITÉ DES REMPLACEMENTS
# ==========================================================

@login_required
def liste_actions_correctives(request):

    # ======================================================
    # 1. RÉCUPÉRER LE PROFIL UTILISATEUR
    # ======================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # ======================================================
    # 2. VÉRIFIER LES PERMISSIONS
    # ======================================================

    roles_autorises = [
        'ADMIN',
        'RESP_QUALITE',
        'AUDITEUR',
        'PILOTE'
    ]

    if profil.role not in roles_autorises:

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de consulter les actions correctives."
        )

        return redirect('dashboard')

    # ======================================================
    # 3. RÉCUPÉRER LES ACTIONS CORRECTIVES
    # ======================================================

    actions = (
        ActionCorrective.objects
        .select_related(
            'non_conformite',
            'responsable',
            'action_remplacee',
            'action_de_remplacement'
        )
    )

    # ======================================================
    # 4. FILTRER LES ACTIONS SELON LE RÔLE
    # ======================================================

    # ADMIN :
    # Peut consulter toutes les actions correctives.

    # RESPONSABLE QUALITÉ :
    # Peut consulter toutes les actions correctives.

    if profil.role in [
        'ADMIN',
        'RESP_QUALITE'
    ]:

        pass

    # ======================================================
    # AUDITEUR
    # ======================================================

    # L'auditeur peut consulter uniquement
    # les actions correctives liées à ses audits.

    elif profil.role == 'AUDITEUR':

        actions = actions.filter(
            non_conformite__audit__auditeur=profil
        )

    # ======================================================
    # PILOTE DE PROCESSUS
    # ======================================================

    # Le pilote peut consulter uniquement
    # les actions correctives qui lui sont affectées.

    elif profil.role == 'PILOTE':

        actions = actions.filter(
            responsable=profil
        )

    # ======================================================
    # 5. TRIER LES ACTIONS CORRECTIVES
    # ======================================================

    actions = list(
        actions.order_by(
            'date_echeance',
            'id'
        )
    )

    # ======================================================
    # 6. PRÉPARER LA TRAÇABILITÉ
    # ======================================================

    for action in actions:

        # Vérifier si cette action corrective
        # remplace une ancienne action.

        action.est_remplacement = (
            action.action_remplacee_id is not None
        )

        # Récupérer l'ancienne action remplacée.

        action.action_precedente = (
            action.action_remplacee
            if action.est_remplacement
            else None
        )

        # Vérifier si cette action corrective
        # a été remplacée par une nouvelle action.

        action.action_suivante = getattr(
            action,
            'action_de_remplacement',
            None
        )

        action.est_remplacee = (
            action.action_suivante is not None
        )

    # ======================================================
    # 7. AFFICHER LA LISTE
    # ======================================================

    return render(
        request,
        'smq/liste_actions_correctives.html',
        {
            'actions': actions
        }
    )
















# ==========================================================
# CRÉER UNE ACTION CORRECTIVE
# ==========================================================

@login_required
def creer_action_corrective(request):

    # ==========================================
    # 1. RÉCUPÉRER LE PROFIL
    # ==========================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')

    # ==========================================
    # 2. VÉRIFIER LES PERMISSIONS
    # ==========================================

    # Seul le responsable qualité peut créer
    # une action corrective.

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Seul le responsable qualité peut "
            "créer une action corrective."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # 3. INITIALISER LE FORMULAIRE
    # ==========================================

    if request.method == 'POST':

        form = ActionCorrectiveForm(
            request.POST
        )

    else:

        form = ActionCorrectiveForm()

    # ==========================================
    # 4. LIMITER LES NON-CONFORMITÉS
    # ==========================================

    # Une action corrective peut être créée
    # uniquement pour une non-conformité
    # en cours de traitement.

    form.fields['non_conformite'].queryset = (
        NonConformite.objects.filter(
            statut='EN_COURS'
        ).order_by('reference')
    )

    # ==========================================
    # 5. TRAITER LA CRÉATION
    # ==========================================

    if request.method == 'POST':

        if form.is_valid():

            # Préparer l'action corrective.

            action = form.save(
                commit=False
            )

            # Toute nouvelle action commence
            # avec le statut À FAIRE.

            action.statut = 'A_FAIRE'

            # Le champ action_remplacee est
            # enregistré automatiquement
            # grâce au ModelForm.

            ancienne_action = action.action_remplacee

            # ==================================
            # 6. ENREGISTREMENT
            # ==================================

            with transaction.atomic():

                action.save()

                # ==============================
                # 7. HISTORIQUE
                # ==============================

                if ancienne_action is not None:

                    enregistrer_historique(
                        request,
                        f"Création de l'action corrective "
                        f"n°{action.id} pour "
                        f"{action.non_conformite.reference}, "
                        f"en remplacement de l'action "
                        f"n°{ancienne_action.id}, "
                        f"jugée non efficace."
                    )

                else:

                    enregistrer_historique(
                        request,
                        f"Création de l'action corrective "
                        f"n°{action.id} pour "
                        f"{action.non_conformite.reference}."
                    )

            # ==================================
            # 8. MESSAGE DE CONFIRMATION
            # ==================================

            if ancienne_action is not None:

                messages.success(
                    request,
                    "Nouvelle action corrective de "
                    "remplacement créée avec succès. "
                    "L'ancienne action et son résultat "
                    "de vérification sont conservés."
                )

            else:

                messages.success(
                    request,
                    "Action corrective créée avec succès."
                )

            return redirect(
                'liste_actions_correctives'
            )

    # ==========================================
    # 9. AFFICHAGE DU FORMULAIRE
    # ==========================================

    return render(
        request,
        'smq/creer_action_corrective.html',
        {
            'form': form
        }
    )


@login_required
def modifier_action_corrective(request, action_id):

    # =====================================================
    # RÉCUPÉRER LE PROFIL SMQ
    # =====================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # =====================================================
    # VÉRIFIER LES DROITS
    # =====================================================

    # Seuls  le responsable qualité
    # peut modifier les informations d'une action corrective.

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de modifier cette action corrective."
        )

        return redirect('liste_actions_correctives')


    # =====================================================
    # RÉCUPÉRER L'ACTION CORRECTIVE
    # =====================================================

    action = get_object_or_404(
        ActionCorrective,
        id=action_id
    )


    # =====================================================
    # INTERDIRE LA MODIFICATION D'UNE ACTION TERMINÉE
    # =====================================================

    if action.statut == 'TERMINEE':

        messages.error(
            request,
            "Cette action corrective est terminée "
            "et ne peut plus être modifiée."
        )

        return redirect('liste_actions_correctives')


    # =====================================================
    # TRAITEMENT DU FORMULAIRE
    # =====================================================

    if request.method == 'POST':

        form = ActionCorrectiveForm(
            request.POST,
            instance=action
        )

        if form.is_valid():

            action = form.save()

            # Historique

            enregistrer_historique(
                request,
                f"Modification de l'action corrective liée à "
                f"la non-conformité : "
                f"{action.non_conformite.reference}"
            )

            messages.success(
                request,
                "Action corrective modifiée avec succès."
            )

            return redirect(
                'liste_actions_correctives'
            )

    else:

        form = ActionCorrectiveForm(
            instance=action
        )


    # =====================================================
    # AFFICHAGE
    # =====================================================

    return render(
        request,
        'smq/modifier_action_corrective.html',
        {
            'form': form,
            'action': action
        }
    )


# ==========================================================
# TRAÇABILITÉ / HISTORIQUE
# ==========================================================

def enregistrer_historique(request, action):

    try:
        profil = request.user.profil_smq
    except Utilisateur.DoesNotExist:
        profil = None

    Historique.objects.create(
        action=action,
        utilisateur=profil
    )


# ==========================================================
# CONSULTER L'HISTORIQUE
# ==========================================================

@login_required
def liste_historique(request):

    # Seul l'administrateur peut consulter l'historique
    if not est_administrateur(request):

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de consulter l'historique."
        )

        return redirect('dashboard')

    # Récupérer toutes les traces
    # Les plus récentes apparaissent en premier
    historiques = Historique.objects.select_related(
        'utilisateur'
    ).all().order_by('-date_action')

    return render(
        request,
        'smq/liste_historique.html',
        {
            'historiques': historiques
        }
    )


@login_required
@require_POST
@interdire_admin_documents
def demander_modification_document(request, document_id):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # Seuls l'administrateur et le responsable qualité
    # peuvent demander une modification

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Vous n'avez pas l'autorisation "
            "de demander une modification."
        )

        return redirect('liste_documents')


    document = get_object_or_404(
        Document,
        id=document_id
    )


    # La demande de modification n'est possible
    # que pour un document en cours de validation

    if document.statut != 'EN_VALIDATION':

        messages.error(
            request,
            "Une modification ne peut être demandée "
            "que pour un document en cours de validation."
        )

        return redirect('liste_documents')


    # Retour du document en brouillon

    document.statut = 'BROUILLON'

    document.save()


    # Traçabilité

    enregistrer_historique(
        request,
        f"Demande de modification du document : "
        f"{document.titre}"
    )


    messages.success(
        request,
        "Le document a été renvoyé en brouillon "
        "pour modification."
    )


    return redirect('liste_documents')



@login_required
@require_POST
def demarrer_audit(request, audit_id):

    
    # RÉCUPÉRER LE PROFIL UTILISATEUR
   
    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

  
    # RÉCUPÉRER L'AUDIT
    

    audit = get_object_or_404(
        Audit,
        id=audit_id
    )

    # ==========================================
    # VÉRIFIER LE RÔLE
   

    # Seul un utilisateur ayant le rôle AUDITEUR
    # peut démarrer un audit.

    if profil.role != 'AUDITEUR':
        messages.error(
            request,
            "Seul l'auditeur désigné peut démarrer cet audit."
        )
        return redirect('liste_audits')

    # ==========================================
    # VÉRIFIER L'AFFECTATION
  

    # L'auditeur ne peut démarrer que les audits
    # qui lui sont personnellement attribués.

    if audit.auditeur_id != profil.id:
        messages.error(
            request,
            "Vous ne pouvez démarrer que les audits "
            "qui vous sont attribués."
        )
        return redirect('liste_audits')

    
    # VÉRIFIER LE STATUT DE L'AUDIT
    

    # Un audit ne peut être démarré
    # que s'il est actuellement planifié.

    if audit.statut != 'PLANIFIE':
        messages.error(
            request,
            "Seul un audit planifié peut être démarré."
        )
        return redirect('liste_audits')

   
    # DÉMARRER L'AUDIT
    

    audit.statut = 'EN_COURS'
    audit.save(update_fields=['statut'])

    
    # ENREGISTRER DANS L'HISTORIQUE
  

    enregistrer_historique(
        request,
        f"Démarrage de l'audit : "
        f"{audit.reference} - {audit.titre}"
    )

    
    # MESSAGE DE CONFIRMATION
    

    messages.success(
        request,
        "L'audit a été démarré avec succès."
    )

    return redirect('liste_audits')



@login_required
@require_POST
def terminer_audit(request, audit_id):

    # ==========================================
    # 1. RÉCUPÉRER LE PROFIL UTILISATEUR
    # ==========================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # ==========================================
    # 2. RÉCUPÉRER L'AUDIT
    # ==========================================

    audit = get_object_or_404(
        Audit,
        id=audit_id
    )

    # ==========================================
    # 3. VÉRIFIER LE RÔLE
    # ==========================================

    # Seul un utilisateur ayant le rôle AUDITEUR
    # peut terminer un audit.

    if profil.role != 'AUDITEUR':
        messages.error(
            request,
            "Seul l'auditeur désigné peut terminer cet audit."
        )
        return redirect('liste_audits')

    # ==========================================
    # 4. VÉRIFIER L'AFFECTATION
    # ==========================================

    # L'auditeur ne peut terminer que les audits
    # qui lui sont personnellement attribués.

    if audit.auditeur_id != profil.id:
        messages.error(
            request,
            "Vous ne pouvez terminer que les audits "
            "qui vous sont attribués."
        )
        return redirect('liste_audits')

    # ==========================================
    # 5. VÉRIFIER LE STATUT
    # ==========================================

    # Un audit ne peut être terminé
    # que s'il est actuellement en cours.

    if audit.statut != 'EN_COURS':
        messages.error(
            request,
            "Seul un audit en cours peut être terminé."
        )
        return redirect('liste_audits')

    # ==========================================
    # 6. TERMINER L'AUDIT
    # ==========================================

    audit.statut = 'TERMINE'
    audit.save(update_fields=['statut'])

    # ==========================================
    # 7. ENREGISTRER DANS L'HISTORIQUE
    # ==========================================

    enregistrer_historique(
        request,
        f"Clôture de l'audit : "
        f"{audit.reference} - {audit.titre}"
    )

    # ==========================================
    # 8. MESSAGE DE CONFIRMATION
    # ==========================================

    messages.success(
        request,
        "L'audit a été terminé avec succès."
    )

    return redirect('liste_audits')


@login_required
@require_POST
def demarrer_traitement_non_conformite(request, nc_id):

    # ==========================================
    # 1. RÉCUPÉRER LE PROFIL UTILISATEUR
    # ==========================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # ==========================================
    # 2. RÉCUPÉRER LA NON-CONFORMITÉ
    # ==========================================

    non_conformite = get_object_or_404(
        NonConformite,
        id=nc_id
    )

    # ==========================================
    # 3. VÉRIFIER LES PERMISSIONS
    # ==========================================

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Seul un responsable qualité peut "
            "prendre en charge une non-conformité."
        )

        return redirect('liste_non_conformites')

    # ==========================================
    # 4. VÉRIFIER LE STATUT
    # ==========================================

    if non_conformite.statut != 'OUVERTE':

        messages.error(
            request,
            "Seule une non-conformité ouverte "
            "peut être prise en charge."
        )

        return redirect('liste_non_conformites')

    # ==========================================
    # 5. ENREGISTRER LA PRISE EN CHARGE
    # ==========================================

    non_conformite.statut = 'EN_COURS'

    non_conformite.pris_en_charge_par = profil

    non_conformite.date_prise_en_charge = timezone.now()

    non_conformite.save(
        update_fields=[
            'statut',
            'pris_en_charge_par',
            'date_prise_en_charge'
        ]
    )

    # ==========================================
    # 6. HISTORIQUE
    # ==========================================

    enregistrer_historique(
        request,
        f"Prise en charge de la non-conformité "
        f"{non_conformite.reference} "
        f"par {profil.prenom} {profil.nom}"
    )

    # ==========================================
    # 7. CONFIRMATION
    # ==========================================

    messages.success(
        request,
        f"La non-conformité {non_conformite.reference} "
        f"a été prise en charge par "
        f"{profil.prenom} {profil.nom}."
    )

    return redirect('liste_non_conformites')


@login_required
@require_POST
def resoudre_non_conformite(request, nc_id):

    # ==========================================
    # 1. RÉCUPÉRER LE PROFIL
    # ==========================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # ==========================================
    # 2. VÉRIFIER LE RÔLE
    # ==========================================

    if profil.role != 'RESP_QUALITE':

        messages.error(
            request,
            "Seul le responsable qualité peut "
            "résoudre une non-conformité."
        )

        return redirect('liste_non_conformites')

    # ==========================================
    # 3. RÉCUPÉRER LA NON-CONFORMITÉ
    # ==========================================

    non_conformite = get_object_or_404(
        NonConformite.objects.select_related('audit'),
        id=nc_id
    )

    # ==========================================
    # 4. VÉRIFIER LE STATUT
    # ==========================================

    if non_conformite.statut != 'EN_COURS':

        messages.error(
            request,
            "La non-conformité doit être "
            "en cours de traitement."
        )

        return redirect('liste_non_conformites')

    # ==========================================
    # 5. RÉCUPÉRER LES ACTIONS
    # ==========================================

    actions = list(
        ActionCorrective.objects.filter(
            non_conformite=non_conformite
        ).select_related('action_remplacee')
    )

    if not actions:

        messages.error(
            request,
            "Impossible de résoudre cette non-conformité : "
            "aucune action corrective n'est associée."
        )

        return redirect('liste_non_conformites')

    # ==========================================
    # 6. TOUTES LES ACTIONS DOIVENT
    #    ÊTRE TERMINÉES
    # ==========================================

    actions_non_terminees = [
        action
        for action in actions
        if action.statut != 'TERMINEE'
    ]

    if actions_non_terminees:

        messages.error(
            request,
            "Impossible de résoudre cette non-conformité : "
            "toutes les actions correctives doivent "
            "être terminées."
        )

        return redirect('liste_non_conformites')

    # ==========================================
    # 7. IDENTIFIER LES REMPLACEMENTS
    # ==========================================

    remplacements = {
        action.action_remplacee_id: action
        for action in actions
        if action.action_remplacee_id is not None
    }

    # ==========================================
    # 8. VÉRIFIER LES LIENS DE REMPLACEMENT
    # ==========================================

    for action in actions:

        if action.action_remplacee_id is None:
            continue

        ancienne_action = action.action_remplacee

        # L'action remplacée doit appartenir
        # à la même non-conformité.

        if (
            ancienne_action.non_conformite_id
            != non_conformite.id
        ):

            messages.error(
                request,
                "Une action corrective remplace une action "
                "appartenant à une autre non-conformité."
            )

            return redirect('liste_non_conformites')

        # Seule une action vérifiée non efficace
        # peut être remplacée.

        if (
            ancienne_action.statut != 'TERMINEE'
            or ancienne_action.resultat_verification
            != 'NON_EFFICACE'
            or ancienne_action.verifiee_par_id
            != non_conformite.audit.auditeur_id
            or ancienne_action.date_verification is None
        ):

            messages.error(
                request,
                "Le lien de remplacement d'une action "
                "corrective est invalide."
            )

            return redirect('liste_non_conformites')

    # ==========================================
    # 9. VÉRIFIER LES ACTIONS NON EFFICACES
    # ==========================================

    for action in actions:

        if action.resultat_verification != 'NON_EFFICACE':
            continue

        # Chaque action non efficace doit
        # posséder une action de remplacement.

        nouvelle_action = remplacements.get(action.id)

        if nouvelle_action is None:

            messages.error(
                request,
                f"Impossible de résoudre la non-conformité : "
                f"l'action n°{action.id}, jugée non efficace, "
                f"n'a pas encore été remplacée."
            )

            return redirect('liste_non_conformites')

        # Le remplacement doit être terminé.

        if nouvelle_action.statut != 'TERMINEE':

            messages.error(
                request,
                f"L'action de remplacement "
                f"n°{nouvelle_action.id} "
                f"doit être terminée."
            )

            return redirect('liste_non_conformites')

    # ==========================================
    # 10. RÉSOUDRE LA NON-CONFORMITÉ
    # ==========================================

    non_conformite.statut = 'RESOLUE'

    non_conformite.save(
        update_fields=['statut']
    )

    # ==========================================
    # 11. HISTORIQUE
    # ==========================================

    enregistrer_historique(
        request,
        f"Résolution de la non-conformité "
        f"{non_conformite.reference} "
        f"par {profil.prenom} {profil.nom}."
    )

    # ==========================================
    # 12. CONFIRMATION
    # ==========================================

    messages.success(
        request,
        f"La non-conformité "
        f"{non_conformite.reference} "
        f"a été marquée comme résolue."
    )

    return redirect('liste_non_conformites')




@login_required
@require_POST
def cloturer_non_conformite(request, nc_id):

    

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

  
    

    # Seul le Responsable qualité peut clôturer
    # une non-conformité.

    if profil.role != 'RESP_QUALITE':
        messages.error(
            request,
            "Seul le Responsable qualité peut "
            "clôturer une non-conformité."
        )
        return redirect('liste_non_conformites')

    

    non_conformite = get_object_or_404(
        NonConformite.objects.select_related('audit'),
        id=nc_id
    )

    

    if non_conformite.statut != 'RESOLUE':
        messages.error(
            request,
            "Seule une non-conformité résolue "
            "peut être clôturée."
        )
        return redirect('liste_non_conformites')

    

    actions = list(
        ActionCorrective.objects.filter(
            non_conformite=non_conformite
        )
    )

    

    # Toutes les actions finales doivent être
    # terminées et vérifiées efficaces.
    # Les actions non efficaces doivent avoir
    # été remplacées.

    if not actions_pretes_pour_cloture(
        non_conformite,
        actions
    ):
        messages.error(
            request,
            "Clôture impossible : toutes les actions "
            "finales doivent être terminées et "
            "vérifiées efficaces. Les actions "
            "non efficaces doivent être remplacées."
        )
        return redirect('liste_non_conformites')

    

    non_conformite.statut = 'CLOTUREE'

    non_conformite.save(
        update_fields=['statut']
    )

   

    enregistrer_historique(
        request,
        f"Clôture de la non-conformité "
        f"{non_conformite.reference} après "
        f"vérification des actions correctives, "
        f"y compris les actions de remplacement."
    )

    

    messages.success(
        request,
        f"La non-conformité "
        f"{non_conformite.reference} "
        f"a été clôturée avec succès."
    )

    return redirect('liste_non_conformites')




@login_required
@require_POST
def demarrer_action_corrective(request, action_id):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # Récupérer l'action corrective
    action = get_object_or_404(
        ActionCorrective,
        id=action_id
    )

    # Seul le pilote affecté peut démarrer l'action
    if (
        profil.role != 'PILOTE'
        or action.responsable_id != profil.id
    ):
        messages.error(
            request,
            "Seul le pilote responsable peut démarrer cette action corrective."
        )
        return redirect('liste_actions_correctives')

    # L'action doit être à faire
    if action.statut != 'A_FAIRE':
        messages.error(
            request,
            "Seule une action corrective à faire peut être démarrée."
        )
        return redirect('liste_actions_correctives')

    # Changement du statut
    action.statut = 'EN_COURS'
    action.save()

    # Historique
    enregistrer_historique(
        request,
        f"Démarrage de l'action corrective : {action.description}"
    )

    messages.success(
        request,
        "L'action corrective est maintenant en cours."
    )

    return redirect('liste_actions_correctives')


@login_required
@require_POST
def terminer_action_corrective(request, action_id):

    # ==========================================
    # RÉCUPÉRER LE PROFIL UTILISATEUR
    # ==========================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # ==========================================
    # RÉCUPÉRER L'ACTION CORRECTIVE
    # ==========================================

    action = get_object_or_404(
        ActionCorrective,
        id=action_id
    )

    # ==========================================
    # VÉRIFIER LES PERMISSIONS
    # ==========================================

    # Seul le pilote affecté à l'action
    # peut la terminer.

    if (
        profil.role != 'PILOTE'
        or action.responsable_id != profil.id
    ):

        messages.error(
            request,
            "Seul le pilote responsable peut terminer "
            "cette action corrective."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # VÉRIFIER LE STATUT
    # ==========================================

    # Une action doit être EN_COURS
    # avant de pouvoir être terminée.

    if action.statut != 'EN_COURS':

        messages.error(
            request,
            "Seule une action corrective en cours "
            "peut être terminée."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # TERMINER L'ACTION
    # ==========================================

    action.statut = 'TERMINEE'
    action.save()

    # ==========================================
    # HISTORIQUE
    # ==========================================

    enregistrer_historique(
        request,
        f"Fin de l'action corrective : "
        f"{action.description}"
    )

    messages.success(
        request,
        "L'action corrective a été terminée avec succès."
    )

    return redirect('liste_actions_correctives')



# ==========================================================
# PARAMÈTRES 
# ==========================================================

@login_required
def parametres(request):

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    return render(
        request,
        'smq/parametres.html',
        {
            'profil': profil
        }
    )


# ==========================================================
# MODIFIER MON MOT DE PASSE 
# ==========================================================

@login_required
def modifier_mot_de_passe(request):

    if request.method == 'POST':

        form = PasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():

            user = form.save()

            # Conserver la session après le changement
            update_session_auth_hash(request, user)

            # Enregistrer l'opération dans l'historique
            enregistrer_historique(
                request,
                "Modification du mot de passe du compte"
            )

            messages.success(
                request,
                "Votre mot de passe a été modifié avec succès."
            )

            # Retour aux paramètres pour tous les rôles
            return redirect('parametres')

    else:
        form = PasswordChangeForm(
            user=request.user
        )

    return render(
        request,
        'smq/modifier_mot_de_passe.html',
        {
            'form': form
        }
    )


# ==========================================================
# RECHERCHE GLOBALE
# ==========================================================


@login_required
def recherche_globale(request):

    # ======================================================
    # PROFIL UTILISATEUR
    # ======================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:

        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )

        return redirect('dashboard')


    # ======================================================
    # TERME RECHERCHÉ
    # ======================================================

    query = request.GET.get(
        'q',
        ''
    ).strip()


    # ======================================================
    # RÉSULTATS VIDES PAR DÉFAUT
    # ======================================================

    processus_resultats = []

    documents_resultats = []

    audits_resultats = []

    non_conformites_resultats = []

    actions_resultats = []

    unites_resultats = []

    utilisateurs_resultats = []

    historiques_resultats = []


    # ======================================================
    # LANCER LA RECHERCHE
    # ======================================================

    if query:


        # ==================================================
        # 1. PROCESSUS
        # Accessible à tous les utilisateurs connectés
        # ==================================================

        processus_resultats = list(
            Processus.objects
            .select_related(
                'unite',
                'pilote'
            )
            .filter(
                Q(nom__icontains=query)
                |
                Q(description__icontains=query)
                |
                Q(unite__nom__icontains=query)
                |
                Q(pilote__nom__icontains=query)
                |
                Q(pilote__prenom__icontains=query)
            )
            .order_by('nom')[:10]
        )


        # ==================================================
        # 2. UNITÉS ORGANISATIONNELLES
        # Accessible à tous les utilisateurs connectés
        # ==================================================

        unites_resultats = list(
            UniteOrganisationnelle.objects
            .filter(
                nom__icontains=query
            )
            .order_by('nom')[:10]
        )


        # ==================================================
        # 3. DOCUMENTS
        # Respect des permissions existantes
        # ==================================================

        documents_base = (
            Document.objects
            .select_related(
                'processus',
                'auteur'
            )
        )


        # ADMIN / RESPONSABLE QUALITÉ :
        # tous les documents
        if profil.role in [
            'ADMIN',
            'RESP_QUALITE'
        ]:

            pass


        # PILOTE / CONTRIBUTEUR :
        # uniquement leurs propres documents
        elif profil.role in [
            'PILOTE',
            'CONTRIBUTEUR'
        ]:

            documents_base = (
                documents_base.filter(
                    auteur=profil
                )
            )


        # RESPONSABLE DIRECTION / AUDITEUR :
        # uniquement les documents publiés
        else:

            documents_base = (
                documents_base.filter(
                    statut='PUBLIE'
                )
            )


        documents_resultats = list(
            documents_base
            .filter(
                Q(titre__icontains=query)
                |
                Q(description__icontains=query)
                |
                Q(processus__nom__icontains=query)
            )
            .order_by(
                '-date_creation',
                '-id'
            )[:10]
        )


        # ==================================================
        # 4. AUDITS
        # ==================================================

        if profil.role in [
            'ADMIN',
            'RESP_QUALITE'
        ]:

            audits_base = (
                Audit.objects.all()
            )


        elif profil.role == 'AUDITEUR':

            audits_base = (
                Audit.objects.filter(
                    auditeur=profil
                )
            )


        else:

            audits_base = (
                Audit.objects.none()
            )


        audits_resultats = list(
            audits_base
            .select_related(
                'unite',
                'auditeur'
            )
            .filter(
                Q(reference__icontains=query)
                |
                Q(titre__icontains=query)
                |
                Q(unite__nom__icontains=query)
                |
                Q(auditeur__nom__icontains=query)
                |
                Q(auditeur__prenom__icontains=query)
            )
            .order_by(
                '-date_audit'
            )[:10]
        )


        # ==================================================
        # 5. NON-CONFORMITÉS
        # ==================================================

        if profil.role in [
            'ADMIN',
            'RESP_QUALITE'
        ]:

            nc_base = (
                NonConformite.objects
                .select_related('audit')
                .all()
            )


        elif profil.role == 'AUDITEUR':

            nc_base = (
                NonConformite.objects
                .select_related('audit')
                .filter(
                    audit__auditeur=profil
                )
            )


        else:

            nc_base = (
                NonConformite.objects.none()
            )


        non_conformites_resultats = list(
            nc_base
            .filter(
                Q(reference__icontains=query)
                |
                Q(description__icontains=query)
                |
                Q(audit__reference__icontains=query)
                |
                Q(audit__titre__icontains=query)
            )
            .order_by('-id')[:10]
        )


        # ==================================================
        # 6. ACTIONS CORRECTIVES
        # ==================================================

        actions_base = (
            ActionCorrective.objects
            .select_related(
                'non_conformite',
                'responsable'
            )
        )


        # ADMIN / RESPONSABLE QUALITÉ :
        # toutes les actions
        if profil.role in [
            'ADMIN',
            'RESP_QUALITE'
        ]:

            pass


        # Autres rôles :
        # uniquement les actions qui leur sont affectées
        else:

            actions_base = (
                actions_base.filter(
                    responsable=profil
                )
            )


        actions_resultats = list(
            actions_base
            .filter(
                Q(description__icontains=query)
                |
                Q(
                    non_conformite__reference__icontains=query
                )
                |
                Q(
                    non_conformite__description__icontains=query
                )
                |
                Q(responsable__nom__icontains=query)
                |
                Q(responsable__prenom__icontains=query)
            )
            .order_by(
                'date_echeance'
            )[:10]
        )


        # ==================================================
        # 7. UTILISATEURS
        # ADMIN UNIQUEMENT
        # ==================================================

        if profil.role == 'ADMIN':

            utilisateurs_resultats = list(
                Utilisateur.objects
                .select_related(
                    'user',
                    'unite'
                )
                .filter(
                    Q(nom__icontains=query)
                    |
                    Q(prenom__icontains=query)
                    |
                    Q(email__icontains=query)
                    |
                    Q(user__username__icontains=query)
                    |
                    Q(unite__nom__icontains=query)
                    |
                    Q(role__icontains=query)
                )
                .order_by(
                    'nom',
                    'prenom'
                )[:10]
            )


        # ==================================================
        # 8. HISTORIQUE
        # ADMIN UNIQUEMENT
        # ==================================================

        if profil.role == 'ADMIN':

            historiques_resultats = list(
                Historique.objects
                .select_related(
                    'utilisateur'
                )
                .filter(
                    Q(action__icontains=query)
                    |
                    Q(
                        utilisateur__nom__icontains=query
                    )
                    |
                    Q(
                        utilisateur__prenom__icontains=query
                    )
                )
                .order_by(
                    '-date_action'
                )[:10]
            )


    # ======================================================
    # NOMBRE TOTAL DE RÉSULTATS
    # ======================================================

    nombre_resultats = (
        len(processus_resultats)
        + len(documents_resultats)
        + len(audits_resultats)
        + len(non_conformites_resultats)
        + len(actions_resultats)
        + len(unites_resultats)
        + len(utilisateurs_resultats)
        + len(historiques_resultats)
    )


    # ======================================================
    # AFFICHAGE
    # ======================================================

    return render(
        request,
        'smq/recherche_globale.html',
        {
            'query':
                query,

            'processus_resultats':
                processus_resultats,

            'documents_resultats':
                documents_resultats,

            'audits_resultats':
                audits_resultats,

            'non_conformites_resultats':
                non_conformites_resultats,

            'actions_resultats':
                actions_resultats,

            'unites_resultats':
                unites_resultats,

            'utilisateurs_resultats':
                utilisateurs_resultats,

            'historiques_resultats':
                historiques_resultats,

            'nombre_resultats':
                nombre_resultats,
        }
    )


# ==========================================================
# CENTRE DE NOTIFICATIONS
# ==========================================================

@login_required
def notifications(request):

    # ======================================================
    # 1. PROFIL UTILISATEUR
    # ======================================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    aujourd_hui = timezone.localdate()

    # ======================================================
    # 2. INITIALISATION
    # ======================================================

    documents_validation = []
    versions_validation = []
    audits_actifs = []
    non_conformites_actives = []
    actions_en_attente = []
    actions_en_retard = []

    # ======================================================
    # 3. NOUVEAUX DOCUMENTS EN ATTENTE DE VALIDATION
    # ======================================================

    if profil.role in ['ADMIN', 'RESP_QUALITE']:

        documents_validation = list(
            Document.objects
            .select_related(
                'processus',
                'auteur'
            )
            .filter(
                statut='EN_VALIDATION'
            )
            .order_by(
                '-date_creation',
                '-id'
            )[:10]
        )

    # ======================================================
    # 4. NOUVELLES VERSIONS EN ATTENTE DE VALIDATION
    # ======================================================

    if profil.role in ['ADMIN', 'RESP_QUALITE']:

        versions_validation = list(
            VersionDocument.objects
            .select_related(
                'document',
                'document__processus'
            )
            .filter(
                statut='EN_VALIDATION'
            )
            .order_by(
                '-date_creation'
            )[:10]
        )

    # ======================================================
    # 5. AUDITS ACTIFS
    # ======================================================

    if profil.role in ['ADMIN', 'RESP_QUALITE']:

        audits_actifs = list(
            Audit.objects
            .select_related(
                'auditeur',
                'unite'
            )
            .filter(
                statut__in=[
                    'PLANIFIE',
                    'EN_COURS'
                ]
            )
            .order_by(
                'date_audit'
            )[:10]
        )

    elif profil.role == 'AUDITEUR':

        audits_actifs = list(
            Audit.objects
            .select_related(
                'auditeur',
                'unite'
            )
            .filter(
                auditeur=profil,
                statut__in=[
                    'PLANIFIE',
                    'EN_COURS'
                ]
            )
            .order_by(
                'date_audit'
            )[:10]
        )

    # ======================================================
    # 6. NON-CONFORMITÉS ACTIVES
    # ======================================================

    if profil.role in ['ADMIN', 'RESP_QUALITE']:

        non_conformites_actives = list(
            NonConformite.objects
            .select_related('audit')
            .filter(
                statut__in=[
                    'OUVERTE',
                    'EN_COURS'
                ]
            )
            .order_by('-id')[:10]
        )

    elif profil.role == 'AUDITEUR':

        non_conformites_actives = list(
            NonConformite.objects
            .select_related('audit')
            .filter(
                audit__auditeur=profil,
                statut__in=[
                    'OUVERTE',
                    'EN_COURS'
                ]
            )
            .order_by('-id')[:10]
        )

    # ======================================================
    # 7. ACTIONS CORRECTIVES
    # ======================================================

    actions_base = (
        ActionCorrective.objects
        .select_related(
            'non_conformite',
            'responsable'
        )
        .filter(
            statut__in=[
                'A_FAIRE',
                'EN_COURS'
            ]
        )
    )

    # ADMIN et RESPONSABLE QUALITÉ :
    # toutes les actions actives

    if profil.role in ['ADMIN', 'RESP_QUALITE']:
        pass

    # Autres rôles :
    # uniquement leurs propres actions

    else:
        actions_base = actions_base.filter(
            responsable=profil
        )

    # ======================================================
    # 8. ACTIONS CORRECTIVES NON ÉCHUES
    # ======================================================

    actions_en_attente = list(
        actions_base
        .filter(
            date_echeance__gte=aujourd_hui
        )
        .order_by(
            'date_echeance'
        )[:10]
    )

    # ======================================================
    # 9. ACTIONS CORRECTIVES EN RETARD
    # ======================================================

    actions_en_retard = list(
        actions_base
        .filter(
            date_echeance__lt=aujourd_hui
        )
        .order_by(
            'date_echeance'
        )[:10]
    )

    # ======================================================
    # 10. CALCUL DU NOMBRE TOTAL DE NOTIFICATIONS
    # ======================================================

    nombre_notifications = (
        len(documents_validation)
        + len(versions_validation)
        + len(audits_actifs)
        + len(non_conformites_actives)
        + len(actions_en_attente)
        + len(actions_en_retard)
    )

    # ======================================================
    # 11. AFFICHAGE
    # ======================================================

    return render(
        request,
        'smq/notifications.html',
        {
            'documents_validation': documents_validation,
            'versions_validation': versions_validation,
            'audits_actifs': audits_actifs,
            'non_conformites_actives': non_conformites_actives,
            'actions_en_attente': actions_en_attente,
            'actions_en_retard': actions_en_retard,
            'nombre_notifications': nombre_notifications,
            'aujourd_hui': aujourd_hui,
        }
    )


# ==========================================================
# VÉRIFIER L'EFFICACITÉ D'UNE ACTION CORRECTIVE
# ==========================================================

@login_required
@require_POST
def verifier_efficacite_action(request, action_id):

    # ==========================================
    # 1. RÉCUPÉRER LE PROFIL
    # ==========================================

    try:
        profil = request.user.profil_smq

    except Utilisateur.DoesNotExist:
        messages.error(
            request,
            "Votre compte ne possède pas de profil SMQ."
        )
        return redirect('dashboard')

    # ==========================================
    # 2. RÉCUPÉRER L'ACTION CORRECTIVE
    # ==========================================

    action = get_object_or_404(
        ActionCorrective.objects.select_related(
            'non_conformite__audit'
        ),
        id=action_id
    )

    non_conformite = action.non_conformite

    # ==========================================
    # 3. VÉRIFIER LE RÔLE
    # ==========================================

    if profil.role != 'AUDITEUR':

        messages.error(
            request,
            "Seul un auditeur peut vérifier "
            "l'efficacité d'une action corrective."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # 4. VÉRIFIER L'AFFECTATION
    # ==========================================

    if (
        non_conformite.audit_id is None
        or non_conformite.audit.auditeur_id != profil.id
    ):

        messages.error(
            request,
            "Vous pouvez uniquement vérifier les actions "
            "correctives liées à vos propres audits."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # 5. VÉRIFIER LE STATUT DE L'ACTION
    # ==========================================

    if action.statut != 'TERMINEE':

        messages.error(
            request,
            "L'action corrective doit être terminée "
            "avant la vérification de son efficacité."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # 6. VÉRIFIER LA NON-CONFORMITÉ
    # ==========================================

    if non_conformite.statut != 'RESOLUE':

        messages.error(
            request,
            "La non-conformité doit être résolue "
            "avant la vérification d'efficacité."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # 7. RÉCUPÉRER LES DONNÉES DU FORMULAIRE
    # ==========================================

    resultat = request.POST.get(
        'resultat_verification',
        ''
    ).strip()

    observation = request.POST.get(
        'observation_verification',
        ''
    ).strip()

    # ==========================================
    # 8. VALIDER LE RÉSULTAT
    # ==========================================

    if resultat not in ['EFFICACE', 'NON_EFFICACE']:

        messages.error(
            request,
            "Veuillez sélectionner un résultat valide."
        )

        return redirect('liste_actions_correctives')

    if not observation:

        messages.error(
            request,
            "Veuillez saisir une observation "
            "pour justifier votre évaluation."
        )

        return redirect('liste_actions_correctives')

    # ==========================================
    # 9. ENREGISTRER LA VÉRIFICATION
    # ==========================================

    action.resultat_verification = resultat

    action.observation_verification = observation

    action.verifiee_par = profil

    action.date_verification = timezone.now()

    action.save(
        update_fields=[
            'resultat_verification',
            'observation_verification',
            'verifiee_par',
            'date_verification'
        ]
    )

    # ==========================================
    # 10. HISTORIQUE
    # ==========================================

    enregistrer_historique(
        request,
        f"Vérification d'efficacité de l'action "
        f"{action.id} liée à "
        f"{non_conformite.reference} : "
        f"{resultat} - {observation}"
    )

    # ==========================================
    # 11. CONFIRMATION
    # ==========================================

    messages.success(
        request,
        "La vérification d'efficacité "
        "a été enregistrée avec succès."
    )

    return redirect('liste_actions_correctives')



def action_non_efficace_a_remplacer(nc, actions):
    """
    Vérifie s'il existe une action non efficace
    qui n'a pas encore été remplacée.
    """

    if nc.audit_id is None:
        return False

    ids_remplaces = {
        action.action_remplacee_id
        for action in actions
        if action.action_remplacee_id is not None
    }

    return any(
        action.id not in ids_remplaces
        and action.statut == 'TERMINEE'
        and action.resultat_verification == 'NON_EFFICACE'
        and action.verifiee_par_id == nc.audit.auditeur_id
        and action.date_verification is not None
        for action in actions
    )


def actions_pretes_pour_cloture(nc, actions):
    """
    Une NC peut être clôturée si :
    - toutes les actions sont terminées et vérifiées ;
    - les anciennes actions non efficaces sont remplacées ;
    - toutes les actions finales sont efficaces.
    """

    if not actions or nc.audit_id is None:
        return False

    auditeur_id = nc.audit.auditeur_id

    if auditeur_id is None:
        return False

    actions_par_id = {
        action.id: action
        for action in actions
    }

    ids_remplaces = set()

    # Vérifier les liens de remplacement.
    for action in actions:

        ancienne_id = action.action_remplacee_id

        if ancienne_id is None:
            continue

        ancienne = actions_par_id.get(ancienne_id)

        if ancienne is None:
            return False

        if ancienne.id == action.id:
            return False

        if ancienne.id in ids_remplaces:
            return False

        if ancienne.resultat_verification != 'NON_EFFICACE':
            return False

        ids_remplaces.add(ancienne.id)

    # Vérifier les résultats d'efficacité.
    for action in actions:

        if action.statut != 'TERMINEE':
            return False

        if action.verifiee_par_id != auditeur_id:
            return False

        if action.date_verification is None:
            return False

        if action.id in ids_remplaces:
            # Ancienne action remplacée :
            # son résultat négatif reste conservé.
            if action.resultat_verification != 'NON_EFFICACE':
                return False

        else:
            # Action finale :
            # elle doit être efficace.
            if action.resultat_verification != 'EFFICACE':
                return False

    return True


