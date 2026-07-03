import re
from dataclasses import dataclass
from typing import List, Optional


# -----------------------------------------------------------------------------
#  1. DEFINICIÓN DE TIPOS DE TOKEN
# -----------------------------------------------------------------------------

class TipoToken:
    # Palabras clave
    PALABRA_CLAVE       = "PALABRA_CLAVE"
    MODIFICADOR         = "MODIFICADOR"
    MODIFICADOR_ACCESO  = "MODIFICADOR_ACCESO"

    # Tipos de dato
    TIPO_DATO           = "TIPO_DATO"

    # Identificadores
    IDENTIFICADOR       = "IDENTIFICADOR"
    IDENTIFICADOR_CLASE = "IDENTIFICADOR_CLASE"

    # Funciones internas del lenguaje
    FUNCION_INTERNA     = "FUNCION_INTERNA"

    # Literales
    LITERAL_ENTERO      = "LITERAL_ENTERO"
    LITERAL_FLOTANTE    = "LITERAL_FLOTANTE"
    LITERAL_CADENA      = "LITERAL_CADENA"
    LITERAL_BOOL        = "LITERAL_BOOL"

    # Operadores
    OP_ASIGNACION       = "OP_ASIGNACION"
    OP_ARITMETICO       = "OP_ARITMETICO"
    OP_COMPARACION      = "OP_COMPARACION"
    OP_LOGICO           = "OP_LOGICO"

    # Delimitadores
    PAREN_ABRE          = "PAREN_ABRE"
    PAREN_CIERRA        = "PAREN_CIERRA"
    CORCHETE_ABRE       = "CORCHETE_ABRE"
    CORCHETE_CIERRA     = "CORCHETE_CIERRA"
    DOS_PUNTOS          = "DOS_PUNTOS"
    COMA                = "COMA"
    PUNTO               = "PUNTO"

    # Indentación (inyectados por IndentProcessor)
    INDENT              = "INDENT"
    DEDENT              = "DEDENT"

    # Especiales
    FIN_DE_LINEA        = "FIN_DE_LINEA"
    FIN_DE_ARCHIVO      = "FIN_DE_ARCHIVO"
    ERROR               = "ERROR"


# -----------------------------------------------------------------------------
#  2. DICCIONARIOS DE PALABRAS RESERVADAS
# -----------------------------------------------------------------------------

PALABRAS_CLAVE = {
    # Control de flujo
    "ari_chayqa"  : TipoToken.PALABRA_CLAVE,   # if
    "mana_chayqa" : TipoToken.PALABRA_CLAVE,   # else
    "micha"       : TipoToken.PALABRA_CLAVE,   # while
    "tupaq"       : TipoToken.PALABRA_CLAVE,   # for
    "kutichiy"    : TipoToken.PALABRA_CLAVE,   # return
    "ruway"       : TipoToken.PALABRA_CLAVE,   # def (función)
    "ayllu"       : TipoToken.PALABRA_CLAVE,   # class
    "tanqay"      : TipoToken.PALABRA_CLAVE,   # import
    "ukhupi"      : TipoToken.PALABRA_CLAVE,   # in (dentro de)
    "usqhaychiy"  : TipoToken.PALABRA_CLAVE,   # break
    "katiy"       : TipoToken.PALABRA_CLAVE,   # continue
    "mana"        : TipoToken.PALABRA_CLAVE,   # not

    # Modificadores
    "sayk_uq"     : TipoToken.MODIFICADOR,     # static
    "ch_usaq"     : TipoToken.MODIFICADOR,     # void
    "sapaq"       : TipoToken.MODIFICADOR_ACCESO,  # public

    # Tipos de dato
    "yupay"       : TipoToken.TIPO_DATO,       # int
    "chiqchi"     : TipoToken.TIPO_DATO,       # float
    "simi"        : TipoToken.TIPO_DATO,       # string
    "cheqaq"      : TipoToken.LITERAL_BOOL,    # True
    "llulla"      : TipoToken.LITERAL_BOOL,    # False

    # Funciones internas
    "qillqay"     : TipoToken.FUNCION_INTERNA, # print
    "ranka"       : TipoToken.FUNCION_INTERNA, # range()
    "tapuy"       : TipoToken.FUNCION_INTERNA, # input
    "yupaypi"     : TipoToken.FUNCION_INTERNA, # int() cast
    "simipi"      : TipoToken.FUNCION_INTERNA, # str() cast
    "ratu"        : TipoToken.FUNCION_INTERNA, # len()
}

