# 🏔️ Compilador PyChua

**PyChua** es un lenguaje de programación educativo con sintaxis inspirada en Python y palabras clave en **quechua**. Este proyecto implementa las fases de análisis de un compilador/transpilador: **léxico**, **sintáctico** y **semántico**, escritas completamente en Python.

## 📋 Descripción

PyChua permite escribir programas usando vocabulario quechua, con una estructura basada en indentación (al estilo de Python). El compilador procesa el código fuente en cuatro etapas:

1. **Analizador léxico** (`LexerQuechua`): convierte el código fuente en una lista de tokens clasificados (palabras clave, identificadores, literales, operadores, delimitadores), reportando los errores léxicos sin detener el análisis.
2. **Procesador de indentación** (`IndentProcessor`): inyecta tokens `INDENT`/`DEDENT` en el flujo de tokens, usando el mismo algoritmo que el tokenizador de Python (pila de niveles de indentación).
3. **Analizador sintáctico** (`Parser`): parser descendente recursivo que construye el **Árbol de Sintaxis Abstracta (AST)** a partir de los tokens, con reporte de errores sintácticos con línea y columna.
4. **Analizador semántico** (`AnalizadorSemantico`): recorre el AST con una tabla de símbolos por ámbitos (global / función / clase) y valida lo que la gramática no puede atrapar: variables no declaradas, funciones o clases redeclaradas, aridad de llamadas, uso de `kutichiy`/`usqhaychiy`/`katiy` fuera de contexto y compatibilidad básica de tipos en operaciones.

> Como PyChua es un **transpilador** (su destino final es código Python, no código máquina), no necesita las fases clásicas de generación de código intermedio ni de optimización propias de un compilador tradicional: el propio AST cumple el rol de representación intermedia, y la optimización queda delegada al intérprete de Python. La última fase pendiente es la **generación de código** (AST → texto Python).

## 🗣️ Palabras clave del lenguaje

| Quechua | Equivalente | Descripción |
|---|---|---|
| `ruway` | `def` | Definición de función |
| `ayllu` | `class` | Definición de clase |
| `ari_chayqa` | `if` | Condicional |
| `mana_chayqa` | `else` | Alternativa del condicional |
| `micha` | `while` | Bucle mientras |
| `tupaq` | `for` | Bucle para |
| `ukhupi` | `in` | Pertenencia (dentro de) |
| `kutichiy` | `return` | Retorno de función |
| `usqhaychiy` | `break` | Romper bucle |
| `katiy` | `continue` | Continuar bucle |
| `tanqay` | `import` | Importación |
| `mana` | `not` | Negación lógica |

### Tipos de dato y literales

| Quechua | Equivalente |
|---|---|
| `yupay` | `int` |
| `chiqchi` | `float` |
| `simi` | `string` |
| `cheqaq` | `True` |
| `llulla` | `False` |

### Funciones internas

| Quechua | Equivalente |
|---|---|
| `qillqay` | `print()` |
| `tapuy` | `input()` |
| `ranka` | `range()` |
| `yupaypi` | `int()` (conversión) |
| `simipi` | `str()` (conversión) |
| `ratu` | `len()` |

### Modificadores

| Quechua | Equivalente |
|---|---|
| `sapaq` | `public` |
| `sayk_uq` | `static` |
| `ch_usaq` | `void` |

Los comentarios se escriben con `@` al inicio de la línea.

## ✨ Ejemplo de código

```text
@ Función que suma dos números
ruway sumar(a, b):
    resultado = a + b
    kutichiy resultado

@ Función con condicional
ruway maximo(a, b):
    ari_chayqa (a > b):
        kutichiy a
    mana_chayqa:
        kutichiy b

@ Función con bucle for
ruway mostrar_rango(n):
    tupaq x ukhupi ranka(n):
        qillqay(x)

@ Programa principal
resultado = sumar(5, 3)
qillqay(resultado)
qillqay(maximo(10, 20))
```

## 📐 Gramática (simplificada)

