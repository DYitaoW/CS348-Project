from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError, OperationalError

from db import SessionLocal, engine, Base
from models import Team, Player
import os


def create_app() -> Flask:

    app = Flask(__name__)
    # CORS:
    # - For local dev you can leave FRONTEND_ORIGIN unset (allows all origins).
    # - For cloud, set FRONTEND_ORIGIN to your deployed frontend origin and we
    #   will only allow that origin.
    frontend_origin = os.getenv("FRONTEND_ORIGIN")
    if frontend_origin:
        CORS(app, resources={r"/*": {"origins": [frontend_origin]}})
    else:
        CORS(app)

    def _is_serialization_failure(exc: Exception) -> bool:
        """
        PostgreSQL SERIALIZABLE transactions can fail with SQLSTATE 40001.
        SQLAlchemy typically wraps driver exceptions in OperationalError.
        """

        if isinstance(exc, OperationalError):
            orig = getattr(exc, "orig", None)
            # Try common locations for SQLSTATE
            sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
            if sqlstate == "40001":
                return True
            # Fallback: string check (last resort)
            msg = str(orig) if orig is not None else str(exc)
            return "40001" in msg or "serialization_failure" in msg.lower()
        return False

    def _run_with_retries(work_fn, max_retries: int = 3):
        """
        Run a unit of DB work with retries for SERIALIZABLE serialization failures.
        Creates a fresh session per attempt.
        """

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                with SessionLocal() as session:
                    return work_fn(session)
            except OperationalError as exc:
                last_exc = exc
                if _is_serialization_failure(exc) and attempt < max_retries - 1:
                    continue
                raise
        raise last_exc  # pragma: no cover

    @app.get("/health")
    def health_check():

        try:
            with SessionLocal() as session:
                session.execute(text("SELECT 1"))
            return jsonify({"status": "ok"})
        except Exception as exc:  # pragma: no cover - for runtime visibility
            return jsonify({"status": "error", "detail": str(exc)}), 500

    @app.post("/init-db")
    def init_db():

        Base.metadata.create_all(bind=engine)
        return jsonify({"status": "ok", "message": "Tables created."})

    @app.post("/reset-db")
    def reset_db():

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return jsonify({"status": "ok", "message": "Tables reset."})

    @app.get("/tables")
    def list_tables():
        inspector = inspect(engine)
        return jsonify({"tables": inspector.get_table_names()})

    @app.get("/teams")
    def list_teams():
        with SessionLocal() as session:
            teams = session.query(Team).order_by(Team.name.asc()).all()
            return jsonify(
                [
                    {
                        "team_id": t.team_id,
                        "name": t.name,
                        "city": t.city,
                        "coach_name": t.coach_name,
                    }
                    for t in teams
                ]
            )

    @app.post("/teams")
    def create_team():
        data = request.get_json(force=True)
        try:
            def work(session):
                team = Team(
                    name=data["name"],
                    city=data["city"],
                    coach_name=data["coach_name"],
                )
                with session.begin():
                    session.add(team)
                return jsonify({"status": "ok", "team_id": team.team_id})

            return _run_with_retries(work)
        except IntegrityError:
            return (
                jsonify(
                    {
                        "error": "A team with the same name and city already exists."
                    }
                ),
                400,
            )
        except OperationalError as exc:
            if _is_serialization_failure(exc):
                return jsonify({"error": "Please retry (concurrent update)."}), 409
            raise

    @app.put("/teams/<int:team_id>")
    def update_team(team_id: int):
        data = request.get_json(force=True)
        try:
            def work(session):
                team = session.get(Team, team_id)
                if not team:
                    return jsonify({"error": "Team not found"}), 404
                with session.begin():
                    team.name = data["name"]
                    team.city = data["city"]
                    team.coach_name = data["coach_name"]
                return jsonify({"status": "ok"})

            return _run_with_retries(work)
        except IntegrityError:
            return (
                jsonify(
                    {
                        "error": "A team with the same name and city already exists."
                    }
                ),
                400,
            )
        except OperationalError as exc:
            if _is_serialization_failure(exc):
                return jsonify({"error": "Please retry (concurrent update)."}), 409
            raise

    @app.delete("/teams/<int:team_id>")
    def delete_team(team_id: int):
        try:
            def work(session):
                team = session.get(Team, team_id)
                if not team:
                    return jsonify({"error": "Team not found"}), 404
                with session.begin():
                    # Players are deleted automatically via ON DELETE CASCADE.
                    session.delete(team)
                return jsonify({"status": "ok"})

            return _run_with_retries(work)
        except OperationalError as exc:
            if _is_serialization_failure(exc):
                return jsonify({"error": "Please retry (concurrent update)."}), 409
            raise

    @app.get("/players")
    def list_players():
        with SessionLocal() as session:
            players = session.query(Player).order_by(Player.name.asc()).all()
            return jsonify(
                [
                    {
                        "player_id": p.player_id,
                        "team_id": p.team_id,
                        "name": p.name,
                        "position": p.position,
                        "jersey_number": p.jersey_number,
                        "goals": p.goals,
                        "assists": p.assists,
                    }
                    for p in players
                ]
            )

    @app.post("/players")
    def create_player():
        data = request.get_json(force=True)
        try:
            def work(session):
                player = Player(
                    team_id=int(data["team_id"]),
                    name=data["name"],
                    position=data["position"],
                    jersey_number=int(data["jersey_number"]),
                    goals=int(data.get("goals", 0)),
                    assists=int(data.get("assists", 0)),
                )
                with session.begin():
                    session.add(player)
                return jsonify({"status": "ok", "player_id": player.player_id})

            return _run_with_retries(work)
        except IntegrityError:
            return (
                jsonify(
                    {
                        "error": "Jersey number must be unique within the team."
                    }
                ),
                400,
            )
        except OperationalError as exc:
            if _is_serialization_failure(exc):
                return jsonify({"error": "Please retry (concurrent update)."}), 409
            raise

    @app.put("/players/<int:player_id>")
    def update_player(player_id: int):
        data = request.get_json(force=True)
        try:
            def work(session):
                player = session.get(Player, player_id)
                if not player:
                    return jsonify({"error": "Player not found"}), 404
                with session.begin():
                    player.team_id = int(data["team_id"])
                    player.name = data["name"]
                    player.position = data["position"]
                    player.jersey_number = int(data["jersey_number"])
                    player.goals = int(data.get("goals", 0))
                    player.assists = int(data.get("assists", 0))
                return jsonify({"status": "ok"})

            return _run_with_retries(work)
        except IntegrityError:
            return (
                jsonify(
                    {
                        "error": "Jersey number must be unique within the team."
                    }
                ),
                400,
            )
        except OperationalError as exc:
            if _is_serialization_failure(exc):
                return jsonify({"error": "Please retry (concurrent update)."}), 409
            raise

    @app.delete("/players/<int:player_id>")
    def delete_player(player_id: int):
        try:
            def work(session):
                player = session.get(Player, player_id)
                if not player:
                    return jsonify({"error": "Player not found"}), 404
                with session.begin():
                    session.delete(player)
                return jsonify({"status": "ok"})

            return _run_with_retries(work)
        except OperationalError as exc:
            if _is_serialization_failure(exc):
                return jsonify({"error": "Please retry (concurrent update)."}), 409
            raise

    @app.post("/transaction/team-with-players")
    def transaction_team_with_players():
        """
        Transaction demo endpoint:
        - Creates a team and multiple players in ONE transaction.
        - If any insert fails (duplicate team, duplicate jersey, etc.), everything rolls back.

        Expected JSON:
          team: { name, city, coach_name }
          players: [ { name, position, jersey_number, goals, assists }, ... ]
        """

        data = request.get_json(force=True)
        team_data = data.get("team") or {}
        players_data = data.get("players") or []

        with SessionLocal() as session:
            try:
                with session.begin():
                    team = Team(
                        name=team_data["name"],
                        city=team_data["city"],
                        coach_name=team_data["coach_name"],
                    )
                    session.add(team)
                    session.flush()  # ensures team.team_id is assigned

                    for p in players_data:
                        session.add(
                            Player(
                                team_id=team.team_id,
                                name=p["name"],
                                position=p["position"],
                                jersey_number=int(p["jersey_number"]),
                                goals=int(p.get("goals", 0)),
                                assists=int(p.get("assists", 0)),
                            )
                        )

                return jsonify({"status": "ok", "team_id": team.team_id})
            except IntegrityError as exc:
                return jsonify({"error": "Transaction failed", "detail": str(exc)}), 400

    @app.get("/report/players")
    def report_players():
        team_id = request.args.get("team_id", default=None, type=int)
        min_goals = request.args.get("min_goals", default=0, type=int)
        min_assists = request.args.get("min_assists", default=0, type=int)
        max_goals = request.args.get("max_goals", default=None, type=int)
        max_assists = request.args.get("max_assists", default=None, type=int)

        # If max values are not provided, allow any upper bound.
        max_goals = 10**9 if max_goals is None else max_goals
        max_assists = 10**9 if max_assists is None else max_assists

        with SessionLocal() as session:
            query = (
                session.query(Player, Team)
                .join(Team, Player.team_id == Team.team_id)
                .filter(Player.goals >= min_goals)
                .filter(Player.goals <= max_goals)
                .filter(Player.assists >= min_assists)
                .filter(Player.assists <= max_assists)
            )
            if team_id:
                query = query.filter(Player.team_id == team_id)

            rows = query.order_by(Player.name.asc()).all()

            count = len(rows)
            avg_goals = (
                sum(p.goals for p, _ in rows) / count if count > 0 else 0
            )
            avg_assists = (
                sum(p.assists for p, _ in rows) / count if count > 0 else 0
            )

            return jsonify(
                {
                    "players": [
                        {
                            "player_id": p.player_id,
                            "team_name": t.name,
                            "name": p.name,
                            "position": p.position,
                            "jersey_number": p.jersey_number,
                            "goals": p.goals,
                            "assists": p.assists,
                        }
                        for p, t in rows
                    ],
                    "stats": {
                        "count": count,
                        "avg_goals": round(avg_goals, 2),
                        "avg_assists": round(avg_assists, 2),
                    },
                }
            )

    return app

#  runs the app
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=True)
