from audit.models import JournalAudit


def journaliser(utilisateur, action, objet, detail="", *, entite_id=None):
    """EF-10 : enregistre qui a fait quoi, sur quel objet (la date est automatique).

    entite_id est utile pour une suppression : après delete(), objet.pk vaut None.
    """
    if not getattr(utilisateur, "is_authenticated", False):
        utilisateur = None
    return JournalAudit.objects.create(
        utilisateur=utilisateur,
        action=action,
        entite=type(objet).__name__,
        entite_id=entite_id if entite_id is not None else objet.pk,
        detail=detail,
    )