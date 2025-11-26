# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = "sqlite:///restaurante.db"  # puedes cambiar a otro motor si quieres

engine = create_engine(
    DATABASE_URL,
    echo=False,           # pon True si quieres ver las consultas en consola
    future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_session():
    """
    Crea una sesión nueva. Usar con with para asegurar rollback en errores.
    """
    return SessionLocal()


def safe_commit(session):
    """
    Commit con rollback automático en caso de error.
    """
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
