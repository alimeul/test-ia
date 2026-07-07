"""Cœur du caviardage NLP — masquage des mots porteurs de sens."""

import random
from functools import lru_cache
from typing import Any

from pipeline.config import settings

try:
    import spacy
    from spacy.language import Language
except ImportError:
    spacy = None
    Language = None

_MASK_CHAR = "\u2588"

_POS_GRAMMATICAUX: frozenset[str] = frozenset({
    "DET", "ADP", "CCONJ", "SCONJ", "PRON", "AUX", "PART", "INTJ", "NUM",
})

_POS_PORTEURS: frozenset[str] = frozenset({
    "NOUN", "PROPN", "VERB", "ADJ", "ADV",
})

_PRIORITE_POS: dict[str, int] = {
    "PROPN": 0,
    "NOUN": 1,
    "ADJ": 2,
    "VERB": 3,
    "ADV": 4,
}


def get_nlp() -> "Language":
    """Charge et retourne le modèle spaCy FR (avec cache)."""
    if spacy is None:
        raise ImportError(
            "spacy n'est pas installé. Installez-le avec : pip install spacy "
            "et téléchargez le modèle avec : "
            f"python -m spacy download {settings.SPACY_MODEL}"
        )
    return _load_model()


@lru_cache(maxsize=1)
def _load_model() -> "Language":
    """Charge le modèle spaCy avec cache (appel unique)."""
    try:
        return spacy.load(settings.SPACY_MODEL)
    except OSError:
        raise OSError(
            f"Le modèle spaCy '{settings.SPACY_MODEL}' n'est pas trouvé. "
            f"Téléchargez-le avec : python -m spacy download {settings.SPACY_MODEL}"
        )


def _extraire_info_titre(titre: str, nlp: "Language") -> tuple[set[str], set[str]]:
    """Extrait les lemmes et mots bruts du titre pour le masquage forcé."""
    doc = nlp(titre)
    lemmes: set[str] = set()
    mots: set[str] = set()
    for token in doc:
        if token.is_alpha:
            if token.lemma_:
                lemmes.add(token.lemma_.lower())
            mots.add(token.text.lower())
    return lemmes, mots


def _construire_texte_caviarde(
    doc: "spacy.tokens.Doc",
    tokens_info: list[dict[str, Any]],
) -> str:
    """Reconstruit le texte avec les mots masqués remplacés par ██."""
    parts: list[str] = []
    for i, token in enumerate(doc):
        if tokens_info[i]["masque"]:
            parts.append(_MASK_CHAR * len(token.text))
        else:
            parts.append(token.text)
        if token.whitespace_:
            parts.append(token.whitespace_)
    return "".join(parts)


def _generer_liste_indices(
    tokens_info: list[dict[str, Any]],
    tokens_masques_idx: set[int],
) -> list[int]:
    """Retourne les positions des tokens masqués triées par importance décroissante."""
    indices = list(tokens_masques_idx)
    indices.sort(key=lambda i: (
        _PRIORITE_POS.get(tokens_info[i]["pos"], 5),
        -len(tokens_info[i]["texte"]),
        tokens_info[i]["texte"],
    ))
    return indices


def rediger_texte(
    texte: str,
    titre: str,
    taux_masquage: float = 1.0,
    seed: int | None = None,
) -> dict[str, Any]:
    """Fonction principale de caviardage d'un article Wikipédia.

    Paramètres
    ----------
    texte : str
        Texte original de l'article à caviarder.
    titre : str
        Titre de l'article (forcé à être masqué dans le texte).
    taux_masquage : float
        Proportion (0.0 - 1.0) des tokens caviardables à masquer.
    seed : int | None
        Seed pour la reproductibilité.

    Retourne
    --------
    dict avec les clés : texte_caviarde, tokens, indices, stats
    """
    if not texte or not texte.strip():
        return {
            "texte_caviarde": "",
            "tokens": [],
            "indices": [],
            "stats": {
                "total_tokens": 0,
                "tokens_masques": 0,
                "taux_effectif": 0.0,
                "entites_masquees": 0,
            },
        }

    if seed is not None:
        random.seed(seed)

    nlp = get_nlp()
    doc = nlp(texte)

    titre_lemmes, titre_mots = _extraire_info_titre(titre, nlp)

    entite_spans: set[int] = set()
    for ent in doc.ents:
        for i in range(ent.start, ent.end):
            entite_spans.add(i)

    tokens_info: list[dict[str, Any]] = []
    indices_caviardables: list[int] = []

    for i, token in enumerate(doc):
        info: dict[str, Any] = {
            "texte": token.text,
            "masque": False,
            "pos": token.pos_,
            "indice_index": None,
            "ws": token.whitespace_,
        }

        if token.is_space or token.is_punct or token.pos_ in _POS_GRAMMATICAUX:
            tokens_info.append(info)
            continue

        if token.pos_ not in _POS_PORTEURS:
            tokens_info.append(info)
            continue

        info["masque"] = True
        indices_caviardables.append(i)
        tokens_info.append(info)

    if not indices_caviardables:
        return {
            "texte_caviarde": texte,
            "tokens": tokens_info,
            "indices": [],
            "stats": {
                "total_tokens": len(doc),
                "tokens_masques": 0,
                "taux_effectif": 0.0,
                "entites_masquees": 0,
            },
        }

    tokens_masques_idx = set(indices_caviardables)
    entites_masquees: set[int] = set()
    for i in indices_caviardables:
        if i in entite_spans:
            for ent_idx, ent in enumerate(doc.ents):
                if ent.start <= i < ent.end:
                    entites_masquees.add(ent_idx)
                    break

    texte_caviarde = _construire_texte_caviarde(doc, tokens_info)

    total_masques = len(tokens_masques_idx)
    stats = {
        "total_tokens": len(doc),
        "tokens_masques": total_masques,
        "taux_effectif": round(total_masques / total_caviardables, 4),
        "entites_masquees": len(entites_masquees),
    }

    indices_tries = _generer_liste_indices(tokens_info, tokens_masques_idx)
    for idx_pos, token_idx in enumerate(indices_tries):
        tokens_info[token_idx]["indice_index"] = idx_pos

    return {
        "texte_caviarde": texte_caviarde,
        "tokens": tokens_info,
        "indices": [tokens_info[i]["texte"] for i in indices_tries],
        "stats": stats,
    }


def generer_indices(tokens: list[dict], nb_indices: int = 5) -> list[str]:
    """Extrait N indices à révéler, en priorisant les mots les plus informatifs.

    Ordre de priorité : noms propres > noms communs > adjectifs > verbes > adverbes.
    À priorité égale, les mots les plus longs (plus rares/spécifiques) sont prioritaires.
    """
    masques = [t for t in tokens if t["masque"]]
    masques.sort(key=lambda t: (
        _PRIORITE_POS.get(t["pos"], 5),
        -len(t["texte"]),
        t["texte"],
    ))
    return [t["texte"] for t in masques[:nb_indices]]
