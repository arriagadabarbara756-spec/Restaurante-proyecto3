# =============================================================================
# app.py  —  Evaluación 3
# Sistema de Gestión de Restaurante con:
# - SQLAlchemy ORM
# - CRUD completo de Clientes / Ingredientes / Menús / Pedidos
# - PDF (Boleta y Carta)
# - Gráficos estadísticos (matplotlib)
# - Interfaz CustomTkinter
# =============================================================================

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import webbrowser
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from crud.menu_crud import listar_menus_basico


# ----------------- CRUD (ORM) -----------------
from crud.cliente_crud import (
    listar_clientes, crear_cliente, actualizar_cliente, eliminar_cliente
)
from crud.ingrediente_crud import (
    listar_ingredientes, crear_ingrediente, actualizar_ingrediente,
    eliminar_ingrediente, cargar_desde_csv
)
from crud.menu_crud import (
    listar_menus, crear_menu, actualizar_menu, eliminar_menu, obtener_menu
)
from crud.pedido_crud import (
    crear_pedido, eliminar_pedido, listar_pedidos, listar_pedidos_por_cliente
)

# ----------------- PDF -----------------
from database import get_session
from pdf.boleta import Boleta
from pdf.carta import generar_menu_pdf

# ----------------- Gráficos -----------------
from graficos import (
    grafico_ventas_por_fecha,
    grafico_menus_mas_vendidos,
    grafico_uso_ingredientes
)

# ----------------- Configuración de colores -----------------
PRIMARY_COLOR = "#B31312"     # rojo
SECONDARY_COLOR = "#FFD93D"   # amarillo
BG_DARK = "#1E1E1E"
TEXT_LIGHT = "#FFFFFF"

