
from django import forms
from django.contrib.auth.models import User
from django.db.models import F, Q

from .models import (
    Utilisateur,
    UniteOrganisationnelle,
    Processus,
    Document,
    VersionDocument,
    Audit,
    NonConformite,
    ActionCorrective,
)


# =========================================================
#  UNITÉS ACTIVES
# =========================================================

def _unites_actives_ou_actuelle(instance, champ='unite'):

    # Lors d'une création, seules les unités actives
    # peuvent être sélectionnées.
    #
    # Lors d'une modification, on conserve également
    # l'unité déjà affectée, même si elle est inactive.

    unite_id = (
        getattr(instance, f'{champ}_id', None)
        if instance is not None and instance.pk
        else None
    )

    conditions = Q(actif=True)

    if unite_id is not None:
        conditions |= Q(pk=unite_id)

    return (
        UniteOrganisationnelle.objects
        .filter(conditions)
        .order_by('nom')
    )


# =========================================================
# UTILISATEUR - CRÉATION
# =========================================================

class UtilisateurForm(forms.ModelForm):

    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur"
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Mot de passe"
    )

    class Meta:

        model = Utilisateur

        fields = [
            'nom',
            'prenom',
            'email',
            'role',
            'unite',
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['unite'].queryset = (
            _unites_actives_ou_actuelle(
                self.instance,
                'unite'
            )
        )

    def clean_username(self):

        username = self.cleaned_data['username']

        if User.objects.filter(
            username=username
        ).exists():

            raise forms.ValidationError(
                "Ce nom d'utilisateur existe déjà."
            )

        return username


# =========================================================
# UTILISATEUR - MODIFICATION
# =========================================================

class UtilisateurModificationForm(forms.ModelForm):

    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur"
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Nouveau mot de passe",
        required=False,
        help_text=(
            "Laissez vide pour conserver "
            "le mot de passe actuel."
        )
    )

    class Meta:

        model = Utilisateur

        fields = [
            'nom',
            'prenom',
            'email',
            'role',
            'unite',
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['unite'].queryset = (
            _unites_actives_ou_actuelle(
                self.instance,
                'unite'
            )
        )

    def clean_username(self):

        username = self.cleaned_data['username']

        if self.instance and self.instance.user:

            existe = (
                User.objects.filter(
                    username=username
                )
                .exclude(
                    id=self.instance.user.id
                )
                .exists()
            )

        else:

            existe = User.objects.filter(
                username=username
            ).exists()

        if existe:

            raise forms.ValidationError(
                "Ce nom d'utilisateur existe déjà."
            )

        return username


# =========================================================
# UNITÉ ORGANISATIONNELLE
# CRÉATION ET MODIFICATION
# =========================================================

class UniteOrganisationnelleForm(forms.ModelForm):

    class Meta:

        model = UniteOrganisationnelle

        fields = [
            'nom',
            'type',
            'description',
            'parent',
        ]

        labels = {
            'parent': 'Unité parente',
        }

        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': 4
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Une nouvelle unité peut avoir comme parent
        # uniquement une unité active.
        #
        # En modification, le parent déjà enregistré
        # reste disponible même s'il est inactif.

        parents_possibles = (
            _unites_actives_ou_actuelle(
                self.instance,
                'parent'
            )
        )

        # Empêcher une unité d'être son propre parent
        # ou de sélectionner une de ses sous-unités.

        if self.instance.pk:

            enfants = {}

            for unite_id, parent_id in (
                UniteOrganisationnelle.objects
                .values_list('id', 'parent_id')
            ):

                enfants.setdefault(
                    parent_id,
                    []
                ).append(unite_id)

            exclus = {self.instance.pk}

            a_explorer = [self.instance.pk]

            while a_explorer:

                unite_courante = a_explorer.pop()

                for enfant_id in enfants.get(
                    unite_courante,
                    []
                ):

                    if enfant_id not in exclus:

                        exclus.add(enfant_id)

                        a_explorer.append(enfant_id)

            parents_possibles = (
                parents_possibles.exclude(
                    pk__in=exclus
                )
            )

        self.fields['parent'].queryset = (
            parents_possibles
        )

        self.fields['parent'].required = False

        self.fields['parent'].empty_label = (
            "Aucune — unité principale"
        )


# =========================================================
# PROCESSUS
# =========================================================

class ProcessusForm(forms.ModelForm):

    class Meta:

        model = Processus

        fields = [
            'nom',
            'description',
            'objectif',
            'unite',
            'pilote',
            'actif',
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Unités actives uniquement pour les
        # nouvelles affectations.

        self.fields['unite'].queryset = (
            _unites_actives_ou_actuelle(
                self.instance,
                'unite'
            )
        )

        # Seuls les utilisateurs actifs ayant
        # le rôle PILOTE peuvent être sélectionnés.

        self.fields['pilote'].queryset = (
            Utilisateur.objects.filter(
                role='PILOTE',
                actif=True
            ).order_by(
                'nom',
                'prenom'
            )
        )


# =========================================================
# DOCUMENT
# =========================================================

class DocumentForm(forms.ModelForm):

    class Meta:

        model = Document

        fields = [
            'titre',
            'description',
            'type',
            'processus',
        ]


# =========================================================
# VERSION DE DOCUMENT
# =========================================================

class VersionDocumentForm(forms.ModelForm):

    class Meta:

        model = VersionDocument

        # Le numéro de version est généré
        # automatiquement dans views.py.

        fields = [
            'fichier',
            'commentaire',
        ]

        widgets = {
            'commentaire': forms.Textarea(
                attrs={
                    'rows': 4
                }
            ),
        }


# =========================================================
# AUDIT
# =========================================================

class AuditForm(forms.ModelForm):

    reference = forms.CharField(
        label="Référence",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
            }
        )
    )

    titre = forms.CharField(
        label="Titre",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
            }
        )
    )

    class Meta:

        model = Audit

        fields = [
            'reference',
            'titre',
            'date_audit',
            'unite',
            'auditeur',
        ]

        widgets = {
            'date_audit': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Unités actives pour les nouvelles affectations.
        # Conserver l'unité actuelle en modification.

        self.fields['unite'].queryset = (
            _unites_actives_ou_actuelle(
                self.instance,
                'unite'
            )
        )

        # Seuls les auditeurs actifs
        # peuvent être sélectionnés.

        self.fields['auditeur'].queryset = (
            Utilisateur.objects.filter(
                role='AUDITEUR',
                actif=True
            ).order_by(
                'nom',
                'prenom'
            )
        )


# =========================================================
# NON-CONFORMITÉ
# =========================================================

class NonConformiteForm(forms.ModelForm):

    class Meta:

        model = NonConformite

        fields = [
            'reference',
            'description',
            'gravite',
            'audit',
        ]

        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': 4
                }
            ),
        }


