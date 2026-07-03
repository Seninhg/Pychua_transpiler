import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional

from f1_analizador_lexico.analizador_lexico import TipoToken
from f2_analizador_sintactico.nodos import (
    NodoAST, NodoPrograma, NodoFuncion, NodoParam, NodoClase,
    NodoAsignacion, NodoRetorno, NodoIf, NodoWhile, NodoFor,
    NodoBreak, NodoContinua,
    NodoBinario, NodoUnario, NodoLlamada, NodoLlamadaMetodo, NodoAccesoAtributo,
    NodoIdentificador, NodoLiteral, NodoLista,
)


# -----------------------------------------------------------------------------
#  TABLAS DE TRADUCCIÓN QUECHUA → PYTHON
# -----------------------------------------------------------------------------

FUNCIONES_INTERNAS_PY = {
    "qillqay" : "print",
    "ranka"   : "range",
    "tapuy"   : "input",
    "yupaypi" : "int",
    "simipi"  : "str",
    "ratu"    : "len",
}

TIPOS_PY = {
    "yupay"   : "int",
    "chiqchi" : "float",
    "simi"    : "str",
}

OPERADORES_LOGICOS_PY = {
    "&&": "and",
    "||": "or",
}

LITERALES_BOOL_PY = {
    "cheqaq": "True",
    "llulla": "False",
}

INDENT = "    "


# -----------------------------------------------------------------------------
#  GENERADOR DE CÓDIGO
# -----------------------------------------------------------------------------

class GeneradorCodigo:
    """
    Recorre el AST (ya validado por el analizador semántico) y produce texto
    Python equivalente. Al ser un transpilador entre lenguajes de alto nivel
    muy similares, esta fase reemplaza directamente a la generación de código
    intermedio y a la optimización de un compilador tradicional: el AST hace
    las veces de representación intermedia y la optimización queda delegada
    al propio intérprete de Python.
    """

    def __init__(self):
        self.lineas: List[str] = []

    def generar(self, programa: NodoPrograma) -> str:
        self.lineas = []
        self._generar_bloque(programa.cuerpo, nivel=0)
        return "\n".join(self.lineas).rstrip("\n") + "\n"

    # ------------------------------------------------------------------
    #  Infraestructura de emisión
    # ------------------------------------------------------------------

    def _emitir(self, texto: str, nivel: int) -> None:
        self.lineas.append(INDENT * nivel + texto)

    def _linea_en_blanco(self) -> None:
        if self.lineas and self.lineas[-1] != "":
            self.lineas.append("")

    def _generar_bloque(self, sentencias: List[NodoAST], nivel: int) -> None:
        if not sentencias:
            self._emitir("pass", nivel)
            return
        for sentencia in sentencias:
            self._generar_sentencia(sentencia, nivel)

    # ------------------------------------------------------------------
    #  Sentencias
    # ------------------------------------------------------------------

    def _generar_sentencia(self, nodo: NodoAST, nivel: int) -> None:
        if isinstance(nodo, NodoFuncion):
            # Los modificadores (sapaq, sayk_uq, ch_usaq) no tienen traducción
            # directa en Python a nivel de función suelta; ch_usaq ya se validó
            # en la fase semántica (una función void no puede retornar valor).
            params = ", ".join(self._generar_param(p) for p in nodo.params)
            self._emitir(f"def {nodo.nombre}({params}):", nivel)
            self._generar_bloque(nodo.cuerpo, nivel + 1)
            self._linea_en_blanco()

        elif isinstance(nodo, NodoClase):
            self._emitir(f"class {nodo.nombre}:", nivel)
            self._generar_bloque(nodo.cuerpo, nivel + 1)
            self._linea_en_blanco()

        elif isinstance(nodo, NodoAsignacion):
            self._emitir(f"{nodo.nombre} = {self._expr(nodo.valor)}", nivel)

        elif isinstance(nodo, NodoRetorno):
            if nodo.valor is not None:
                self._emitir(f"return {self._expr(nodo.valor)}", nivel)
            else:
                self._emitir("return", nivel)

        elif isinstance(nodo, NodoIf):
            self._emitir(f"if {self._expr(nodo.condicion)}:", nivel)
            self._generar_bloque(nodo.cuerpo, nivel + 1)
            if nodo.sino is not None:
                self._emitir("else:", nivel)
                self._generar_bloque(nodo.sino, nivel + 1)

        elif isinstance(nodo, NodoWhile):
            self._emitir(f"while {self._expr(nodo.condicion)}:", nivel)
            self._generar_bloque(nodo.cuerpo, nivel + 1)

        elif isinstance(nodo, NodoFor):
            self._emitir(f"for {nodo.variable} in {self._expr(nodo.iterable)}:", nivel)
            self._generar_bloque(nodo.cuerpo, nivel + 1)

        elif isinstance(nodo, NodoBreak):
            self._emitir("break", nivel)

        elif isinstance(nodo, NodoContinua):
            self._emitir("continue", nivel)

        else:
            # Sentencia-expresión suelta (p. ej. una llamada a función sin asignar)
            self._emitir(self._expr(nodo), nivel)

    def _generar_param(self, param: NodoParam) -> str:
        tipo_py = TIPOS_PY.get(param.tipo)
        return f"{param.nombre}: {tipo_py}" if tipo_py else param.nombre

    # ------------------------------------------------------------------
    #  Expresiones
    # ------------------------------------------------------------------

    def _expr(self, nodo: NodoAST) -> str:
        if isinstance(nodo, NodoLiteral):
            if nodo.tipo == TipoToken.LITERAL_BOOL:
                return LITERALES_BOOL_PY.get(nodo.valor, nodo.valor)
            return nodo.valor

        if isinstance(nodo, NodoIdentificador):
            return nodo.nombre

        if isinstance(nodo, NodoBinario):
            op = OPERADORES_LOGICOS_PY.get(nodo.operador, nodo.operador)
            return f"({self._expr(nodo.izquierda)} {op} {self._expr(nodo.derecha)})"

        if isinstance(nodo, NodoUnario):
            if nodo.operador == "mana":
                return f"(not {self._expr(nodo.operando)})"
            return f"(-{self._expr(nodo.operando)})"

        if isinstance(nodo, NodoLlamada):
            nombre_py = FUNCIONES_INTERNAS_PY.get(nodo.nombre, nodo.nombre)
            args = ", ".join(self._expr(a) for a in nodo.args)
            return f"{nombre_py}({args})"

        if isinstance(nodo, NodoLlamadaMetodo):
            args = ", ".join(self._expr(a) for a in nodo.args)
            return f"{self._expr(nodo.objeto)}.{nodo.metodo}({args})"

        if isinstance(nodo, NodoAccesoAtributo):
            return f"{self._expr(nodo.objeto)}.{nodo.atributo}"

        if isinstance(nodo, NodoLista):
            elementos = ", ".join(self._expr(e) for e in nodo.elementos)
            return f"[{elementos}]"

        raise ValueError(f"Nodo de expresión no soportado por el generador: {type(nodo).__name__}")


# -----------------------------------------------------------------------------
#  IMPRESIÓN DEL RESULTADO
# -----------------------------------------------------------------------------

def imprimir_codigo_generado(codigo: str) -> None:
    ancho = 78
    print("\n" + "=" * ancho)
    print("  CÓDIGO PYTHON GENERADO")
    print("=" * ancho)
    print(codigo)
    print("=" * ancho + "\n")
