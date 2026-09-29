"""Vista nula: traga todo (para benchmarks silenciosos y tests)."""

from __future__ import annotations

from lab_bioinspirados.nucleo.puertos import Informe
from lab_bioinspirados.nucleo.tipos import Resultado


class VistaNula:
    """Implementa el puerto Vista sin ningún efecto."""

    def mostrar(self, resultado: Resultado) -> None:
        """Ignora el resultado."""

    def render(self, informe: Informe) -> None:
        """Ignora el informe."""
