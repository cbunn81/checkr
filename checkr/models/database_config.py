# standard library imports
import logging
import os

# third party imports
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

logging.basicConfig(filename="sqlalchemy.log", encoding="utf-8", level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Session = sessionmaker(bind=engine)

Base = declarative_base()
