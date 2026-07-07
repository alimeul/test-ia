import json
from datetime import date
from typing import Any

from sqlmodel import Session, select

from app.models.article import Article
from app.models.defi import Defi
from app.models.partie import Partie

_MOTS_GRAMMA: set[str] = {
    "le", "la", "les", "l", "de", "du", "des", "d",
    "un", "une", "ce", "cet", "cette", "ces",
    "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes", "ses",
    "notre", "votre", "leur", "nos", "vos", "leurs",
    "au", "aux", "a", "en", "et", "ou", "sur", "dans", "par", "pour",
    "avec", "sans", "chez", "vers", "depuis", "pendant",
    "que", "qui", "dont", "ou", "ne", "pas", "plus",
}


def _extraire_mots_titre(titre: str) -> list[str]:
    mots = set()
    for part in titre.replace("-", " ").replace("'", " ").split():
        mot = part.strip("'\"").lower()
        if mot and mot not in _MOTS_GRAMMA and len(mot) > 1:
            mots.add(mot)
    return sorted(mots)


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


def _mots_dans_texte(texte_caviarde_json: str, mot: str) -> list[str]:
    data = json.loads(texte_caviarde_json)
    mot_low = mot.lower().strip()
    trouves = []
    for t in data["tokens"]:
        if not t["masque"]:
            continue
        t_low = t["texte"].lower()
        if t_low == mot_low or (len(mot_low) >= 3 and mot_low in t_low):
            trouves.append(t["texte"])
    return trouves


def _compter_occurrences(texte_caviarde_json: str, mot: str) -> int:
    data = json.loads(texte_caviarde_json)
    mot_low = mot.lower().strip()
    count = 0
    for t in data["tokens"]:
        if not t["masque"]:
            continue
        t_low = t["texte"].lower()
        if t_low == mot_low or (len(mot_low) >= 3 and mot_low in t_low):
            count += 1
    return count


def _construire_propositions(partie: Partie, texte_caviarde_json: str) -> list[dict[str, Any]]:
    props: list[dict] = json.loads(partie.mots_proposes)
    mots_reveles_set = {m.lower() for m in json.loads(partie.mots_reveles)}
    result = []
    for p in props:
        mot = p["mot"]
        trouve = mot.lower() in mots_reveles_set
        nb_occ = _compter_occurrences(texte_caviarde_json, mot) if trouve else 0
        result.append({"mot": mot, "trouve": trouve, "nb_occurrences": nb_occ})
    return result


def check_answer(
    session: Session,
    defi: Defi,
    session_id: str,
    mot_propose: str,
) -> dict[str, Any]:
    partie = get_ou_creer_partie(session, defi, session_id)
    if partie.termine:
        return {
            "correct": False,
            "essais_restants": 0,
            "gagne": partie.gagne,
            "titre": None,
            "erreur": "Partie déjà terminée",
        }

    article = get_article_for_defi(session, defi)
    if article is None:
        raise RuntimeError("Article introuvable pour ce défi")

    mots_titre = _extraire_mots_titre(article.titre)
    mot_propre = mot_propose.strip()

    # Track this proposal
    props: list[dict] = json.loads(partie.mots_proposes)
    if mot_propre.lower() not in {p["mot"].lower() for p in props}:
        props.append({"mot": mot_propre})
    partie.mots_proposes = json.dumps(props, ensure_ascii=False)

    # Find matching tokens in text
    mots_trouves = _mots_dans_texte(defi.texte_caviarde, mot_propre)

    if mots_trouves:
        mots_reveles: list[str] = json.loads(partie.mots_reveles)
        if mot_propre.lower() not in {m.lower() for m in mots_reveles}:
            mots_reveles.append(mots_trouves[0])

        partie.essais_effectues += 1
        partie.mots_reveles = json.dumps(mots_reveles, ensure_ascii=False)

        # Check if all title words are now revealed
        reveles_set = {m.lower() for m in mots_reveles}
        mots_titre_trouves = [mt for mt in mots_titre if mt.lower() in reveles_set]
        all_found = len(mots_titre_trouves) == len(mots_titre)

        if all_found:
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

        texte_mis_a_jour = reconstruire_texte(defi.texte_caviarde, mots_reveles)
        propositions = _construire_propositions(partie, defi.texte_caviarde)

        return {
            "correct": all_found,
            "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
            "gagne": all_found,
            "titre": article.titre if (all_found or partie.termine) else None,
            "mot_revele": mot_propre,
            "texte_mis_a_jour": texte_mis_a_jour,
            "mots_titre": mots_titre,
            "mots_titre_trouves": mots_titre_trouves,
            "propositions": propositions,
        }

    # Word not found in text — costs an attempt
    partie.essais_effectues += 1
    if partie.essais_effectues >= partie.max_essais:
        partie.termine = True
        partie.score = 0

    session.add(partie)
    session.commit()
    session.refresh(partie)

    reveles_set = {m.lower() for m in json.loads(partie.mots_reveles)}
    mots_titre_trouves = [mt for mt in mots_titre if mt.lower() in reveles_set]
    propositions = _construire_propositions(partie, defi.texte_caviarde)

    return {
        "correct": False,
        "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
        "gagne": False,
        "titre": article.titre if partie.termine else None,
        "mot_revele": None,
        "texte_mis_a_jour": None,
        "mots_titre": mots_titre,
        "mots_titre_trouves": mots_titre_trouves,
        "propositions": propositions,
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
        t_low = t["texte"].lower()
        should_reveal = t_low in mots_set or any(
            len(m) >= 3 and m in t_low for m in mots_set
        )
        if t["masque"] and should_reveal:
            parts.append(t["texte"])
        elif t["masque"]:
            parts.append("\u2588" * len(t["texte"]))
        else:
            parts.append(t["texte"])
        parts.append(t.get("ws", ""))
    return "".join(parts)


def get_partie_etat(session: Session, defi: Defi, session_id: str) -> dict[str, Any]:
    partie = get_ou_creer_partie(session, defi, session_id)
    article = get_article_for_defi(session, defi)
    indices: list[str] = json.loads(defi.indices)
    mots_titre = _extraire_mots_titre(article.titre) if article else []
    mots_reveles = json.loads(partie.mots_reveles)
    reveles_set = {m.lower() for m in mots_reveles}
    mots_titre_trouves = [mt for mt in mots_titre if mt.lower() in reveles_set]
    propositions = _construire_propositions(partie, defi.texte_caviarde) if article else []
    return {
        "essais_effectues": partie.essais_effectues,
        "essais_restants": max(0, partie.max_essais - partie.essais_effectues),
        "indices_reveles": partie.indices_reveles,
        "indices_restants": min(len(indices), partie.max_indices) - partie.indices_reveles,
        "gagne": partie.gagne,
        "termine": partie.termine,
        "score": partie.score,
        "mots_reveles": mots_reveles,
        "mots_titre": mots_titre,
        "mots_titre_trouves": mots_titre_trouves,
        "propositions": propositions,
    }
