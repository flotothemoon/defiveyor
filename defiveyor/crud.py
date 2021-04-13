import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.environ["DATABASE_URL"]
# patch 'postgres' to 'postgresql' url since sqlalchemy only accepts the latter
DATABASE_URL = DATABASE_URL.replace("postgres:", "postgresql:")
if "sslmode" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL + "?sslmode=require"

engine = create_engine(DATABASE_URL, echo=False, future=True)
Session = sessionmaker(engine, expire_on_commit=False)