# =========================================================
# ACTION CORRECTIVE
# =========================================================

class ActionCorrectiveForm(forms.ModelForm):

    class Meta:

        model = ActionCorrective

        fields = [
            'description',
            'date_echeance',
            'non_conformite',
            'responsable',
            'action_remplacee',
        ]

        widgets = {

            'description': forms.Textarea(
                attrs={
                    'rows': 4
                }
            ),

            'date_echeance': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
        }

        labels = {
            'description': 'Description de l’action corrective',
            'date_echeance': 'Date d’échéance',
            'non_conformite': 'Non-conformité associée',
            'responsable': 'Pilote responsable',
            'action_remplacee': 'Action corrective à remplacer',
        }

    # =====================================================
    # INITIALISATION DU FORMULAIRE
    # =====================================================

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # =================================================
        # PILOTES RESPONSABLES
        # =================================================

        # Seuls les pilotes actifs peuvent être
        # responsables d'une action corrective.

        self.fields['responsable'].queryset = (
            Utilisateur.objects.filter(
                role='PILOTE',
                actif=True
            ).order_by(
                'nom',
                'prenom'
            )
        )

        # =================================================
        # ACTIONS CORRECTIVES REMPLAÇABLES
        # =================================================

        # Une action peut être remplacée si :
        # - elle est terminée ;
        # - elle a été jugée non efficace ;
        # - elle a été vérifiée par l'auditeur affecté ;
        # - sa NC est en cours de traitement ;
        # - elle n'a pas déjà été remplacée.

        actions_remplacables = (
            ActionCorrective.objects.filter(

                statut='TERMINEE',

                resultat_verification='NON_EFFICACE',

                date_verification__isnull=False,

                verifiee_par_id=F(
                    'non_conformite__audit__auditeur_id'
                ),

                non_conformite__statut='EN_COURS',

                action_de_remplacement__isnull=True

            )
        )

        # En modification, conserver l'action
        # précédemment liée dans les choix.

        if (
            self.instance.pk
            and self.instance.action_remplacee_id
        ):

            actions_remplacables = (
                actions_remplacables
                | ActionCorrective.objects.filter(
                    pk=self.instance.action_remplacee_id
                )
            )

        self.fields['action_remplacee'].queryset = (
            actions_remplacables
            .select_related('non_conformite')
            .order_by(
                'non_conformite__reference',
                'id'
            )
        )

        # Le champ est facultatif pour
        # une action corrective initiale.

        self.fields['action_remplacee'].required = False

        self.fields['action_remplacee'].empty_label = (
            "Aucune — nouvelle action initiale"
        )

        self.fields['action_remplacee'].help_text = (
            "Sélectionnez une ancienne action uniquement "
            "si elle a été jugée non efficace."
        )

        # Affichage explicite des anciennes actions.

        self.fields[
            'action_remplacee'
        ].label_from_instance = lambda action: (
            f"Action n°{action.id} — "
            f"{action.non_conformite.reference} — "
            f"{action.description[:70]}"
        )

    # =====================================================
    # VALIDATION DU FORMULAIRE
    # =====================================================

    def clean(self):

        cleaned_data = super().clean()

        non_conformite = cleaned_data.get(
            'non_conformite'
        )

        action_remplacee = cleaned_data.get(
            'action_remplacee'
        )

        if non_conformite is None:
            return cleaned_data

        # =================================================
        # VÉRIFIER LE STATUT DE LA NON-CONFORMITÉ
        # =================================================

        # Une nouvelle action ne peut être créée
        # que pour une NC en cours de traitement.

        if (
            not self.instance.pk
            and non_conformite.statut != 'EN_COURS'
        ):

            self.add_error(
                'non_conformite',
                "La non-conformité doit être "
                "en cours de traitement."
            )

        # =================================================
        #  VÉRIFIER L'ACTION REMPLACÉE
        # =================================================

        if action_remplacee is not None:

            # L'ancienne action doit appartenir
            # à la même non-conformité.

            if (
                action_remplacee.non_conformite_id
                != non_conformite.id
            ):

                self.add_error(
                    'action_remplacee',
                    "L'action à remplacer doit appartenir "
                    "à la même non-conformité."
                )

            # Elle doit être terminée et
            # avoir un résultat non efficace.

            if (
                action_remplacee.statut != 'TERMINEE'
                or action_remplacee.resultat_verification
                != 'NON_EFFICACE'
            ):

                self.add_error(
                    'action_remplacee',
                    "Seule une action terminée et jugée "
                    "non efficace peut être remplacée."
                )

            # Vérification réalisée par
            # l'auditeur affecté à l'audit.

            if (
                action_remplacee.verifiee_par_id
                != non_conformite.audit.auditeur_id
                or action_remplacee.date_verification is None
            ):

                self.add_error(
                    'action_remplacee',
                    "L'ancienne action doit avoir été "
                    "vérifiée par l'auditeur affecté."
                )

            # Empêcher de remplacer une action
            # qui possède déjà un remplacement.

            remplacement_existant = (
                ActionCorrective.objects.filter(
                    action_remplacee=action_remplacee
                )
                .exclude(
                    pk=self.instance.pk
                )
                .exists()
            )

            if remplacement_existant:

                self.add_error(
                    'action_remplacee',
                    "Cette action corrective possède "
                    "déjà une action de remplacement."
                )

        # =================================================
        #  OBLIGER LE REMPLACEMENT SI NÉCESSAIRE
        # =================================================

        # Pour une nouvelle action, si la NC
        # possède une action non efficace
        # non encore remplacée, il faut
        # sélectionner cette ancienne action.

        if (
            not self.instance.pk
            and non_conformite.statut == 'EN_COURS'
            and action_remplacee is None
        ):

            action_non_efficace_en_attente = (
                ActionCorrective.objects.filter(

                    non_conformite=non_conformite,

                    statut='TERMINEE',

                    resultat_verification='NON_EFFICACE',

                    date_verification__isnull=False,

                    verifiee_par_id=(
                        non_conformite.audit.auditeur_id
                    ),

                    action_de_remplacement__isnull=True

                ).exists()
            )

            if action_non_efficace_en_attente:

                self.add_error(
                    'action_remplacee',
                    "Cette non-conformité possède une "
                    "action non efficace. Sélectionnez "
                    "l'action à remplacer."
                )

        # =================================================
        # PRÉSERVER LE LIEN DE REMPLACEMENT
        # =================================================

        # Une fois créée, la relation entre
        # les deux actions ne doit pas être
        # modifiée depuis ce formulaire.

        if self.instance.pk:

            ancien_id = (
                self.instance.action_remplacee_id
            )

            nouveau_id = (
                action_remplacee.pk
                if action_remplacee is not None
                else None
            )

            if ancien_id != nouveau_id:

                self.add_error(
                    'action_remplacee',
                    "Le lien de remplacement d'une "
                    "action existante ne peut pas "
                    "être modifié."
                )

        return cleaned_data
