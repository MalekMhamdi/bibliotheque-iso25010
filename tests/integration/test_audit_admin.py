"""EF-10 : les actions faites dans /admin sont aussi journalisées."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from audit.models import JournalAudit
from catalogue.models import Auteur

pytestmark = pytest.mark.django_db
A = JournalAudit.Action


@pytest.fixture
def admin_client(client):
    superuser = get_user_model().objects.create_superuser(
        username="root", email="root@exemple.com", password="MotDePasse!2026"
    )
    client.force_login(superuser)
    return client, superuser


def test_creation_dans_l_admin_est_journalisee(admin_client):
    client, superuser = admin_client

    client.post(reverse("admin:catalogue_auteur_add"), {"nom": "Victor Hugo", "nationalite": "FR"})

    entree = JournalAudit.objects.get()
    assert entree.utilisateur == superuser
    assert entree.action == A.CREATION
    assert entree.entite == "Auteur"


def test_modification_dans_l_admin_est_journalisee(admin_client):
    client, _ = admin_client
    auteur = Auteur.objects.create(nom="Zola", nationalite="FR")

    client.post(
        reverse("admin:catalogue_auteur_change", args=[auteur.pk]),
        {"nom": "Émile Zola", "nationalite": "FR"},
    )

    entree = JournalAudit.objects.get()
    assert entree.action == A.MODIFICATION
    assert entree.entite_id == auteur.pk


def test_suppression_dans_l_admin_est_journalisee(admin_client):
    client, _ = admin_client
    auteur = Auteur.objects.create(nom="Zola", nationalite="FR")
    pk = auteur.pk

    client.post(reverse("admin:catalogue_auteur_delete", args=[pk]), {"post": "yes"})

    assert not Auteur.objects.filter(pk=pk).exists()
    entree = JournalAudit.objects.get()
    assert entree.action == A.SUPPRESSION
    assert entree.entite_id == pk


def test_suppression_groupee_dans_l_admin_est_journalisee(admin_client):
    client, _ = admin_client
    a1 = Auteur.objects.create(nom="A1")
    a2 = Auteur.objects.create(nom="A2")

    client.post(
        reverse("admin:catalogue_auteur_changelist"),
        {"action": "delete_selected", "_selected_action": [a1.pk, a2.pk], "post": "yes"},
    )

    assert not Auteur.objects.exists()
    assert JournalAudit.objects.filter(action=A.SUPPRESSION).count() == 2


def test_penalite_impayee_modifiable_dans_l_admin(admin_client):
    """RM-04 : l'admin peut solder la pénalité d'un adhérent."""
    client, _ = admin_client
    adherent = get_user_model().objects.create_user(
        username="adh", email="adh@exemple.com", password="MotDePasse!2026"
    )
    adherent.penalite_impayee = Decimal("5.00")
    adherent.save()

    reponse = client.get(reverse("admin:comptes_utilisateur_change", args=[adherent.pk]))

    assert 'name="penalite_impayee"' in reponse.content.decode()
