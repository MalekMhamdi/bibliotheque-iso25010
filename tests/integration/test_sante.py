"""Tests de santé : le serveur démarre et répond."""


def test_health_repond_ok(client):
    # Agir : on visite l'adresse /health/
    reponse = client.get("/health/")

    # Vérifier : le serveur répond 200 (OK) avec le bon contenu
    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}