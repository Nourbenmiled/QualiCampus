from django.contrib import admin
from .models import (
    UniteOrganisationnelle,
    Utilisateur,
    Processus,
    Document,
    VersionDocument,
    Audit,
    NonConformite,
    ActionCorrective,
    Historique,
)


admin.site.register(UniteOrganisationnelle)
admin.site.register(Utilisateur)
admin.site.register(Processus)
admin.site.register(Document)
admin.site.register(VersionDocument)
admin.site.register(Audit)
admin.site.register(NonConformite)
admin.site.register(ActionCorrective)
admin.site.register(Historique)