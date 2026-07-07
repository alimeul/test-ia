"""Point d'entrée CLI du pipeline NLP.

Usage :
    python -m pipeline fetch [--count 30]
    python -m pipeline stats
    python -m pipeline list
    python -m pipeline caviarder [--article-id N] [--article-titre TITRE] [--taux 0.5]
"""

import argparse
import asyncio
import json

from pipeline.article_store import (
    get_all_titles,
    get_article_by_id,
    get_statistics,
    init_db,
    save_article,
)
from pipeline.config import settings
from pipeline.difficulte import calculer_score_difficulte
from pipeline.filters import is_eligible
from pipeline.redacteur import rediger_texte
from pipeline.wikipedia_client import fetch_article_detail, fetch_random_articles


def cmd_fetch(args: argparse.Namespace):
    """Récupère des articles aléatoires, les filtre et stocke les éligibles."""
    init_db(settings.DB_PATH)
    existing = get_all_titles(settings.DB_PATH)
    articles = asyncio.run(fetch_random_articles(args.count))

    eligible = [a for a in articles if is_eligible(a, existing)]
    for article in eligible:
        save_article(settings.DB_PATH, article)
        print(f"✓ {article['titre']} ({article['categorie']})")

    print(
        f"\nRécupérés : {len(articles)}  "
        f"Éligibles : {len(eligible)}  "
        f"Déjà présents : {len(articles) - len(eligible)}"
    )


def cmd_stats(args: argparse.Namespace):
    """Affiche les statistiques de la base."""
    init_db(settings.DB_PATH)
    stats = get_statistics(settings.DB_PATH)
    print(f"Total articles : {stats['total_articles']}")
    for cat, count in stats["categories"].items():
        print(f"  {cat} : {count}")


def cmd_list(args: argparse.Namespace):
    """Liste les articles stockés."""
    init_db(settings.DB_PATH)
    titles = get_all_titles(settings.DB_PATH)
    for title in sorted(titles):
        print(title)
    print(f"\nTotal : {len(titles)}")


def cmd_caviarder(args: argparse.Namespace):
    """Caviarde un article depuis la base ou depuis l'API Wikipédia."""
    init_db(settings.DB_PATH)

    article: dict | None = None
    if args.article_id is not None:
        article = get_article_by_id(settings.DB_PATH, args.article_id)
        if article is None:
            print(f"Article ID {args.article_id} introuvable dans la base.")
            return
    elif args.article_titre is not None:
        article = asyncio.run(fetch_article_detail(args.article_titre))
        if article is None:
            print(f"Article '{args.article_titre}' introuvable sur Wikipédia.")
            return
    else:
        print("Utilisez --article-id ou --article-titre.")
        return

    resultat = rediger_texte(
        texte=article["contenu"],
        titre=article["titre"],
        taux_masquage=args.taux,
    )

    difficulte = calculer_score_difficulte(
        popularite=article.get("popularite", 0),
        total_tokens=resultat["stats"]["total_tokens"],
        tokens_masques=resultat["stats"]["tokens_masques"],
        entites_masquees=resultat["stats"]["entites_masquees"],
        longueur_texte=len(article["contenu"]),
        nb_indices=len(resultat["indices"]),
    )

    if args.json:
        output = {
            "article": {"titre": article["titre"], "id": article.get("pageid")},
            "texte_caviarde": resultat["texte_caviarde"],
            "stats": resultat["stats"],
            "difficulte": difficulte,
            "indices": resultat["indices"][:10],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"\n--- {article['titre']} ---")
    print(f"Difficulté : {difficulte['niveau']} ({difficulte['score']}/10)")
    print(f"Stats : {resultat['stats']}")
    print(f"\nTexte caviardé (extrait) :\n{resultat['texte_caviarde'][:500]}...")
    print(f"\nIndices disponibles : {', '.join(resultat['indices'][:10])}")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline NLP Wikidle — récupération et filtrage d'articles Wikipédia"
    )
    subparsers = parser.add_subparsers(dest="command")

    fetch_parser = subparsers.add_parser("fetch", help="Récupère et filtre des articles")
    fetch_parser.add_argument(
        "--count",
        type=int,
        default=settings.FETCH_COUNT,
        help=f"Nombre d'articles à récupérer (défaut: {settings.FETCH_COUNT})",
    )
    fetch_parser.set_defaults(func=cmd_fetch)

    stats_parser = subparsers.add_parser("stats", help="Affiche les statistiques de la base")
    stats_parser.set_defaults(func=cmd_stats)

    list_parser = subparsers.add_parser("list", help="Liste les articles stockés")
    list_parser.set_defaults(func=cmd_list)

    caviarder_parser = subparsers.add_parser(
        "caviarder", help="Caviarde un article depuis la base ou l'API"
    )
    caviarder_parser.add_argument(
        "--article-id", type=int, default=None, help="ID de l'article dans la base"
    )
    caviarder_parser.add_argument(
        "--article-titre", type=str, default=None, help="Titre de l'article Wikipédia"
    )
    caviarder_parser.add_argument(
        "--taux",
        type=float,
        default=settings.CAVIARDAGE_TAUX_DEFAUT,
        help=f"Taux de masquage (défaut: {settings.CAVIARDAGE_TAUX_DEFAUT})",
    )
    caviarder_parser.add_argument(
        "--json", action="store_true", help="Sortie au format JSON"
    )
    caviarder_parser.set_defaults(func=cmd_caviarder)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
