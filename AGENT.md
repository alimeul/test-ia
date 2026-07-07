# AGENT.md

Ce fichier fournit le contexte nécessaire à un agent de codage (Claude Code ou équivalent) pour travailler efficacement sur ce projet. Il est dérivé du cahier des charges v1.1 (juillet 2026).

---

## 1. Résumé du projet

Jeu quotidien type "Wordle" basé sur des articles Wikipédia caviardés (mots-clés masqués). Le joueur doit deviner le titre de l'article à partir du texte partiellement masqué, en proposant des titres et/ou en révélant des indices supplémentaires.

**Cœur technique différenciant : le pipeline NLP de sélection et de caviardage des articles.** C'est la partie qui mérite le plus de rigueur et de tests — le reste (frontend de jeu, scoring, partage) est un CRUD applicatif classique.

**Hors périmètre V1 (ne pas implémenter sans confirmation) :**
- Multijoueur temps réel
- Application mobile native
- Comptes utilisateurs complets / leaderboard
- Monétisation
- Choix de difficulté par le joueur
- Mode "libre" (article aléatoire à volonté)

---

## 2. Stack technique (décidée)

- **Backend : Python + FastAPI**
  - Choisi pour unifier le langage avec le pipeline NLP (spaCy/transformers), éviter la duplication de logique de traitement de texte entre deux écosystèmes, et bénéficier de la validation automatique + doc OpenAPI via Pydantic.
  - Serveur ASGI : `uvicorn` (perf async suffisante pour un jeu quotidien, y compris le pic de trafic à minuit).
- **Pipeline NLP : Python** (spaCy et/ou transformers selon les besoins de calibrage), **découplé du service API** — voir règle d'architecture ci-dessous.
- **Frontend :** JS moderne (React/Vue), responsive mobile-first, pas de compte obligatoire pour jouer.
- **Base de données :** à définir précisément (PostgreSQL recommandé par défaut avec FastAPI/SQLAlchemy ou SQLModel), stockage des articles traités, historique des défis, statistiques.
- **Conteneurisation :** un conteneur Docker par service (frontend, backend FastAPI, pipeline NLP).

### Règle structurante : découplage API / pipeline NLP

Même langage ne veut pas dire même process. Le pipeline NLP tourne en **batch** (job nocturne : cron, Celery beat, ou scheduler simple) et écrit ses résultats en base. Le service FastAPI ne fait que **lire/servir** les défis déjà générés et validés — il ne doit **jamais** déclencher de caviardage à la volée sur une requête de jeu.

```
/frontend      → SPA React ou Vue, mobile-first
/backend       → FastAPI (lecture/écriture défis, tentatives, scoring)
/nlp-pipeline  → job Python batch, indépendant du backend (invocable seul)
/infra         → docker-compose / Dockerfiles par service
```

- **Source des données :** API/dumps Wikipédia FR (licence CC-BY-SA — attribution obligatoire visible sur le site).

---

## 3. Modèle de données (à respecter/étendre, ne pas casser la forme)

Recommandation : modéliser avec des schémas Pydantic (ou SQLModel) partagés/cohérents entre le pipeline NLP et l'API FastAPI, pour éviter toute divergence de format entre ce qui est généré et ce qui est servi.

- **Article source** : titre, contenu original, catégorie, popularité, date d'import.
- **Défi quotidien** : référence article, date de publication, version caviardée, paramètres de difficulté.
- **Tentative/partie** : session (utilisateur ou anonyme), défi joué, essais, indices révélés, résultat, score.
- **Statistiques utilisateur** : série en cours, meilleure série, parties jouées/gagnées.

---

## 4. Règles métier critiques (ne jamais enfreindre)

Ces règles sont des invariants produit — toute implémentation ou modification touchant ces zones doit les préserver explicitement, et un agent doit signaler s'il ne peut pas les garantir.

1. **Aucune fuite de la réponse** :
   - Le titre de l'article et ses variantes évidentes (synonymes proches) doivent être masqués dans le texte.
   - Les entités nommées trop identifiantes (personnes, lieux, dates spécifiques) doivent être masquées.
   - Images, légendes, infobox, métadonnées visibles ne doivent jamais révéler la réponse — les neutraliser ou les masquer.
   - Le partage de résultat (façon Wordle) ne doit jamais contenir le titre en clair.
