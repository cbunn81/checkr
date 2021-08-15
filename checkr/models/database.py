# standard library imports
import logging

# third party imports
from sqlalchemy import (
    select,
    update,
    ForeignKey,
    Column,
    Integer,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import relationship, declarative_mixin
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

# local imports
from models.database_config import Base, Session, engine
from helpers import create_checksum


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
    def create(cls, **kwargs) -> None:
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
        kwargs["algorithm"] = algorithm
        super().create(**kwargs)

    @classmethod
    def get_result(cls, path: str, algorithm_name: str) -> dict:
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        with Session() as session:
            return (
                session.execute(
                    select(
                        cls.id,
                        cls.path,
                        Algorithm.name.label("algorithm_name"),
                        cls.checksum,
                    )
                    .join(Algorithm)
                    .where(cls.path == path and cls.algorithm == algorithm)
                )
                .one_or_none()
                ._asdict()
            )

    @classmethod
    def get_checksum(cls, path: str, algorithm_name: str) -> str:
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        with Session() as session:
            return session.execute(
                select(cls.checksum).where(
                    cls.path == path and cls.algorithm == algorithm
                )
            ).scalar_one_or_none()

    @classmethod
    def update_checksum(cls, path: str, algorithm_name: str, checksum: str) -> None:
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        with Session() as session:
            session.execute(
                update(File)
                .where(cls.path == path and cls.algorithm == algorithm)
                .values(checksum=checksum)
            )
            try:
                session.commit()
            except IntegrityError:
                session.rollback()


Index("path_algorithm_index", File.path, File.algorithm_id, unique=True)

Base.metadata.create_all(engine)


def store_result_in_db(
    checkfilename: str, checksum: str, algorithm: str = "blake2b"
) -> None:
    File.create(path=checkfilename, algorithm_name=algorithm, checksum=checksum)


def update_result_in_db(
    checkfilename: str, checksum: str, algorithm: str = "blake2b"
) -> None:
    File.update_checksum(
        path=checkfilename, algorithm_name=algorithm, checksum=checksum
    )


def get_stored_checksum_from_db(checkfilename: str, algorithm: str = "blake2b") -> None:
    return File.get_checksum(path=checkfilename, algorithm_name=algorithm)


def check_file_against_db(checkfilename: str, algorithm: str = "blake2b") -> bool:
    logger = logging.getLogger("checkr")
    stored_checksum = get_stored_checksum_from_db(
        checkfilename=checkfilename, algorithm=algorithm
    )
    if stored_checksum is not None:
        new_checksum = create_checksum(filename=checkfilename, algorithm=algorithm)
        if stored_checksum == new_checksum:
            return True
        else:
            return False
    else:
        logger.warning(f"No checksum exists for file ({checkfilename}) in database.")
