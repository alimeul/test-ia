"""Point d'entrée CLI du pipeline NLP.

Usage :
    python -m pipeline fetch [--count 30]
    python -m pipeline stats
    python -m pipeline list
"""

import argparse
import asyncio

from pipeline.article_store import (
    get_all_titles,
    get_statistics,
    init_db,
    save_article,
)
from pipeline.config import settings
from pipeline.filters import is_eligible
from pipeline.wikipedia_client import fetch_random_articles


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

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