# =============================================================================
#                               APLICACIÓN PRINCIPAL
# =============================================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ================================
        # CONFIGURACIÓN GENERAL DE VENTANA
        # ================================
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("🍔 Sistema Restaurante — EV3 (SQLAlchemy)")
        self.geometry("1200x750")
        self.minsize(1200, 750)
        self.maxsize(1200, 750)
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)

        # Mantener referencias de imágenes
        self._image_refs = {}

        # ================================
        # CUADERNO PRINCIPAL DE PESTAÑAS
        # ================================
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Crear todas las pestañas
        self._crear_pestana_ingredientes()
        self._crear_pestana_menus()
        self._crear_pestana_clientes()
        self._crear_pestana_compra()
        self._crear_pestana_pedidos()
        self._crear_pestana_graficos()

    # ==============================================================
    # Cada una de estas funciones se expandirá en las siguientes partes:
    # ==============================================================
    # ============================================================
    #                   PESTAÑA: INGREDIENTES (CRUD + CSV)
    # ============================================================
    def _crear_pestana_ingredientes(self):
        frame = ctk.CTkFrame(self.notebook, fg_color=BG_DARK)
        self.notebook.add(frame, text="🧂 Ingredientes")


        # ------------------ NUEVO LAYOUT: 2 COLUMNAS ------------------
        main_content = ctk.CTkFrame(frame, fg_color=BG_DARK)
        main_content.pack(fill="both", expand=True, padx=20, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=2)
        main_content.grid_rowconfigure(0, weight=1)

        # IZQUIERDA: Formulario y botones
        left = ctk.CTkFrame(main_content, fg_color="#232323", corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=0)

        ctk.CTkLabel(left, text="Gestión de Ingredientes", font=("Segoe UI Black", 22), text_color=SECONDARY_COLOR).pack(pady=(10, 20))

        form = ctk.CTkFrame(left, fg_color="#252525", corner_radius=12)
        form.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(form, text="Nombre:", text_color="white").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.ing_nombre = ctk.CTkEntry(form, width=160)
        self.ing_nombre.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(form, text="Unidad:", text_color="white").grid(row=1, column=0, padx=5, pady=8, sticky="e")
        self.ing_unidad = ctk.CTkEntry(form, width=120)
        self.ing_unidad.grid(row=1, column=1, padx=5, pady=8)

        ctk.CTkLabel(form, text="Stock:", text_color="white").grid(row=2, column=0, padx=5, pady=8, sticky="e")
        self.ing_stock = ctk.CTkEntry(form, width=120)
        self.ing_stock.grid(row=2, column=1, padx=5, pady=8)

        btn_frame = ctk.CTkFrame(left, fg_color=BG_DARK)
        btn_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(
            btn_frame, text="Agregar", fg_color=PRIMARY_COLOR,
            hover_color="#991111", command=self._agregar_ingrediente
        ).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(
            btn_frame, text="Actualizar", fg_color=SECONDARY_COLOR,
            hover_color="#FFC93C", text_color="black",
            command=self._actualizar_ingrediente
        ).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(
            btn_frame, text="Eliminar", fg_color="#7A0000",
            hover_color="#5A0000", command=self._eliminar_ingrediente
        ).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(
            left, text="Cargar CSV de Ingredientes", fg_color="#007ACC",
            hover_color="#005A9E", command=self._cargar_csv_ingredientes
        ).pack(pady=20, padx=10, fill="x")

        # DERECHA: Tabla
        right = ctk.CTkFrame(main_content, fg_color="#2C2C2C", corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        ctk.CTkLabel(right, text="Lista de Ingredientes", font=("Segoe UI", 18), text_color=SECONDARY_COLOR).pack(pady=(10, 0))
        cols = ("ID", "Nombre", "Unidad", "Stock")
        self.tree_ing = ttk.Treeview(right, columns=cols, show="headings", height=22)
        for col in cols:
            self.tree_ing.heading(col, text=col)
            self.tree_ing.column(col, anchor="center", width=120)
        self.tree_ing.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_ing.bind("<<TreeviewSelect>>", self._on_ingrediente_select)

    # ============================================================
    #               FUNCIONES CRUD DE INGREDIENTES
    # ============================================================

    def _refresh_ingredientes(self):
        """Recarga los ingredientes desde la BD y actualiza el Treeview."""
        for item in self.tree_ing.get_children():
            self.tree_ing.delete(item)

        for ing in listar_ingredientes():
            self.tree_ing.insert("", tk.END, values=(ing.id, ing.nombre, ing.unidad, ing.stock))

    def _on_ingrediente_select(self, event):
        sel = self.tree_ing.selection()
        if not sel:
            return

        ing_id, nombre, unidad, stock = self.tree_ing.item(sel[0], "values")

        # Rellenar formulario
        self.ing_nombre.delete(0, tk.END)
        self.ing_unidad.delete(0, tk.END)
        self.ing_stock.delete(0, tk.END)

        self.ing_nombre.insert(0, nombre)
        self.ing_unidad.insert(0, unidad)
        self.ing_stock.insert(0, str(stock))


    def _agregar_ingrediente(self):
        nombre = self.ing_nombre.get().strip()
        unidad = self.ing_unidad.get().strip()
        stock = self.ing_stock.get().strip()

        try:
            crear_ingrediente(nombre, unidad, float(stock))
            messagebox.showinfo("OK", "Ingrediente agregado correctamente.")
            self._refresh_ingredientes()
            # Actualizar ingredientes en pestaña Menú si existe el método y frame
            if hasattr(self, '_cargar_ingredientes_para_menu'):
                self._cargar_ingredientes_para_menu()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el ingrediente:\n{str(e)}")

    def _actualizar_ingrediente(self):
        sel = self.tree_ing.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un ingrediente.")

        ing_id = int(self.tree_ing.item(sel[0], "values")[0])

        nombre = self.ing_nombre.get().strip()
        unidad = self.ing_unidad.get().strip()
        stock = self.ing_stock.get().strip()

        try:
            actualizar_ingrediente(ing_id, nombre, unidad, float(stock))
            messagebox.showinfo("OK", "Ingrediente actualizado.")
            self._refresh_ingredientes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar:\n{str(e)}")

    def _eliminar_ingrediente(self):
        sel = self.tree_ing.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un ingrediente.")

        ing_id = int(self.tree_ing.item(sel[0], "values")[0])

        try:
            eliminar_ingrediente(ing_id)
            messagebox.showinfo("OK", "Ingrediente eliminado.")
            self._refresh_ingredientes()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar:\n{str(e)}")

    def _cargar_csv_ingredientes(self):
        """Carga CSV usando map/filter/reduce → BD."""
        ruta = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="Selecciona el archivo CSV de ingredientes"
        )
        if not ruta:
            return

        try:
            cargar_desde_csv(ruta)
            messagebox.showinfo("OK", "CSV cargado correctamente.")
            self._refresh_ingredientes()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al cargar CSV:\n{str(e)}")

        pass

    # ============================================================
    #                  PESTAÑA: MENÚS (CRUD + ORM)
    # ============================================================
    def _crear_pestana_menus(self):
        frame = ctk.CTkFrame(self.notebook, fg_color=BG_DARK)
        self.notebook.add(frame, text="🍽 Menús")


        # ------------------ NUEVO LAYOUT: 2 COLUMNAS ------------------
        main_content = ctk.CTkFrame(frame, fg_color=BG_DARK)
        main_content.pack(fill="both", expand=True, padx=20, pady=10)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_columnconfigure(1, weight=2)
        main_content.grid_rowconfigure(0, weight=1)

        # IZQUIERDA: Formulario, botones y selección de ingredientes
        left = ctk.CTkFrame(main_content, fg_color="#232323", corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=0)

        ctk.CTkLabel(left, text="Gestión de Menús", font=("Segoe UI Black", 22), text_color=SECONDARY_COLOR).pack(pady=(10, 20))

        form = ctk.CTkFrame(left, fg_color="#252525", corner_radius=12)
        form.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(form, text="Nombre:", text_color="white").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.menu_nombre = ctk.CTkEntry(form, width=160)
        self.menu_nombre.grid(row=0, column=1, padx=5, pady=8)

        ctk.CTkLabel(form, text="Precio:", text_color="white").grid(row=1, column=0, padx=5, pady=8, sticky="e")
        self.menu_precio = ctk.CTkEntry(form, width=120)
        self.menu_precio.grid(row=1, column=1, padx=5, pady=8)

        ctk.CTkLabel(form, text="Descripción:", text_color="white").grid(row=2, column=0, padx=5, pady=8, sticky="e")
        self.menu_descripcion = ctk.CTkEntry(form, width=220)
        self.menu_descripcion.grid(row=2, column=1, padx=5, pady=8)

        btn_frame = ctk.CTkFrame(left, fg_color=BG_DARK)
        btn_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(
            btn_frame, text="Generar Menús",
            fg_color="#007ACC", hover_color="#005A9E",
            command=self._refresh_menus
        ).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(
            btn_frame, text="Crear Menú", fg_color=PRIMARY_COLOR,
            hover_color="#991111",
            command=self._crear_menu
        ).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(
            btn_frame, text="Actualizar Menú", fg_color=SECONDARY_COLOR,
            text_color="black", hover_color="#FFC93C",
            command=self._actualizar_menu
        ).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(
            btn_frame, text="Eliminar Menú", fg_color="#7A0000",
            hover_color="#5A0000",
            command=self._eliminar_menu
        ).pack(side="left", padx=5, expand=True, fill="x")

        # Ingredientes para el menú
        ing_box_frame = ctk.CTkFrame(left, fg_color="#333333", corner_radius=12)
        ing_box_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        ctk.CTkLabel(
            ing_box_frame, text="Ingredientes del Menú",
            text_color=TEXT_LIGHT, font=("Segoe UI Semibold", 15)
        ).pack(pady=8)
        # Scrollable ingredientes
        ing_scroll_canvas = tk.Canvas(ing_box_frame, bg="#222222", highlightthickness=0, bd=0, relief="flat")
        ing_scroll_canvas.pack(fill="both", expand=True, padx=6, pady=(6, 12))
        scrollbar = ctk.CTkScrollbar(ing_box_frame, orientation="vertical", command=ing_scroll_canvas.yview)
        scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.ing_sel_frame = ctk.CTkFrame(ing_scroll_canvas, fg_color="#222222", corner_radius=12)
        def _resize_ingredientes(event):
            canvas_width = event.width
            ing_scroll_canvas.itemconfig("ingredientes_frame", width=canvas_width)
        self.ing_sel_frame.bind(
            "<Configure>",
            lambda e: ing_scroll_canvas.configure(scrollregion=ing_scroll_canvas.bbox("all"))
        )
        window_id = ing_scroll_canvas.create_window((0, 0), window=self.ing_sel_frame, anchor="nw", tags="ingredientes_frame")
        ing_scroll_canvas.bind("<Configure>", _resize_ingredientes)
        ing_scroll_canvas.configure(yscrollcommand=scrollbar.set)
        self.menu_ingredientes_list = []
        self._cargar_ingredientes_para_menu()

        # DERECHA: Tabla
        right = ctk.CTkFrame(main_content, fg_color="#2C2C2C", corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        ctk.CTkLabel(right, text="Lista de Menús", font=("Segoe UI", 18), text_color=SECONDARY_COLOR).pack(pady=(10, 0))
        cols = ("ID", "Nombre", "Precio", "Descripción")
        self.tree_menus = ttk.Treeview(right, columns=cols, show="headings", height=22)
        self.tree_menus.heading("ID", text="ID")
        self.tree_menus.column("ID", width=60, anchor="center")
        self.tree_menus.heading("Nombre", text="Nombre")
        self.tree_menus.column("Nombre", width=180, anchor="center")
        self.tree_menus.heading("Precio", text="Precio")
        self.tree_menus.column("Precio", width=120, anchor="center")
        self.tree_menus.heading("Descripción", text="Descripción")
        self.tree_menus.column("Descripción", width=300, anchor="w")
        self.tree_menus.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_menus.bind("<<TreeviewSelect>>", self._on_menu_select)


    # ============================================================
    #                  FUNCIONES DE MENÚS (CRUD)
    # ============================================================

    def _refresh_menus(self):
        from crud.menu_crud import crear_menus_predeterminados, listar_menus
        import tkinter as tk
        crear_menus_predeterminados()
        for item in self.tree_menus.get_children():
            self.tree_menus.delete(item)
        for m in listar_menus():
            self.tree_menus.insert(
                "",
                tk.END,
                values=(m.id, m.nombre, f"${m.precio:,.0f}", m.descripcion or "")
            )


    def _cargar_ingredientes_para_menu(self):
        """Crea una lista editable de ingredientes + cantidades."""
        # Limpiar frame previo
        for w in self.ing_sel_frame.winfo_children():
            w.destroy()

        self.menu_ingredientes_list = []

        ingredientes = listar_ingredientes()

        for ing in ingredientes:
            fila = ctk.CTkFrame(self.ing_sel_frame, fg_color="#444444", corner_radius=10)
            fila.pack(fill="x", pady=4, padx=6)

            # Check para seleccionar ingrediente
            sel_var = tk.IntVar()
            chk = ctk.CTkCheckBox(fila, text=ing.nombre, variable=sel_var)
            chk.pack(side="left", padx=10)

            # Cantidad requerida
            qty = ctk.CTkEntry(fila, width=80, placeholder_text="Cant.")
            qty.pack(side="right", padx=10)

            self.menu_ingredientes_list.append((ing.id, sel_var, qty))

    def _crear_menu(self):
        nombre = self.menu_nombre.get().strip()
        precio = self.menu_precio.get().strip()
        desc = self.menu_descripcion.get().strip()

        if not nombre or not precio:
            return messagebox.showerror("Error", "Nombre y precio son obligatorios.")

        ingredientes_dict = {}
        for ing_id, var, qty in self.menu_ingredientes_list:
            if var.get() == 1:
                try:
                    cant = float(qty.get())
                    if cant < 0:
                        return messagebox.showerror("Cantidad inválida", "No puedes ingresar cantidades negativas para los ingredientes.")
                    if cant > 0:
                        ingredientes_dict[ing_id] = cant
                except:
                    return messagebox.showerror("Cantidad inválida", "La cantidad debe ser un número válido.")

        if not ingredientes_dict:
            return messagebox.showerror("Error", "Debes seleccionar al menos un ingrediente.")

        try:
            from crud.ingrediente_crud import listar_ingredientes
            crear_menu(nombre, desc, float(precio), ingredientes_dict)
            cant_ingredientes = len(ingredientes_dict)
            # Obtener nombres de ingredientes
            ingredientes_bd = {ing.id: ing.nombre for ing in listar_ingredientes()}
            def fmt_cantidad(val):
                if isinstance(val, float) and val.is_integer():
                    return str(int(val))
                return str(val)
            nombres = [f"{ingredientes_bd[iid]} (cantidad: {fmt_cantidad(ingredientes_dict[iid])})" for iid in ingredientes_dict.keys() if iid in ingredientes_bd]
            nombres_str = "\n".join(nombres)
            messagebox.showinfo("OK", f"Menú creado correctamente. Ingredientes usados: {cant_ingredientes}\n{nombres_str}")
            if hasattr(self, '_refrescar_menus_compra'):
                self._refrescar_menus_compra()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_menu_select(self, event):
        sel = self.tree_menus.selection()
        if not sel:
            return

        menu_id, nombre, precio, descripcion = self.tree_menus.item(sel[0], "values")

        self.menu_nombre.delete(0, tk.END)
        self.menu_precio.delete(0, tk.END)
        self.menu_descripcion.delete(0, tk.END)

        self.menu_nombre.insert(0, nombre)
        self.menu_precio.insert(0, precio.replace("$", "").replace(".", ""))
        self.menu_descripcion.insert(0, descripcion)

    def _actualizar_menu(self):
        sel = self.tree_menus.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un menú.")

        menu_id = int(self.tree_menus.item(sel[0], "values")[0])

        nombre = self.menu_nombre.get().strip()
        precio = self.menu_precio.get().strip()
        desc = self.menu_descripcion.get().strip()

        ingredientes_dict = {}
        for ing_id, var, qty in self.menu_ingredientes_list:
            if var.get() == 1:
                try:
                    cant = float(qty.get())
                    if cant > 0:
                        ingredientes_dict[ing_id] = cant
                except:
                    pass

        try:
            actualizar_menu(menu_id, nombre, desc, float(precio), ingredientes_dict)
            messagebox.showinfo("OK", "Menú actualizado.")
            if hasattr(self, '_refrescar_menus_compra'):
                self._refrescar_menus_compra()
        except Exception as e:
            messagebox.showerror("Error", str(e))



    def _eliminar_menu(self):
        sel = self.tree_menus.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un menú.")

        menu_id = int(self.tree_menus.item(sel[0], "values")[0])

        try:
            eliminar_menu(menu_id)
            messagebox.showinfo("OK", "Menú eliminado.")
            self._refresh_menus()
            self._cargar_ingredientes_para_menu()   # <-- IMPORTANTE
            if hasattr(self, '_refrescar_menus_compra'):
                self._refrescar_menus_compra()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ============================================================
    #                  PESTAÑA: CLIENTES (CRUD + ORM)
    # ============================================================
    def _crear_pestana_clientes(self):
        frame = ctk.CTkFrame(self.notebook, fg_color=BG_DARK)
        self.notebook.add(frame, text="👤 Clientes")

        title = ctk.CTkLabel(
            frame, text="Gestión de Clientes",
            font=("Segoe UI Black", 24),
            text_color=SECONDARY_COLOR
        )
        title.pack(pady=15)

        # ------------------ FORMULARIO Y BOTONES ARRIBA ------------------

        form_btns_frame = ctk.CTkFrame(frame, fg_color="transparent")
        form_btns_frame.pack(fill="x", pady=(10, 0))

        # Centrado del formulario
        form = ctk.CTkFrame(form_btns_frame, fg_color="#252525", corner_radius=12)
        form.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        form.pack(pady=0)

        ctk.CTkLabel(form, text="Nombre:", text_color="white").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.cli_nombre = ctk.CTkEntry(form, width=220)
        self.cli_nombre.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(form, text="Correo:", text_color="white").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.cli_correo = ctk.CTkEntry(form, width=220)
        self.cli_correo.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(form, text="Teléfono:", text_color="white").grid(row=0, column=4, padx=10, pady=10, sticky="e")
        self.cli_telefono = ctk.CTkEntry(form, width=160)
        self.cli_telefono.grid(row=0, column=5, padx=10, pady=10, sticky="w")

        # Centrado de botones
        btn_frame = ctk.CTkFrame(form_btns_frame, fg_color=BG_DARK)
        btn_frame.pack(pady=10)

        btn_frame.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkButton(
            btn_frame, text="Agregar Cliente", fg_color=PRIMARY_COLOR,
            hover_color="#991111", command=self._agregar_cliente,
            width=180
        ).grid(row=0, column=0, padx=20, pady=0)
        ctk.CTkButton(
            btn_frame, text="Actualizar Cliente", fg_color=SECONDARY_COLOR,
            hover_color="#FFC93C", text_color="black",
            command=self._actualizar_cliente,
            width=180
        ).grid(row=0, column=1, padx=20, pady=0)
        ctk.CTkButton(
            btn_frame, text="Eliminar Cliente", fg_color="#7A0000",
            hover_color="#5A0000", command=self._eliminar_cliente,
            width=180
        ).grid(row=0, column=2, padx=20, pady=0)

        # ------------------ TREEVIEW DE CLIENTES ------------------
        tree_frame = ctk.CTkFrame(frame, fg_color="#2C2C2C", corner_radius=12)
        tree_frame.pack(pady=10)

        cols = ("ID", "Nombre", "Correo", "Teléfono")
        self.tree_cli = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)

        for col in cols:
            self.tree_cli.heading(col, text=col)
            self.tree_cli.column(col, anchor="center", width=200)

        self.tree_cli.pack(padx=20, pady=15, ipadx=150, ipady=150)
        self.tree_cli.bind("<<TreeviewSelect>>", self._on_cliente_select)

        self._refresh_clientes()

    # ============================================================
    #                  FUNCIONES CRUD DE CLIENTES
    # ============================================================
    def _refresh_clientes(self):
        """Recarga los clientes desde la BD."""
        for item in self.tree_cli.get_children():
            self.tree_cli.delete(item)

        for c in listar_clientes():
            self.tree_cli.insert("", tk.END, values=(c.id, c.nombre, c.correo, c.telefono))

    def _on_cliente_select(self, event):
        sel = self.tree_cli.selection()
        if not sel:
            return

        cli_id, nombre, correo, telefono = self.tree_cli.item(sel[0], "values")

        # Rellenar formulario
        self.cli_nombre.delete(0, tk.END)
        self.cli_correo.delete(0, tk.END)
        self.cli_telefono.delete(0, tk.END)

        self.cli_nombre.insert(0, nombre)
        self.cli_correo.insert(0, correo)
        self.cli_telefono.insert(0, telefono if telefono else "")


    def _agregar_cliente(self):
        import re
        nombre = self.cli_nombre.get().strip()
        correo = self.cli_correo.get().strip()
        telefono = self.cli_telefono.get().strip()

        # Validar nombre: solo letras y espacios, no vacío
        if not nombre or not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombre):
            return messagebox.showerror("Error", "El nombre solo debe contener letras y espacios, y no puede estar vacío.")

        # Validar correo: formato email estricto
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', correo):
            return messagebox.showerror("Error", "Ingrese un correo electrónico válido.")

        # Validar teléfono: solo números, largo 8 o 9 dígitos (chile), puede empezar con 9
        tel_limpio = re.sub(r'\D', '', telefono)
        if not tel_limpio or not re.match(r'^(9\d{8}|[2-9]\d{7})$', tel_limpio):
            return messagebox.showerror("Error", "Ingrese un teléfono válido (8 o 9 dígitos, solo números). Ej: 912345678")

        try:
            crear_cliente(nombre, correo, tel_limpio)
            messagebox.showinfo("OK", "Cliente agregado correctamente.")
            self._refresh_clientes()
            self._recargar_clientes_combo()
            self._recargar_pedidos_clientes_combo()
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def _actualizar_cliente(self):
        import re
        sel = self.tree_cli.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un cliente.")

        cli_id = int(self.tree_cli.item(sel[0], "values")[0])

        nombre = self.cli_nombre.get().strip()
        correo = self.cli_correo.get().strip()
        telefono = self.cli_telefono.get().strip()

        # Validar nombre: solo letras y espacios, no vacío
        if not nombre or not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombre):
            return messagebox.showerror("Error", "El nombre solo debe contener letras y espacios, y no puede estar vacío.")

        # Validar correo: formato email estricto
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', correo):
            return messagebox.showerror("Error", "Ingrese un correo electrónico válido.")

        # Validar teléfono: solo números, largo 8 o 9 dígitos (chile), puede empezar con 9
        tel_limpio = re.sub(r'\D', '', telefono)
        if not tel_limpio or not re.match(r'^(9\d{8}|[2-9]\d{7})$', tel_limpio):
            return messagebox.showerror("Error", "Ingrese un teléfono válido (8 o 9 dígitos, solo números). Ej: 912345678")

        try:
            actualizar_cliente(cli_id, nombre, correo, tel_limpio)
            messagebox.showinfo("OK", "Cliente actualizado.")
            self._refresh_clientes()
            self._recargar_clientes_combo()
            self._recargar_pedidos_clientes_combo()
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def _eliminar_cliente(self):
        sel = self.tree_cli.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un cliente.")

        cli_id = int(self.tree_cli.item(sel[0], "values")[0])

        try:
            eliminar_cliente(cli_id)
            messagebox.showinfo("OK", "Cliente eliminado.")
            self._refresh_clientes()
            self._recargar_clientes_combo()
            self._recargar_pedidos_clientes_combo()
        except Exception as e:
            messagebox.showerror("Error", str(e))

        pass

    # ============================================================
    #             PESTAÑA: COMPRA (PEDIDO + BOLETA)
    # ============================================================

    def _crear_pestana_compra(self):
        frame = ctk.CTkFrame(self.notebook, fg_color=BG_DARK)
        self.notebook.add(frame, text="🛒 Compra")

        title = ctk.CTkLabel(
            frame, text="Panel de Compra",
            font=("Segoe UI Black", 24),
            text_color=SECONDARY_COLOR
        )
        title.pack(pady=15)

        # Recuadro principal vertical
        main_box = ctk.CTkFrame(frame, fg_color="#232323", corner_radius=12)
        main_box.pack(fill="both", expand=True, padx=40, pady=20)

        # Arriba: Cliente, fecha y descripción
        top_row = ctk.CTkFrame(main_box, fg_color="#252525", corner_radius=12)
        top_row.pack(fill="x", padx=30, pady=(20, 10))
        top_row.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        ctk.CTkLabel(top_row, text="Cliente:", text_color="white").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.cmb_cliente = ctk.CTkComboBox(top_row, width=220, state="readonly", fg_color="#222", border_color=SECONDARY_COLOR, button_color=PRIMARY_COLOR, dropdown_fg_color="#222", dropdown_text_color=TEXT_LIGHT, text_color=TEXT_LIGHT)
        self.cmb_cliente.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self._recargar_clientes_combo()
        ctk.CTkLabel(top_row, text="Fecha:", text_color="white").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.entry_fecha = ctk.CTkEntry(top_row, width=120)
        self.entry_fecha.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        from datetime import datetime
        self.entry_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))
        ctk.CTkLabel(top_row, text="Descripción del pedido:", text_color="white").grid(row=0, column=4, padx=10, pady=10, sticky="e")
        self.entry_descripcion_pedido = ctk.CTkEntry(top_row, width=220)
        self.entry_descripcion_pedido.grid(row=0, column=5, padx=10, pady=10, sticky="w")

        # Centro: Menús disponibles
        menus_box = ctk.CTkFrame(main_box, fg_color="#2C2C2C", corner_radius=12)
        menus_box.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        ctk.CTkLabel(menus_box, text="Menús Disponibles", font=("Segoe UI", 18), text_color=SECONDARY_COLOR).pack(pady=(10, 0))
        cols = ("ID", "Nombre", "Precio")
        self.tree_compra_menus = ttk.Treeview(menus_box, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree_compra_menus.heading(col, text=col)
            self.tree_compra_menus.column(col, anchor="center", width=180)
        self.tree_compra_menus.pack(fill="x", padx=10, pady=10)
        self.tree_compra_menus.bind("<Double-1>", lambda e: self._agregar_menu_al_carrito())
        self._refrescar_menus_compra()
        ctk.CTkButton(
            menus_box, text="Agregar al Carrito", fg_color=PRIMARY_COLOR,
            hover_color="#991111", command=self._agregar_menu_al_carrito
        ).pack(pady=5, padx=10, fill="x")

        # Abajo: Carrito y acciones
        cart_box = ctk.CTkFrame(main_box, fg_color="#1F1F1F", corner_radius=12)
        cart_box.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkLabel(cart_box, text="Carrito / Pedido Actual", text_color=TEXT_LIGHT, font=("Segoe UI Semibold", 16)).pack(pady=10)
        cols2 = ("ID", "Nombre", "Cantidad", "Precio Unit.", "Subtotal")
        self.tree_carrito = ttk.Treeview(cart_box, columns=cols2, show="headings", height=6)
        for c in cols2:
            self.tree_carrito.heading(c, text=c)
            self.tree_carrito.column(c, anchor="center", width=120)
        self.tree_carrito.pack(fill="x", padx=10, pady=5)

        # Botones alineados a la derecha
        btns_carrito_frame = ctk.CTkFrame(cart_box, fg_color="transparent")
        btns_carrito_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(
            btns_carrito_frame, text="Eliminar Seleccionado", fg_color="#7A0000",
            hover_color="#5A0000", command=self._remover_del_carrito,
            width=160
        ).pack(side="right", padx=(10, 0))
        ctk.CTkButton(
            btns_carrito_frame, text="Generar Pedido y Boleta",
            fg_color=SECONDARY_COLOR, text_color="black",
            hover_color="#FFC93C",
            command=self._generar_pedido_y_boleta,
            width=200
        ).pack(side="right", padx=(0, 10))


    # ============================================================
    #                  FUNCIONES DE COMPRA
    # ============================================================

    def _recargar_clientes_combo(self):
        clientes = listar_clientes()
        values = [f"{c.id} - {c.nombre}" for c in clientes]
        self.cmb_cliente.configure(values=values)
        # Siempre seleccionar el primer cliente si existe, o limpiar si no hay
        if values:
            self.cmb_cliente.set(values[0])
        else:
            self.cmb_cliente.set("")




    def _refrescar_menus_compra(self):
        for i in self.tree_compra_menus.get_children():
            self.tree_compra_menus.delete(i)

        for m in listar_menus_basico():
            self.tree_compra_menus.insert("", tk.END,
                values=(m.id, m.nombre, f"${m.precio:,.0f}")
            )

    # ------------------ AGREGAR AL CARRITO ------------------
    def _agregar_menu_al_carrito(self):
        sel = self.tree_compra_menus.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un menú.")

        mid, nombre, precio = self.tree_compra_menus.item(sel[0], "values")
        mid = int(mid)

        # Conversión robusta de precio
        precio_float = float(precio.replace("$", "").replace(".", "").replace(",", ""))

        # ============================
        # VALIDAR STOCK DISPONIBLE
        # ============================
        
        from crud.menu_crud import obtener_menu
        menu = obtener_menu(mid)


        if not menu:
            return messagebox.showerror("Error", "Menú no encontrado.")

        # Calcular stock máximo posible según ingredientes
        max_unidades_posibles = float("inf")

        for mi in menu.ingredientes:
            ing = mi.ingrediente
            if ing.stock <= 0:
                return messagebox.showerror("Sin stock", f"No hay stock de {ing.nombre}")

            posibles = ing.stock // mi.cantidad
            if posibles < max_unidades_posibles:
                max_unidades_posibles = posibles

        if max_unidades_posibles < 1:
            return messagebox.showerror("Sin stock", f"No se puede agregar '{nombre}'. Stock insuficiente.")

        # ============================
        # CONTAR CUÁNTAS UNIDADES YA HAY EN CARRITO
        # ============================
        cantidad_actual = 0
        for row in self.tree_carrito.get_children():
            rid, _, cant, _, _ = self.tree_carrito.item(row, "values")
            if int(rid) == mid:
                cantidad_actual = int(cant)

        if cantidad_actual + 1 > max_unidades_posibles:
            return messagebox.showerror(
                "Límite alcanzado",
                f"No puedes agregar más unidades de '{nombre}'.\n"
                f"Máximo permitido: {max_unidades_posibles}"
            )

        # ============================
        # AGREGAR O INCREMENTAR EN CARRITO
        # ============================
        for row in self.tree_carrito.get_children():
            rid, _, cant, _, _ = self.tree_carrito.item(row, "values")
            if int(rid) == mid:
                nueva = int(cant) + 1
                subtotal = nueva * precio_float
                self.tree_carrito.item(row, values=(mid, nombre, nueva, precio, f"${subtotal:,.0f}"))
                return

        # Si es la primera vez que se agrega
        self.tree_carrito.insert("", tk.END,
            values=(mid, nombre, 1, precio, f"${precio_float:,.0f}")
        )


    # ------------------ ELIMINAR DEL CARRITO ------------------
    def _remover_del_carrito(self):
        sel = self.tree_carrito.selection()
        if not sel:
            return
        self.tree_carrito.delete(sel[0])

    # ============================================================
    #     CREAR PEDIDO EN BD + VALIDAR STOCK + GENERAR BOLETA
    # ============================================================

    def _generar_pedido_y_boleta(self):
        # ----- Validar cliente -----
        if not self.cmb_cliente.get():
            return messagebox.showerror("Error", "Debes seleccionar un cliente.")

        cli_id = int(self.cmb_cliente.get().split(" - ")[0])

        # ----- Validar carrito -----
        items = {}
        for row in self.tree_carrito.get_children():
            mid, _, cant, _, _ = self.tree_carrito.item(row, "values")
            items[int(mid)] = int(cant)

        if not items:
            return messagebox.showerror("Error", "El carrito está vacío.")

        # ----- Validar y obtener fecha -----
        fecha_str = self.entry_fecha.get().strip()
        import re
        from datetime import datetime
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", fecha_str):
            return messagebox.showerror("Error", "La fecha debe tener el formato DD/MM/AAAA y solo números.")
        try:
            fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
            # Mantener la hora actual
            now = datetime.now()
            fecha_dt = fecha_dt.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
        except Exception:
            return messagebox.showerror("Error", "Fecha inválida. Usa el formato DD/MM/AAAA.")

        # Restringir fechas futuras
        hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_sin_hora = fecha_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        if fecha_sin_hora > hoy:
            return messagebox.showerror("Error", "No puedes seleccionar una fecha futura. Solo hasta hoy (%s)." % hoy.strftime("%d/%m/%Y"))

        # ----- Crear pedido en BD -----
        try:
            from crud import pedido_crud
            descripcion = self.entry_descripcion_pedido.get().strip()
            pedido = pedido_crud.crear_pedido(cli_id, items, descripcion, fecha_dt)
        except Exception as e:
            return messagebox.showerror("Error", str(e))

        # ----- BOLETA PDF -----
        detalle_pdf = []
        total = 0

        for row in self.tree_carrito.get_children():
            mid, nombre, cant, precio, sub = self.tree_carrito.item(row, "values")
            # Eliminar $ y separadores de miles (coma o punto)
            precio_val = float(precio.replace("$", "").replace(",", "").replace(".", ""))
            subtotal = precio_val * int(cant)
            detalle_pdf.append((nombre, int(cant), precio_val, subtotal))
            total += subtotal

        iva = total * 0.19
        total_final = total + iva

        # Solicitar ubicación para guardar la boleta
        from tkinter import filedialog
        default_filename = f"boleta_{pedido.id}.pdf"
        salida = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_filename,
            title="Guardar Boleta PDF"
        )
        if not salida:
            messagebox.showwarning("Cancelado", "No se guardó la boleta.")
            return
        Boleta(detalle_pdf, fecha=fecha_dt).generar_pdf(salida)

        messagebox.showinfo("OK", f"Pedido #{pedido.id} creado y boleta generada.")

        # Abrir boleta PDF
        try:
            webbrowser.open(salida)
        except:
            pass

        # Limpiar carrito
        for row in self.tree_carrito.get_children():
            self.tree_carrito.delete(row)

        pass

    # ============================================================
    #                     PESTAÑA: PEDIDOS
    # ============================================================
    def _crear_pestana_pedidos(self):
        frame = ctk.CTkFrame(self.notebook, fg_color=BG_DARK)
        self.notebook.add(frame, text="📦 Pedidos")

        title = ctk.CTkLabel(
            frame, text="Gestión de Pedidos",
            font=("Segoe UI Black", 24), text_color=SECONDARY_COLOR
        )
        title.pack(pady=15)

        # ------------------ FILTRO POR CLIENTE ------------------
        filter_frame = ctk.CTkFrame(frame, fg_color="#252525", corner_radius=12)
        filter_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(filter_frame, text="Filtrar por Cliente:", text_color="white").pack(side="left", padx=10)

        self.cmb_ped_cli = ctk.CTkComboBox(filter_frame, width=320, state="readonly", fg_color="#222", border_color=SECONDARY_COLOR, button_color=PRIMARY_COLOR, dropdown_fg_color="#222", dropdown_text_color=TEXT_LIGHT, text_color=TEXT_LIGHT)
        self.cmb_ped_cli.pack(side="left", padx=10)

        self._recargar_pedidos_clientes_combo()

        ctk.CTkButton(
            filter_frame, text="Filtrar", fg_color=PRIMARY_COLOR,
            command=self._filtrar_pedidos
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            filter_frame, text="Mostrar Todos", fg_color=SECONDARY_COLOR,
            text_color="black", command=self._listar_todos_pedidos
        ).pack(side="left", padx=10)

        # ------------------ TREEVIEW ------------------
        tree_frame = ctk.CTkFrame(frame, fg_color="#2C2C2C", corner_radius=12)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)


        cols = ("ID", "Cliente", "Fecha", "Total", "Descripción", "Cantidad Menús")
        self.tree_pedidos = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)

        for col in cols:
            self.tree_pedidos.heading(col, text=col)
            self.tree_pedidos.column(col, anchor="center", width=180)

        self.tree_pedidos.pack(fill="both", expand=True, padx=10, pady=10)

        self._listar_todos_pedidos()

        # ------------------ BOTÓN ELIMINAR ------------------
        ctk.CTkButton(
            frame, text="Eliminar Pedido", fg_color="#7A0000",
            command=self._eliminar_pedido
        ).pack(pady=15)


    # ============================================================
    #                  FUNCIONES DE PEDIDOS
    # ============================================================

    def _recargar_pedidos_clientes_combo(self):
        clientes = listar_clientes()
        values = [f"{c.id} - {c.nombre}" for c in clientes]
        self.cmb_ped_cli.configure(values=values)
        # Siempre seleccionar el primer cliente si existe, o limpiar si no hay
        if values:
            self.cmb_ped_cli.set(values[0])
        else:
            self.cmb_ped_cli.set("")

    def _listar_todos_pedidos(self):
        for i in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(i)

        for p in listar_pedidos():
            cantidad_menus = sum(item.cantidad for item in p.items)
            self.tree_pedidos.insert("", tk.END, values=(
                p.id,
                p.cliente.nombre,
                p.fecha.strftime("%d/%m/%Y %H:%M"),
                f"${p.total:,.0f}",
                p.descripcion if p.descripcion else "",
                cantidad_menus
            ))

    def _filtrar_pedidos(self):
        if not self.cmb_ped_cli.get():
            return messagebox.showwarning("Atención", "Selecciona un cliente.")

        cli_id = int(self.cmb_ped_cli.get().split(" - ")[0])

        for i in self.tree_pedidos.get_children():
            self.tree_pedidos.delete(i)

        for p in listar_pedidos_por_cliente(cli_id):
            cantidad_menus = sum(item.cantidad for item in p.items)
            self.tree_pedidos.insert("", tk.END, values=(
                p.id,
                p.cliente.nombre,
                p.fecha.strftime("%d/%m/%Y %H:%M"),
                f"${p.total:,.0f}",
                p.descripcion if p.descripcion else "",
                cantidad_menus
            ))

    def _eliminar_pedido(self):
        sel = self.tree_pedidos.selection()
        if not sel:
            return messagebox.showwarning("Atención", "Selecciona un pedido.")

        pid = int(self.tree_pedidos.item(sel[0], "values")[0])

        try:
            eliminar_pedido(pid)
            messagebox.showinfo("OK", "Pedido eliminado.")
            self._listar_todos_pedidos()
        except Exception as e:
            messagebox.showerror("Error", str(e))



    # ============================================================
    #                     PESTAÑA: GRÁFICOS
    # ============================================================
    def _crear_pestana_graficos(self):
        frame = ctk.CTkFrame(self.notebook, fg_color=BG_DARK)
        self.notebook.add(frame, text="📊 Gráficos")

        title = ctk.CTkLabel(
            frame, text="Estadísticas del Sistema",
            font=("Segoe UI Black", 24), text_color=SECONDARY_COLOR
        )
        title.pack(pady=15)

        # ------------------ SELECCIÓN DE GRÁFICO ------------------
        options = ["Ventas por Fecha", "Menús más Vendidos", "Uso de Ingredientes"]

        self.cmb_grafico = ctk.CTkComboBox(frame, values=options, state="readonly", width=320, fg_color="#222", border_color=SECONDARY_COLOR, button_color=PRIMARY_COLOR, dropdown_fg_color="#222", dropdown_text_color=TEXT_LIGHT, text_color=TEXT_LIGHT)
        self.cmb_grafico.set("Ventas por Fecha")
        self.cmb_grafico.pack(pady=10)

        ctk.CTkButton(
            frame, text="Generar Gráfico",
            fg_color=PRIMARY_COLOR, hover_color="#991111",
            command=self._generar_grafico
        ).pack(pady=10)

        # ------------------ ÁREA DEL GRÁFICO ------------------
        self.graph_area = ctk.CTkFrame(frame, fg_color="#2C2C2C", corner_radius=12)
        self.graph_area.pack(fill="both", expand=True, padx=20, pady=10)


    # ============================================================
    #                  FUNCIONES DE GRÁFICOS
    # ============================================================
    def _generar_grafico(self):
        for w in self.graph_area.winfo_children():
            w.destroy()

        op = self.cmb_grafico.get()

        try:
            if op == "Ventas por Fecha":
                fig = grafico_ventas_por_fecha()
            elif op == "Menús más Vendidos":
                fig = grafico_menus_mas_vendidos()
            else:
                fig = grafico_uso_ingredientes()
        except Exception as e:
            return messagebox.showerror("Error", str(e))

        canvas = FigureCanvasTkAgg(fig, master=self.graph_area)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill="both", expand=True, padx=10, pady=10)

        pass

# ==================== INICIAR LA APP ====================
if __name__ == "__main__":
    app = App()
    app.mainloop()
