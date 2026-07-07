import json
from datetime import date
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models.article import Article
from app.models.defi import Defi

SAMPLE_TEXTE = (
    "Paris est la capitale de la France. "
    "Elle est située sur la Seine. "
    "La ville compte plus de deux millions d'habitants."
)


@pytest.fixture
def db_session(tmp_path: Path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        article = Article(
            titre="Paris",
            contenu_original=SAMPLE_TEXTE,
            categorie="Géographie",
            popularite=500,
            date_import=date.today(),
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        defi = Defi(
            article_id=article.id,
            date_publication=date.today(),
            texte_caviarde=json.dumps({
                "texte": "█████ est la capitale de la ██████.",
                "tokens": [
                    {"texte": "Paris", "masque": True, "pos": "PROPN"},
                    {"texte": "est", "masque": False, "pos": "AUX"},
                    {"texte": "la", "masque": False, "pos": "DET"},
                    {"texte": "capitale", "masque": False, "pos": "NOUN"},
                    {"texte": "de", "masque": False, "pos": "ADP"},
                    {"texte": "la", "masque": False, "pos": "DET"},
                    {"texte": "France", "masque": True, "pos": "PROPN"},
                ],
            }),
            score_difficulte=5.0,
            indices=json.dumps(["France", "Paris"]),
        )
        session.add(defi)
        session.commit()

        yield session


@pytest.fixture
def client(db_session):
    def _get_test_session():
        yield db_session

    app.dependency_overrides[get_session] = _get_test_session
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client


@pytest.mark.anyio
async def test_defi_aujourdhui_retourne_200(client):
    response = await client.get("/api/defis/aujourdhui")
    assert response.status_code == 200
    data = response.json()
    assert "texte_caviarde" in data
    assert "date" in data
    assert "nb_indices_disponibles" in data


@pytest.mark.anyio
async def test_defi_aujourdhui_pas_de_titre(client):
    response = await client.get("/api/defis/aujourdhui")
    data = response.json()
    assert "titre" not in data


@pytest.mark.anyio
async def test_proposer_bonne_reponse(client):
    response = await client.post(
        "/api/defis/aujourdhui/proposer?session_id=test-123",
        json={"titre_propose": "Paris"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] is True
    assert data["gagne"] is True
    assert data["titre"] == "Paris"


@pytest.mark.anyio
async def test_proposer_mauvaise_reponse(client):
    response = await client.post(
        "/api/defis/aujourdhui/proposer?session_id=test-456",
        json={"titre_propose": "Lyon"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] is False
    assert data["gagne"] is False
    assert data["titre"] is None


@pytest.mark.anyio
async def test_proposer_insensible_casse(client):
    response = await client.post(
        "/api/defis/aujourdhui/proposer?session_id=test-casse",
        json={"titre_propose": "paris"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] is True


@pytest.mark.anyio
async def test_reveler_indice(client):
    response = await client.post(
        "/api/defis/aujourdhui/reveler?session_id=test-indice",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert "indice" in data
    assert data["indice_index"] >= 0
    assert data["indices_restants"] >= 0


@pytest.mark.anyio
async def test_reveler_indice_partie_terminee(client):
    await client.post(
        "/api/defis/aujourdhui/proposer?session_id=test-terminee",
        json={"titre_propose": "Paris"},
    )
    response = await client.post(
        "/api/defis/aujourdhui/reveler?session_id=test-terminee",
        json={},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_partie_etat(client):
    await client.post(
        "/api/defis/aujourdhui/proposer?session_id=test-etat",
        json={"titre_propose": "Lyon"},
    )
    response = await client.get(
        "/api/defis/aujourdhui/partie?session_id=test-etat"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["essais_effectues"] == 1
    assert "essais_restants" in data
    assert "indices_reveles" in data
    assert "score" in data


@pytest.mark.anyio
async def test_max_essais_atteint(client):
    session_id = "test-max"
    for _ in range(5):
        response = await client.post(
            f"/api/defis/aujourdhui/proposer?session_id={session_id}",
            json={"titre_propose": "Lyon"},
        )
    data = response.json()
    assert data["gagne"] is False
    assert data["essais_restants"] == 0

    response = await client.post(
        f"/api/defis/aujourdhui/proposer?session_id={session_id}",
        json={"titre_propose": "Paris"},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_titre_non_expose_sans_victoire(client):
    response = await client.post(
        "/api/defis/aujourdhui/proposer?session_id=test-expose",
        json={"titre_propose": "Marseille"},
    )
    data = response.json()
    assert data["correct"] is False
    assert data["titre"] is None
