from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UniteOrganisationnelle(models.Model):

    nom = models.CharField(max_length=150)

    type = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    # Statut de l'unité : active ou inactive
    actif = models.BooleanField(default=True)

    # Hiérarchie organisationnelle
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sous_unites',
        verbose_name='Unité parente'
    )

    def clean(self):
        super().clean()

        # Une unité peut ne pas avoir de parent
        if self.parent_id is None:
            return

        # Interdire qu'une unité soit son propre parent
        if (
            self.pk is not None
            and self.parent_id == self.pk
        ):
            raise ValidationError({
                'parent':
                "Une unité ne peut pas être son propre parent."
            })

        # Empêcher les relations circulaires
        ancetre_id = self.parent_id
        identifiants_visites = set()

        while ancetre_id is not None:

            if (
                ancetre_id == self.pk
                or ancetre_id in identifiants_visites
            ):
                raise ValidationError({
                    'parent':
                    "Cette hiérarchie créerait une relation circulaire."
                })

            identifiants_visites.add(ancetre_id)

            ancetre_id = (
                UniteOrganisationnelle.objects
                .filter(pk=ancetre_id)
                .values_list('parent_id', flat=True)
                .first()
            )

    def save(self, *args, **kwargs):

        # Vérifier la hiérarchie avant l'enregistrement
        self.clean()

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.nom

class Utilisateur(models.Model):

    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('RESP_QUALITE', 'Responsable qualité'),
        ('RESP_DIRECTION', 'Responsable de direction'),
        ('PILOTE', 'Pilote de processus'),
        ('AUDITEUR', 'Auditeur'),
        ('CONTRIBUTEUR', 'Contributeur'),
    ]
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='profil_smq'
)

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES
    )

    actif = models.BooleanField(default=True)

    unite = models.ForeignKey(
        UniteOrganisationnelle,
        on_delete=models.CASCADE,
        related_name='utilisateurs'
    )

    def __str__(self):
        return f"{self.prenom} {self.nom}"

class Processus(models.Model):
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    objectif = models.CharField(max_length=255)
    actif = models.BooleanField(default=True)

    unite = models.ForeignKey(
        UniteOrganisationnelle,
        on_delete=models.CASCADE,
        related_name='processus'
    )

    pilote = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processus_pilotes'
    )

    def __str__(self):
        return self.nom    

class Document(models.Model):

    TYPE_CHOICES = [
        ('PROCEDURE', 'Procédure'),
        ('INSTRUCTION', 'Instruction'),
        ('FORMULAIRE', 'Formulaire'),
        ('POLITIQUE', 'Politique'),
        ('MANUEL', 'Manuel'),
        ('ENREGISTREMENT', 'Enregistrement'),
    ]

    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('EN_VALIDATION', 'En validation'),
        ('VALIDE', 'Validé'),
        ('PUBLIE', 'Publié'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='BROUILLON'
    )

    date_creation = models.DateField(auto_now_add=True)

    processus = models.ForeignKey(
        Processus,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    auteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_crees'
    )

    def __str__(self):
        return self.titre


class VersionDocument(models.Model):

    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('EN_VALIDATION', 'En validation'),
        ('VALIDE', 'Validé'),
        ('PUBLIE', 'Publié'),
        ('ARCHIVE', 'Archivé'),
    ]

    numero_version = models.CharField(
        max_length=20
    )

    fichier = models.FileField(
        upload_to='documents/'
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    commentaire = models.TextField(
        blank=True
    )

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )

    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='versions_creees'
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='BROUILLON'
    )

    def __str__(self):
        return f"{self.document.titre} - Version {self.numero_version}"





class Audit(models.Model):

    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifié'),
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]

    reference = models.CharField(
        max_length=50,
        unique=True
    )

    titre = models.CharField(
        max_length=200
    )

    date_audit = models.DateField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PLANIFIE'
    )

    unite = models.ForeignKey(
        UniteOrganisationnelle,
        on_delete=models.CASCADE,
        related_name='audits'
    )

    auditeur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audits_realises'
    )

    def __str__(self):
        return f"{self.reference} - {self.titre}"


class NonConformite(models.Model):

    GRAVITE_CHOICES = [
        ('MINEURE', 'Mineure'),
        ('MAJEURE', 'Majeure'),
        ('CRITIQUE', 'Critique'),
    ]

    STATUT_CHOICES = [
        ('OUVERTE', 'Ouverte'),
        ('EN_COURS', 'En cours de traitement'),
        ('RESOLUE', 'Résolue'),
        ('CLOTUREE', 'Clôturée'),
    ]

    

    reference = models.CharField(
        max_length=50,
        unique=True
    )

    description = models.TextField()

    gravite = models.CharField(
        max_length=20,
        choices=GRAVITE_CHOICES
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='OUVERTE'
    )

    

    audit = models.ForeignKey(
        Audit,
        on_delete=models.CASCADE,
        related_name='non_conformites'
    )

    

    pris_en_charge_par = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='non_conformites_prises_en_charge',
        verbose_name='Pris en charge par'
    )

    date_prise_en_charge = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de prise en charge'
    )

    

    def __str__(self):
        return self.reference



class ActionCorrective(models.Model):

    # ==========================================
    # STATUTS DES ACTIONS CORRECTIVES
    # ==========================================

    STATUT_CHOICES = [
        ('A_FAIRE', 'À faire'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    ]

    # ==========================================
    # RÉSULTATS DE VÉRIFICATION D'EFFICACITÉ
    # ==========================================

    RESULTAT_VERIFICATION_CHOICES = [
        ('EFFICACE', 'Efficace'),
        ('NON_EFFICACE', 'Non efficace'),
    ]

    # ==========================================
    # INFORMATIONS DE L'ACTION CORRECTIVE
    # ==========================================

    description = models.TextField()

    date_echeance = models.DateField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='A_FAIRE'
    )

    # ==========================================
    # NON-CONFORMITÉ ASSOCIÉE
    # ==========================================

    non_conformite = models.ForeignKey(
        NonConformite,
        on_delete=models.CASCADE,
        related_name='actions_correctives'
    )

    # ==========================================
    # PILOTE RESPONSABLE DE L'ACTION
    # ==========================================

    responsable = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_correctives'
    )

    # ==========================================
    # VÉRIFICATION D'EFFICACITÉ
    # ==========================================

    # Résultat de la vérification effectuée
    # par l'auditeur.

    resultat_verification = models.CharField(
        max_length=20,
        choices=RESULTAT_VERIFICATION_CHOICES,
        null=True,
        blank=True
    )

    # Observation ou justification de l'auditeur.

    observation_verification = models.TextField(
        blank=True
    )

    # Auditeur ayant effectué la vérification.

    verifiee_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_verifiees'
    )

    # Date et heure de la vérification.

    date_verification = models.DateTimeField(
        null=True,
        blank=True
    )
       # Lien vers l'ancienne action corrective
    # lorsque celle-ci a été jugée non efficace.

    action_remplacee = models.OneToOneField(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='action_de_remplacement',
        verbose_name="Action corrective remplacée"
    )


    # ==========================================
    # AFFICHAGE
    # ==========================================

    def __str__(self):
        return (
            f"Action {self.id} - "
            f"{self.non_conformite.reference}"
        )



class Historique(models.Model):
    action = models.CharField(max_length=255)

    date_action = models.DateTimeField(
        auto_now_add=True
    )

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historiques'
    )

    def __str__(self):
        return f"{self.action} - {self.date_action}"