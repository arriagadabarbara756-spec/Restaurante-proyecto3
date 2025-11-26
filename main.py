# main.py
from database import engine, Base
import models  # importa para registrar las clases en Base


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tablas creadas correctamente.")
