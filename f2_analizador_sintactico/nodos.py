from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Any


# -----------------------------------------------------------------------------
#  BASE
# -----------------------------------------------------------------------------

class NodoAST:
    """Clase base para todos los nodos del AST."""


# -----------------------------------------------------------------------------
#  NIVEL DE PROGRAMA
# -----------------------------------------------------------------------------

@dataclass
class NodoPrograma(NodoAST):
    cuerpo: List[NodoAST]


# -----------------------------------------------------------------------------
#  DECLARACIONES
# -----------------------------------------------------------------------------

@dataclass
class NodoParam(NodoAST):
    nombre : str
    tipo   : Optional[str] = None


@dataclass
class NodoFuncion(NodoAST):
    nombre : str
    params : List[NodoParam]
    cuerpo : List[NodoAST]
    linea  : int = 0


# -----------------------------------------------------------------------------
#  SENTENCIAS
# -----------------------------------------------------------------------------

@dataclass
class NodoAsignacion(NodoAST):
    nombre : str
    valor  : NodoAST
    linea  : int = 0


@dataclass
class NodoRetorno(NodoAST):
    valor : Optional[NodoAST]
    linea : int = 0


@dataclass
class NodoIf(NodoAST):
    condicion : NodoAST
    cuerpo    : List[NodoAST]
    sino      : Optional[List[NodoAST]]
    linea     : int = 0


@dataclass
class NodoWhile(NodoAST):
    condicion : NodoAST
    cuerpo    : List[NodoAST]
    linea     : int = 0


@dataclass
class NodoFor(NodoAST):
    variable  : str
    iterable  : NodoAST
    cuerpo    : List[NodoAST]
    linea     : int = 0


@dataclass
class NodoBreak(NodoAST):
    linea : int = 0


@dataclass
class NodoContinua(NodoAST):
    linea : int = 0


# -----------------------------------------------------------------------------
#  EXPRESIONES
# -----------------------------------------------------------------------------

@dataclass
class NodoBinario(NodoAST):
    izquierda : NodoAST
    operador  : str
    derecha   : NodoAST
    linea     : int = 0


@dataclass
class NodoUnario(NodoAST):
    operador  : str
    operando  : NodoAST
    linea     : int = 0


@dataclass
class NodoLlamada(NodoAST):
    nombre : str
    args   : List[NodoAST]
    linea  : int = 0


@dataclass
class NodoIdentificador(NodoAST):
    nombre : str
    linea  : int = 0


@dataclass
class NodoLiteral(NodoAST):
    valor : Any
    tipo  : str    # LITERAL_ENTERO | LITERAL_FLOTANTE | LITERAL_CADENA | LITERAL_BOOL
    linea : int = 0


@dataclass
class NodoLista(NodoAST):
    elementos : List[NodoAST]
    linea     : int = 0
