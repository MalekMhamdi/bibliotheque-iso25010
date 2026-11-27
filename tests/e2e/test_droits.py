"""E2E EF-02 : contrôle d'accès vu depuis un vrai navigateur."""

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

MOT_DE_PASSE = "MotDePasse!2026"


def _se_connecter(live_server, page, nom):
    page.goto(f"{live_server.url}/comptes/connexion/")
    page.fill("input[name=username]", nom)
    page.fill("input[name=password]", MOT_DE_PASSE)
    page.click("button[type=submit], input[type=submit]")
    page.wait_for_url(f"{live_server.url}/")


def test_adherent_acces_direct_utilisateurs_refuse(live_server, page, creer_utilisateur):
    creer_utilisateur("ADHERENT")
    _se_connecter(live_server, page, "adherent")
    reponse = page.goto(f"{live_server.url}/comptes/utilisateurs/")
    assert reponse.status == 403


def test_adherent_ne_voit_pas_le_lien_utilisateurs(live_server, page, creer_utilisateur):
    creer_utilisateur("ADHERENT")
    _se_connecter(live_server, page, "adherent")
    assert page.locator("a[href='/comptes/utilisateurs/']").count() == 0


def test_admin_acces_utilisateurs_autorise(live_server, page, creer_utilisateur):
    creer_utilisateur("ADMIN")
    _se_connecter(live_server, page, "admin")
    reponse = page.goto(f"{live_server.url}/comptes/utilisateurs/")
    assert reponse.status == 200
