"""Journalisation (EF-10) des actions faites dans /admin : écrite une seule fois."""

from audit.models import JournalAudit
from audit.services import journaliser


class JournalAdminMixin:
    """À placer AVANT admin.ModelAdmin / UserAdmin dans la liste des parents."""

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        action = JournalAudit.Action.MODIFICATION if change else JournalAudit.Action.CREATION
        journaliser(request.user, action, obj)

    def delete_model(self, request, obj):
        pk = obj.pk  # après delete(), pk vaut None
        super().delete_model(request, obj)
        journaliser(request.user, JournalAudit.Action.SUPPRESSION, obj, entite_id=pk)

    def delete_queryset(self, request, queryset):
        """Action « Supprimer la sélection » : une entrée par objet supprimé."""
        objets = [(obj, obj.pk) for obj in queryset]
        super().delete_queryset(request, queryset)
        for obj, pk in objets:
            journaliser(request.user, JournalAudit.Action.SUPPRESSION, obj, entite_id=pk)
