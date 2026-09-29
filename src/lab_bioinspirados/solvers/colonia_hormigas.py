"""Colonia de hormigas ACO (plantilla TODO para estudiantes).

Contrato a usar:
- Desempate ``<`` estricto al actualizar la mejor (primero gana).
- Throttling: ``cada_n_pasos`` evaluaciones entre ``Paso``.
- Presupuestos: ``iteraciones`` × ``hormigas`` acota evaluaciones;
  ``presupuesto_evaluaciones`` corta antes (``agotado=False``).
- Parámetros ACO: ``hormigas``, ``alfa`` (feromona), ``beta`` (heurística),
  ``evaporacion`` en [0, 1].
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class ColoniaHormigas(Solver):
    """TODO estudiantes: ACO con matriz de feromonas + regla proporcional."""

    NOMBRE: ClassVar[str] = "colonia-hormigas"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite; >0 corta tras N evaluaciones (agotado=False).",
        ),
        Param("hormigas", 10, "Hormigas por iteración."),
        Param("alfa", 1.0, "Peso de la feromona."),
        Param("beta", 2.0, "Peso de la heurística (1/distancia)."),
        Param("evaporacion", 0.5, "Tasa de evaporación en [0, 1]."),
        Param("iteraciones", 100, "Iteraciones de la colonia."),
    )
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        if nombre in ("cada_n_pasos", "hormigas", "iteraciones") and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ParametroInvalido(f"{nombre} debe ser int >= 1", detalles={"valor": valor})
        if nombre == "presupuesto_evaluaciones" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_evaluaciones debe ser int >= 0", detalles={"valor": valor}
            )
        if nombre in ("alfa", "beta") and (
            isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor < 0
        ):
            raise ParametroInvalido(f"{nombre} debe ser número >= 0", detalles={"valor": valor})
        if nombre == "evaporacion" and (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not 0 <= valor <= 1
        ):
            raise ParametroInvalido("evaporacion debe estar en [0, 1]", detalles={"valor": valor})

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente(
            "ColoniaHormigas pendiente. TODO: "
            "1) feromonas uniformes; "
            "2) cada hormiga construye tour con p ~ feromona^alfa * heuristica^beta; "
            "3) evalúa con problema.costo y quédate el primer < (estricto); "
            "4) evapora y refuerza la mejor; throttling cada_n_pasos; "
            "5) devuelve (Solucion, evaluaciones, agotado, pasos)."
        )
