# ============================================================
#         CREAR MENÚS PREDETERMINADOS (DESDE APP)
# ============================================================
def crear_menus_predeterminados():
    menus_defecto = [
        {
            "nombre": "Papas fritas",
            "descripcion": "Papas fritas clásicas, crujientes y doradas.",
            "precio": 500,
            "ingredientes": {"papas": 5}
        },
        {
            "nombre": "Pepsi",
            "descripcion": "Bebida gaseosa refrescante Pepsi.",
            "precio": 1100,
            "ingredientes": {"pepsi": 1}
        },
        {
            "nombre": "Completo",
            "descripcion": "Pan con vienesa, tomate y palta, estilo chileno.",
            "precio": 1800,
            "ingredientes": {"vienesa": 1, "pan de completo": 1, "tomate": 1, "palta": 1}
        },
        {
            "nombre": "Hamburguesa",
            "descripcion": "Hamburguesa tradicional con queso y carne.",
            "precio": 3500,
            "ingredientes": {"pan de hamburguesa": 1, "lamina de queso": 1, "churrasco de carne": 1}
        },
        {
            "nombre": "Panqueques",
            "descripcion": "Panqueques rellenos de manjar y espolvoreados con azúcar flor.",
            "precio": 2000,
            "ingredientes": {"panqueques": 2, "manjar": 1, "azucar flor": 1}
        },
        {
            "nombre": "Pollo frito",
            "descripcion": "Presa de pollo empanizada y frita, muy crocante.",
            "precio": 2800,
            "ingredientes": {"presa de pollo": 1, "porcion de harina": 1, "porcion de aceite": 1}
        },
        {
            "nombre": "Ensalada mixta",
            "descripcion": "Ensalada fresca de lechuga, tomate y zanahoria rallada.",
            "precio": 1500,
            "ingredientes": {"lechuga": 1, "tomate": 1, "zanahoria rallada": 1}
        }
    ]

    from crud.ingrediente_crud import listar_ingredientes
    from sqlalchemy.orm import Session
    from database import get_session, safe_commit
    import tkinter.messagebox as messagebox

    with get_session() as session:
        existentes = {m.nombre.lower() for m in session.scalars(select(MenuORM)).all()}
        ingredientes_bd = {ing.nombre.lower(): ing for ing in session.scalars(select(IngredienteORM)).all()}
        generados = []
        errores = []
        for menu in menus_defecto:
            if menu["nombre"].lower() not in existentes:
                faltantes = []
                for nombre_ing, cantidad in menu["ingredientes"].items():
                    ing = ingredientes_bd.get(nombre_ing.lower())
                    if not ing:
                        faltantes.append(f"Ingrediente '{nombre_ing}' no encontrado.")
                    elif ing.stock < cantidad:
                        faltantes.append(f"No hay suficiente stock de '{nombre_ing}' (stock: {ing.stock}, requerido: {cantidad})")
                if faltantes:
                    errores.append(f"No se pudo crear el menú '{menu['nombre']}':\n" + "\n".join(faltantes))
                    continue
                # Descontar stock
                for nombre_ing, cantidad in menu["ingredientes"].items():
                    ing = ingredientes_bd[nombre_ing.lower()]
                    ing.stock -= cantidad
                # Crear menú
                try:
                    nuevo_menu = MenuORM(
                        nombre=menu["nombre"],
                        descripcion=menu["descripcion"],
                        precio=menu["precio"]
                    )
                    session.add(nuevo_menu)
                    session.flush()
                    for nombre_ing, cantidad in menu["ingredientes"].items():
                        ing = ingredientes_bd[nombre_ing.lower()]
                        session.add(MenuIngrediente(
                            menu_id=nuevo_menu.id,
                            ingrediente_id=ing.id,
                            cantidad=float(cantidad)
                        ))
                    safe_commit(session)
                    generados.append(menu["nombre"])
                except Exception as e:
                    errores.append(f"Error al crear menú '{menu['nombre']}': {e}")
        # Mostrar solo una ventana emergente al final
        import tkinter.messagebox as messagebox
        if generados:
            messagebox.showinfo("Menús generados", f"Menús generados correctamente: {', '.join(generados)}")
        if errores:
            messagebox.showwarning("Errores al generar menús", '\n\n'.join(errores))
# ============================================================
#      LIMPIAR INGREDIENTES HUÉRFANOS DE MENÚS
# ============================================================
def limpiar_menu_ingredientes_huerfanos():
    from database import get_session
    from models import MenuIngrediente, IngredienteORM
    with get_session() as session:
        huerfanos = session.query(MenuIngrediente).outerjoin(IngredienteORM, MenuIngrediente.ingrediente_id == IngredienteORM.id).filter(IngredienteORM.id == None).all()
        count = 0
        for mi in huerfanos:
            session.delete(mi)
            count += 1
        session.commit()
    return count
