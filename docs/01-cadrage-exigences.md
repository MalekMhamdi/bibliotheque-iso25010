# 01 – Cadrage et exigences

Projet : **Bibliothèque ISO 25010**. Application web de gestion d'une bibliothèque : catalogue, adhérents, prêts.

Chaque exigence porte un **identifiant** (EF-xx, RM-xx, EQ-xx). Ces identifiants serviront de lignes dans la matrice de traçabilité : exigence ↔ test ↔ outil ↔ résultat.

---

## 1. Rôles et droits

| Action | Admin | Bibliothécaire | Adhérent |
|---|:-:|:-:|:-:|
| Gérer les comptes utilisateurs (CRUD, rôles, activation) | ✅ | ❌ | ❌ |
| Gérer les livres et auteurs (CRUD) | ✅ | ✅ | ❌ |
| Consulter et rechercher le catalogue | ✅ | ✅ | ✅ |
| Réserver un livre pour soi | ❌ | ❌ | ✅ |
| Remettre un livre / enregistrer un retour | ❌ | ✅ | ❌ |
| Annuler une réservation | ❌ | ✅ | ✅ (les siennes) |
| Voir ses propres prêts et pénalités | ✅ | ✅ | ✅ |
| Voir tous les prêts | ✅ | ✅ | ❌ |
| Tableau de bord | ✅ | ✅ | ❌ |
| Journal d'audit | ✅ | ❌ | ❌ |

Toute action non autorisée renvoie **HTTP 403** (API) ou une page « Accès refusé » (web).

---

## 2. Entités et relations

| Entité | Attributs principaux |
|---|---|
| **Utilisateur** | id, nom, email (unique), mot_de_passe_hash, rôle (ADMIN / BIBLIOTHECAIRE / ADHERENT), actif, penalite_impayee |
| **Auteur** | id, nom, nationalité |
| **Livre** | id, titre, isbn (unique, 13 chiffres), année, catégorie, nb_exemplaires |
| **Prêt** | id, utilisateur_id, livre_id, statut, date_reservation, date_emprunt, date_retour_prevue, date_retour_effective, penalite |
| **JournalAudit** | id, utilisateur_id, action, entité, entité_id, date_heure, détail |

Relations :
- **Livre ↔ Auteur : N-N** (un livre a plusieurs auteurs, un auteur écrit plusieurs livres), via une table d'association `livre_auteur`.
- **Utilisateur → Prêt : 1-N**
- **Livre → Prêt : 1-N**
- **Utilisateur → JournalAudit : 1-N**

`nb_disponibles` d'un livre n'est pas stocké : il est **calculé** (nb_exemplaires − prêts actifs). On évite ainsi deux valeurs qui se contredisent.

---

## 3. Workflow d'un prêt

```
            réserver                remettre                rendre
 (aucun) ───────────▶ RESERVE ───────────────▶ EN_COURS ──────────────▶ RENDU
                         │                        │                        ▲
                annuler  │      date dépassée     ▼        rendre          │
                         ▼                    EN_RETARD ───────────────────┘
                      ANNULE
```

| Transition | Qui | Autorisée depuis |
|---|---|---|
| réserver | Adhérent | – (crée le prêt) |
| remettre | Bibliothécaire | RESERVE |
| passer en retard | Système (automatique) | EN_COURS, si aujourd'hui > date_retour_prevue |
| rendre | Bibliothécaire | EN_COURS, EN_RETARD |
| annuler | Adhérent (le sien) ou Bibliothécaire | RESERVE |

**RENDU** et **ANNULE** sont des états **finaux** : aucune transition n'en sort.

Un prêt est dit **actif** s'il est RESERVE, EN_COURS ou EN_RETARD.

---

## 4. Exigences fonctionnelles

