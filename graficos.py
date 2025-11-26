
# graficos.py
import matplotlib.pyplot as plt
from collections import Counter
from sqlalchemy import select, func
from database import get_session
from models import Pedido, PedidoMenu, MenuORM, IngredienteORM, MenuIngrediente
import warnings
from matplotlib.ticker import FixedLocator

# Ocultar warnings de Matplotlib
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")


def grafico_ventas_por_fecha():
    """
    Retorna una figura con ventas por fecha (suma total por día).
    """
    with get_session() as session:
        rows = session.execute(
            select(func.date(Pedido.fecha), func.sum(Pedido.total)).group_by(func.date(Pedido.fecha))
        ).all()

    if not rows:
        raise ValueError("No hay datos disponibles para graficar ventas por fecha.")

    fechas = [r[0] for r in rows]
    totales = [r[1] for r in rows]

    fig, ax = plt.subplots()
    ax.plot(fechas, totales, marker="o")
    ax.set_title("Ventas por fecha")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Total vendido")
    fig.autofmt_xdate()
    return fig


def grafico_menus_mas_vendidos(top_n: int = 5):
    """
    Figura con los menús más comprados.
    """
    with get_session() as session:
        rows = session.execute(
            select(MenuORM.nombre, func.sum(PedidoMenu.cantidad))
            .join(PedidoMenu.menu)
            .group_by(MenuORM.nombre)
            .order_by(func.sum(PedidoMenu.cantidad).desc())
        ).all()

    if not rows:
        raise ValueError("No hay datos disponibles para graficar menús más vendidos.")

    filas = rows[:top_n]
    nombres = [r[0] for r in filas]
    cantidades = [r[1] for r in filas]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(nombres, cantidades)
    ax.set_title("Menús más vendidos", fontsize=12)
    ax.set_ylabel("Cantidad vendida", fontsize=10)
    # Usar FixedLocator para evitar warning
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, rotation=30, ha="right", fontsize=9)
    ax.tick_params(axis='y', labelsize=9)
    fig.tight_layout()
    return fig


def grafico_uso_ingredientes():
    """
    Uso de ingredientes en todos los pedidos.
    """
    with get_session() as session:
        pedidos = session.scalars(select(Pedido)).all()
        if not pedidos:
            raise ValueError("No hay pedidos para calcular uso de ingredientes.")
        # contabilizar ingredientes a través de los pedidos
        contador = Counter()
        for ped in pedidos:
            for item in ped.items:
                menu = item.menu
                for mi in menu.ingredientes:
                    if mi.ingrediente is None:
                        continue
                    total_ing = mi.cantidad * item.cantidad
                    contador[mi.ingrediente.nombre] += total_ing

    if not contador:
        raise ValueError("No hay datos de uso de ingredientes.")

    nombres = list(contador.keys())
    valores = list(contador.values())

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.bar(nombres, valores)
    ax.set_title("Uso de ingredientes", fontsize=12)
    ax.set_ylabel("Cantidad utilizada", fontsize=10)
    # Usar FixedLocator para evitar warning
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, rotation=30, ha="right", fontsize=9)
    ax.tick_params(axis='y', labelsize=9)
    fig.tight_layout()
    return fig
