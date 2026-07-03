from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional


# -----------------------------------------------------------------------------
#  SÍMBOLO
# -----------------------------------------------------------------------------

@dataclass
class Simbolo:
    nombre     : str
    categoria  : str              # 'variable' | 'parametro' | 'funcion' | 'clase'
    tipo       : Optional[str] = None
    linea      : int = 0
    num_params : Optional[int] = None   # solo aplica a categoria == 'funcion'


# -----------------------------------------------------------------------------
#  ÁMBITO (SCOPE)
# -----------------------------------------------------------------------------

class Ambito:
    """
    Representa un ámbito de visibilidad (global, función o clase).
    La resolución de nombres sube por la cadena de ámbitos padres,
    replicando el alcance léxico de Python.
    """

    def __init__(self, nombre: str, padre: Optional["Ambito"] = None):
        self.nombre   = nombre
        self.padre    = padre
        self.simbolos : Dict[str, Simbolo] = {}

    def declarar(self, simbolo: Simbolo) -> bool:
        """Registra un símbolo. Devuelve False si ya existía en ESTE ámbito."""
        ya_existia = simbolo.nombre in self.simbolos
        self.simbolos[simbolo.nombre] = simbolo
        return not ya_existia

    def existe_local(self, nombre: str) -> bool:
        return nombre in self.simbolos

    def resolver(self, nombre: str) -> Optional[Simbolo]:
        ambito: Optional[Ambito] = self
        while ambito is not None:
            if nombre in ambito.simbolos:
                return ambito.simbolos[nombre]
            ambito = ambito.padre
        return None


# -----------------------------------------------------------------------------
#  IMPRESIÓN DE LA TABLA DE SÍMBOLOS
# -----------------------------------------------------------------------------

def imprimir_tabla_simbolos(ambitos: List[Ambito]) -> None:
    ancho = 78
    print("\n" + "=" * ancho)
    print("  TABLA DE SÍMBOLOS")
    print("=" * ancho)

    for ambito in ambitos:
        print(f"\n  Ámbito: {ambito.nombre}")
        if not ambito.simbolos:
            print("    (vacío)")
            continue
        print(f"    {'NOMBRE':<18}{'CATEGORÍA':<14}{'TIPO':<12}{'LÍNEA':<8}")
        print(f"    {'-'*17} {'-'*13} {'-'*11} {'-'*7}")
        for simbolo in ambito.simbolos.values():
            tipo_str = simbolo.tipo or "-"
            print(f"    {simbolo.nombre:<18}{simbolo.categoria:<14}{tipo_str:<12}{simbolo.linea:<8}")

    print("\n" + "=" * ancho + "\n")
