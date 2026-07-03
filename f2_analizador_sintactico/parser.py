import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional

from f1_analizador_lexico.analizador_lexico import LexerQuechua, Token, TipoToken
from f1_analizador_lexico.indent_processor   import IndentProcessor
from f2_analizador_sintactico.nodos import (
    NodoAST, NodoPrograma, NodoFuncion, NodoParam, NodoClase,
    NodoAsignacion, NodoRetorno, NodoIf, NodoWhile, NodoFor,
    NodoBreak, NodoContinua,
    NodoBinario, NodoUnario, NodoLlamada, NodoLlamadaMetodo, NodoAccesoAtributo,
    NodoIdentificador, NodoLiteral, NodoLista,
)


# -----------------------------------------------------------------------------
#  EXCEPCIÓN DE ERROR SINTÁCTICO
# -----------------------------------------------------------------------------

class ErrorSintactico(Exception):
    def __init__(self, mensaje: str, linea: int, columna: int):
        self.mensaje = mensaje
        self.linea   = linea
        self.columna = columna
        super().__init__(f"[Error sintáctico] L{linea}:C{columna} — {mensaje}")


# -----------------------------------------------------------------------------
#  PARSER DESCENDENTE RECURSIVO
# -----------------------------------------------------------------------------

class Parser:
    """
    Construye el AST a partir del flujo de tokens producido por el lexer
    y post-procesado por IndentProcessor.

    Gramática (simplificada):
        programa      → declaracion* EOF
        declaracion   → def_funcion | def_clase | sentencia
        def_funcion   → modificadores? 'ruway' IDENT '(' params? ')' ':' bloque
        def_clase     → 'ayllu' IDENT_CLASE ':' bloque
        bloque        → INDENT sentencia+ DEDENT
        sentencia     → retorno | si | mientras | para | break | continua | expr_stmt
        expr_stmt     → expresion ('=' expresion)?
        expresion     → logica
        logica        → comparacion (('&&'|'||') comparacion)*
        comparacion   → aritmetica (op_rel aritmetica)*
        aritmetica    → termino (('+' | '-') termino)*
        termino       → potencia (('*'|'/'|'%'|'//') potencia)*
        potencia      → unario ('**' unario)*
        unario        → 'mana' unario | '-' unario | primario
        primario      → literal | llamada | identificador | '(' expr ')' | lista
    """

    def __init__(self, tokens: List[Token]):
        self.tokens  = tokens
        self.pos     = 0
        self.errores : List[str] = []

    # ------------------------------------------------------------------
    #  Infraestructura
    # ------------------------------------------------------------------

    def actual(self) -> Token:
        return self.tokens[self.pos]

    def avanzar(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def esperar(self, tipo: str, lexema: Optional[str] = None) -> Token:
        tok = self.actual()
        if tok.tipo != tipo:
            raise ErrorSintactico(
                f"Se esperaba {tipo!r}, se encontró {tok.lexema!r} ({tok.tipo})",
                tok.linea, tok.columna,
            )
        if lexema is not None and tok.lexema != lexema:
            raise ErrorSintactico(
                f"Se esperaba '{lexema}', se encontró '{tok.lexema}'",
                tok.linea, tok.columna,
            )
        return self.avanzar()

    def ver(self, tipo: str) -> bool:
        return self.actual().tipo == tipo

    def ver_lexema(self, lexema: str) -> bool:
        return self.actual().lexema == lexema

    def ver_tipo_lexema(self, tipo: str, lexema: str) -> bool:
        tok = self.actual()
        return tok.tipo == tipo and tok.lexema == lexema

    def sincronizar(self) -> None:
        """Recuperación en modo pánico: avanza hasta DEDENT o EOF."""
        while not self.ver(TipoToken.FIN_DE_ARCHIVO) and not self.ver(TipoToken.DEDENT):
            self.avanzar()

    def _registrar_error(self, exc: ErrorSintactico) -> None:
        self.errores.append(f"  {exc}")

    # ------------------------------------------------------------------
    #  Punto de entrada
    # ------------------------------------------------------------------

    def parsear(self) -> NodoPrograma:
        cuerpo: List[NodoAST] = []
        while not self.ver(TipoToken.FIN_DE_ARCHIVO):
            if self.ver(TipoToken.FIN_DE_LINEA) or self.ver(TipoToken.DEDENT):
                self.avanzar()
                continue
            try:
                cuerpo.append(self._parsear_declaracion())
            except ErrorSintactico as e:
                self._registrar_error(e)
                self.sincronizar()
        return NodoPrograma(cuerpo=cuerpo)

    # ------------------------------------------------------------------
    #  Declaraciones de nivel superior
    # ------------------------------------------------------------------

    def _parsear_declaracion(self) -> NodoAST:
        tok = self.actual()

        # Modificadores opcionales antes de 'ruway'
        modificadores: List[str] = []
        while tok.tipo in (TipoToken.MODIFICADOR, TipoToken.MODIFICADOR_ACCESO):
            modificadores.append(self.avanzar().lexema)
            tok = self.actual()

        if self.ver_lexema("ruway"):
            return self._parsear_funcion(modificadores)
        if self.ver_lexema("ayllu"):
            return self._parsear_clase()
        return self._parsear_sentencia()

    def _parsear_funcion(self, modificadores: List[str]) -> NodoFuncion:
        linea = self.actual().linea
        self.esperar(TipoToken.PALABRA_CLAVE, "ruway")
        nombre = self.esperar(TipoToken.IDENTIFICADOR).lexema
        self.esperar(TipoToken.PAREN_ABRE)
        params = self._parsear_params()
        self.esperar(TipoToken.PAREN_CIERRA)
        self.esperar(TipoToken.DOS_PUNTOS)
        cuerpo = self._parsear_bloque()
        return NodoFuncion(nombre=nombre, params=params, cuerpo=cuerpo,
                           modificadores=modificadores, linea=linea)

    def _parsear_params(self) -> List[NodoParam]:
        params: List[NodoParam] = []
        if self.ver(TipoToken.PAREN_CIERRA):
            return params
        params.append(self._parsear_un_param())
        while self.ver(TipoToken.COMA):
            self.avanzar()
            params.append(self._parsear_un_param())
        return params

    def _parsear_un_param(self) -> NodoParam:
        # Tipo de dato opcional seguido de nombre
        tipo: Optional[str] = None
        if self.ver(TipoToken.TIPO_DATO):
            tipo = self.avanzar().lexema
        nombre = self.esperar(TipoToken.IDENTIFICADOR).lexema
        return NodoParam(nombre=nombre, tipo=tipo)

    def _parsear_clase(self) -> NodoClase:
        linea = self.actual().linea
        self.esperar(TipoToken.PALABRA_CLAVE, "ayllu")
        nombre = self.esperar(TipoToken.IDENTIFICADOR_CLASE).lexema
        self.esperar(TipoToken.DOS_PUNTOS)
        cuerpo = self._parsear_bloque()
        return NodoClase(nombre=nombre, cuerpo=cuerpo, linea=linea)

    # ------------------------------------------------------------------
    #  Bloque (delimitado por INDENT / DEDENT)
    # ------------------------------------------------------------------

    def _parsear_bloque(self) -> List[NodoAST]:
        if self.ver(TipoToken.FIN_DE_LINEA):
            self.avanzar()
        self.esperar(TipoToken.INDENT)
        sentencias: List[NodoAST] = []
        while not self.ver(TipoToken.DEDENT) and not self.ver(TipoToken.FIN_DE_ARCHIVO):
            if self.ver(TipoToken.FIN_DE_LINEA):
                self.avanzar()
                continue
            try:
                sentencias.append(self._parsear_sentencia())
            except ErrorSintactico as e:
                self._registrar_error(e)
                self.sincronizar()
        self.esperar(TipoToken.DEDENT)
        return sentencias

    # ------------------------------------------------------------------
    #  Sentencias
    # ------------------------------------------------------------------

    def _parsear_sentencia(self) -> NodoAST:
        tok = self.actual()

        if tok.lexema == "kutichiy":
            return self._parsear_retorno()
        if tok.lexema == "ari_chayqa":
            return self._parsear_if()
        if tok.lexema == "micha":
            return self._parsear_while()
        if tok.lexema == "tupaq":
            return self._parsear_for()
        if tok.lexema == "usqhaychiy":
            self.avanzar()
            self._consumir_fin_linea()
            return NodoBreak(linea=tok.linea)
        if tok.lexema == "katiy":
            self.avanzar()
            self._consumir_fin_linea()
            return NodoContinua(linea=tok.linea)

        return self._parsear_expr_stmt()

    def _consumir_fin_linea(self) -> None:
        if self.ver(TipoToken.FIN_DE_LINEA):
            self.avanzar()

    def _parsear_retorno(self) -> NodoRetorno:
        linea = self.actual().linea
        self.esperar(TipoToken.PALABRA_CLAVE, "kutichiy")
        valor: Optional[NodoAST] = None
        if not self.ver(TipoToken.FIN_DE_LINEA) and not self.ver(TipoToken.DEDENT):
            valor = self._parsear_expresion()
        self._consumir_fin_linea()
        return NodoRetorno(valor=valor, linea=linea)

    def _parsear_if(self) -> NodoIf:
        linea = self.actual().linea
        self.esperar(TipoToken.PALABRA_CLAVE, "ari_chayqa")
        self.esperar(TipoToken.PAREN_ABRE)
        condicion = self._parsear_expresion()
        self.esperar(TipoToken.PAREN_CIERRA)
        self.esperar(TipoToken.DOS_PUNTOS)
        cuerpo = self._parsear_bloque()

        sino: Optional[List[NodoAST]] = None
        if self.ver_lexema("mana_chayqa"):
            self.avanzar()
            self.esperar(TipoToken.DOS_PUNTOS)
            sino = self._parsear_bloque()

        return NodoIf(condicion=condicion, cuerpo=cuerpo, sino=sino, linea=linea)

    def _parsear_while(self) -> NodoWhile:
        linea = self.actual().linea
        self.esperar(TipoToken.PALABRA_CLAVE, "micha")
        self.esperar(TipoToken.PAREN_ABRE)
        condicion = self._parsear_expresion()
        self.esperar(TipoToken.PAREN_CIERRA)
        self.esperar(TipoToken.DOS_PUNTOS)
        cuerpo = self._parsear_bloque()
        return NodoWhile(condicion=condicion, cuerpo=cuerpo, linea=linea)

    def _parsear_for(self) -> NodoFor:
        linea = self.actual().linea
        self.esperar(TipoToken.PALABRA_CLAVE, "tupaq")
        variable = self.esperar(TipoToken.IDENTIFICADOR).lexema
        self.esperar(TipoToken.PALABRA_CLAVE, "ukhupi")
        iterable = self._parsear_expresion()
        self.esperar(TipoToken.DOS_PUNTOS)
        cuerpo = self._parsear_bloque()
        return NodoFor(variable=variable, iterable=iterable, cuerpo=cuerpo, linea=linea)

    def _parsear_expr_stmt(self) -> NodoAST:
        """
        Parsea una expresión. Si va seguida de '=', es una asignación.
        Soporta: identificador = expr  y  expresión pura (llamada a función, etc.)
        """
        linea = self.actual().linea
        expr  = self._parsear_expresion()

        if self.ver(TipoToken.OP_ASIGNACION):
            # Lado izquierdo debe ser un identificador simple
            if not isinstance(expr, NodoIdentificador):
                raise ErrorSintactico(
                    "El lado izquierdo de una asignación debe ser un identificador",
                    linea, self.actual().columna,
                )
            self.avanzar()
            valor = self._parsear_expresion()
            self._consumir_fin_linea()
            return NodoAsignacion(nombre=expr.nombre, valor=valor, linea=linea)

        self._consumir_fin_linea()
        return expr

    # ------------------------------------------------------------------
    #  Expresiones (precedencia de menor a mayor)
    # ------------------------------------------------------------------

    def _parsear_expresion(self) -> NodoAST:
        return self._parsear_logica()

    def _parsear_logica(self) -> NodoAST:
        izq = self._parsear_comparacion()
        while self.ver(TipoToken.OP_LOGICO):
            op   = self.avanzar()
            der  = self._parsear_comparacion()
            izq  = NodoBinario(izquierda=izq, operador=op.lexema, derecha=der, linea=op.linea)
        return izq

    def _parsear_comparacion(self) -> NodoAST:
        izq = self._parsear_aritmetica()
        while self.ver(TipoToken.OP_COMPARACION):
            op  = self.avanzar()
            der = self._parsear_aritmetica()
            izq = NodoBinario(izquierda=izq, operador=op.lexema, derecha=der, linea=op.linea)
        return izq

    def _parsear_aritmetica(self) -> NodoAST:
        izq = self._parsear_termino()
        while self.ver(TipoToken.OP_ARITMETICO) and self.actual().lexema in ('+', '-'):
            op  = self.avanzar()
            der = self._parsear_termino()
            izq = NodoBinario(izquierda=izq, operador=op.lexema, derecha=der, linea=op.linea)
        return izq

    def _parsear_termino(self) -> NodoAST:
        izq = self._parsear_potencia()
        while self.ver(TipoToken.OP_ARITMETICO) and self.actual().lexema in ('*', '/', '%', '//'):
            op  = self.avanzar()
            der = self._parsear_potencia()
            izq = NodoBinario(izquierda=izq, operador=op.lexema, derecha=der, linea=op.linea)
        return izq

    def _parsear_potencia(self) -> NodoAST:
        base = self._parsear_unario()
        if self.ver(TipoToken.OP_ARITMETICO) and self.actual().lexema == '**':
            op  = self.avanzar()
            exp = self._parsear_unario()
            return NodoBinario(izquierda=base, operador=op.lexema, derecha=exp, linea=op.linea)
        return base

    def _parsear_unario(self) -> NodoAST:
        tok = self.actual()
        if tok.lexema == "mana" and tok.tipo == TipoToken.PALABRA_CLAVE:
            self.avanzar()
            return NodoUnario(operador="mana", operando=self._parsear_unario(), linea=tok.linea)
        if self.ver(TipoToken.OP_ARITMETICO) and tok.lexema == '-':
            self.avanzar()
            return NodoUnario(operador="-", operando=self._parsear_unario(), linea=tok.linea)
        return self._parsear_primario()

    def _parsear_primario(self) -> NodoAST:
        tok = self.actual()

        # Literales
        if tok.tipo in (TipoToken.LITERAL_ENTERO, TipoToken.LITERAL_FLOTANTE,
                        TipoToken.LITERAL_CADENA, TipoToken.LITERAL_BOOL):
            self.avanzar()
            return NodoLiteral(valor=tok.lexema, tipo=tok.tipo, linea=tok.linea)

        # Expresión entre paréntesis
        if self.ver(TipoToken.PAREN_ABRE):
            self.avanzar()
            expr = self._parsear_expresion()
            self.esperar(TipoToken.PAREN_CIERRA)
            return expr

        # Lista literal [elem, elem, ...]
        if self.ver(TipoToken.CORCHETE_ABRE):
            return self._parsear_lista()

        # Función interna: qillqay(...), ranka(...), etc.
        if tok.tipo == TipoToken.FUNCION_INTERNA:
            return self._parsear_llamada_interna()

        # Identificador: variable, llamada de función, acceso a atributo
        if tok.tipo in (TipoToken.IDENTIFICADOR, TipoToken.IDENTIFICADOR_CLASE):
            return self._parsear_identificador_o_llamada()

        raise ErrorSintactico(
            f"Expresión no válida: '{tok.lexema}' ({tok.tipo})",
            tok.linea, tok.columna,
        )

    def _parsear_lista(self) -> NodoLista:
        linea = self.actual().linea
        self.esperar(TipoToken.CORCHETE_ABRE)
        elementos: List[NodoAST] = []
        if not self.ver(TipoToken.CORCHETE_CIERRA):
            elementos.append(self._parsear_expresion())
            while self.ver(TipoToken.COMA):
                self.avanzar()
                elementos.append(self._parsear_expresion())
        self.esperar(TipoToken.CORCHETE_CIERRA)
        return NodoLista(elementos=elementos, linea=linea)

    def _parsear_llamada_interna(self) -> NodoLlamada:
        tok = self.avanzar()
        self.esperar(TipoToken.PAREN_ABRE)
        args = self._parsear_args()
        self.esperar(TipoToken.PAREN_CIERRA)
        return NodoLlamada(nombre=tok.lexema, args=args, linea=tok.linea)

    def _parsear_identificador_o_llamada(self) -> NodoAST:
        tok    = self.avanzar()
        nodo   : NodoAST = NodoIdentificador(nombre=tok.lexema, linea=tok.linea)

        # Llamada a función: nombre(...)
        if self.ver(TipoToken.PAREN_ABRE):
            self.avanzar()
            args = self._parsear_args()
            self.esperar(TipoToken.PAREN_CIERRA)
            nodo = NodoLlamada(nombre=tok.lexema, args=args, linea=tok.linea)

        # Acceso a atributo: objeto.atributo o objeto.metodo(...)
        while self.ver(TipoToken.PUNTO):
            self.avanzar()
            attr = self.esperar(TipoToken.IDENTIFICADOR).lexema
            if self.ver(TipoToken.PAREN_ABRE):
                self.avanzar()
                args = self._parsear_args()
                self.esperar(TipoToken.PAREN_CIERRA)
                nodo = NodoLlamadaMetodo(objeto=nodo, metodo=attr, args=args, linea=tok.linea)
            else:
                nodo = NodoAccesoAtributo(objeto=nodo, atributo=attr, linea=tok.linea)

        return nodo

    def _parsear_args(self) -> List[NodoAST]:
        args: List[NodoAST] = []
        if self.ver(TipoToken.PAREN_CIERRA):
            return args
        args.append(self._parsear_expresion())
        while self.ver(TipoToken.COMA):
            self.avanzar()
            args.append(self._parsear_expresion())
        return args


# -----------------------------------------------------------------------------
#  IMPRESIÓN DEL AST
# -----------------------------------------------------------------------------

def imprimir_ast(nodo: NodoAST, indent: int = 0) -> None:
    prefijo = "  " * indent
    nombre  = type(nodo).__name__

    if isinstance(nodo, NodoPrograma):
        print(f"{prefijo}Programa")
        for hijo in nodo.cuerpo:
            imprimir_ast(hijo, indent + 1)

    elif isinstance(nodo, NodoFuncion):
        mods = f" [{', '.join(nodo.modificadores)}]" if nodo.modificadores else ""
        print(f"{prefijo}Funcion '{nodo.nombre}'{mods}  (L{nodo.linea})")
        for p in nodo.params:
            tipo_str = f": {p.tipo}" if p.tipo else ""
            print(f"{prefijo}  Param '{p.nombre}'{tipo_str}")
        for hijo in nodo.cuerpo:
            imprimir_ast(hijo, indent + 1)

    elif isinstance(nodo, NodoClase):
        print(f"{prefijo}Clase '{nodo.nombre}'  (L{nodo.linea})")
        for hijo in nodo.cuerpo:
            imprimir_ast(hijo, indent + 1)

    elif isinstance(nodo, NodoAsignacion):
        print(f"{prefijo}Asignacion '{nodo.nombre}'  (L{nodo.linea})")
        imprimir_ast(nodo.valor, indent + 1)

    elif isinstance(nodo, NodoRetorno):
        print(f"{prefijo}Retorno  (L{nodo.linea})")
        if nodo.valor:
            imprimir_ast(nodo.valor, indent + 1)

    elif isinstance(nodo, NodoIf):
        print(f"{prefijo}Si  (L{nodo.linea})")
        print(f"{prefijo}  Condicion:")
        imprimir_ast(nodo.condicion, indent + 2)
        print(f"{prefijo}  Entonces:")
        for hijo in nodo.cuerpo:
            imprimir_ast(hijo, indent + 2)
        if nodo.sino:
            print(f"{prefijo}  SiNo:")
            for hijo in nodo.sino:
                imprimir_ast(hijo, indent + 2)

    elif isinstance(nodo, NodoWhile):
        print(f"{prefijo}Mientras  (L{nodo.linea})")
        print(f"{prefijo}  Condicion:")
        imprimir_ast(nodo.condicion, indent + 2)
        print(f"{prefijo}  Cuerpo:")
        for hijo in nodo.cuerpo:
            imprimir_ast(hijo, indent + 2)

    elif isinstance(nodo, NodoFor):
        print(f"{prefijo}Para '{nodo.variable}' en  (L{nodo.linea})")
        imprimir_ast(nodo.iterable, indent + 1)
        print(f"{prefijo}  Cuerpo:")
        for hijo in nodo.cuerpo:
            imprimir_ast(hijo, indent + 2)

    elif isinstance(nodo, NodoBreak):
        print(f"{prefijo}Break  (L{nodo.linea})")

    elif isinstance(nodo, NodoContinua):
        print(f"{prefijo}Continua  (L{nodo.linea})")

    elif isinstance(nodo, NodoBinario):
        print(f"{prefijo}Binario '{nodo.operador}'  (L{nodo.linea})")
        imprimir_ast(nodo.izquierda, indent + 1)
        imprimir_ast(nodo.derecha,   indent + 1)

    elif isinstance(nodo, NodoUnario):
        print(f"{prefijo}Unario '{nodo.operador}'  (L{nodo.linea})")
        imprimir_ast(nodo.operando, indent + 1)

    elif isinstance(nodo, NodoLlamada):
        print(f"{prefijo}Llamada '{nodo.nombre}'  (L{nodo.linea})")
        for arg in nodo.args:
            imprimir_ast(arg, indent + 1)

    elif isinstance(nodo, NodoLlamadaMetodo):
        print(f"{prefijo}LlamadaMetodo '.{nodo.metodo}'  (L{nodo.linea})")
        print(f"{prefijo}  Objeto:")
        imprimir_ast(nodo.objeto, indent + 2)
        for arg in nodo.args:
            imprimir_ast(arg, indent + 1)

    elif isinstance(nodo, NodoAccesoAtributo):
        print(f"{prefijo}Atributo '{nodo.atributo}'  (L{nodo.linea})")
        imprimir_ast(nodo.objeto, indent + 1)

    elif isinstance(nodo, NodoIdentificador):
        print(f"{prefijo}Identificador '{nodo.nombre}'  (L{nodo.linea})")

    elif isinstance(nodo, NodoLiteral):
        print(f"{prefijo}Literal {nodo.tipo} = {nodo.valor!r}  (L{nodo.linea})")

    elif isinstance(nodo, NodoLista):
        print(f"{prefijo}Lista  (L{nodo.linea})")
        for elem in nodo.elementos:
            imprimir_ast(elem, indent + 1)

    else:
        print(f"{prefijo}{nombre}")
