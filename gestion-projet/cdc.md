# Cahier des charges
## Projet : Wikidle — Jeu quotidien de devinette d'articles Wikipédia (type Caviardeul)

**Version :** 1.1
**Date :** Juillet 2026
**Auteur :** Antoine

---

## 1. Contexte et objectifs

### 1.1 Contexte
Les jeux quotidiens type "Wordle" (Wordle, Curiosum, Caviardeul, etc.) connaissent un fort engagement grâce à leur format simple, gratuit, rejouable une fois par jour, et facilement partageable sur les réseaux sociaux.

Le concept "Caviardeul" reprend le principe suivant : un article de Wikipédia est présenté avec les mots significatifs masqués (caviardés). Le joueur doit deviner de quel article il s'agit, en révélant progressivement des mots ou en proposant directement un titre.

### 1.2 Objectifs du projet
- Développer un site web permettant de jouer à un défi quotidien basé sur des articles Wikipédia caviardés.
- Générer une forte rétention grâce à un format quotidien et partageable.
- Automatiser au maximum la sélection et le caviardage des articles grâce à des traitements IA/NLP, pour limiter la charge de curation manuelle.
- Proposer une expérience simple, rapide, sans friction (pas de compte obligatoire pour jouer).

### 1.3 Objectifs non retenus (hors périmètre V1)
- Modes multijoueurs en temps réel.
- Application mobile native (le site sera responsive/mobile-first).
- Monétisation avancée (pub, dons) — à évaluer en V2.

---

## 2. Description du produit

### 2.1 Principe du jeu
Chaque jour, un article Wikipédia est sélectionné et son contenu est affiché avec les mots "porteurs de sens" masqués par des bandeaux noirs (façon document caviardé). Le joueur doit deviner le titre de l'article.

