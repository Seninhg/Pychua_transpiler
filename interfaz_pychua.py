import sys
import os
import io
import traceback
from contextlib import redirect_stdout

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

RAIZ = os.path.dirname(os.path.abspath(__file__))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from f1_analizador_lexico.analizador_lexico import LexerQuechua, imprimir_tabla
from f1_analizador_lexico.indent_processor import IndentProcessor
from f2_analizador_sintactico.parser import Parser, imprimir_ast
from f3_analizador_semantico.analizador_semantico import AnalizadorSemantico, imprimir_resultado_semantico
from f3_analizador_semantico.tabla_simbolos import imprimir_tabla_simbolos
from f4_generador_codigo.generador_codigo import GeneradorCodigo


# -----------------------------------------------------------------------------
#  CONSTANTES
# -----------------------------------------------------------------------------

SRC_DIR = os.path.join(RAIZ, "src")

CODIGO_INICIAL = (
    "ruway sumar(a, b):\n"
    "    resultado = a + b\n"
    "    kutichiy resultado\n"
    "\n"
    "qillqay(sumar(5, 3))\n"
)


# -----------------------------------------------------------------------------
#  UTILIDADES
# -----------------------------------------------------------------------------

def _capturar(funcion, *args) -> str:
    """Ejecuta una función 'imprimir_*' del pipeline y devuelve lo impreso como texto."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        funcion(*args)
    return buffer.getvalue()


def _listar_ejemplos() -> list:
    if not os.path.isdir(SRC_DIR):
        return []
    return sorted(f for f in os.listdir(SRC_DIR) if f.endswith(".txt"))


def _entrada_dialogo(prompt: str = "") -> str:
    """Sustituye a input() cuando el código generado usa 'tapuy': pide el valor con un diálogo."""
    valor = simpledialog.askstring("Entrada requerida (tapuy)", prompt or "Ingresa un valor:", parent=ventana)
    return valor if valor is not None else ""


# -----------------------------------------------------------------------------
#  VENTANA PRINCIPAL Y ENTRADA DE CÓDIGO
# -----------------------------------------------------------------------------

ventana = tk.Tk()
ventana.title("Transpilador PyChua → Python")
ventana.geometry("1050x780")
ventana.configure(padx=15, pady=15)

tk.Label(ventana, text="Código fuente PyChua:", font=("Arial", 12, "bold")).pack(anchor="w")

frame_entrada = tk.Frame(ventana)
frame_entrada.pack(fill=tk.X, pady=(5, 5))

entrada_codigo = tk.Text(frame_entrada, width=100, height=10, font=("Consolas", 11), wrap="none")
entrada_codigo.pack(side=tk.LEFT, fill=tk.X, expand=True)
_scroll_entrada = tk.Scrollbar(frame_entrada, command=entrada_codigo.yview)
_scroll_entrada.pack(side=tk.RIGHT, fill=tk.Y)
entrada_codigo.configure(yscrollcommand=_scroll_entrada.set)
entrada_codigo.insert("1.0", CODIGO_INICIAL)


# -----------------------------------------------------------------------------
#  PESTAÑAS DE RESULTADOS (una por fase del pipeline)
# -----------------------------------------------------------------------------

notebook = ttk.Notebook(ventana)
notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))


def _crear_pestana(nombre: str, bg: str = None, fg: str = None) -> tk.Text:
    frame = tk.Frame(notebook)
    notebook.add(frame, text=nombre)
    texto = tk.Text(frame, font=("Consolas", 10), bg=bg, fg=fg, wrap="none")
    scroll_y = tk.Scrollbar(frame, command=texto.yview)
    texto.configure(yscrollcommand=scroll_y.set)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    return texto


txt_lexico     = _crear_pestana("1. Léxico")
txt_sintactico = _crear_pestana("2. Sintáctico (AST)")
txt_semantico  = _crear_pestana("3. Semántico")
txt_codigo     = _crear_pestana("4. Código Python", bg="#1e1e1e", fg="#00ff00")
txt_ejecucion  = _crear_pestana("5. Ejecución", bg="#1e1e1e", fg="#dddddd")

_PESTANAS = (txt_lexico, txt_sintactico, txt_semantico, txt_codigo, txt_ejecucion)


# -----------------------------------------------------------------------------
#  LÓGICA DE LA INTERFAZ
# -----------------------------------------------------------------------------

def _limpiar_pestanas() -> None:
    for widget in _PESTANAS:
        widget.delete("1.0", tk.END)


def cargar_ejemplo() -> None:
    nombre = combo_ejemplos.get()
    if not nombre:
        messagebox.showwarning("Advertencia", "Selecciona un ejemplo de la lista.")
        return
    with open(os.path.join(SRC_DIR, nombre), encoding="utf-8") as f:
        contenido = f.read()
    entrada_codigo.delete("1.0", tk.END)
    entrada_codigo.insert("1.0", contenido)


def limpiar() -> None:
    entrada_codigo.delete("1.0", tk.END)


def transpilar() -> None:
    _limpiar_pestanas()
    codigo = entrada_codigo.get("1.0", tk.END)
    if not codigo.strip():
        messagebox.showwarning("Advertencia", "Ingresa código PyChua para transpilar.")
        return

    # 1. Análisis léxico
    lexer = LexerQuechua(codigo)
    tokens = lexer.analizar()
    txt_lexico.insert(tk.END, _capturar(imprimir_tabla, tokens, lexer.errores))
    if lexer.errores:
        for widget in (txt_sintactico, txt_semantico, txt_codigo, txt_ejecucion):
            widget.insert(tk.END, "Detenido por errores léxicos.")
        notebook.select(txt_lexico.master)
        return

    # 2. Indentación + análisis sintáctico
    tokens = IndentProcessor(tokens).procesar()
    parser = Parser(tokens)
    ast = parser.parsear()
    txt_sintactico.insert(tk.END, _capturar(imprimir_ast, ast))
    if parser.errores:
        txt_sintactico.insert(tk.END, "\nERRORES SINTÁCTICOS:\n" + "\n".join(parser.errores))
        for widget in (txt_semantico, txt_codigo, txt_ejecucion):
            widget.insert(tk.END, "Detenido por errores sintácticos.")
        notebook.select(txt_sintactico.master)
        return

    # 3. Análisis semántico
    analizador = AnalizadorSemantico()
    errores_semanticos = analizador.analizar(ast)
    txt_semantico.insert(tk.END, _capturar(imprimir_resultado_semantico, errores_semanticos))
    txt_semantico.insert(tk.END, _capturar(imprimir_tabla_simbolos, analizador.ambitos))
    if errores_semanticos:
        for widget in (txt_codigo, txt_ejecucion):
            widget.insert(tk.END, "Detenido por errores semánticos.")
        notebook.select(txt_semantico.master)
        return

    # 4. Generación de código Python
    generador = GeneradorCodigo()
    codigo_python = generador.generar(ast)
    txt_codigo.insert(tk.END, codigo_python)

    # 5. Ejecución del código generado
    buffer_salida = io.StringIO()
    globales_ejecucion = {"input": _entrada_dialogo}
    try:
        with redirect_stdout(buffer_salida):
            exec(compile(codigo_python, "<pychua>", "exec"), globales_ejecucion)
        txt_ejecucion.insert(tk.END, buffer_salida.getvalue() or "(el programa no produjo salida)")
    except Exception:
        txt_ejecucion.insert(tk.END, buffer_salida.getvalue())
        txt_ejecucion.insert(tk.END, "\n--- ERROR EN TIEMPO DE EJECUCIÓN ---\n")
        txt_ejecucion.insert(tk.END, traceback.format_exc())

    notebook.select(txt_codigo.master)


# -----------------------------------------------------------------------------
#  BARRA DE CONTROLES
# -----------------------------------------------------------------------------

frame_controles = tk.Frame(ventana)
frame_controles.pack(fill=tk.X, pady=5)

tk.Label(frame_controles, text="Ejemplo:").pack(side=tk.LEFT)
combo_ejemplos = ttk.Combobox(frame_controles, values=_listar_ejemplos(), width=25, state="readonly")
combo_ejemplos.pack(side=tk.LEFT, padx=5)

tk.Button(frame_controles, text="Cargar ejemplo", command=cargar_ejemplo).pack(side=tk.LEFT, padx=5)
tk.Button(frame_controles, text="Limpiar", command=limpiar).pack(side=tk.LEFT, padx=5)
tk.Button(frame_controles, text="⚡ TRANSPILAR A PYTHON ⚡", bg="#205c33", fg="white",
          font=("Arial", 11, "bold"), command=transpilar).pack(side=tk.RIGHT, padx=5)

ventana.mainloop()