| ID | Exigence |
|---|---|
| EF-01 | Un utilisateur se connecte avec email + mot de passe et se déconnecte. |
| EF-02 | Les droits d'accès respectent le tableau de la section 1. |
| EF-03 | CRUD complet des **livres** (avec choix des auteurs). |
| EF-04 | CRUD complet des **auteurs**. |
| EF-05 | CRUD complet des **utilisateurs** (admin). |
| EF-06 | CRUD des **prêts** via le workflow (création = réservation, suppression = annulation). |
| EF-07 | Le workflow des prêts respecte la section 3 ; toute transition interdite est refusée. |
| EF-08 | Recherche du catalogue (≥ 10 000 livres) par titre, auteur, ISBN, catégorie, avec pagination. |
| EF-09 | Tableau de bord : prêts actifs, prêts en retard, top 5 des livres empruntés, total des pénalités, filtre par période. |
| EF-10 | Journal d'audit : chaque création, modification, suppression et transition de prêt est enregistrée (qui, quoi, quand). |

---

## 5. Règles métier (≥ 5, testables)

| ID | Règle | Valeurs de test prévues |
|---|---|---|
| **RM-01** | Un adhérent a **au maximum 3 prêts actifs**. | 2 actifs → accepté · **3 actifs → refusé** (valeur limite) |
| **RM-02** | Durée de prêt : `date_retour_prevue = date_emprunt + 14 jours`. | Emprunt le 01/03 → retour prévu le 15/03 ; passage de fin de mois (25/02 → 11/03) |
| **RM-03** | Pénalité = **0,50 € par jour de retard**, **plafonnée à 10 €**. | 0 j → 0 € · 1 j → 0,50 € · 19 j → 9,50 € · **20 j → 10 €** · **21 j → 10 €** |
| **RM-04** | Un adhérent peut réserver **si** son compte est actif **ET** il n'a aucun prêt EN_RETARD **ET** sa pénalité impayée = 0. | MC/DC : 3 conditions → **4 cas** (voir ci-dessous) |
| **RM-05** | L'**ISBN est unique** et composé de 13 chiffres. | ISBN existant → refusé · 12 ou 14 chiffres → refusé · 13 chiffres nouveaux → accepté |
| **RM-06** | On ne peut réserver un livre que si `nb_disponibles > 0`. | 1 disponible → accepté · **0 disponible → refusé** |
| **RM-07** | Un email ne peut appartenir qu'à un seul utilisateur. | Email déjà utilisé → refusé |

**MC/DC de RM-04** (A = compte actif, B = aucun retard, C = pénalité = 0) :

| Cas | A | B | C | Résultat attendu |
|---|:-:|:-:|:-:|---|
| 1 | V | V | V | autorisé |
| 2 | **F** | V | V | refusé (seul A change) |
| 3 | V | **F** | V | refusé (seul B change) |
| 4 | V | V | **F** | refusé (seul C change) |

---

## 6. Exigences de qualité ISO/IEC 25010 (chiffrées)

| ID | Caractéristique | Exigence mesurable | Outil de preuve |
|---|---|---|---|
| EQ-01 | Aptitude fonctionnelle | 100 % des EF et RM couvertes par ≥ 1 test qui passe | pytest, Playwright |
| EQ-02 | Efficacité de performance | Recherche et listes : **p95 < 500 ms** avec **20 utilisateurs simultanés** pendant 2 min, **0 % d'erreurs** | Locust |
| EQ-03 | Compatibilité | Les parcours E2E passent sur **Chromium et Firefox** ; le contrat de l'API (codes HTTP, format JSON) est vérifié | Playwright, Newman |
| EQ-04 | Facilité d'utilisation | Réserver un livre en **≤ 4 clics** depuis l'accueil ; messages d'erreur explicites ; score **accessibilité Lighthouse ≥ 90** | Playwright, Lighthouse |
| EQ-05 | Fiabilité | Une erreur en cours d'opération **n'enregistre rien de partiel** (rollback) ; les données **survivent à un redémarrage** ; aucune erreur ne fait planter le serveur | pytest (scénarios dédiés), Docker |
| EQ-06 | Sécurité | Mots de passe hachés (bcrypt) ; **403** testé sur chaque route protégée ; **0 alerte High** pour Bandit, pip-audit et OWASP ZAP | pytest, Bandit, pip-audit, ZAP |
| EQ-07 | Maintenabilité | Architecture en couches ; **couverture ≥ 80 %** ; complexité cyclomatique **≤ 10** par fonction ; **0 erreur** de lint | pytest-cov, radon, Ruff |
| EQ-08 | Portabilité | `docker compose up` sur une machine vierge → application disponible ; guide d'installation suivi avec succès par une autre personne | Docker Compose |