OPERADORES_ARITMETICOS = {'+', '-', '*', '/', '%', '**', '//'}
OPERADORES_COMPARACION = {'==', '!=', '<=', '>=', '<', '>'}
OPERADORES_LOGICOS     = {'&&', '||'}


# -----------------------------------------------------------------------------
#  3. ESTRUCTURA DE UN TOKEN
# -----------------------------------------------------------------------------

@dataclass
class Token:
    tipo    : str
    lexema  : str
    linea   : int
    columna : int

    def __repr__(self):
        return f"Token({self.tipo}, '{self.lexema}', L{self.linea}:C{self.columna})"


# -----------------------------------------------------------------------------
#  4. DEFINICIÓN DE PATRONES (AFD mediante expresiones regulares)
# -----------------------------------------------------------------------------

PATRONES = [
    # Comentarios (se ignoran)
    ("COMENTARIO",      r'@[^\n]*'),

    # Literales de cadena
    (TipoToken.LITERAL_CADENA,   r'"[^"]*"|\'[^\']*\''),

    # Literales numéricos
    (TipoToken.LITERAL_FLOTANTE, r'\d+\.\d+'),
    (TipoToken.LITERAL_ENTERO,   r'\d+'),

    # Operadores de comparación (deben ir antes que los aritméticos)
    (TipoToken.OP_COMPARACION,   r'==|!=|<=|>=|<|>'),

    # Operadores aritméticos
    (TipoToken.OP_ARITMETICO,    r'\*\*|//|[+\-*/%]'),

    # Operadores lógicos
    (TipoToken.OP_LOGICO,        r'&&|\|\|'),

    # Operador de asignación
    (TipoToken.OP_ASIGNACION,    r'='),

    # Delimitadores
    (TipoToken.PAREN_ABRE,       r'\('),
    (TipoToken.PAREN_CIERRA,     r'\)'),
    (TipoToken.CORCHETE_ABRE,    r'\['),
    (TipoToken.CORCHETE_CIERRA,  r'\]'),
    (TipoToken.DOS_PUNTOS,       r':'),
    (TipoToken.COMA,             r','),
    (TipoToken.PUNTO,            r'\.'),

    # Identificadores y palabras clave (incluye caracteres especiales del quechua)
    ("PALABRA_O_ID",             r"[a-zA-ZñÑáéíóúÁÉÍÓÚüÜ_][a-zA-ZñÑáéíóúÁÉÍÓÚüÜ0-9_']*"),

    # Espacios en blanco (se ignoran)
    ("ESPACIO",                  r'[ \t]+'),

    # Nueva línea
    (TipoToken.FIN_DE_LINEA,     r'\n'),
]

# Compilar todos los patrones en un único regex con grupos nombrados
REGEX_MAESTRO = re.compile(
    '|'.join(f'(?P<PAT{i}>{patron})' for i, (_, patron) in enumerate(PATRONES))
)


# -----------------------------------------------------------------------------
#  5. CLASE PRINCIPAL: ANALIZADOR LÉXICO
# -----------------------------------------------------------------------------

