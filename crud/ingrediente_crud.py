# crud/ingrediente_crud.py
import csv
from functools import reduce
from sqlalchemy import select
from database import get_session, safe_commit
from models import IngredienteORM


def crear_ingrediente(nombre: str, unidad: str, stock: float):
    if not nombre.strip():
        raise ValueError("El nombre del ingrediente no puede estar vacío.")
    if stock <= 0:
        raise ValueError("El stock debe ser un número positivo mayor que cero.")
    with get_session() as session:
        nombre_norm = nombre.strip().lower()
        ya = session.scalars(select(IngredienteORM).where(IngredienteORM.nombre.ilike(nombre_norm))).first()
        if ya:
            raise ValueError("Ya existe un ingrediente con ese nombre.")
        ing = IngredienteORM(nombre=nombre_norm, unidad=unidad.strip(), stock=float(stock))
        session.add(ing)
        safe_commit(session)
        session.refresh(ing)
        return ing


def actualizar_ingrediente(id_ing: int, nombre: str, unidad: str, stock: float):
    if stock <= 0:
        raise ValueError("El stock debe ser positivo.")
    with get_session() as session:
        ing = session.get(IngredienteORM, id_ing)
        if not ing:
            raise ValueError("Ingrediente no encontrado.")
        ing.nombre = nombre.strip().lower()
        ing.unidad = unidad.strip()
        ing.stock = float(stock)
        safe_commit(session)
        return ing


def eliminar_ingrediente(id_ing: int):
    with get_session() as session:
        ing = session.get(IngredienteORM, id_ing)
        if not ing:
            raise ValueError("Ingrediente no encontrado.")
        session.delete(ing)
        safe_commit(session)


def listar_ingredientes():
    with get_session() as session:
        return session.scalars(
            select(IngredienteORM).order_by(IngredienteORM.id.asc())
        ).all()



def cargar_desde_csv(ruta_csv: str):
    """
    Lee CSV (nombre,unidad,cantidad) y los guarda/actualiza en BD usando ORM.
    Respeta la unidad original del CSV y la actualiza si el ingrediente ya existía.
    """
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        lector = csv.reader(f)
        encabezado = next(lector, None)

        filas = list(lector)

    # filter: descartar filas mal formadas
    filas_validas = list(filter(lambda row: len(row) == 3 and row[0].strip(), filas))

    # map: transformar a dicts normalizados
    def fila_a_dict(fila):
        nombre, unidad, cantidad = fila
        try:
            cant_f = float(cantidad)
        except Exception:
            cant_f = 0.0
        return {
            "nombre": nombre.strip().lower(),
            "unidad": unidad.strip().lower(),
            "cantidad": cant_f
        }

    datos = list(map(fila_a_dict, filas_validas))

    # reduce: sumar cantidades de un mismo ingrediente
    def acum(acc, elem):
        nombre = elem["nombre"]
        if nombre not in acc:
            acc[nombre] = {"unidad": elem["unidad"], "cantidad": 0.0}
        acc[nombre]["cantidad"] += elem["cantidad"]
        return acc

    acumulado = reduce(acum, datos, {})

    # guardar en BD
    with get_session() as session:
        for nombre, info in acumulado.items():
            unidad = info["unidad"]
            cantidad = info["cantidad"]

            if cantidad <= 0:
                continue

            ing = session.scalars(
                select(IngredienteORM).where(IngredienteORM.nombre == nombre)
            ).first()

            if ing:
                # si ya existe, sumamos stock Y actualizamos la unidad según el CSV
                ing.stock += cantidad
                if unidad and ing.unidad != unidad:
                    ing.unidad = unidad
            else:
                # si no existe, usamos la unidad del CSV
                ing = IngredienteORM(
                    nombre=nombre,
                    unidad=unidad,
                    stock=cantidad
                )
                session.add(ing)

        safe_commit(session)


