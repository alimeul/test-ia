import json
from datetime import date
from typing import Any

from sqlmodel import Session, select

from app.models.article import Article
from app.models.defi import Defi
from app.models.partie import Partie


def get_defi_by_date(session: Session, defi_date: date | None = None) -> Defi | None:
    if defi_date is None:
        defi_date = date.today()
    statement = select(Defi).where(Defi.date_publication == defi_date)
    return session.exec(statement).first()


def get_or_create_defi_du_jour(session: Session, defi_date: date | None = None) -> Defi:
    if defi_date is None:
        defi_date = date.today()
    defi = get_defi_by_date(session, defi_date)
    if defi is not None:
        return defi
    raise RuntimeError(
        f"Aucun défi trouvé pour le {defi_date}. "
        "Exécutez le pipeline pour générer le défi du jour."
    )


def get_article_for_defi(session: Session, defi: Defi) -> Article | None:
    statement = select(Article).where(Article.id == defi.article_id)
    return session.exec(statement).first()


def get_ou_creer_partie(session: Session, defi: Defi, session_id: str) -> Partie:
    statement = select(Partie).where(
        Partie.defi_id == defi.id,
        Partie.session_id == session_id,
    )
    partie = session.exec(statement).first()
    if partie is not None:
        return partie
    partie = Partie(defi_id=defi.id, session_id=session_id)
    session.add(partie)
    session.commit()
    session.refresh(partie)
    return partie


def _compute_score(essais: int, indices: int, max_essais: int) -> int:
    score = 1000
    score -= essais * 100
    score -= indices * 50
    if indices == 0:
        score += 200
    return max(0, score)


def _normalize_titre(titre: str) -> str:
    return titre.strip().lower()


def _mots_dans_texte(texte_caviarde_json: str, mot: str) -> list[str]:
    data = json.loads(texte_caviarde_json)
    mot_low = mot.lower().strip()
    trouves = []
    for t in data["tokens"]:
        if t["masque"] and t["texte"].lower() == mot_low:
            trouves.append(t["texte"])
    return trouves


def check_answer(
    session: Session,
    defi: Defi,
    session_id: str,
    titre_propose: str,
) -> dict[str, Any]:
    partie = get_ou_creer_partie(session, defi, session_id)
    if partie.termine:
        return {
            "correct": partie.gagne,
            "essais_restants": 0,
            "gagne": partie.gagne,
            "titre": None,
            "erreur": "Partie déjà terminée",
        }

    article = get_article_for_defi(session, defi)
    if article is None:
        raise RuntimeError("Article introuvable pour ce défi")

    # Check if it's the correct title
    correct = _normalize_titre(titre_propose) == _normalize_titre(article.titre)

    if correct:
        partie.essais_effectues += 1
        partie.gagne = True
        partie.termine = True
        partie.score = _compute_score(
            partie.essais_effectues, partie.indices_reveles, partie.max_essais
        )
        session.add(partie)
        session.commit()
        session.refresh(partie)
        return {
            "correct": True,
            "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
            "gagne": True,
            "titre": article.titre,
        }

    # Check if it's a word present in the masked text
    mots_trouves = _mots_dans_texte(defi.texte_caviarde, titre_propose)
    if mots_trouves and not partie.termine:
        mots_reveles: list[str] = json.loads(partie.mots_reveles)
        mot_normalise = titre_propose.strip().lower()
        if mot_normalise not in {m.lower() for m in mots_reveles}:
            mots_reveles.append(mots_trouves[0])

        partie.essais_effectues += 1
        partie.mots_reveles = json.dumps(mots_reveles, ensure_ascii=False)

        if partie.essais_effectues >= partie.max_essais:
            partie.termine = True
            partie.score = 0

        session.add(partie)
        session.commit()
        session.refresh(partie)

        texte_mis_a_jour = reconstruire_texte(defi.texte_caviarde, mots_reveles)

        return {
            "correct": False,
            "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
            "gagne": False,
            "titre": None,
            "mot_revele": titre_propose.strip(),
            "texte_mis_a_jour": texte_mis_a_jour,
        }

    # Wrong guess (neither title nor word in text)
    partie.essais_effectues += 1
    if partie.essais_effectues >= partie.max_essais:
        partie.termine = True
        partie.score = 0

    session.add(partie)
    session.commit()
    session.refresh(partie)

    return {
        "correct": False,
        "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
        "gagne": False,
        "titre": article.titre if partie.termine else None,
    }


def reveler_indice(
    session: Session,
    defi: Defi,
    session_id: str,
) -> dict[str, Any]:
    partie = get_ou_creer_partie(session, defi, session_id)
    if partie.termine:
        return {
            "indice": "", "indice_index": -1,
            "indices_restants": 0, "erreur": "Partie déjà terminée",
        }

    indices: list[str] = json.loads(defi.indices)

    if partie.indices_reveles >= len(indices) or partie.indices_reveles >= partie.max_indices:
        return {
            "indice": "", "indice_index": -1,
            "indices_restants": 0, "erreur": "Plus d'indices disponibles",
        }

    indice = indices[partie.indices_reveles]
    partie.indices_reveles += 1
    session.add(partie)
    session.commit()

    return {
        "indice": indice,
        "indice_index": partie.indices_reveles - 1,
        "indices_restants": min(len(indices), partie.max_indices) - partie.indices_reveles,
    }


def reconstruire_texte(texte_caviarde_json: str, mots_reveles: list[str]) -> str:
    data = json.loads(texte_caviarde_json)
    tokens = data["tokens"]
    mots_set = {m.lower() for m in mots_reveles}
    parts = []
    for t in tokens:
        if t["masque"] and t["texte"].lower() in mots_set:
            parts.append(t["texte"])
        elif t["masque"]:
            parts.append("\u2588" * len(t["texte"]))
        else:
            parts.append(t["texte"])
        parts.append(t.get("ws", ""))
    return "".join(parts)


def get_partie_etat(session: Session, defi: Defi, session_id: str) -> dict[str, Any]:
    partie = get_ou_creer_partie(session, defi, session_id)
    indices: list[str] = json.loads(defi.indices)
    return {
        "essais_effectues": partie.essais_effectues,
        "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
        "indices_reveles": partie.indices_reveles,
        "indices_restants": min(len(indices), partie.max_indices) - partie.indices_reveles,
        "gagne": partie.gagne,
        "termine": partie.termine,
        "score": partie.score,
        "mots_reveles": json.loads(partie.mots_reveles),
    }
