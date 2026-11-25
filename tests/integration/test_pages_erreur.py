"""EQ-08 / EQ-05 : une page inexistante affiche une page d'erreur propre."""


def test_page_404_personnalisee(client):
    reponse = client.get("/cette-page-nexiste-pas/")
    assert reponse.status_code == 404
    assert "Page introuvable" in reponse.content.decode()