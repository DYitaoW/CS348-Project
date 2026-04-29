"""
SQLAlchemy ORM models for the Soccer League Stats Manager.

These classes map to database tables and define relationships
between them. The comments are intentionally detailed to make
learning and maintenance easier.
"""

from __future__ import annotations

from typing import List
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base

# the main team table that stores the team info.
class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("name", "city", name="uq_team_name_city"),
    )

    # team data 
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    coach_name: Mapped[str] = mapped_column(String(100), nullable=False)
    players: Mapped[List[Player]] = relationship(
        "Player",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("team_id", "jersey_number", name="uq_team_jersey"),
        CheckConstraint("jersey_number >= 0", name="ck_jersey_non_negative"),
        CheckConstraint("goals >= 0", name="ck_goals_non_negative"),
        CheckConstraint("assists >= 0", name="ck_assists_non_negative"),
        # Indexes to speed up the player search/report filters.
        Index("ix_players_team_id", "team_id"),
        Index("ix_players_goals", "goals"),
        Index("ix_players_assists", "assists"),
    )

    # player info, has a foreign key to a team, also is deleted if the team is deleted 
    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.team_id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(50), nullable=False)
    jersey_number: Mapped[int] = mapped_column(Integer, nullable=False)
    goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    team: Mapped[Team] = relationship("Team", back_populates="players")
