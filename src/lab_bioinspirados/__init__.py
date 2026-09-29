"""Laboratorio docente de algoritmos bioinspirados (fase 1).

Desacoplo en tres capas:

- ``nucleo``: ABCs + tipos + errores + puertos + verificación (solo stdlib).
- ``problemas``: instancias concretas (Viajero/TSP cuadrado; único que puede usar numpy).
- ``solvers``: algoritmos (fuerza bruta; plantillas TODO para estudiantes).
- ``vistas``: presentación (consola / nula; nunca importan problemas ni solvers).
- ``ejemplos``: composition root que cablea todo (fuera del paquete).
"""

__version__ = "0.1.0"

from lab_bioinspirados.nucleo.errores import (
    ErrorBioinspirado,
    GeometriaNoDisponible,
    LoteInvalido,
    MatrizInvalida,
    OrdenInvalido,
    ParametroInvalido,
    PluginInvalido,
    PluginNoEncontrado,
    ProblemaDemasiadoGrande,
    SolverPendiente,
    VersionIncompatible,
)
from lab_bioinspirados.nucleo.problema import Problema
from lab_bioinspirados.nucleo.puertos import Geometria2D, Informe, Modelo, Vista, VistaViva
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import (
    LotePuntos,
    Param,
    Paso,
    Punto,
    Resultado,
    Solucion,
)
from lab_bioinspirados.problemas.viajero import TSPCuadrado, Viajero
from lab_bioinspirados.solvers.fuerza_bruta import ColoniaDeHormigas, FuerzaBruta
from lab_bioinspirados.vistas.consola import VistaConsola
from lab_bioinspirados.vistas.nula import VistaNula

__all__ = [
    "ColoniaDeHormigas",
    "ErrorBioinspirado",
    "FuerzaBruta",
    "Geometria2D",
    "GeometriaNoDisponible",
    "Informe",
    "LoteInvalido",
    "LotePuntos",
    "MatrizInvalida",
    "Modelo",
    "OrdenInvalido",
    "Param",
    "ParametroInvalido",
    "Paso",
    "PluginInvalido",
    "PluginNoEncontrado",
    "Problema",
    "ProblemaDemasiadoGrande",
    "Punto",
    "Resultado",
    "Solucion",
    "Solver",
    "SolverPendiente",
    "TSPCuadrado",
    "VersionIncompatible",
    "Viajero",
    "Vista",
    "VistaConsola",
    "VistaNula",
    "VistaViva",
    "__version__",
]
