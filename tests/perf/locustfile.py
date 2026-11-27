"""Test de charge EQ-02 : 20 utilisateurs, liste, recherche, page 2, mes prêts."""

import random

from locust import HttpUser, between, task

MOTS = ["roman", "histoire", "science", "art", "voyage", "cuisine", "BD", "poésie"]


class Adherent(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        page = self.client.get("/comptes/connexion/")
        jeton = self.client.cookies.get("csrftoken")
        reponse = self.client.post(
            "/comptes/connexion/",
            {
                "username": "adherent_api",
                "password": "MotDePasse!2026",
                "csrfmiddlewaretoken": jeton,
            },
            headers={"Referer": self.host + "/comptes/connexion/"},
        )
        assert page.status_code == 200
        assert reponse.status_code == 200

    @task(4)
    def liste(self):
        self.client.get("/catalogue/livres/", name="/catalogue/livres/")

    @task(3)
    def recherche(self):
        self.client.get(f"/catalogue/livres/?q={random.choice(MOTS)}", name="/catalogue/livres/?q=")

    @task(2)
    def page_2(self):
        self.client.get("/catalogue/livres/?page=2", name="/catalogue/livres/?page=2")

    @task(1)
    def mes_prets(self):
        self.client.get("/prets/mes-prets/", name="/prets/mes-prets/")