class LexerQuechua:
    """
    Analizador léxico para el lenguaje de programación Quechua.
    Lee el código fuente y genera una lista de tokens clasificados.
    Los errores léxicos se reportan y el análisis continúa.
    """

    def __init__(self, codigo_fuente: str):
        self.codigo   = codigo_fuente
        self.tokens   : List[Token] = []
        self.errores  : List[str]   = []
        self.linea    = 1
        self.col_ini  = 0  # posición donde empieza la línea actual

    def _clasificar_palabra(self, lexema: str, linea: int, columna: int) -> Token:
        """Determina si una palabra es reservada o un identificador."""
        if lexema in PALABRAS_CLAVE:
            return Token(PALABRAS_CLAVE[lexema], lexema, linea, columna)

        # Identificador de clase: empieza con mayúscula
        if lexema[0].isupper():
            return Token(TipoToken.IDENTIFICADOR_CLASE, lexema, linea, columna)

        # Identificador normal
        return Token(TipoToken.IDENTIFICADOR, lexema, linea, columna)

    def analizar(self) -> List[Token]:
        """Ejecuta el análisis léxico y retorna la lista de tokens."""
        pos = 0
        n   = len(self.codigo)

        while pos < n:
            match = REGEX_MAESTRO.match(self.codigo, pos)

            if not match:
                # Carácter no reconocido → ERROR léxico, continúa
                caracter = self.codigo[pos]
                columna  = pos - self.col_ini + 1
                self.errores.append(
                    f"  [Error léxico] Carácter no reconocido '{caracter}' "
                    f"en línea {self.linea}, columna {columna}"
                )
                self.tokens.append(Token(TipoToken.ERROR, caracter, self.linea, columna))
                pos += 1
                continue

            # Identificar cuál grupo coincidió
            grupo_idx = next(
                i for i, g in enumerate(match.groups()) if g is not None
            )
            tipo_raw, _ = PATRONES[grupo_idx]
            lexema       = match.group()
            columna      = match.start() - self.col_ini + 1

            if tipo_raw == "COMENTARIO" or tipo_raw == "ESPACIO":
                # Ignorar comentarios y espacios
                pass

            elif tipo_raw == TipoToken.FIN_DE_LINEA:
                self.tokens.append(Token(TipoToken.FIN_DE_LINEA, '\n', self.linea, columna))
                self.linea   += 1
                self.col_ini  = match.end()

            elif tipo_raw == "PALABRA_O_ID":
                token = self._clasificar_palabra(lexema, self.linea, columna)
                self.tokens.append(token)

            else:
                self.tokens.append(Token(tipo_raw, lexema, self.linea, columna))

            pos = match.end()

        # Token de fin de archivo
        self.tokens.append(Token(TipoToken.FIN_DE_ARCHIVO, "EOF", self.linea, 0))
        return self.tokens


# -----------------------------------------------------------------------------
#  6. SALIDA: TABLA COMPLETA DE TOKENS
# -----------------------------------------------------------------------------

def imprimir_tabla(tokens: List[Token], errores: List[str]) -> None:
    """Imprime la tabla de tokens con tipo, lexema, línea y columna."""

    col_tipo   = max(len(t.tipo)   for t in tokens) + 2
    col_lexema = max(len(t.lexema) for t in tokens) + 2
    col_linea  = 8
    col_col    = 8

    ancho_total = col_tipo + col_lexema + col_linea + col_col + 7

    separador = "+" + "-"*col_tipo + "+" + "-"*col_lexema + "+" + "-"*col_linea + "+" + "-"*col_col + "+"
    encabezado = (
        f"| {'TIPO DE TOKEN':<{col_tipo-1}}"
        f"| {'LEXEMA':<{col_lexema-1}}"
        f"| {'LÍNEA':<{col_linea-1}}"
        f"| {'COLUMNA':<{col_col-1}}|"
    )

    print("\n" + "="*ancho_total)
    print("  ANALIZADOR LÉXICO — LENGUAJE QUECHUA")
    print("="*ancho_total)
    print(separador)
    print(encabezado)
    print(separador)

    for token in tokens:
        fila = (
            f"| {token.tipo:<{col_tipo-1}}"
            f"| {token.lexema:<{col_lexema-1}}"
            f"| {token.linea:<{col_linea-1}}"
            f"| {token.columna:<{col_col-1}}|"
        )
        print(fila)

    print(separador)
    print(f"\n  Total de tokens: {len(tokens)}")

    # Resumen por tipo
    print("\n" + "="*ancho_total)
    print("  RESUMEN POR TIPO DE TOKEN")
    print("="*ancho_total)

    conteo = {}
    for t in tokens:
        conteo[t.tipo] = conteo.get(t.tipo, 0) + 1

    for tipo, cantidad in sorted(conteo.items()):
        print(f"  {tipo:<30} : {cantidad}")

    # Errores léxicos
    if errores:
        print("\n" + "="*ancho_total)
        print("  ERRORES LÉXICOS ENCONTRADOS")
        print("="*ancho_total)
        for error in errores:
            print(error)
    else:
        print("\n  ✓ Sin errores léxicos.")

    print("="*ancho_total + "\n")
