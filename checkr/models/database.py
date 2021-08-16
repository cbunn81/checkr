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
    """Add columns for creation and update timestamps."""

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
    """A mixin to give a generic creation method to other classes."""

    @classmethod
    def create(cls, **kwargs) -> None:
        """A generic creation method for other classes to use.
        Includes session handling as well as a check to see if
        an existing record exists, in which case the session is rolled back."""
        obj = cls(**kwargs)
        with Session() as session:
            session.add(obj)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()


class Algorithm(BaseMixin, TimestampMixin, Base):
    """A class to handle the Algorithm table in the database."""

    __tablename__ = "algorithms"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)

    @classmethod
    def get_by_name(cls, name: str) -> object:
        """Retrieve an algorithm object when given the name of the algorithm (e.g. "blake2b").

        Args:
            name (str): The name of the algorithm (e.g. "blake2b").

        Returns:
            object: An algorithm object.
        """
        with Session() as session:
            return session.execute(
                select(cls).where(cls.name == name)
            ).scalar_one_or_none()


class File(BaseMixin, TimestampMixin, Base):
    """A class to handle the File table in the database."""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    path = Column(Text, nullable=False)
    algorithm_id = Column(Integer, ForeignKey("algorithms.id"), nullable=False)
    algorithm = relationship("Algorithm")
    checksum = Column(Text, nullable=False)

    @classmethod
    def create(cls, algorithm_name: str, **kwargs) -> None:
        """An inherited class method that creates a File object.

        Args:
            algorithm_name (str): The name of the algorithm used to generate a file's checksum (e.g. "blake2b").
        """
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        if algorithm is None:
            Algorithm.create(name=algorithm_name)
            algorithm = Algorithm.get_by_name(name=algorithm_name)
        kwargs["algorithm"] = algorithm
        super().create(**kwargs)

    @classmethod
    def get_result(cls, path: str, algorithm_name: str) -> dict:
        """Retrieve result data on a file from the database. Path and algorithm name are
            required as a file could have more than one record if it has been scanned with
            multiple checksum algorithms.

        Args:
            path (str): The path to the file.
            algorithm_name (str): The algorithm used to generate the checksum (e.g. "blake2b").

        Returns:
            dict: A dictionary containing the result row from the database.
        """
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
        """Retrieve a checksum digest for a file. The algorithm name needs to be
            given because there could be multiple records for the same file from
            different algorithms.

        Args:
            path (str): The path of the file.
            algorithm_name (str): The algorithm used (e.g. "blake2b").

        Returns:
            str: The checksum digest.
        """
        algorithm = Algorithm.get_by_name(name=algorithm_name)
        with Session() as session:
            return session.execute(
                select(cls.checksum).where(
                    cls.path == path and cls.algorithm == algorithm
                )
            ).scalar_one_or_none()

    @classmethod
    def update_checksum(cls, path: str, algorithm_name: str, checksum: str) -> None:
        """Update the checksum digest for an existing record.

        Args:
            path (str): The path of the file.
            algorithm_name (str): The algorithm used (e.g. "blake2b").
            checksum (str): The new checksum digest to update with.
        """
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
    """Store a result in the database.

    Args:
        checkfilename (str): The file being checked.
        checksum (str): The checksum digest.
        algorithm (str, optional): The algorithm used. Defaults to "blake2b".
    """
    File.create(path=checkfilename, algorithm_name=algorithm, checksum=checksum)


def update_result_in_db(
    checkfilename: str, checksum: str, algorithm: str = "blake2b"
) -> None:
    """Update a result in the database.

    Args:
        checkfilename (str): The file being checked.
        checksum (str): The checksum digest.
        algorithm (str, optional): The algorithm used. Defaults to "blake2b".
    """
    File.update_checksum(
        path=checkfilename, algorithm_name=algorithm, checksum=checksum
    )


def get_stored_checksum_from_db(checkfilename: str, algorithm: str = "blake2b") -> str:
    """Get the checksum result for a file from the database. The algorithm name must
        be given because there could be multiple records for the same file if multiple
        algorithms have been used.

    Args:
        checkfilename (str): The file for the checksum being retrieved.
        algorithm (str, optional): The algorithm used. Defaults to "blake2b".

    Returns:
            str: The checksum digest.
    """
    return File.get_checksum(path=checkfilename, algorithm_name=algorithm)


def check_file_against_db(checkfilename: str, algorithm: str = "blake2b") -> bool:
    """Check if the current checksum matches what is stored in the database. Both
        file name and algorithm need to be given because there could multiple
        records for the same file if multiple algorithms have been used.

    Args:
        checkfilename (str): The file being checked.
        algorithm (str, optional): The algorithm used. Defaults to "blake2b".

    Returns:
        bool: True if the checksums match, false if they don't.
    """
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
