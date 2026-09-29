"""Cargador de plugins: descubre solvers/problemas sin romper nada (solo stdlib).

Cuarentena: si un módulo falla al importar o no cumple el contrato, se
registra con ``error`` en vez de lanzar. ``recargar`` solo lanza
``PluginNoEncontrado``; el resto hace fallback al último registro bueno.
``vigilar`` sondea mtimes cada segundo en un hilo y avisa al cambiar.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import pkgutil
import threading
from dataclasses import dataclass, field
from pathlib import Path

from lab_bioinspirados.nucleo.errores import PluginNoEncontrado

CONTRATO_ESPERADO = 1


@dataclass(frozen=True, slots=True)
class InfoPlugin:
    """Ficha de un plugin descubierto (solver o problema)."""

    nombre: str
    modulo: str
    clase: str
    pendiente: bool = False
    version: str = "0.1.0"
    contrato: int = 1
    ruta: str = ""
    firma: str = ""
    error: str = ""
    alias: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Registro:
    """Foto de lo descubierto: solvers + problemas + generación."""

    solvers: tuple[InfoPlugin, ...] = ()
    problemas: tuple[InfoPlugin, ...] = ()
    generacion: int = 0

    def buscar(self, nombre: str) -> InfoPlugin | None:
        """Busca por ``nombre`` (o ``modulo.clase``) en solvers y problemas."""
        for info in (*self.solvers, *self.problemas):
            if nombre in (info.nombre, info.clase, f"{info.modulo}.{info.clase}", *info.alias):
                return info
        return None


@dataclass(frozen=True, slots=True)
class Recarga:
    """Resultado de ``recargar``: qué cambió sin romper lo anterior."""

    generacion: int
    cambios: tuple[str, ...] = ()
    errores: tuple[str, ...] = ()
    registro: Registro | None = field(default=None, compare=False)


def _firma_de(ruta: Path) -> str:
    try:
        return hashlib.sha256(ruta.read_bytes()).hexdigest()[:12]
    except OSError:
        return ""


def _clases_de(modulo_nombre: str) -> tuple[list[type], str]:
    try:
        modulo = importlib.import_module(modulo_nombre)
    except Exception as exc:  # noqa: BLE001 - cuarentena, no lanzar
        return [], f"{type(exc).__name__}: {exc}"
    try:
        from lab_bioinspirados.nucleo.problema import Problema
        from lab_bioinspirados.nucleo.solver import Solver
    except Exception:  # noqa: BLE001 - sin núcleo no hay plugins
        Problema = Solver = object  # type: ignore[assignment]
    clases: list[type] = []
    for valor in vars(modulo).values():
        if not isinstance(valor, type):
            continue
        if getattr(valor, "__module__", "") != modulo_nombre:
            continue  # importado de otro módulo, no propio
        try:
            if issubclass(valor, (Problema, Solver)) and valor not in (Problema, Solver):
                if valor not in clases:  # evita duplicados por alias (p. ej. TSPCuadrado)
                    clases.append(valor)
        except TypeError:
            continue
    return clases, ""


def _nombre_de(clase: type) -> str:
    nombre = getattr(clase, "NOMBRE", None)
    if isinstance(nombre, str) and nombre:
        return nombre
    return clase.__name__


def _alias_de(clase: type) -> tuple[str, ...]:
    """Alias aceptados por ``Registro.buscar`` además de NOMBRE/clase (aditivo)."""
    alias = getattr(clase, "ALIAS", ())
    if isinstance(alias, str):
        return (alias,)
    try:
        return tuple(str(a) for a in alias)
    except TypeError:
        return ()


class Loader:
    """Descubre plugins en los paquetes de solvers y problemas."""

    def __init__(
        self,
        paquete_solvers: str = "lab_bioinspirados.solvers",
        paquete_problemas: str = "lab_bioinspirados.problemas",
    ) -> None:
        self._paquete_solvers = paquete_solvers
        self._paquete_problemas = paquete_problemas
        self._generacion = 0
        self._ultimo: Registro = Registro()
        self._mtimes: dict[str, float] = {}
        self._hilo: threading.Thread | None = None
        self._parar: threading.Event | None = None

    def _explorar(self, paquete: str, es_solver: bool) -> list[InfoPlugin]:  # noqa: FBT001
        infos: list[InfoPlugin] = []
        try:
            raiz = importlib.import_module(paquete)
        except Exception as exc:  # noqa: BLE001 - cuarentena
            return [
                InfoPlugin(
                    nombre=paquete,
                    modulo=paquete,
                    clase="?",
                    ruta="",
                    error=f"{type(exc).__name__}: {exc}",
                )
            ]
        camino = getattr(raiz, "__path__", None)
        if camino is None:
            return []
        for dato in pkgutil.iter_modules(list(camino)):
            modulo_nombre = f"{paquete}.{dato.name}"
            ruta = ""
            try:
                espec = importlib.util.find_spec(modulo_nombre)
                ruta = str(espec.origin or "") if espec else ""
            except Exception:  # noqa: BLE001 - ruta opcional
                ruta = ""
            firma = _firma_de(Path(ruta)) if ruta else ""
            clases, error_import = _clases_de(modulo_nombre)
            if error_import:
                infos.append(
                    InfoPlugin(
                        nombre=dato.name,
                        modulo=modulo_nombre,
                        clase="?",
                        ruta=ruta,
                        firma=firma,
                        error=error_import,
                    )
                )
                continue
            if not clases:
                continue
            for clase in clases:
                nombre = _nombre_de(clase)
                pendiente = bool(getattr(clase, "PENDIENTE", False))
                version = str(getattr(clase, "VERSION", "0.1.0"))
                contrato = int(getattr(clase, "CONTRATO", 1))
                error = ""
                if contrato != CONTRATO_ESPERADO:
                    error = f"VersionIncompatible: contrato={contrato}"
                infos.append(
                    InfoPlugin(
                        nombre=nombre,
                        modulo=modulo_nombre,
                        clase=clase.__name__,
                        pendiente=pendiente,
                        version=version,
                        contrato=contrato,
                        ruta=ruta,
                        firma=firma,
                        error=error,
                        alias=_alias_de(clase),
                    )
                )
        _ = es_solver
        return sorted(infos, key=lambda i: i.nombre)

    def descubrir(self) -> Registro:
        """Escanea ambos paquetes y devuelve un Registro nuevo (cuarentena)."""
        solvers = self._explorar(self._paquete_solvers, True)
        problemas = self._explorar(self._paquete_problemas, False)
        self._generacion += 1
        registro = Registro(
            solvers=tuple(solvers), problemas=tuple(problemas), generacion=self._generacion
        )
        self._ultimo = registro
        self._mtimes = self._foto_mtimes(registro)
        return registro

    def recargar(self, nombre: str | None = None) -> Recarga:
        """Re-descubre con fallback al último bueno.

        Solo lanza ``PluginNoEncontrado`` si se pide un ``nombre`` que ya no
        existe; cualquier otro error queda en cuarentena (``errores``).
        """
        previo = self._ultimo
        try:
            nuevo = self.descubrir()
        except Exception as exc:  # noqa: BLE001 - fallback, no lanzar
            return Recarga(
                generacion=previo.generacion,
                cambios=(),
                errores=(f"{type(exc).__name__}: {exc}",),
                registro=previo,
            )
        if nombre is not None and nuevo.buscar(nombre) is None:
            self._ultimo = previo
            raise PluginNoEncontrado(
                f"plugin {nombre!r} no encontrado tras recargar",
                detalles={"nombre": nombre, "generacion": nuevo.generacion},
            )
        anteriores = {i.nombre for i in (*previo.solvers, *previo.problemas)}
        actuales = {i.nombre for i in (*nuevo.solvers, *nuevo.problemas)}
        cambios = tuple(sorted(anteriores ^ actuales))
        errores = tuple(i.error for i in (*nuevo.solvers, *nuevo.problemas) if i.error)
        return Recarga(
            generacion=nuevo.generacion, cambios=cambios, errores=errores, registro=nuevo
        )

    def _foto_mtimes(self, registro: Registro) -> dict[str, float]:
        foto: dict[str, float] = {}
        for info in (*registro.solvers, *registro.problemas):
            if info.ruta:
                try:
                    foto[info.ruta] = Path(info.ruta).stat().st_mtime
                except OSError:
                    continue
        return foto

    def vigilar(
        self,
        al_cambiar: object = None,
        intervalo: float = 1.0,
    ) -> threading.Thread:
        """Arranca polling de mtimes cada ``intervalo`` s; avisa con recarga."""

        def _bucle(parar: threading.Event) -> None:
            while not parar.wait(intervalo):
                cambiado = False
                for ruta, antes in list(self._mtimes.items()):
                    try:
                        ahora = Path(ruta).stat().st_mtime
                    except OSError:
                        cambiado = True
                        break
                    if ahora != antes:
                        cambiado = True
                        break
                if cambiado:
                    try:
                        nuevo = self.descubrir()
                    except Exception:  # noqa: BLE001 - cuarentena
                        continue
                    if callable(al_cambiar):
                        try:
                            al_cambiar(nuevo)  # type: ignore[operator]
                        except Exception:  # noqa: BLE001 - callback no rompe
                            continue

        self.detener()
        parar = threading.Event()
        hilo = threading.Thread(target=_bucle, args=(parar,), daemon=True)
        self._parar = parar
        self._hilo = hilo
        hilo.start()
        return hilo

    def detener(self) -> None:
        """Para el hilo de vigilancia si está corriendo."""
        if self._parar is not None:
            self._parar.set()
        if self._hilo is not None and self._hilo.is_alive():
            self._hilo.join(timeout=2.0)
        self._hilo = None
        self._parar = None

    def __del__(self) -> None:  # pragma: no cover - limpieza best-effort
        try:
            self.detener()
        except Exception:  # noqa: BLE001
            pass