```text
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
```

## 📁 Estructura del proyecto

```text
COMPILADOR PYCHUA/
├── f1_analizador_lexico/
│   ├── analizador_lexico.py    # Lexer: tokens, patrones (regex) y tabla de salida
│   ├── indent_processor.py     # Inyección de tokens INDENT/DEDENT
│   └── analizador_lexico.md    # Documentación del analizador léxico
├── f2_analizador_sintactico/
│   ├── parser.py               # Parser descendente recursivo (construye el AST)
│   └── nodos.py                # Definición de los nodos del AST
├── f3_analizador_semantico/
│   ├── analizador_semantico.py # Recorrido del AST: validaciones semánticas
│   └── tabla_simbolos.py       # Símbolo y Ámbito (tabla de símbolos por scopes)
├── src/
│   ├── ejemplo.txt             # Programas de ejemplo en PyChua
│   ├── ejemplo2.txt
│   ├── ejemploAlexis.txt
│   └── melany.txt
├── compilador_pychua.ipynb     # Notebook para ejecutar el compilador completo
└── README.md
```

## 🚀 Uso

### Requisitos

- Python 3.10 o superior (solo usa la biblioteca estándar, sin dependencias externas)
- Jupyter Notebook (opcional, para usar el notebook interactivo)

### Desde el notebook

Abre [compilador_pychua.ipynb](compilador_pychua.ipynb) en Jupyter o VS Code y ejecuta las celdas para analizar cualquiera de los ejemplos de `src/`.

### Desde Python

```python
from f1_analizador_lexico.analizador_lexico import LexerQuechua, imprimir_tabla
from f1_analizador_lexico.indent_processor import IndentProcessor
from f2_analizador_sintactico.parser import Parser
from f3_analizador_semantico.analizador_semantico import AnalizadorSemantico, imprimir_resultado_semantico

with open("src/ejemplo.txt", encoding="utf-8") as f:
    codigo = f.read()

# 1. Análisis léxico
lexer  = LexerQuechua(codigo)
tokens = lexer.analizar()
imprimir_tabla(tokens, lexer.errores)

# 2. Procesamiento de indentación
tokens = IndentProcessor(tokens).procesar()

# 3. Análisis sintáctico → AST
parser = Parser(tokens)
ast = parser.parsear()

# 4. Análisis semántico
analizador = AnalizadorSemantico()
errores_semanticos = analizador.analizar(ast)
imprimir_resultado_semantico(errores_semanticos)
```

## 🛠️ Detalles de implementación

- **Lexer**: basado en un regex maestro compilado a partir de una tabla de patrones ordenada por prioridad (equivalente a un AFD). Soporta caracteres del quechua/español (`ñ`, tildes, `'`) en los identificadores.
- **Manejo de errores**: los errores léxicos, sintácticos y semánticos se acumulan con su línea (y columna cuando aplica), permitiendo reportar múltiples errores en una sola pasada.
- **Identificadores de clase**: se distinguen automáticamente porque inician con mayúscula.
- **Analizador semántico**: usa una tabla de símbolos con un ámbito global y un ámbito por función/clase (sin anidamiento, ya que la gramática actual no permite `ruway` dentro de otro `ruway`/`ayllu`). Infiere tipos básicos (`yupay`, `chiqchi`, `simi`, `bool`, `lista`) de forma conservadora: solo reporta incompatibilidades cuando ambos operandos tienen un tipo conocido. Como el parser reutiliza `NodoLlamada` tanto para `foo(x)` como para `objeto.foo(x)` sin distinguirlas, la validación de existencia/aridad de una llamada solo se aplica cuando el nombre coincide con una función o clase global conocida; el resto se asume como posible llamada a método dinámico y no se marca como error.

## 📚 Contexto académico

Proyecto desarrollado para el curso de **Compiladores**, como ejercicio práctico de construcción de las fases de análisis de un compilador, con el valor agregado de promover el quechua en la programación.

## 📄 Licencia

Este proyecto es de uso educativo y libre.
