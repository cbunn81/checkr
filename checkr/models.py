# standard library imports
import logging

# third party imports
from sqlalchemy import (
    create_engine,
    select,
    ForeignKey,
    Column,
    Integer,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, declarative_mixin
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError


logging.basicConfig(filename="sqlalchemy.log", encoding="utf-8", level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine = create_engine("sqlite:///checkr.sqlite")
Base = declarative_base()
Session = sessionmaker(bind=engine)


@declarative_mixin
class TimestampMixin:
    time_created = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    time_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class BaseMixin(object):
    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        with Session() as session:
            session.add(obj)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()


class Algorithm(BaseMixin, TimestampMixin, Base):
    __tablename__ = "algorithms"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)

    @classmethod
    def get_by_name(cls, name: str) -> object:
        with Session() as session:
            return session.execute(
                select(cls).where(cls.name == name)
            ).scalar_one_or_none()


class File(BaseMixin, TimestampMixin, Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)
    algorithm_id = Column(Integer, ForeignKey("algorithms.id"), nullable=False)
    algorithm = relationship("Algorithm")
    checksum = Column(Text, nullable=False)

    @classmethod
    def create(cls, algorithm_name: str, **kwargs) -> None:
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        if algorithm is None:
            Algorithm.create(name=algorithm_name)
            algorithm = Algorithm.get_by_name(name=algorithm_name)
        obj = cls(algorithm=algorithm, **kwargs)
        with Session() as session:
            session.add(obj)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()

    @classmethod
    def get_checksum(cls, path: str, algorithm_name: str) -> str:
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        with Session() as session:
            return session.execute(
                select(cls.checksum).where(
                    cls.path == path and cls.algorithm == algorithm
                )
            ).scalar_one_or_none()


Index("path_algorithm_index", File.path, File.algorithm_id, unique=True)

Base.metadata.create_all(engine)
