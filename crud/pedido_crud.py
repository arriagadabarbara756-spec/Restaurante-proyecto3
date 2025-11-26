from datetime import datetime
from functools import reduce
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import get_session, safe_commit
from models import Pedido, PedidoMenu, MenuORM, Cliente, MenuIngrediente, IngredienteORM


def crear_pedido(id_cliente: int, items: dict[int, int], descripcion: str = "", fecha=None):
    if not items:
        raise ValueError("El pedido no tiene productos.")

    with get_session() as session:
        cliente = session.get(Cliente, id_cliente)
        if not cliente:
            raise ValueError("Cliente no válido.")

        menus = session.scalars(
            select(MenuORM)
            .options(
                joinedload(MenuORM.ingredientes)
                .joinedload(MenuIngrediente.ingrediente)
            )
            .where(MenuORM.id.in_(items.keys()))
        ).unique().all()

        if len(menus) != len(items):
            raise ValueError("Hay menús que no existen.")

        requeridos = {}
        for menu in menus:
            cant_menu = items[menu.id]
            for mi in menu.ingredientes:
                req = mi.cantidad * cant_menu
                requeridos[mi.ingrediente_id] = requeridos.get(mi.ingrediente_id, 0.0) + req

        ingredientes = session.scalars(
            select(IngredienteORM).where(IngredienteORM.id.in_(requeridos.keys()))
        ).all()

        faltantes = [
            (ing.id, requeridos[ing.id], ing.stock)
            for ing in ingredientes
            if requeridos[ing.id] > ing.stock
        ]

        if faltantes:
            raise ValueError(
                "Stock insuficiente:\n" +
                "\n".join(f"- Ing {fid}: req={req}, stock={stock}" for fid, req, stock in faltantes)
            )

        total = sum(menu.precio * items[menu.id] for menu in menus)

        if fecha is None:
            fecha = datetime.now()

        pedido = Pedido(
            cliente_id=id_cliente,
            fecha=fecha,
            total=total,
            descripcion=descripcion
        )
        session.add(pedido)
        session.flush()

        for menu in menus:
            session.add(PedidoMenu(
                pedido_id=pedido.id,
                menu_id=menu.id,
                cantidad=items[menu.id],
                precio_unitario=menu.precio
            ))

        for ing in ingredientes:
            ing.stock -= requeridos[ing.id]

        safe_commit(session)
        session.refresh(pedido)
        return pedido


# ================================================
# 🚀 LISTADOS DE PEDIDOS CON .unique() (OBLIGATORIO)
# ================================================

def listar_pedidos():
    with get_session() as session:
        result = session.scalars(
            select(Pedido)
            .options(
                joinedload(Pedido.cliente),
                joinedload(Pedido.items).joinedload(PedidoMenu.menu)
            )
        )
        return result.unique().all()



def listar_pedidos_por_cliente(id_cliente: int):
    with get_session() as session:
        result = session.scalars(
            select(Pedido)
            .options(
                joinedload(Pedido.cliente),
                joinedload(Pedido.items).joinedload(PedidoMenu.menu)
            )
            .where(Pedido.cliente_id == id_cliente)
            .order_by(Pedido.fecha.desc())
        )
        return result.unique().all()  # <-- FIX


def eliminar_pedido(id_pedido: int):
    with get_session() as session:
        ped = session.get(Pedido, id_pedido)
        if not ped:
            raise ValueError("Pedido no encontrado.")
        session.delete(ped)
        safe_commit(session)
