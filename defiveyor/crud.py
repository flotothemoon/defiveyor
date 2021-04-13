import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ['DATABASE_URL']

engine = create_engine(DATABASE_URL, echo=True, future=True)
Session = sessionmaker(engine)


def insert_bootstrap_objects():
    with Session() as session:
        # TODO
        pass
