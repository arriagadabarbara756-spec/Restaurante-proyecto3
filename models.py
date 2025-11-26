# models.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False, unique=True)
    telefono = Column(String(50), nullable=True)

    pedidos = relationship("Pedido", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente {self.id} {self.nombre} ({self.correo})>"


class IngredienteORM(Base):
    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    unidad = Column(String(50), nullable=False)
    stock = Column(Float, nullable=False, default=0.0)  # stock >= 0

    def __repr__(self):
        return f"<Ingrediente {self.nombre} {self.stock} {self.unidad}>"


class MenuORM(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False, default=0.0)

    ingredientes = relationship("MenuIngrediente", back_populates="menu", cascade="all, delete-orphan")
    pedidos = relationship("PedidoMenu", back_populates="menu")

    def __repr__(self):
        return f"<Menu {self.nombre} ${self.precio}>"


class MenuIngrediente(Base):
    __tablename__ = "menu_ingredientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), nullable=False)
    cantidad = Column(Float, nullable=False)  # cantidad requerida para 1 menú

    menu = relationship("MenuORM", back_populates="ingredientes")
    ingrediente = relationship("IngredienteORM")

    __table_args__ = (
        UniqueConstraint("menu_id", "ingrediente_id", name="uq_menu_ingrediente"),
    )


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.now, nullable=False)
    total = Column(Float, nullable=False, default=0.0)
    descripcion = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="pedidos")
    items = relationship("PedidoMenu", back_populates="pedido", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pedido {self.id} cliente={self.cliente_id} total={self.total}>"


class PedidoMenu(Base):
    __tablename__ = "pedido_menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    pedido = relationship("Pedido", back_populates="items")
    menu = relationship("MenuORM", back_populates="pedidos")