### 2.2 Mécaniques de jeu (MVP)
- **Un article par jour**, identique pour tous les joueurs (comme Wordle).
- Le joueur peut :
  - Proposer un titre d'article à tout moment (champ de recherche avec autocomplétion sur les titres Wikipédia).
  - Demander à révéler un mot caviardé supplémentaire (avec un coût, ex. impact sur le score/nombre d'essais).
- Fin de partie :
  - Victoire si le bon titre est trouvé.
  - Nombre d'essais/reveals limité (ex. 5 à 10 tentatives ou reveals), sinon défaite et révélation de la réponse.
- Système de score basé sur le nombre d'indices utilisés et/ou le nombre d'essais.

### 2.3 Fonctionnalités additionnelles (MVP)
- Partage du résultat sous forme de grille/résumé textuel (façon Wordle), sans révéler la réponse.
- Historique des parties précédentes (articles des jours passés, jouables en mode "rattrapage").
- Statistiques personnelles (série en cours, meilleur score, taux de réussite) — nécessite un stockage local ou un compte léger.

### 2.4 Fonctionnalités envisagées en V2 (hors MVP)
- Comptes utilisateurs et classement (leaderboard) entre amis.
- Choix de la difficulté (catégorie d'articles, taux de mots masqués).
- Mode "libre" (rejouer un article aléatoire à volonté, pas seulement le défi du jour).
- Statistiques globales communautaires (% de joueurs ayant trouvé, temps moyen).

---

## 3. Public cible
- Joueurs occasionnels de jeux quotidiens type Wordle/Curiosum.
- Curieux de culture générale, amateurs de Wikipédia.
- Public francophone en priorité (contenu basé sur Wikipédia FR), extension possible à d'autres langues en V2.

---

## 4. Sélection et traitement des articles (cœur IA du projet)

Cette partie constitue le composant IA/NLP central du produit et doit être détaillée avec le plus grand soin.

### 4.1 Sélection des articles sources
Critères à définir pour qu'un article soit éligible au jeu quotidien :
- Longueur minimale/maximale (éviter les articles trop courts ou trop longs).
- Popularité suffisante (nombre de vues, présence dans les articles "notables") pour rester devinable, sans être trop simple non plus.
- Exclusion de certaines catégories sensibles (voir section 8 — contenu sensible).
- Éviter la répétition d'un même article sur une période donnée (historique des articles déjà utilisés).

### 4.2 Caviardage automatique
Le traitement NLP doit identifier et masquer les mots "porteurs de sens" tout en conservant une lisibilité du texte :
- Masquage du titre de l'article et de ses variantes évidentes (nom, synonymes proches).
- Masquage des entités nommées clés (personnes, lieux, dates spécifiques trop identifiantes).
- Masquage des mots rares/spécifiques permettant une identification immédiate, en conservant les mots "de liaison" et le contexte grammatical.
- Paramétrage du taux de caviardage (ex. % de mots masqués) pour calibrer la difficulté.
- Vérification qu'aucune image, légende ou métadonnée visible ne révèle involontairement la réponse (infobox, image principale, etc. à masquer ou neutraliser).

### 4.3 Calibrage de la difficulté
- Prévoir un système de score de difficulté par article (basé sur la notoriété, la longueur du texte visible, le nombre d'indices).
- Objectif : garantir une difficulté cohérente et pas totalement aléatoire d'un jour à l'autre.

### 4.4 Validation avant publication
- Prévoir une étape de contrôle (automatique et/ou humaine) avant la mise en ligne d'un article caviardé, pour éviter :
  - une réponse trop évidente ou au contraire impossible à trouver ;
  - un contenu inapproprié ou sensible ;
  - une erreur de caviardage laissant apparaître la réponse.

---

## 5. Architecture technique

### 5.1 Stack retenue

- **Backend : Python + FastAPI.**
  Ce choix est motivé par le fait que le cœur du projet — le pipeline de sélection et de caviardage — sera lui-même écrit en Python (NLP : spaCy et/ou transformers). Unifier le langage entre backend et pipeline IA évite de dupliquer la logique de traitement de texte entre deux écosystèmes, et permet de partager les schémas de données (via Pydantic) entre les deux composants. FastAPI apporte en prime une validation automatique des données et une documentation OpenAPI générée sans effort, pour un ensemble d'endpoints qui reste volontairement simple (CRUD léger : défi du jour, tentatives, scoring).
  Serveur ASGI : `uvicorn`, dont les performances asynchrones sont largement suffisantes pour la charge attendue (jeu quotidien, y compris le pic de connexions à l'heure de publication).

- **Frontend :** framework JS moderne (React/Vue), responsive mobile-first.

- **Base de données :** stockage des articles traités, historique des défis, statistiques utilisateurs. PostgreSQL proposé par défaut (à confirmer), avec SQLAlchemy ou SQLModel comme ORM côté FastAPI.

- **Traitement IA/NLP :** pipeline Python dédié (batch, exécuté en amont, pas en temps réel pendant le jeu) pour la sélection et le caviardage des articles.
  **Point d'architecture important :** même si le pipeline NLP et le backend partagent le même langage, ils doivent rester des processus/services distincts. Le pipeline tourne en tâche planifiée (cron, Celery beat, ou scheduler équivalent) et écrit ses résultats en base ; le backend FastAPI ne fait que lire/servir des défis déjà générés et validés — il ne doit jamais déclencher de traitement NLP à la volée sur une requête de jeu.

- **Conteneurisation :** application dockerisée, un conteneur par service (frontend, backend FastAPI, pipeline NLP en service séparé).

### 5.2 Source des données
- Utilisation de l'API Wikipédia / dumps Wikipédia (contenu sous licence CC-BY-SA — voir section 8).
- Pipeline d'import et de mise à jour périodique des articles sources.

### 5.3 Fréquence de génération
- Génération du défi du jour en avance (ex. traitement nocturne du pipeline NLP) plutôt qu'en temps réel, pour permettre la validation avant publication.

---

## 6. Contraintes non fonctionnelles

- **Performance :** temps de chargement rapide de la page de jeu ; le backend FastAPI ne fait que servir des données déjà générées, sans dépendance bloquante à un traitement IA en temps réel pendant la partie.
- **Disponibilité :** le défi du jour doit être disponible dès minuit (fuseau horaire à définir) pour tous les joueurs.
- **Accessibilité :** contraste suffisant, navigation clavier possible, compatible lecteurs d'écran dans la mesure du possible.
- **Sécurité :** protection basique contre les abus (rate limiting sur les tentatives, anti-triche minimal côté API — les schémas de réponse Pydantic ne doivent jamais inclure le titre de l'article en clair tant que la partie n'est pas terminée).
- **Confidentialité :** si des statistiques utilisateurs sont stockées, minimiser les données collectées (pas de données sensibles sans consentement explicite).

---

## 7. Modèle de données (à affiner)

Éléments principaux à prévoir (modélisables en schémas Pydantic/SQLModel partagés entre pipeline NLP et backend FastAPI, pour garantir la cohérence des formats) :
- **Article source :** titre, contenu original, métadonnées (catégorie, popularité, date d'import).
- **Défi quotidien :** référence à l'article, date de publication, version caviardée, paramètres de difficulté.
- **Tentative/partie :** utilisateur (ou session anonyme), défi joué, essais effectués, indices révélés, résultat (gagné/perdu), score.
- **Statistiques utilisateur :** série en cours, meilleure série, nombre de parties jouées/gagnées.

---

## 8. Contenu sensible et propriété intellectuelle

- Le contenu Wikipédia est sous licence **CC-BY-SA** : l'attribution de la source doit être visible sur le site, et toute réutilisation doit respecter les termes de cette licence.
- Exclure ou filtrer les articles portant sur des sujets sensibles (violence, contenus disturbants, sujets à forte polarisation) pour rester adapté à un usage grand public.
- Prévoir une liste noire de catégories/articles à exclure du tirage, ajustable manuellement.

---

## 9. Découpage en sprints (proposition indicative)

| Sprint | Objectif principal |
|--------|--------------------|
| Sprint 0 | Cadrage technique (stack retenue : FastAPI + pipeline Python), setup du dépôt et de la CI/CD, dockerisation de base |
| Sprint 1 | Pipeline de récupération des articles Wikipédia + stockage |
| Sprint 2 | Algorithme de caviardage (NLP) + calibrage difficulté |
| Sprint 3 | Backend API FastAPI (défi du jour, gestion des tentatives, scoring) |
| Sprint 4 | Frontend MVP (affichage du défi, saisie des réponses, reveals) |
| Sprint 5 | Historique des défis passés + statistiques utilisateur |
| Sprint 6 | Partage de résultat (façon Wordle) + tests bout en bout |
| Sprint 7 | Durcissement (sécurité, performance, accessibilité) + mise en production |

---

## 10. Critères d'acceptation (MVP)

- Un nouvel article caviardé est disponible chaque jour à heure fixe, sans intervention manuelle en routine.
- Un joueur peut proposer un titre et recevoir un retour (bonne/mauvaise réponse) en moins de 2 secondes.
- Un joueur peut révéler des mots supplémentaires et voir l'impact sur son score en temps réel.
- Le partage du résultat ne révèle jamais le titre de l'article à un tiers qui n'a pas encore joué.
- Aucun contenu sensible n'apparaît dans les défis publiés sans validation préalable.
- Le site est utilisable sur mobile et desktop sans bug bloquant.

---

## 11. Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Caviardage trop simple ou trop difficile | Mauvaise expérience joueur | Calibrage + tests utilisateurs avant lancement |
| Fuite de la réponse via métadonnées (image, infobox) | Jeu cassé | Contrôle systématique avant publication |
| Article sensible sélectionné automatiquement | Image du produit | Liste noire de catégories + validation avant publication |
| Charge de curation manuelle sous-estimée | Retard de production de contenu | Automatiser un maximum le pipeline, prévoir une file d'articles pré-validés |
| Non-respect de la licence Wikipédia | Risque juridique | Attribution claire, vérification des conditions CC-BY-SA |
| Couplage accidentel entre pipeline NLP et backend | Latence/fragilité du jeu en production | Maintenir des services Docker séparés, pipeline en batch uniquement (cf. section 5.1) |

---

## 12. Livrables attendus

- Code source du site (frontend + backend FastAPI), dockerisé.
- Pipeline de génération/caviardage des défis quotidiens (Python).
- Documentation technique (architecture, déploiement, pipeline de contenu).
- Documentation fonctionnelle (règles du jeu, calibrage de la difficulté).

---

## 13. Points à valider avec le porteur de projet

- Nom définitif du projet et identité visuelle.
- Fréquence exacte de publication et fuseau horaire de référence.
- Nécessité ou non d'un compte utilisateur dès le MVP.
- Langue(s) cible(s) pour le lancement (FR uniquement ou multilingue).
- Niveau d'automatisation souhaité pour la validation des articles (100% automatique vs relecture humaine).
- Choix définitif de la base de données (PostgreSQL proposé par défaut) et de l'ORM (SQLAlchemy vs SQLModel).
- Mécanisme d'orchestration du job batch NLP (cron simple, Celery, ou autre scheduler).