# crud/menu_crud.py
from functools import reduce
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import get_session, safe_commit
from models import MenuORM, MenuIngrediente, IngredienteORM


# ============================================================
#                  CREAR MENÚ
# ============================================================
def crear_menu(nombre: str, descripcion: str, precio: float, ingredientes_cantidades: dict[int, float]):
    """
    ingredientes_cantidades: dict {id_ingrediente: cantidad_requerida}
    """
    if not nombre.strip():
        raise ValueError("El nombre del menú no puede estar vacío.")
    if precio <= 0:
        raise ValueError("El precio debe ser positivo.")
    if any(c <= 0 for c in ingredientes_cantidades.values()):
        raise ValueError("Las cantidades de ingredientes deben ser positivas.")

    with get_session() as session:
        existe = session.scalars(
            select(MenuORM).where(MenuORM.nombre.ilike(nombre.strip()))
        ).first()
        if existe:
            raise ValueError("Ya existe un menú con ese nombre.")

        ids = list(ingredientes_cantidades.keys())
        encontrados = session.scalars(
            select(IngredienteORM).where(IngredienteORM.id.in_(ids))
        ).all()
        if len(encontrados) != len(ids):
            raise ValueError("Hay ingredientes que no existen.")

        menu = MenuORM(
            nombre=nombre.strip(),
            descripcion=descripcion.strip(),
            precio=float(precio)
        )
        session.add(menu)
        session.flush()  # obtener id

        # asignar ingredientes
        for id_ing, cant in ingredientes_cantidades.items():
            session.add(MenuIngrediente(
                menu_id=menu.id,
                ingrediente_id=id_ing,
                cantidad=float(cant)
            ))

        safe_commit(session)
        session.refresh(menu)
        return menu


# ============================================================
#            LISTADOS DE MENÚS (USADOS EN COMPRA)
# ============================================================

# 🚀 Versión ligera: NO carga ingredientes.
# Usar esta función en la pestaña COMPRA para EVITAR el error unique()
def listar_menus_basico():
    with get_session() as session:
        return session.scalars(
            select(MenuORM).order_by(MenuORM.nombre)
        ).all()


# ============================================================
#       LISTAR MENÚS COMPLETOS (CON INGREDIENTES)
# ============================================================

def listar_menus():
    """Cargar menús + ingredientes (para edición)."""
    with get_session() as session:
        result = session.scalars(
            select(MenuORM)
            .options(
                joinedload(MenuORM.ingredientes)
                .joinedload(MenuIngrediente.ingrediente)
            )
            .order_by(MenuORM.nombre)
        )
        return result.unique().all()   # ✔ OBLIGATORIO


def obtener_menu(id_menu: int):
    with get_session() as session:
        result = session.scalars(
            select(MenuORM)
            .options(
                joinedload(MenuORM.ingredientes)
                .joinedload(MenuIngrediente.ingrediente)
            )
            .where(MenuORM.id == id_menu)
        )
        return result.unique().one_or_none()


# ============================================================
#                    ACTUALIZAR MENÚ
# ============================================================

def actualizar_menu(id_menu: int, nombre: str, descripcion: str, precio: float,
                    ingredientes_cantidades: dict[int, float]):
    if precio <= 0:
        raise ValueError("El precio debe ser positivo.")

    with get_session() as session:
        menu = session.get(MenuORM, id_menu)
        if not menu:
            raise ValueError("Menú no encontrado.")

        menu.nombre = nombre.strip()
        menu.descripcion = descripcion.strip()
        menu.precio = float(precio)

        # borrar ingredientes anteriores
        for mi in list(menu.ingredientes):
            session.delete(mi)
        session.flush()

        # agregar nuevos ingredientes
        for id_ing, cant in ingredientes_cantidades.items():
            if cant <= 0:
                continue
            session.add(MenuIngrediente(
                menu_id=menu.id,
                ingrediente_id=id_ing,
                cantidad=float(cant)
            ))

        safe_commit(session)
        return menu


# ============================================================
#                       ELIMINAR MENÚ
# ============================================================

def eliminar_menu(id_menu: int):
    from models import PedidoMenu
    with get_session() as session:
        menu = session.get(MenuORM, id_menu)
        if not menu:
            raise ValueError("Menú no encontrado.")

        en_pedido = session.scalars(
            select(PedidoMenu).where(PedidoMenu.menu_id == id_menu)
        ).first()
        if en_pedido:
            raise ValueError("No se puede eliminar un menú que tiene pedidos asociados.")

        session.delete(menu)
        safe_commit(session)
