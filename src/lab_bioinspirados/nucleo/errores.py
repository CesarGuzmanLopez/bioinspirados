"""ABC del laboratorio (solo stdlib, sin mensajes con rutas ni stack)."""

from __future__ import annotations


class ErrorBioinspirado(Exception):
    """Base con ``codigo`` estable para comparar en tests sin mirar texto."""

    CODIGO = "BIOINSPIRADO"

    def __init__(
        self,
        mensaje: str = "",
        *,
        codigo: str = "",
        detalles: dict | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo or type(self).CODIGO
        self.detalles = dict(detalles) if detalles else {}

    def __str__(self) -> str:
        base = f"[{self.codigo}] {self.mensaje}".rstrip()
        if self.detalles:
            extras = ", ".join(f"{k}={v!r}" for k, v in self.detalles.items())
            return f"{base} ({extras})"
        return base


class OrdenInvalido(ErrorBioinspirado):
    """Un tour no es canónico abierto (inicio != 0, repetidos, fuera de rango...)."""

    CODIGO = "ORDEN_INVALIDO"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class MatrizInvalida(ErrorBioinspirado):
    """La matriz de un problema no es cuadrada / simétrica / válida."""

    CODIGO = "MATRIZ_INVALIDA"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class ProblemaDemasiadoGrande(ErrorBioinspirado):
    """El problema supera ``LIMITE_ENUMERACION`` y no se puede enumerar."""

    CODIGO = "PROBLEMA_DEMASIADO_GRANDE"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class SolverPendiente(ErrorBioinspirado):
    """El solver es una plantilla TODO aún no implementada por el estudiante."""

    CODIGO = "SOLVER_PENDIENTE"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class ParametroInvalido(ErrorBioinspirado):
    """Parámetro desconocido o fuera de rango en el constructor del solver."""

    CODIGO = "PARAMETRO_INVALIDO"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class PluginInvalido(ErrorBioinspirado):
    """Un plugin descubierto no cumple el contrato (falta NOMBRE, VERSION...)."""

    CODIGO = "PLUGIN_INVALIDO"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class PluginNoEncontrado(ErrorBioinspirado):
    """Único error que lanza ``Recarga``: el plugin pedido ya no existe."""

    CODIGO = "PLUGIN_NO_ENCONTRADO"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class VersionIncompatible(ErrorBioinspirado):
    """El plugin pide un CONTRATO distinto al del núcleo."""

    CODIGO = "VERSION_INCOMPATIBLE"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class GeometriaNoDisponible(ErrorBioinspirado):
    """El problema no tiene geometría (DIMENSIONES == 0 o sin coordenadas)."""

    CODIGO = "GEOMETRIA_NO_DISPONIBLE"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)


class LoteInvalido(ErrorBioinspirado):
    """Parámetros de lote/LOD inválidos en ``stream_puntos``."""

    CODIGO = "LOTE_INVALIDO"

    def __init__(self, mensaje: str = "", detalles: dict | None = None) -> None:
        super().__init__(mensaje, detalles=detalles)
