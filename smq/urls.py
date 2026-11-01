from django.urls import path
from . import views

urlpatterns = [

    path('login/', views.connexion, name='login'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('logout/', views.deconnexion, name='logout'),

    path(
        'utilisateurs/',
        views.liste_utilisateurs,
        name='liste_utilisateurs'
    ),

    path(
        'utilisateurs/ajouter/',
        views.creer_utilisateur,
        name='creer_utilisateur'
    ),


    path(
    'utilisateurs/<int:utilisateur_id>/modifier/',
    views.modifier_utilisateur,
    name='modifier_utilisateur'
),


   path(
    'utilisateurs/<int:utilisateur_id>/statut/',
    views.changer_statut_utilisateur,
    name='changer_statut_utilisateur'
),
path(
    'unites/',
    views.liste_unites,
    name='liste_unites'
),

path(
    'unites/ajouter/',
    views.creer_unite,
    name='creer_unite'
),

path(
    'unites/<int:unite_id>/modifier/',
    views.modifier_unite,
    name='modifier_unite'
),


path(
    'processus/',
    views.liste_processus,
    name='liste_processus'
),


path(
    'processus/ajouter/',
    views.creer_processus,
    name='creer_processus'
),


path(
    'processus/<int:processus_id>/modifier/',
    views.modifier_processus,
    name='modifier_processus'
),
path(
    'processus/<int:processus_id>/supprimer/',
    views.supprimer_processus,
    name='supprimer_processus'
),

path(
    'processus/<int:processus_id>/statut/',
    views.changer_statut_processus,
    name='changer_statut_processus'
),


path(
    'documents/',
    views.liste_documents,
    name='liste_documents'
),

path(
    'documents/ajouter/',
    views.creer_document,
    name='creer_document'
),


path(
    'documents/<int:document_id>/versions/ajouter/',
    views.ajouter_version_document,
    name='ajouter_version_document'
),


path(
    'documents/<int:document_id>/versions/',
    views.liste_versions_document,
    name='liste_versions_document'
),

path(
    'documents/<int:document_id>/soumettre/',
    views.soumettre_document,
    name='soumettre_document'
),


path(
    'documents/<int:document_id>/valider/',
    views.valider_document,
    name='valider_document'
),



path(
    'documents/<int:document_id>/publier/',
    views.publier_document,
    name='publier_document'
),

path(
    'documents/publies/',
    views.documents_publies,
    name='documents_publies'
),


path(
    'audits/',
    views.liste_audits,
    name='liste_audits'
),

path(
    'audits/ajouter/',
    views.creer_audit,
    name='creer_audit'
),

path(
    'audits/<int:audit_id>/modifier/',
    views.modifier_audit,
    name='modifier_audit'
),

# =========================
# NON-CONFORMITÉS
# =========================

path(
    'non-conformites/',
    views.liste_non_conformites,
    name='liste_non_conformites'
),

path(
    'non-conformites/ajouter/',
    views.creer_non_conformite,
    name='creer_non_conformite'
),


path(
    'non-conformites/<int:nc_id>/modifier/',
    views.modifier_non_conformite,
    name='modifier_non_conformite'
),


# =========================
# ACTIONS CORRECTIVES
# =========================

path(
    'actions-correctives/',
    views.liste_actions_correctives,
    name='liste_actions_correctives'
),

path(
    'actions-correctives/ajouter/',
    views.creer_action_corrective,
    name='creer_action_corrective'
),



path(
    'actions-correctives/<int:action_id>/modifier/',
    views.modifier_action_corrective,
    name='modifier_action_corrective'
),



path(
    'historique/',
    views.liste_historique,
    name='liste_historique'
),



path(
    'documents/<int:document_id>/demander-modification/',
    views.demander_modification_document,
    name='demander_modification_document'
),

path(
    'audits/<int:audit_id>/demarrer/',
    views.demarrer_audit,
    name='demarrer_audit'
),

path(
    'audits/<int:audit_id>/terminer/',
    views.terminer_audit,
    name='terminer_audit'
),

path(
    'non-conformites/<int:nc_id>/demarrer-traitement/',
    views.demarrer_traitement_non_conformite,
    name='demarrer_traitement_non_conformite'
),

path(
    'non-conformites/<int:nc_id>/resoudre/',
    views.resoudre_non_conformite,
    name='resoudre_non_conformite'
),

path(
    'non-conformites/<int:nc_id>/cloturer/',
    views.cloturer_non_conformite,
    name='cloturer_non_conformite'
),


path(
    'actions-correctives/<int:action_id>/demarrer/',
    views.demarrer_action_corrective,
    name='demarrer_action_corrective'
),

path(
    'actions-correctives/<int:action_id>/terminer/',
    views.terminer_action_corrective,
    name='terminer_action_corrective'
),

path(
    'documents/<int:document_id>/supprimer/',
    views.supprimer_document,
    name='supprimer_document'
),


path(
    'versions/<int:version_id>/soumettre/',
    views.soumettre_version_document,
    name='soumettre_version_document'
),

path(
    'versions/<int:version_id>/demander-modification/',
    views.demander_modification_version_document,
    name='demander_modification_version_document'
),



path(
    'versions/<int:version_id>/valider/',
    views.valider_version_document,
    name='valider_version_document'
),



path(
    'versions/<int:version_id>/modifier/',
    views.modifier_version_document,
    name='modifier_version_document'
),


path(
    'versions/<int:version_id>/publier/',
    views.publier_version_document,
    name='publier_version_document'
),



path(
    'parametres/',
    views.parametres,
    name='parametres'
),
path(
    'parametres/mot-de-passe/',
    views.modifier_mot_de_passe,
    name='modifier_mot_de_passe'
),
path(
    'recherche/',
    views.recherche_globale,
    name='recherche_globale'
),
path(
    'notifications/',
    views.notifications,
    name='notifications'
),
path(
    'actions-correctives/<int:action_id>/verifier-efficacite/',
    views.verifier_efficacite_action,
    name='verifier_efficacite_action'
),


path(
    'non-conformites/<int:nc_id>/reprendre/',
    views.reprendre_traitement_non_conformite,
    name='reprendre_traitement_non_conformite'
),

path(
    'unites/<int:unite_id>/supprimer/',
    views.supprimer_unite,
    name='supprimer_unite'
),


path(
    'unites/<int:unite_id>/statut/',
    views.changer_statut_unite,
    name='changer_statut_unite'
),



path(
    'utilisateurs/<int:utilisateur_id>/supprimer/',
    views.supprimer_utilisateur,
    name='supprimer_utilisateur'
),

path(
    'documents/<int:document_id>/modifier/',
    views.modifier_document,
    name='modifier_document'
),

path(
    'audits/<int:audit_id>/annuler/',
    views.annuler_audit,
    name='annuler_audit'
),

]

