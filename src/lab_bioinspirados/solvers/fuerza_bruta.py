"""Fuerza bruta (único solver exacto de fase 1) + plantilla TODO de hormigas."""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.solver import Solver
from lab_bioinspirados.nucleo.tipos import Param, Paso, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class FuerzaBruta(Solver):
    """Recorre ``enumerar()`` UNA vez (streaming lazy, sin lista).

    Se queda el primer menor (``<`` estricto). Emite ``Paso`` throttled por
    ``cada_n_pasos`` Y ``cada_n_ms``; respeta ``presupuesto_evaluaciones``
    (0 = sin limite) y ``presupuesto_segundos`` (0 = sin limite); corta
    limpio (``agotado=False`` + ``motivo_corte``) si el observador devuelve
    truthy o si se llama ``solicitar_corte``.
    """

    NOMBRE: ClassVar[str] = "fuerza-bruta"
    PENDIENTE: ClassVar[bool] = False
    REQUIERE_ENUMERACION: ClassVar[bool] = True
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param(
            "cada_n_pasos",
            1000,
            "Emite un Paso al observador cada N evaluaciones.",
        ),
        Param(
            "cada_n_ms",
            100,
            "Emite un Paso si pasaron N ms desde el anterior (viveza en n grande).",
        ),
        Param(
            "presupuesto_evaluaciones",
            0,
            "0 = sin límite (agota la enumeración); >0 corta tras N evaluaciones.",
        ),
        Param(
            "presupuesto_segundos",
            0,
            "0 = sin límite; >0 corta tras N segundos (agotado=False).",
        ),
    )

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        if nombre == "cada_n_pasos" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ParametroInvalido("cada_n_pasos debe ser int >= 1", detalles={"valor": valor})
        if nombre == "cada_n_ms" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 1
        ):
            raise ParametroInvalido("cada_n_ms debe ser int >= 1", detalles={"valor": valor})
        if nombre == "presupuesto_evaluaciones" and (
            isinstance(valor, bool) or not isinstance(valor, int) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_evaluaciones debe ser int >= 0", detalles={"valor": valor}
            )
        if nombre == "presupuesto_segundos" and (
            isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor < 0
        ):
            raise ParametroInvalido(
                "presupuesto_segundos debe ser número >= 0", detalles={"valor": valor}
            )

    def _emitir(
        self, pasos: int, evaluaciones: int, mejor_orden: tuple[int, ...], mejor_costo: float
    ) -> tuple[int, bool]:
        """Emite un Paso; devuelve ``(pasos, detener)`` según el observador."""
        pasos += 1
        detener = self._notificar(
            Paso(
                numero=pasos,
                evaluaciones=evaluaciones,
                mejor=Solucion(orden=mejor_orden, costo=mejor_costo),
            )
        )
        return pasos, detener

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        cada = self._params["cada_n_pasos"]
        cada_ms = self._params["cada_n_ms"] / 1000.0
        presupuesto = self._params["presupuesto_evaluaciones"]
        limite_s = self._params["presupuesto_segundos"]
        inicio = perf_counter()
        ultimo_emit = inicio
        mejor_orden: tuple[int, ...] | None = None
        mejor_costo = float("inf")
        evaluaciones = 0
        pasos = 0
        agotado = True
        for orden in problema.enumerar():  # UNA pasada, sin lista: O(1) memoria
            costo = problema.costo(orden)
            evaluaciones += 1
            if costo < mejor_costo:  # estricto: el primero gana
                mejor_orden = tuple(orden)
                mejor_costo = costo
            detener = False
            if evaluaciones % cada == 0:
                ultimo_emit = perf_counter()
                pasos, detener = self._emitir(pasos, evaluaciones, mejor_orden, mejor_costo)
            elif (evaluaciones & 127) == 0:
                # Viveza por tiempo entre umbrales de conteo (chequeo barato).
                ahora = perf_counter()
                if ahora - ultimo_emit >= cada_ms and self._observador is not None:
                    ultimo_emit = ahora
                    pasos, detener = self._emitir(pasos, evaluaciones, mejor_orden, mejor_costo)
            if detener:
                self._motivo_corte = "corte solicitado por el observador"
                agotado = False
                break
            motivo_externo = self._hay_corte()
            if motivo_externo:
                self._motivo_corte = motivo_externo
                agotado = False
                break
            if presupuesto > 0 and evaluaciones >= presupuesto:
                self._motivo_corte = f"presupuesto_evaluaciones={presupuesto}"
                agotado = False
                break
            if limite_s > 0 and (evaluaciones & 127) == 0 and perf_counter() - inicio >= limite_s:
                self._motivo_corte = f"presupuesto_segundos={limite_s}"
                agotado = False
                break
        assert mejor_orden is not None, "enumerar() vacío en problema resoluble"
        return Solucion(orden=mejor_orden, costo=mejor_costo), evaluaciones, agotado, pasos


class ColoniaDeHormigas(Solver):
    """TODO estudiantes: metaheurística de colonias de hormigas (ejemplo de plantilla).

    Pasos sugeridos:
    1. ``PENDIENTE = False`` al terminar.
    2. Añadir Params (n_hormigas, alfa, beta, evaporacion, iteraciones...).
    3. ``REQUIERE_ENUMERACION = False`` (muestrea, no enumera).
    4. Implementar ``_resolver`` con desempate ``<`` y throttling ``cada_n_pasos``.
    """

    NOMBRE: ClassVar[str] = "colonia-hormigas"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = (
        Param("cada_n_pasos", 1000, "Emite un Paso al observador cada N evaluaciones."),
        # TODO: añadir n_hormigas, alfa, beta, evaporacion, iteraciones...
    )

    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        raise SolverPendiente("ColoniaDeHormigas aún no implementada (TODO estudiantes)")