2. **Génération anticipée, pas temps réel** : le défi du jour doit être prêt avant publication (traitement nocturne du pipeline NLP), avec une étape de validation (auto et/ou humaine) avant mise en ligne.
3. **Un seul défi par jour, identique pour tous les joueurs**, disponible à heure fixe (fuseau horaire à confirmer avec le porteur de projet).
4. **Pas de répétition d'article** sur une période donnée — vérifier l'historique avant sélection.
5. **Filtrage de contenu sensible** : exclusion via liste noire de catégories/articles (violence, contenu perturbant, sujets polarisants), ajustable manuellement. Toute automatisation de sélection d'article doit appliquer ce filtre avant tout autre traitement.
6. **Licence CC-BY-SA** : attribution Wikipédia visible sur toutes les pages affichant du contenu dérivé.
7. **Anti-triche minimal côté API** : ne jamais exposer la réponse en clair dans les réponses de l'API FastAPI tant que la partie n'est pas terminée (ex. pas de titre en clair dans le payload avant victoire/défaite — attention en particulier aux schémas Pydantic de sortie qui pourraient inclure le champ titre par défaut).

---

## 5. Caviardage NLP — paramètres à exposer

Le module de caviardage doit être **paramétrable**, pas codé en dur, car le calibrage de difficulté est un axe de travail continu :

- Taux de mots masqués (%) configurable.
- Distinction mots "porteurs de sens" (à masquer) vs mots de liaison/grammaticaux (à conserver).
- Score de difficulté calculé par article (notoriété, longueur visible, nombre d'indices) pour garantir une cohérence jour après jour.
- Sortie attendue : texte caviardé + métadonnées de difficulté + liste des indices révélables progressivement — format sérialisable (JSON/Pydantic) consommé tel quel par le backend FastAPI, sans retraitement.

---

## 6. Conventions de code attendues

- **Backend FastAPI** :
  - Schémas de requête/réponse en Pydantic, avec des schémas de sortie explicitement dépourvus du champ "réponse" tant que la partie n'est pas terminée (cf. règle 7 ci-dessus).
  - Routeurs séparés par domaine (`defis`, `tentatives`, `stats`) plutôt qu'un fichier monolithique.
  - Dépendances FastAPI (`Depends`) pour la session DB et l'authentification légère/session anonyme.
- **Pipeline NLP** :
  - Invocable indépendamment du backend (script ou job planifié), aucune dépendance à l'API FastAPI en cours d'exécution.
  - Fonctions de sélection/filtrage de contenu sensible et de caviardage testables unitairement avec des articles "fixtures", pour vérifier qu'aucune fuite de réponse n'apparaît (cf. section 4.1).
- **Général** :
  - Un service = un conteneur Docker (frontend, backend FastAPI, pipeline NLP séparés).
  - Tests de non-régression sur le format de sortie du caviardage (le partage de résultat et l'affichage frontend en dépendent).

---

## 7. Contraintes non fonctionnelles

- Temps de réponse rapide (< 2s sur une tentative), aucune dépendance bloquante à un traitement IA en temps réel pendant la partie — le backend FastAPI ne fait que lire des données déjà générées.
- Disponibilité du défi dès minuit (fuseau à définir).
- Accessibilité : contraste, navigation clavier, compatibilité lecteurs d'écran.
- Rate limiting sur les tentatives de jeu (middleware FastAPI ou reverse proxy).
- Minimisation des données utilisateur collectées (pas de données sensibles sans consentement explicite).

---

## 8. Sprints indicatifs (ordre de priorité suggéré)

| Sprint | Objectif |
|--------|----------|
| 0 | Cadrage technique (stack validée : FastAPI + pipeline Python), CI/CD, dockerisation |
| 1 | Pipeline de récupération des articles Wikipédia + stockage |
| 2 | Algorithme de caviardage (NLP) + calibrage difficulté |
| 3 | Backend FastAPI (défi du jour, tentatives, scoring) |
| 4 | Frontend MVP (affichage, saisie, reveals) |
| 5 | Historique des défis + statistiques utilisateur |
| 6 | Partage de résultat + tests end-to-end |
| 7 | Durcissement (sécurité, perf, accessibilité) + mise en prod |

---

## 9. Points encore ouverts (demander confirmation avant de trancher en dur dans le code)

- Fuseau horaire de référence pour la publication quotidienne.
- Nécessité d'un compte utilisateur dès le MVP (actuellement : non, stockage local/session).
- Langue(s) cible(s) au lancement (FR uniquement présumé).
- Niveau d'automatisation de la validation des articles (100% auto vs relecture humaine) — impacte directement l'architecture du pipeline (queue de validation à prévoir dans tous les cas, cf. risque "charge de curation sous-estimée").
- Choix définitif de la base de données (PostgreSQL proposé par défaut, à confirmer) et de l'ORM (SQLAlchemy vs SQLModel).
- Mécanisme exact d'orchestration du job batch NLP (cron simple, Celery, autre scheduler).

Si une tâche touche à l'un de ces points, l'agent doit signaler l'hypothèse retenue plutôt que de la coder silencieusement en dur.