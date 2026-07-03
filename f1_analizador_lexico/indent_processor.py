import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List
from f1_analizador_lexico.analizador_lexico import Token, TipoToken


class IndentProcessor:
    """
    Post-procesa el flujo de tokens del lexer e inyecta tokens INDENT/DEDENT
    basándose en la columna del primer token de cada línea.

    Algoritmo (equivalente al tokenizador de Python):
      - Mantiene una pila de niveles de indentación, iniciando en [0].
      - Tras cada FIN_DE_LINEA, el primer token no-vacío de la siguiente línea
        define el nivel de indentación actual (columna - 1).
      - Si sube  → emite INDENT y empuja el nivel.
      - Si baja  → emite DEDENT(s) hasta igualar el nivel en la pila.
      - Si no coincide exactamente → error de indentación.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens  = tokens
        self.errores : List[str] = []

    def procesar(self) -> List[Token]:
        resultado   : List[Token] = []
        pila        : List[int]   = [0]
        prev_newline               = True   # inicio de archivo = tras newline implícito

        i = 0
        n = len(self.tokens)

        while i < n:
            tok = self.tokens[i]

            # FIN_DE_ARCHIVO: cerrar todos los bloques abiertos
            if tok.tipo == TipoToken.FIN_DE_ARCHIVO:
                while len(pila) > 1:
                    pila.pop()
                    resultado.append(Token(TipoToken.DEDENT, 'DEDENT', tok.linea, tok.columna))
                resultado.append(tok)
                i += 1
                continue

            # FIN_DE_LINEA: marcar que la próxima línea real inicia bloque candidato
            if tok.tipo == TipoToken.FIN_DE_LINEA:
                # Emitir solo si hay contenido antes en la línea actual
                if resultado and resultado[-1].tipo not in (
                    TipoToken.FIN_DE_LINEA, TipoToken.INDENT, TipoToken.DEDENT
                ):
                    resultado.append(tok)
                prev_newline = True
                i += 1
                continue

            # Primer token real tras un salto de línea → calcular indentación
            if prev_newline:
                nivel = tok.columna - 1

                if nivel > pila[-1]:
                    pila.append(nivel)
                    resultado.append(Token(TipoToken.INDENT, 'INDENT', tok.linea, 1))

                elif nivel < pila[-1]:
                    while len(pila) > 1 and nivel < pila[-1]:
                        pila.pop()
                        resultado.append(Token(TipoToken.DEDENT, 'DEDENT', tok.linea, 1))
                    if nivel != pila[-1]:
                        self.errores.append(
                            f"  [Error de indentación] Nivel {nivel} no coincide con "
                            f"ningún bloque previo en línea {tok.linea}"
                        )

                prev_newline = False

            resultado.append(tok)
            i += 1

        return resultado
