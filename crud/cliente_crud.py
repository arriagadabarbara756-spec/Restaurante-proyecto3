# crud/cliente_crud.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from database import get_session, safe_commit
from models import Cliente


def crear_cliente(nombre: str, correo: str, telefono: str | None = None):
    if not nombre.strip() or not correo.strip():
        raise ValueError("Nombre y correo no pueden estar vacíos.")
    with get_session() as session:
        nuevo = Cliente(nombre=nombre.strip(), correo=correo.strip(), telefono=telefono)
        session.add(nuevo)
        try:
            safe_commit(session)
        except IntegrityError:
            session.rollback()
            raise ValueError("El correo ya está registrado.")
        session.refresh(nuevo)
        return nuevo


def listar_clientes():
    with get_session() as session:
        return session.scalars(select(Cliente).order_by(Cliente.nombre)).all()


def actualizar_cliente(id_cliente: int, nombre: str, correo: str, telefono: str | None = None):
    with get_session() as session:
        c = session.get(Cliente, id_cliente)
        if not c:
            raise ValueError("Cliente no encontrado.")
        c.nombre = nombre.strip()
        c.correo = correo.strip()
        c.telefono = telefono
        try:
            safe_commit(session)
        except IntegrityError:
            session.rollback()
            raise ValueError("El correo ya está registrado para otro cliente.")
        return c


def eliminar_cliente(id_cliente: int):
    """
    No permite eliminar si tiene pedidos asociados.
    """
    from models import Pedido
    with get_session() as session:
        c = session.get(Cliente, id_cliente)
        if not c:
            raise ValueError("Cliente no encontrado.")
        # Verificar pedidos
        tiene_pedidos = session.query(Pedido).filter_by(cliente_id=id_cliente).first()
        if tiene_pedidos:
            raise ValueError("No se puede eliminar un cliente con pedidos asociados.")
        session.delete(c)
        safe_commit(session)
