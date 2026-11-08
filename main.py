import os
import json
import urllib.request
from datetime import datetime
import flet as ft

DB_FILE = "datos_negocio_movil.json"

CATALOGO_INICIAL = {
    "Topper Circular": {"precio": 7.0, "stock": 10},
    "Topper Básico 2 Capas": {"precio": 5.0, "stock": 15},
    "Piñata Cuadrada Básica": {"precio": 10.0, "stock": 4},
    "Impresión DTF - Insignia": {"precio": 1.0, "stock": 50},
    "Franela Blanca Piel de Durazno": {"precio": 12.0, "stock": 8},
    "Hoja de Stickers": {"precio": 4.0, "stock": 30},
    "Agenda Tamaño Carta": {"precio": 15.0, "stock": 5},
}

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if "productos" not in datos or not datos["productos"]:
                    datos["productos"] = CATALOGO_INICIAL
                if "ventas" not in datos: datos["ventas"] = []
                if "caja_abierta" not in datos: datos["caja_abierta"] = True
                if "clientes" not in datos: datos["clientes"] = []
                return datos
        except Exception:
            pass
    return {
        "ventas": [], 
        "productos": CATALOGO_INICIAL, 
        "caja_abierta": True, 
        "clientes": []
    }

def guardar_datos(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def obtener_tasa_euro():
    url = "https://open.er-api.com/v6/latest/EUR"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            datos = json.loads(response.read().decode())
            return datos["rates"]["VES"]
    except Exception:
        return 45.0

def main(page: ft.Page):
    page.title = "GestorJhormary Móvil"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.scroll = ft.ScrollMode.AUTO

    db = cargar_datos()
    tasa = obtener_tasa_euro()
    carrito = []
    
    tasa_banner = ft.Container(
        content=ft.Text(f"💶 Tasa BCV: {tasa:.2f} VES", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.RED_400,
        padding=8,
        border_radius=8,
        alignment="center"
    )

    marca_banner = ft.Container(
        content=ft.Text("✨ @inversionesjhormary ✨ - Propiedad Exclusiva", color=ft.Colors.PINK_900, weight=ft.FontWeight.BOLD, size=12),
        bgcolor=ft.Colors.PINK_50,
        padding=6,
        border_radius=8,
        alignment="center"
    )

    txt_cliente = ft.TextField(label="Nombre del Cliente", prefix_icon="person", border_radius=8, dense=True)
    dd_productos = ft.Dropdown(
        label="Seleccionar Producto",
        options=[ft.dropdown.Option(p) for p in db["productos"].keys()],
        border_radius=8,
        dense=True
    )
    txt_cantidad = ft.TextField(label="Cant", value="1", width=70, border_radius=8, dense=True)
    
    txt_abono = ft.TextField(label="Abono ($)", value="0", width=110, border_radius=8, dense=True)
    dd_metodo_pago = ft.Dropdown(
        label="Método de Pago",
        options=[ft.dropdown.Option("Efectivo ($)"), ft.dropdown.Option("Pago Móvil"), ft.dropdown.Option("Zelle"), ft.dropdown.Option("Efectivo Bs")],
        value="Pago Móvil", width=140, border_radius=8, dense=True
    )
    dd_estado_pago = ft.Dropdown(
        label="Estado Pago",
        options=[ft.dropdown.Option("Pagado"), ft.dropdown.Option("Abonado"), ft.dropdown.Option("Pendiente")],
        value="Abonado", width=130, border_radius=8, dense=True
    )
    txt_dias_entrega = ft.TextField(label="Días Entrega", value="3", width=100, border_radius=8, dense=True)

    lista_carrito_view = ft.ListView(expand=1, spacing=4, height=80)
    lbl_total = ft.Text("Total: $0.00 USD", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PINK_700)
    
    txt_recibo_pantalla = ft.TextField(
        label="Recibo / Comprobante Generado",
        multiline=True,
        min_lines=4,
        max_lines=6,
        read_only=True,
        border_radius=8,
        text_size=11
    )

    def agregar_al_carrito(e):
        p_nombre = dd_productos.value
        if not p_nombre: return
        try:
            cant = float(txt_cantidad.value)
        except ValueError:
            cant = 1.0

        subtotal = db["productos"][p_nombre]["precio"] * cant
        carrito.append({"nombre": p_nombre, "cantidad": cant, "subtotal": subtotal})
        lista_carrito_view.controls.append(ft.Text(f"• {int(cant)}x {p_nombre} - ${subtotal:.2f}", size=11))
        
        total_gen = sum(item["subtotal"] for item in carrito)
        lbl_total.value = f"Total: ${total_gen:.2f} USD | {(total_gen * tasa):,.2f} Bs"
        page.update()

    btn_agregar = ft.FilledButton("Añadir", icon="add", on_click=agregar_al_carrito, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE)

    def registrar_venta_movil(e):
        if not db.get("caja_abierta", True):
            page.show_snack_bar(ft.SnackBar(ft.Text("¡La caja está cerrada! Ábrala primero.")))
            return
        if not carrito:
            page.show_snack_bar(ft.SnackBar(ft.Text("¡Agrega productos al carrito!")))
            return
        
        total_v = sum(i["subtotal"] for i in carrito)
        try:
            abono_val = float(txt_abono.value or 0)
        except ValueError:
            abono_val = 0.0
            
        restante = total_v - abono_val
        cliente_nombre = txt_cliente.value.strip() or "Cliente General"

        nueva_venta = {
            "id": datetime.now().strftime('%Y%m%d%H%M%S'),
            "fecha": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "cliente": cliente_nombre,
            "productos": list(carrito),
            "total_divisa": total_v,
            "abono": abono_val,
            "restante": restante,
            "metodo_pago": dd_metodo_pago.value,
            "estado_pago": dd_estado_pago.value,
            "dias_entrega": txt_dias_entrega.value,
            "tasa": tasa
        }
        db["ventas"].append(nueva_venta)
        
        for item in carrito:
            p_n = item["nombre"]
            if p_n in db["productos"]:
                db["productos"][p_n]["stock"] -= item["cantidad"]

        guardar_datos(db)
        
        comprobante = (
            f"=== COMPROBANTE INVERSIONESJHORMARY ===\n"
            f"Autor: @inversionesjhormary\n"
            f"📅 Fecha: {nueva_venta['fecha']}\n"
            f"👤 Cliente: {nueva_venta['cliente']}\n"
            f"💳 Método: {nueva_venta['metodo_pago']} | Estado: {nueva_venta['estado_pago']}\n"
            f"📦 Días Entrega Est.: {nueva_venta['dias_entrega']} días\n"
            f"----------------------------------------\n"
            f"Total Venta: ${total_v:.2f} USD ({(total_v*tasa):,.2f} Bs)\n"
            f"Abonado: ${abono_val:.2f} | Resta: ${restante:.2f}\n"
            f"========================================\n"
        )
        txt_recibo_pantalla.value = comprobante

        carrito.clear()
        lista_carrito_view.controls.clear()
        lbl_total.value = "Total: $0.00 USD"
        txt_cliente.value = ""
        actualizar_todo()
        page.show_snack_bar(ft.SnackBar(ft.Text("¡Venta registrada con éxito!")))
        page.update()

    btn_vender = ft.FilledButton("⚡ Registrar Venta y Generar Recibo", icon="check", on_click=registrar_venta_movil, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)

    contenido_principal = ft.Container(expand=True)

    tab_ventas_content = ft.Column([
        tasa_banner, marca_banner, txt_cliente,
        ft.Row([dd_productos, txt_cantidad], alignment="space_between"),
        ft.Row([txt_abono, dd_metodo_pago], alignment="space_between"),
        ft.Row([dd_estado_pago, txt_dias_entrega], alignment="space_between"),
        btn_agregar, ft.Divider(), lista_carrito_view, lbl_total, btn_vender, ft.Divider(),
        ft.Text("📋 Recibo generado:", weight=ft.FontWeight.BOLD, size=11), txt_recibo_pantalla
    ], spacing=5, scroll=ft.ScrollMode.AUTO)

    tab_inventario_content = ft.Column([
        tasa_banner, marca_banner, ft.Text("📦 Gestión de Inventario", weight=ft.FontWeight.BOLD, size=14),
    ], spacing=5, scroll=ft.ScrollMode.AUTO)

    tab_clientes_content = ft.Column([
        tasa_banner, marca_banner, ft.Text("👥 Directorio de Clientes", weight=ft.FontWeight.BOLD, size=14),
    ], spacing=5, scroll=ft.ScrollMode.AUTO)

    tab_caja_content = ft.Column([
        tasa_banner, marca_banner, ft.Text("💵 Control de Caja", weight=ft.FontWeight.BOLD, size=14),
    ], spacing=5, scroll=ft.ScrollMode.AUTO)

    contenido_principal.content = tab_ventas_content

    def actualizar_todo():
        dd_productos.options = [ft.dropdown.Option(p) for p in db["productos"].keys()]
        page.update()

    def mostrar_ventas(e):
        contenido_principal.content = tab_ventas_content
        page.update()

    def mostrar_inventario(e):
        contenido_principal.content = tab_inventario_content
        page.update()

    def mostrar_clientes(e):
        contenido_principal.content = tab_clientes_content
        page.update()

    def mostrar_caja(e):
        contenido_principal.content = tab_caja_content
        page.update()

    barra_inferior = ft.Container(
        content=ft.Row([
            ft.TextButton("Ventas", icon="point_of_sale", on_click=mostrar_ventas),
            ft.TextButton("Inventario", icon="inventory", on_click=mostrar_inventario),
            ft.TextButton("Clientes", icon="people", on_click=mostrar_clientes),
            ft.TextButton("Caja", icon="attach_money", on_click=mostrar_caja),
        ], alignment="space_around"),
        bgcolor=ft.Colors.PINK_50,
        padding=6,
        border_radius=8
    )

    page.add(ft.Column([
        contenido_principal,
        barra_inferior
    ], expand=True))

    actualizar_test = lambda: None

if __name__ == "__main__":
    ft.run(main)