"""E2E EQ-03 / EF-01 : connexion dans un vrai navigateur."""

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

MOT_DE_PASSE = "MotDePasse!2026"  # celui de la fixture creer_utilisateur


def _ouvrir_connexion(live_server, page):
    page.goto(f"{live_server.url}/comptes/connexion/")


def test_connexion_reussie(live_server, page, creer_utilisateur):
    creer_utilisateur("ADHERENT")  # nom d'utilisateur : "adherent"
    _ouvrir_connexion(live_server, page)
    page.fill("input[name=username]", "adherent")
    page.fill("input[name=password]", MOT_DE_PASSE)
    page.click("button[type=submit], input[type=submit]")
    page.wait_for_url(f"{live_server.url}/")
    assert "/comptes/connexion" not in page.url


def test_connexion_refusee_mauvais_mot_de_passe(live_server, page, creer_utilisateur):
    creer_utilisateur("ADHERENT")
    _ouvrir_connexion(live_server, page)
    page.fill("input[name=username]", "adherent")
    page.fill("input[name=password]", "mauvais")
    page.click("button[type=submit], input[type=submit]")
    assert "/comptes/connexion" in page.url
    assert page.locator("input[name=password]").is_visible()
