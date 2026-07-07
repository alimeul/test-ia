import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models.article import Article
from app.models.defi import Defi
from app.models.partie import Partie

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
DAY_BEFORE = TODAY - timedelta(days=2)


@pytest.fixture
def db_multi(tmp_path: Path):
    db_file = tmp_path / "test_multi.db"
    engine = create_engine(f"sqlite:///{db_file}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        article = Article(
            titre="Paris",
            contenu_original="Paris est la capitale de la France.",
            categorie="Géographie",
            popularite=500,
            date_import=date.today(),
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        for d in [TODAY, YESTERDAY, DAY_BEFORE]:
            defi = Defi(
                article_id=article.id,
                date_publication=d,
                texte_caviarde=json.dumps({
                    "texte": "█████ est la capitale de la ██████.",
                    "tokens": [
                        {"texte": "Paris", "masque": True, "pos": "PROPN", "ws": " "},
                        {"texte": "est", "masque": False, "pos": "AUX", "ws": " "},
                        {"texte": "la", "masque": False, "pos": "DET", "ws": " "},
                        {"texte": "capitale", "masque": False, "pos": "NOUN", "ws": " "},
                        {"texte": "de", "masque": False, "pos": "ADP", "ws": " "},
                        {"texte": "la", "masque": False, "pos": "DET", "ws": " "},
                        {"texte": "France", "masque": True, "pos": "PROPN", "ws": "."},
                    ],
                }),
                score_difficulte=5.0,
                indices=json.dumps(["France"]),
            )
            session.add(defi)
        session.commit()

        session.add(
            Partie(defi_id=1, session_id="stats-test", essais_effectues=2, termine=True, gagne=True, score=800)
        )
        session.add(
            Partie(defi_id=1, session_id="stats-test-bad", essais_effectues=5, termine=True, gagne=False, score=0)
        )
        session.add(
            Partie(defi_id=2, session_id="stats-test", essais_effectues=1, termine=True, gagne=True, score=900)
        )
        session.add(
            Partie(defi_id=3, session_id="stats-test", essais_effectues=3, termine=True, gagne=True, score=650)
        )
        session.commit()

        yield session


@pytest.fixture
def client(db_multi):
    def _get_test_session():
        yield db_multi

    app.dependency_overrides[get_session] = _get_test_session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client


@pytest.mark.anyio
async def test_historique_defis(client):
    response = await client.get("/api/defis/historique")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["date"] == TODAY.isoformat()
    assert data[2]["date"] == DAY_BEFORE.isoformat()


@pytest.mark.anyio
async def test_defi_par_date_ok(client):
    response = await client.get(f"/api/defis/{YESTERDAY.isoformat()}")
    assert response.status_code == 200
    data = response.json()
    assert "texte_caviarde" in data
    assert data["date"] == YESTERDAY.isoformat()


@pytest.mark.anyio
async def test_defi_par_date_invalide(client):
    response = await client.get("/api/defis/9999-99-99")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_defi_par_date_inexistante(client):
    response = await client.get("/api/defis/2020-01-01")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_stats_session_complete(client):
    response = await client.get("/api/stats/session?session_id=stats-test")
    assert response.status_code == 200
    data = response.json()
    assert data["total_parties"] == 3
    assert data["total_gagnees"] == 3
    assert data["taux_reussite"] == 100.0
    assert data["meilleur_score"] == 900
    assert data["meilleure_serie"] >= 1


@pytest.mark.anyio
async def test_stats_session_avec_perte(client):
    response = await client.get("/api/stats/session?session_id=stats-test-bad")
    assert response.status_code == 200
    data = response.json()
    assert data["total_parties"] == 1
    assert data["total_gagnees"] == 0
    assert data["taux_reussite"] == 0.0
    assert data["meilleur_score"] == 0


@pytest.mark.anyio
async def test_stats_session_vierge(client):
    response = await client.get("/api/stats/session?session_id=personne")
    assert response.status_code == 200
    data = response.json()
    assert data["total_parties"] == 0
    assert data["taux_reussite"] == 0.0


@pytest.mark.anyio
async def test_rattrapage_proposer(client):
    yesterday = YESTERDAY.isoformat()
    response = await client.post(
        f"/api/defis/{yesterday}/proposer?session_id=rattrapage-test",
        json={"titre_propose": "Paris"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] is True
    assert data["gagne"] is True
    assert data["titre"] == "Paris"


@pytest.mark.anyio
async def test_rattrapage_reveler(client):
    yesterday = YESTERDAY.isoformat()
    response = await client.post(
        f"/api/defis/{yesterday}/reveler?session_id=rattrapage-revele",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["indice"] == "France"
    assert data["indices_restants"] == 0


@pytest.mark.anyio
async def test_rattrapage_partie_etat(client):
    yesterday = YESTERDAY.isoformat()
    await client.post(
        f"/api/defis/{yesterday}/proposer?session_id=rattrapage-etat",
        json={"titre_propose": "Lyon"},
    )
    response = await client.get(
        f"/api/defis/{yesterday}/partie?session_id=rattrapage-etat"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["essais_effectues"] == 1
    assert data["termine"] is False


@pytest.mark.anyio
async def test_proposer_apres_victoire_renvoie_erreur(client):
    sid = "deja-gagne"
    await client.post(
        "/api/defis/aujourdhui/proposer?session_id=" + sid,
        json={"titre_propose": "Paris"},
    )
    response = await client.post(
        "/api/defis/aujourdhui/proposer?session_id=" + sid,
        json={"titre_propose": "Lyon"},
    )
    assert response.status_code == 400
    assert "terminée" in response.json()["detail"]
