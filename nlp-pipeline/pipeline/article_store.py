"""Stockage des articles dans une base SQLite via SQLModel.

Le modèle Article est indépendant de celui du backend (même structure).
"""

from datetime import date
from pathlib import Path

from sqlalchemy import Text
from sqlmodel import Field, Session, SQLModel, create_engine, func, select


class Article(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titre: str = Field(index=True)
    contenu_original: str = Field(sa_type=Text)
    categorie: str = Field(index=True)
    popularite: int = Field(default=0)
    date_import: date


def _get_engine(db_path: str):
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


def init_db(db_path: str):
    """Crée la base de données et les tables si elles n'existent pas.

    Retourne l'engine SQLAlchemy pour usage éventuel.
    """
    engine = _get_engine(db_path)
    SQLModel.metadata.create_all(engine)
    return engine


def article_exists(db_path: str, titre: str) -> bool:
    """Vérifie si un article avec ce titre existe déjà dans la base."""
    engine = _get_engine(db_path)
    with Session(engine) as session:
        statement = select(Article).where(Article.titre == titre)
        return session.exec(statement).first() is not None


def save_article(db_path: str, article_data: dict) -> Article:
    """Sauvegarde un article dans la base et retourne l'instance créée."""
    engine = _get_engine(db_path)
    with Session(engine) as session:
        article = Article(
            titre=article_data.get("titre", ""),
            contenu_original=article_data.get("contenu", ""),
            categorie=article_data.get("categorie", "Général"),
            popularite=article_data.get("popularite", 0),
            date_import=article_data.get("date_import", date.today()),
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        return article


def get_all_titles(db_path: str) -> set[str]:
    """Retourne l'ensemble des titres déjà importés."""
    engine = _get_engine(db_path)
    with Session(engine) as session:
        statement = select(Article.titre)
        return set(session.exec(statement).all())


def get_article_by_id(db_path: str, article_id: int) -> dict | None:
    """Récupère un article par son ID."""
    engine = _get_engine(db_path)
    with Session(engine) as session:
        statement = select(Article).where(Article.id == article_id)
        article = session.exec(statement).first()
        if article is None:
            return None
        return {
            "pageid": article.id,
            "titre": article.titre,
            "contenu": article.contenu_original,
            "categorie": article.categorie,
            "popularite": article.popularite,
        }


def get_statistics(db_path: str) -> dict:
    """Retourne des statistiques sur les articles stockés.

    Retourne un dict avec le nombre total d'articles et
    la répartition par catégorie.
    """
    engine = _get_engine(db_path)
    with Session(engine) as session:
        total = session.exec(select(func.count(Article.id))).one()

        rows = session.exec(
            select(Article.categorie, func.count(Article.id))
            .group_by(Article.categorie)
            .order_by(func.count(Article.id).desc())
        ).all()
        categories = {row[0]: row[1] for row in rows}

        return {
            "total_articles": total,
            "categories": categories,
        }
