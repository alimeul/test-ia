from datetime import date

from sqlmodel import Session, select

from app.models.defi import Defi
from app.models.partie import Partie


def get_historique_defis(session: Session) -> list[dict]:
    statement = select(Defi).order_by(Defi.date_publication.desc())
    defis = session.exec(statement).all()
    return [
        {
            "date": d.date_publication.isoformat(),
            "difficulte": d.score_difficulte,
        }
        for d in defis
    ]


def get_defi_by_date_str(session: Session, date_str: str) -> Defi | None:
    try:
        defi_date = date.fromisoformat(date_str)
    except ValueError:
        return None
    statement = select(Defi).where(Defi.date_publication == defi_date)
    return session.exec(statement).first()


def calculer_stats_session(session: Session, session_id: str) -> dict:
    statement = select(Partie).where(
        Partie.session_id == session_id, Partie.termine == True
    )
    parties = session.exec(statement).all()

    total = len(parties)
    gagnees = sum(1 for p in parties if p.gagne)

    best_score = max((p.score for p in parties), default=0)

    partie_dates = sorted(
        {p.id: p.date_partie.date() for p in parties if p.gagne}.values(),
        reverse=True,
    )

    current_streak = 0
    best_streak = 0
    if partie_dates:
        today = date.today()
        expected = today
        streak = 0
        for d in sorted(set(partie_dates), reverse=True):
            if d == expected:
                streak += 1
                expected = date.fromordinal(d.toordinal() - 1)
            elif d < expected:
                break
        current_streak = streak

        sorted_dates = sorted(set(partie_dates))
        temp_streak = 1
        best_streak = 1 if sorted_dates else 0
        for i in range(1, len(sorted_dates)):
            prev = sorted_dates[i - 1]
            curr = sorted_dates[i]
            if curr.toordinal() == prev.toordinal() + 1:
                temp_streak += 1
                best_streak = max(best_streak, temp_streak)
            else:
                temp_streak = 1

    return {
        "total_parties": total,
        "total_gagnees": gagnees,
        "taux_reussite": round(gagnees / total * 100, 1) if total > 0 else 0.0,
        "serie_actuelle": current_streak,
        "meilleure_serie": best_streak,
        "meilleur_score": best_score,
    }
