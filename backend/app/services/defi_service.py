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

    partie.essais_effectues += 1
    correct = _normalize_titre(titre_propose) == _normalize_titre(article.titre)

    if correct:
        partie.gagne = True
        partie.termine = True
        partie.score = _compute_score(
            partie.essais_effectues, partie.indices_reveles, partie.max_essais
        )
    elif partie.essais_effectues >= partie.max_essais:
        partie.termine = True
        partie.score = 0

    session.add(partie)
    session.commit()
    session.refresh(partie)

    return {
        "correct": correct,
        "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
        "gagne": partie.gagne,
        "titre": article.titre if correct or partie.termine else None,
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
    }
