import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional

from f1_analizador_lexico.analizador_lexico import (
    TipoToken, OPERADORES_ARITMETICOS, OPERADORES_COMPARACION, OPERADORES_LOGICOS,
)
from f3_analizador_semantico.tabla_simbolos import Simbolo, Ambito
from f2_analizador_sintactico.nodos import (
    NodoAST, NodoPrograma, NodoFuncion, NodoClase,
    NodoAsignacion, NodoRetorno, NodoIf, NodoWhile, NodoFor,
    NodoBreak, NodoContinua,
    NodoBinario, NodoUnario, NodoLlamada, NodoAccesoAtributo,
    NodoIdentificador, NodoLiteral, NodoLista,
)


# -----------------------------------------------------------------------------
#  EXCEPCIÓN DE ERROR SEMÁNTICO
# -----------------------------------------------------------------------------

class ErrorSemantico(Exception):
    def __init__(self, mensaje: str, linea: int):
        self.mensaje = mensaje
        self.linea   = linea
        super().__init__(f"[Error semántico] L{linea} — {mensaje}")


# -----------------------------------------------------------------------------
#  TABLAS AUXILIARES
# -----------------------------------------------------------------------------

# Tipo inferido de cada literal, a partir del tipo de token que arrastra el NodoLiteral
MAPA_TIPOS_LITERAL = {
    TipoToken.LITERAL_ENTERO   : "yupay",
    TipoToken.LITERAL_FLOTANTE : "chiqchi",
    TipoToken.LITERAL_CADENA   : "simi",
    TipoToken.LITERAL_BOOL     : "bool",
}

TIPOS_NUMERICOS = {"yupay", "chiqchi"}

# Aridad esperada (mín, máx) de las funciones internas del lenguaje; None = sin límite
FUNCIONES_INTERNAS_ARIDAD = {
    "qillqay" : None,      # print(...)
    "ranka"   : (1, 3),    # range()
    "tapuy"   : (0, 1),    # input()
    "yupaypi" : (1, 1),    # int()
    "simipi"  : (1, 1),    # str()
    "ratu"    : (1, 1),    # len()
}


# -----------------------------------------------------------------------------
#  ANALIZADOR SEMÁNTICO
# -----------------------------------------------------------------------------

