# Documentación del Analizador Léxico — PyChua

PyChua es un lenguaje de programación con sintaxis inspirada en Python, cuyos elementos reservados están escritos en **quechua**. Mantiene la indentación como delimitador de bloques y no requiere punto y coma ni llaves.

---

## Ejemplo comparativo

### Python
```python
def sumar(a, b):
    resultado = a + b
    return resultado

print(sumar(5, 3))
```

### PyChua
```pychua
ruway huñuy(a, b):
    resultado = a + b
    kutichiy resultado

qillqay(huñuy(5, 3))
```

---

## Diccionario de traducción completo

### Palabras clave — control de flujo

| Python      | PyChua        | Significado literal en quechua | Tipo de token |
|-------------|---------------|-------------------------------|---------------|
| `if`        | `ari_chayqa`  | "si es así"                   | `PALABRA_CLAVE` |
| `else`      | `mana_chayqa` | "si no es así"                | `PALABRA_CLAVE` |
| `while`     | `micha`       | "mientras / hasta"            | `PALABRA_CLAVE` |
| `for`       | `tupaq`       | "para (iteración)"            | `PALABRA_CLAVE` |
| `in`        | `ukhupi`      | "dentro de"                   | `PALABRA_CLAVE` |
| `return`    | `kutichiy`    | "devolver / regresar"         | `PALABRA_CLAVE` |
| `def`       | `ruway`       | "hacer / función"             | `PALABRA_CLAVE` |
| `break`     | `usqhaychiy`  | "interrumpir"                 | `PALABRA_CLAVE` |
| `continue`  | `katiy`       | "continuar"                   | `PALABRA_CLAVE` |
| `not`       | `mana`        | "no / negación"               | `PALABRA_CLAVE` |

### Tipos de dato

| Python   | PyChua    | Significado literal      | Tipo de token |
|----------|-----------|--------------------------|---------------|
| `int`    | `yupay`   | "número"                 | `TIPO_DATO`   |
| `float`  | `chiqchi` | "decimal / fracción"     | `TIPO_DATO`   |
| `string` | `simi`    | "palabra / lenguaje"     | `TIPO_DATO`   |

### Literales booleanos

| Python  | PyChua   | Significado literal | Tipo de token   |
|---------|----------|---------------------|-----------------|
| `True`  | `cheqaq` | "verdad / verdadero"| `LITERAL_BOOL`  |
| `False` | `llulla` | "mentira / falso"   | `LITERAL_BOOL`  |

### Funciones internas (built-ins)

| Python   | PyChua    | Significado literal       | Tipo de token     |
|----------|-----------|---------------------------|-------------------|
| `print`  | `qillqay` | "escribir / mostrar"      | `FUNCION_INTERNA` |
| `range`  | `ranka`   | "rango / serie"           | `FUNCION_INTERNA` |
| `input`  | `tapuy`   | "preguntar / pedir"       | `FUNCION_INTERNA` |
| `int()`  | `yupaypi` | "convertir a número"      | `FUNCION_INTERNA` |
| `str()`  | `simipi`  | "convertir a palabra"     | `FUNCION_INTERNA` |
| `len()`  | `ratu`    | "cantidad / longitud"     | `FUNCION_INTERNA` |

### Operadores

| Python       | PyChua       | Descripción                  | Tipo de token    |
|--------------|--------------|------------------------------|------------------|
| `=`          | `=`          | Asignación                   | `OP_ASIGNACION`  |
| `+`          | `+`          | Suma                         | `OP_ARITMETICO`  |
| `-`          | `-`          | Resta                        | `OP_ARITMETICO`  |
| `*`          | `*`          | Multiplicación               | `OP_ARITMETICO`  |
| `/`          | `/`          | División                     | `OP_ARITMETICO`  |
| `%`          | `%`          | Módulo                       | `OP_ARITMETICO`  |
| `**`         | `**`         | Potencia                     | `OP_ARITMETICO`  |
| `//`         | `//`         | División entera              | `OP_ARITMETICO`  |
| `==`         | `==`         | Igualdad                     | `OP_COMPARACION` |
| `!=`         | `!=`         | Desigualdad                  | `OP_COMPARACION` |
| `<`          | `<`          | Menor que                    | `OP_COMPARACION` |
| `>`          | `>`          | Mayor que                    | `OP_COMPARACION` |
| `<=`         | `<=`         | Menor o igual                | `OP_COMPARACION` |
| `>=`         | `>=`         | Mayor o igual                | `OP_COMPARACION` |
| `and`        | `&&`         | Y lógico                     | `OP_LOGICO`      |
| `or`         | `\|\|`       | O lógico                     | `OP_LOGICO`      |

> **Nota:** PyChua usa `&&` y `||` en lugar de `and`/`or` de Python.

### Delimitadores y signos de puntuación

| Símbolo | Descripción          | Tipo de token    |
|---------|----------------------|------------------|
| `(`     | Paréntesis abre      | `PAREN_ABRE`     |
| `)`     | Paréntesis cierra    | `PAREN_CIERRA`   |
| `[`     | Corchete abre        | `CORCHETE_ABRE`  |
| `]`     | Corchete cierra      | `CORCHETE_CIERRA`|
| `:`     | Dos puntos           | `DOS_PUNTOS`     |
| `,`     | Coma                 | `COMA`           |

### Literales y identificadores

| Categoría              | Ejemplos                  | Tipo de token         |
|------------------------|---------------------------|-----------------------|
| Número entero          | `0`, `42`, `100`          | `LITERAL_ENTERO`      |
| Número flotante        | `3.14`, `0.5`             | `LITERAL_FLOTANTE`    |
| Cadena de texto        | `"hola"`, `'mundo'`       | `LITERAL_CADENA`      |
| Nombre de variable     | `resultado`, `i`, `nombre`| `IDENTIFICADOR`       |

### Tokens especiales (generados por el procesador)

| Token          | Descripción                                              |
|----------------|----------------------------------------------------------|
| `INDENT`       | Inicio de bloque (aumento de indentación)                |
| `DEDENT`       | Fin de bloque (disminución de indentación)               |
| `FIN_DE_LINEA` | Salto de línea significativo                             |
| `FIN_DE_ARCHIVO` | Fin del archivo fuente                                 |
| `ERROR`        | Carácter o secuencia no reconocida por el léxico         |

---

## Ejemplos de programas completos

### Condicional (`if` / `else`)

```pychua
ruway maximo(a, b):
    ari_chayqa (a > b):
        kutichiy a
    mana_chayqa:
        kutichiy b
```

```python
def maximo(a, b):
    if a > b:
        return a
    else:
        return b
```

### Bucle `while`

```pychua
ruway contador(n):
    i = 0
    micha (i < n):
        qillqay(i)
        i = i + 1
```

```python
def contador(n):
    i = 0
    while i < n:
        print(i)
        i = i + 1
```

### Bucle `for`

```pychua
ruway mostrar_rango(n):
    tupaq x ukhupi ranka(n):
        qillqay(x)
```

```python
def mostrar_rango(n):
    for x in range(n):
        print(x)
```

### Entrada del usuario y conversión de tipos

```pychua
nombre = tapuy("¿Cómo te llamas? ")
edad   = yupaypi(tapuy("¿Cuántos años tienes? "))
qillqay("Hola " + simipi(nombre) + ", tienes " + simipi(edad) + " años.")
```

```python
nombre = input("¿Cómo te llamas? ")
edad   = int(input("¿Cuántos años tienes? "))
print("Hola " + str(nombre) + ", tienes " + str(edad) + " años.")
```

---
