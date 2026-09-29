"""ABC Solver: configuración validada + template ``resolver`` (solo stdlib)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter
from typing import TYPE_CHECKING, Callable, ClassVar

from lab_bioinspirados.nucleo.errores import ParametroInvalido, SolverPendiente
from lab_bioinspirados.nucleo.tipos import Param, Paso, Resultado, Solucion

if TYPE_CHECKING:
    from lab_bioinspirados.nucleo.problema import Problema


class Solver(ABC):
    """Contrato que todo algoritmo implementa.

    Reglas: desempate ``<`` estricto (el primero gana), sin I/O ni ``print``,
    progreso solo vía ``observador`` throttled por ``cada_n_pasos``.
    """

    NOMBRE: ClassVar[str] = "solver"
    PENDIENTE: ClassVar[bool] = True
    REQUIERE_ENUMERACION: ClassVar[bool] = False
    PARAMETROS: ClassVar[tuple[Param, ...]] = ()
    VERSION: ClassVar[str] = "0.1.0"
    CONTRATO: ClassVar[int] = 1
    DIMENSIONES: ClassVar[int] = 0

    def __init__(
        self,
        *,
        observador: Callable[[Paso], None] | None = None,
        **params: object,
    ) -> None:
        conocidos = {p.nombre for p in type(self).PARAMETROS}
        desconocidos = sorted(set(params) - conocidos)
        if desconocidos:
            raise ParametroInvalido(
                f"parámetros desconocidos para {type(self).NOMBRE}: {desconocidos}",
                detalles={"desconocidos": desconocidos, "conocidos": sorted(conocidos)},
            )
        valores = {p.nombre: p.defecto for p in type(self).PARAMETROS}
        valores.update(params)
        for nombre, valor in valores.items():
            self._validar_parametro(nombre, valor)
        self._params = valores
        self._observador = observador
        self._corte_solicitado = ""
        self._motivo_corte = ""

    def _validar_parametro(self, nombre: str, valor: object) -> None:
        """Gancho: el solver concreto chequea rangos; base lo acepta todo."""

    @property
    def parametros(self) -> dict:
        """Copia de la configuración efectiva (defectos + lo pasado)."""
        return dict(self._params)

    def _notificar(self, paso: Paso) -> bool:
        """Emite ``paso``; devuelve True si el observador pide detener.

        Protocolo de cancelación cooperativa: si el observador devuelve un
        valor truthy, el solver corta limpio (``agotado=False`` + motivo).
        """
        if self._observador is None:
            return False
        return bool(self._observador(paso))

    def solicitar_corte(self, motivo: str = "corte solicitado") -> None:
        """Pide al solver que corte limpio en la próxima iteración."""
        self._corte_solicitado = motivo or "corte solicitado"

    def _hay_corte(self) -> str:
        """Motivo pendiente de corte externo ("" si nadie lo pidió)."""
        motivo = self._corte_solicitado
        self._corte_solicitado = ""
        return motivo

    def resolver(self, problema: Problema) -> Resultado:
        """Template concreto: plantilla? → resoluble → enumerable? → algoritmo."""
        if type(self).PENDIENTE:
            raise SolverPendiente(f"{type(self).NOMBRE} es plantilla TODO sin implementar")
        problema.exigir_resoluble()
        if type(self).REQUIERE_ENUMERACION:
            problema.exigir_enumerable()
        self._motivo_corte = ""
        self._corte_solicitado = ""
        inicio = perf_counter()
        solucion, evaluaciones, agotado, pasos = self._resolver(problema)
        segundos = perf_counter() - inicio
        return Resultado(
            problema=problema.nombre,
            solucion=solucion,
            solver=type(self).NOMBRE,
            evaluaciones=evaluaciones,
            segundos=segundos,
            parametros=self.parametros,
            agotado=agotado,
            pasos_emitidos=pasos,
            motivo_corte=self._motivo_corte,
        )

    @abstractmethod
    def _resolver(self, problema: Problema) -> tuple[Solucion, int, bool, int]:
        """Devuelve ``(solucion, evaluaciones, agotado, pasos_emitidos)``."""
