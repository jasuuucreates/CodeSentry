"""Database layer: three tables stored with SQLAlchemy 2.x (synchronous ORM, no asyncio).

* ``Run``         one analysis batch (its name, settings, summary and timing).
* ``Submission``  one uploaded source file of a run, with its full text.
* ``PairScore``   the comparison of two submissions of the same run. The headline scores get their
                  own columns (so they could be queried or sorted in SQL); the complete PairResult
                  produced by the engine is kept as JSON in ``result_json``.

Deleting a Run deletes its submissions and pair scores (cascade), both in the ORM and, through
``ON DELETE CASCADE`` foreign keys, inside SQLite itself.
See docs/ARCHITECTURE_CONTRACT.md, section 7.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Common base class of every table."""


def _utc_now() -> datetime:
    # SQLite has no time-zone type, so the value is stored as naive UTC and labelled as UTC
    # again when it is turned into ISO 8601 (see Run.created_iso).
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Run(Base):
    __tablename__ = "runs"
    # AUTOINCREMENT stops SQLite from handing the id of a deleted run to a new run, so an old
    # bookmark can never open somebody else's results.
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Submission.id",
    )
    pair_scores: Mapped[list["PairScore"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PairScore.id",
    )

    @property
    def config(self) -> dict:
        return json.loads(self.config_json or "{}")

    @property
    def summary(self) -> dict:
        return json.loads(self.summary_json or "{}")

    @property
    def created_iso(self) -> str:
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return created.isoformat(timespec="seconds")

    def to_summary(self) -> dict:
        """The ``RunSummary`` object of the API contract."""
        summary = self.summary
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_iso,
            "file_count": summary.get("files", 0),
            "pair_count": summary.get("pairs_compared", 0),
            "high": summary.get("high", 0),
            "moderate": summary.get("moderate", 0),
            "low": summary.get("low", 0),
            "max_score": summary.get("max_score", 0.0),
            "mean_score": summary.get("mean_score", 0.0),
            "elapsed_ms": self.elapsed_ms,
        }


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warnings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    run: Mapped[Run] = relationship(back_populates="submissions")

    @property
    def warnings(self) -> list:
        return json.loads(self.warnings_json or "[]")

    def to_file_dict(self) -> dict:
        """The ``files[]`` entry of a BatchResult (no source text)."""
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "lines": self.line_count,
            "tokens": self.token_count,
            "warnings": self.warnings,
        }


class PairScore(Base):
    __tablename__ = "pair_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    a_submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    b_submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    fused: Mapped[float] = mapped_column(Float, nullable=False)
    token: Mapped[float] = mapped_column(Float, nullable=False)
    structure: Mapped[float | None] = mapped_column(Float, nullable=True)
    text_baseline: Mapped[float | None] = mapped_column(Float, nullable=True)
    tfidf_baseline: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped[Run] = relationship(back_populates="pair_scores")

    @property
    def result(self) -> dict:
        return json.loads(self.result_json)


class Database:
    """Owns the SQLAlchemy engine and session factory of one Flask app.

    Each app (the real server, or every test) gets its own instance, stored in
    ``app.extensions["codesentry_db"]``, so tests never share state.
    """

    def __init__(self, url: str):
        connect_args: dict = {}
        engine_kwargs: dict = {}
        if url.startswith("sqlite"):
            # Flask serves requests on several threads; each request opens its own session, so a
            # connection may be used by a thread other than the one that created it.
            connect_args["check_same_thread"] = False
            if ":memory:" in url or url.rstrip("/") == "sqlite:":
                # An in-memory database exists only inside one connection: share that single
                # connection between all sessions, or every request would see an empty database.
                engine_kwargs["poolclass"] = StaticPool
        self.engine = create_engine(url, connect_args=connect_args, **engine_kwargs)

        if url.startswith("sqlite"):
            @event.listens_for(self.engine, "connect")
            def _enable_foreign_keys(dbapi_connection, _record):  # pragma: no cover - trivial
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def session(self):
        """A new ORM session; use it as a context manager (``with db.session() as s:``)."""
        return self.Session()

    def dispose(self) -> None:
        self.engine.dispose()