class AnalizadorSemantico:
    """
    Recorre el AST producido por el Parser y valida lo que la gramática por sí
    sola no puede atrapar: variables no declaradas, funciones/clases repetidas,
    aridad de llamadas, uso de 'kutichiy'/'usqhaychiy'/'katiy' fuera de contexto
    y compatibilidad básica de tipos en operaciones.

    Nota de diseño: el parser reutiliza NodoLlamada tanto para llamadas directas
    (foo(x)) como para llamadas a método (obj.foo(x) -> NodoLlamada('foo', [obj, x])),
    sin un indicador que las distinga. Por eso la validación de existencia/aridad
    solo se aplica a nombres que resuelven a una función o clase global conocida;
    el resto se asume como una posible llamada a método dinámico y no se reporta
    como error, para evitar falsos positivos.
    """

    def __init__(self):
        self.global_ambito   = Ambito("global")
        self.errores         : List[str] = []
        self.ambitos         : List[Ambito] = [self.global_ambito]
        self._pila_funciones : List[dict] = []
        self._nivel_bucle    = 0

    # ------------------------------------------------------------------
    #  Punto de entrada
    # ------------------------------------------------------------------

    def analizar(self, programa: NodoPrograma) -> List[str]:
        self._registrar_declaraciones_globales(programa.cuerpo)
        for nodo in programa.cuerpo:
            self._visitar(nodo, self.global_ambito)
        return self.errores

    def _registrar_declaraciones_globales(self, cuerpo: List[NodoAST]) -> None:
        """
        Primera pasada: registra funciones y clases de nivel superior antes de
        analizar sus cuerpos, para permitir referencias hacia adelante y
        recursividad mutua entre funciones.
        """
        for nodo in cuerpo:
            if isinstance(nodo, NodoFuncion):
                simbolo = Simbolo(nodo.nombre, "funcion", linea=nodo.linea, num_params=len(nodo.params))
                if not self.global_ambito.declarar(simbolo):
                    self._error(f"La función '{nodo.nombre}' ya fue declarada", nodo.linea)
            elif isinstance(nodo, NodoClase):
                simbolo = Simbolo(nodo.nombre, "clase", linea=nodo.linea)
                if not self.global_ambito.declarar(simbolo):
                    self._error(f"La clase '{nodo.nombre}' ya fue declarada", nodo.linea)

    def _error(self, mensaje: str, linea: int) -> None:
        self.errores.append(f"  {ErrorSemantico(mensaje, linea)}")

    # ------------------------------------------------------------------
    #  Sentencias
    # ------------------------------------------------------------------

    def _visitar(self, nodo: NodoAST, ambito: Ambito) -> None:
        if isinstance(nodo, NodoFuncion):
            self._visitar_funcion(nodo)

        elif isinstance(nodo, NodoClase):
            self._visitar_clase(nodo)

        elif isinstance(nodo, NodoAsignacion):
            tipo = self._visitar_expr(nodo.valor, ambito)
            ambito.declarar(Simbolo(nodo.nombre, "variable", tipo=tipo, linea=nodo.linea))

        elif isinstance(nodo, NodoRetorno):
            if not self._pila_funciones:
                self._error("'kutichiy' (return) usado fuera de una función", nodo.linea)
            elif self._pila_funciones[-1]["void"] and nodo.valor is not None:
                nombre_fn = self._pila_funciones[-1]["nombre"]
                self._error(f"La función void '{nombre_fn}' no puede retornar un valor", nodo.linea)
            if nodo.valor is not None:
                self._visitar_expr(nodo.valor, ambito)

        elif isinstance(nodo, NodoIf):
            self._visitar_expr(nodo.condicion, ambito)
            for sentencia in nodo.cuerpo:
                self._visitar(sentencia, ambito)
            if nodo.sino:
                for sentencia in nodo.sino:
                    self._visitar(sentencia, ambito)

        elif isinstance(nodo, NodoWhile):
            self._visitar_expr(nodo.condicion, ambito)
            self._nivel_bucle += 1
            for sentencia in nodo.cuerpo:
                self._visitar(sentencia, ambito)
            self._nivel_bucle -= 1

        elif isinstance(nodo, NodoFor):
            self._visitar_expr(nodo.iterable, ambito)
            ambito.declarar(Simbolo(nodo.variable, "variable", linea=nodo.linea))
            self._nivel_bucle += 1
            for sentencia in nodo.cuerpo:
                self._visitar(sentencia, ambito)
            self._nivel_bucle -= 1

        elif isinstance(nodo, NodoBreak):
            if self._nivel_bucle == 0:
                self._error("'usqhaychiy' (break) usado fuera de un bucle", nodo.linea)

        elif isinstance(nodo, NodoContinua):
            if self._nivel_bucle == 0:
                self._error("'katiy' (continue) usado fuera de un bucle", nodo.linea)

        else:
            # Sentencia-expresión suelta (p. ej. una llamada a función sin asignar)
            self._visitar_expr(nodo, ambito)

    def _visitar_funcion(self, nodo: NodoFuncion) -> None:
        ambito_funcion = Ambito(f"función '{nodo.nombre}'", padre=self.global_ambito)
        self.ambitos.append(ambito_funcion)

        nombres_vistos = set()
        for param in nodo.params:
            if param.nombre in nombres_vistos:
                self._error(f"Parámetro '{param.nombre}' duplicado en la función '{nodo.nombre}'", nodo.linea)
            nombres_vistos.add(param.nombre)
            ambito_funcion.declarar(Simbolo(param.nombre, "parametro", tipo=param.tipo, linea=nodo.linea))

        self._pila_funciones.append({
            "nombre": nodo.nombre,
            "void"  : "ch_usaq" in nodo.modificadores,
        })
        for sentencia in nodo.cuerpo:
            self._visitar(sentencia, ambito_funcion)
        self._pila_funciones.pop()

    def _visitar_clase(self, nodo: NodoClase) -> None:
        ambito_clase = Ambito(f"clase '{nodo.nombre}'", padre=self.global_ambito)
        self.ambitos.append(ambito_clase)
        for sentencia in nodo.cuerpo:
            self._visitar(sentencia, ambito_clase)

    # ------------------------------------------------------------------
    #  Expresiones (devuelven el tipo inferido, o None si no es determinable)
    # ------------------------------------------------------------------

    def _visitar_expr(self, nodo: NodoAST, ambito: Ambito) -> Optional[str]:
        if isinstance(nodo, NodoLiteral):
            return MAPA_TIPOS_LITERAL.get(nodo.tipo)

        if isinstance(nodo, NodoIdentificador):
            simbolo = ambito.resolver(nodo.nombre)
            if simbolo is None:
                self._error(f"Variable '{nodo.nombre}' no declarada", nodo.linea)
                return None
            return simbolo.tipo

        if isinstance(nodo, NodoBinario):
            return self._tipo_binario(nodo, ambito)

        if isinstance(nodo, NodoUnario):
            return self._tipo_unario(nodo, ambito)

        if isinstance(nodo, NodoLlamada):
            return self._visitar_llamada(nodo, ambito)

        if isinstance(nodo, NodoAccesoAtributo):
            self._visitar_expr(nodo.objeto, ambito)
            return None   # el tipo de un atributo no es verificable estáticamente

        if isinstance(nodo, NodoLista):
            for elemento in nodo.elementos:
                self._visitar_expr(elemento, ambito)
            return "lista"

        return None

    def _tipo_binario(self, nodo: NodoBinario, ambito: Ambito) -> Optional[str]:
        t_izq = self._visitar_expr(nodo.izquierda, ambito)
        t_der = self._visitar_expr(nodo.derecha, ambito)
        op    = nodo.operador

        if op in OPERADORES_ARITMETICOS:
            if "simi" in (t_izq, t_der):
                if op == "+" and t_izq == "simi" and t_der == "simi":
                    return "simi"
                if t_izq is not None and t_der is not None:
                    self._error(
                        f"El operador '{op}' no admite operandos de tipo 'simi' junto con "
                        f"'{t_der if t_izq == 'simi' else t_izq}'",
                        nodo.linea,
                    )
                return None
            if t_izq in TIPOS_NUMERICOS and t_der in TIPOS_NUMERICOS:
                return "chiqchi" if "chiqchi" in (t_izq, t_der) else "yupay"
            return None

        if op in OPERADORES_COMPARACION:
            if op in ("<", ">", "<=", ">=") and "simi" in (t_izq, t_der) and t_izq != t_der:
                self._error(f"No se puede comparar '{t_izq}' con '{t_der}' usando '{op}'", nodo.linea)
            return "bool"

        if op in OPERADORES_LOGICOS:
            return "bool"

        return None

    def _tipo_unario(self, nodo: NodoUnario, ambito: Ambito) -> Optional[str]:
        tipo = self._visitar_expr(nodo.operando, ambito)
        if nodo.operador == "-":
            if tipo == "simi":
                self._error("El operador unario '-' no admite operandos de tipo 'simi'", nodo.linea)
                return None
            return tipo
        return "bool"   # 'mana' (not)

    def _visitar_llamada(self, nodo: NodoLlamada, ambito: Ambito) -> Optional[str]:
        for arg in nodo.args:
            self._visitar_expr(arg, ambito)

        if nodo.nombre in FUNCIONES_INTERNAS_ARIDAD:
            rango = FUNCIONES_INTERNAS_ARIDAD[nodo.nombre]
            if rango is not None:
                minimo, maximo = rango
                if not (minimo <= len(nodo.args) <= maximo):
                    self._error(
                        f"'{nodo.nombre}' espera entre {minimo} y {maximo} argumento(s), recibió {len(nodo.args)}",
                        nodo.linea,
                    )
            return None

        simbolo = self.global_ambito.resolver(nodo.nombre)
        if simbolo is not None and simbolo.categoria == "funcion":
            if simbolo.num_params is not None and len(nodo.args) != simbolo.num_params:
                self._error(
                    f"La función '{nodo.nombre}' espera {simbolo.num_params} argumento(s), "
                    f"recibió {len(nodo.args)}",
                    nodo.linea,
                )
            return None

        if simbolo is not None and simbolo.categoria == "clase":
            return simbolo.nombre   # instanciación: el tipo resultante es la propia clase

        # Nombre no reconocido como función/clase global: puede ser una llamada a
        # método dinámico (ver nota de diseño en la clase). No se reporta error.
        return None


# -----------------------------------------------------------------------------
#  IMPRESIÓN DE RESULTADOS
# -----------------------------------------------------------------------------

def imprimir_resultado_semantico(errores: List[str]) -> None:
    ancho = 78
    print("\n" + "=" * ancho)
    print("  ANALIZADOR SEMÁNTICO — LENGUAJE PYCHUA")
    print("=" * ancho)
    if errores:
        print("  ERRORES SEMÁNTICOS ENCONTRADOS")
        print("=" * ancho)
        for error in errores:
            print(error)
    else:
        print("\n  ✓ Sin errores semánticos.")
    print("=" * ancho + "\n")
