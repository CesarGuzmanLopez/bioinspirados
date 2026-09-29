"""Vista elegante de consola. Solo recibe Informe/Resultado (nunca problemas/solvers)."""

from __future__ import annotations

import os
import re
import sys

from lab_bioinspirados.nucleo.puertos import Informe, Modelo
from lab_bioinspirados.nucleo.tipos import Paso, Resultado

ORDEN_MAX_VISIBLE = 32
BARRA_ANCHO = 24

_RE_ANSI = re.compile(r"\033\[[0-9;]*m")
_RE_ESPACIO = re.compile(r"espacio\s*[=:]\s*(\d+)", re.IGNORECASE)
_RE_VEREDICTO = re.compile(r"(óptimo|optimo|primero)\s*=\s*([^\s,;]+)", re.IGNORECASE)
_RE_PENDIENTE = re.compile(
    r"pendiente|TODO|no implementad|por implementar|falta implementar", re.IGNORECASE
)

_VALOR_SI = {"sí", "si", "yes", "true", "1", "ok", "verdadero", "v"}
_VALOR_NO = {"no", "false", "0", "falso", "f"}

PISTA_PENDIENTES = (
    "PISTA: completa el stub marcado con «TODO estudiante» en solvers/ o "
    "problemas/ y vuelve a correr la demo."
)


def _tinta(texto: str, codigo: str, color: bool) -> str:
    """Envuelve en ANSI solo si el color está activo (sin color → texto plano)."""
    if not color:
        return texto
    return f"\033[{codigo}m{texto}\033[0m"


def _ancho_visible(texto: str) -> int:
    """Ancho sin contar secuencias ANSI (para alinear la caja con color)."""
    return len(_RE_ANSI.sub("", texto))


def _texto_orden(orden: tuple[int, ...], maximo: int = ORDEN_MAX_VISIBLE) -> str:
    """Tour cerrado con →; si supera ``maximo`` muestra cabeza … cola (elegante)."""
    if not orden:
        return "(vacío)"
    if len(orden) <= maximo:
        return " → ".join(map(str, (*orden, orden[0])))
    cabeza, cola = 10, 10
    partes = [str(i) for i in orden[:cabeza]] + ["…"]
    partes += [str(i) for i in orden[-cola:]] + [str(orden[0])]
    return f"{' → '.join(partes)}  (n={len(orden)}, truncado)"


def _espacio_en_detalle(detalle: tuple[str, ...]) -> int | None:
    """Espacio conocido si alguna línea extra dice ``espacio=N`` (si no, None)."""
    for linea in detalle:
        coincidencia = _RE_ESPACIO.search(linea)
        if coincidencia:
            try:
                total = int(coincidencia.group(1))
            except ValueError:
                continue
            if total > 0:
                return total
    return None


def _texto_barra(evaluaciones: int, espacio: int, ancho: int, color: bool) -> str:
    """Barra ``[████░░] evals/espacio (pct%)`` accesible también sin color."""
    fraccion = min(1.0, evaluaciones / espacio) if espacio > 0 else 0.0
    llenos = round(fraccion * ancho)
    barra = "█" * llenos + "░" * (ancho - llenos)
    relleno = _tinta("[" + barra + "]", "32", color)
    return f"{relleno} {evaluaciones}/{espacio} ({fraccion:.0%})"


def _veredicto_bonito(veredicto: str, color: bool) -> str:
    """Decora ``óptimo=sí/no, primero=sí/no`` con ✓ verde / ✗ rojo (símbolo siempre)."""
    if not veredicto:
        return veredicto

    def _marca(coincidencia: re.Match[str]) -> str:
        clave, valor = coincidencia.group(1), coincidencia.group(2)
        normalizado = valor.lower().rstrip(".,")
        if normalizado in _VALOR_SI:
            return f"{clave}={valor} {_tinta('✓', '32', color)}"
        if normalizado in _VALOR_NO:
            return f"{clave}={valor} {_tinta('✗', '31', color)}"
        return coincidencia.group(0)

    return _RE_VEREDICTO.sub(_marca, veredicto)


def _partir_detalle(detalle: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """Separa líneas normales de pendientes (TODO/pendiente) para la sección PISTA."""
    normales, pendientes = [], []
    for linea in detalle:
        (pendientes if _RE_PENDIENTE.search(linea) else normales).append(linea)
    return normales, pendientes


class VistaConsola:
    """Dibuja informes con texto elegante; toda la I/O vive aquí."""

    def __init__(
        self,
        *,
        usar_color: bool | None = None,
        max_orden: int = ORDEN_MAX_VISIBLE,
        ancho_barra: int = BARRA_ANCHO,
    ) -> None:
        """``usar_color=None`` = auto (NO_COLOR o no-tty → plano, accesible)."""
        self._usar_color = usar_color
        self._max_orden = max(1, max_orden)
        self._ancho_barra = max(4, ancho_barra)
        self._modelo: Modelo | None = None
        self._ultimo_paso: Paso | None = None
        self._espacio_modelo: int | None = None

    def _resuelve_color(self) -> bool:
        """ANSI solo si se pidió o si hay tty real sin NO_COLOR (auto-no-color)."""
        if self._usar_color is not None:
            return self._usar_color
        if "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
            return False
        try:
            return sys.stdout.isatty()
        except Exception:  # noqa: BLE001 — la vista nunca debe lanzar por el color
            return False

    def mostrar(self, resultado: Resultado) -> None:
        """Puente cómodo: construye el Informe y lo dibuja."""
        self.render(Informe.desde_resultado(resultado, titulo="Resultado"))

    def on_modelo(self, modelo: Modelo) -> None:
        """Guarda la foto inicial (VistaViva); nunca lanza, solo habilita progreso."""
        try:
            self._modelo = modelo
            total = int(getattr(modelo, "total", 0) or 0)
            self._espacio_modelo = total if total > 0 else None
        except Exception:  # noqa: BLE001 — la vista viva nunca debe romper al solver
            self._espacio_modelo = None

    def on_paso(self, paso: Paso) -> None:
        """Recibe progreso (VistaViva); silencioso y sin lanzar por contrato."""
        try:
            self._ultimo_paso = paso
        except Exception:  # noqa: BLE001 — la vista viva nunca debe romper al solver
            pass

    def render(self, informe: Informe) -> None:
        color = self._resuelve_color()
        print(_tinta(f"◆ {informe.problema} × {informe.solver}", "1;36", color))

        if informe.agotado:
            estado = _tinta("agotado ✓", "32", color)
        else:
            estado = _tinta("cortado (presupuesto) …", "33", color)
        filas = [
            ("orden", _texto_orden(informe.orden, self._max_orden)),
            ("costo", _tinta(f"{informe.costo:.6g}", "1", color)),
            ("evaluaciones", str(informe.evaluaciones)),
        ]
        espacio = _espacio_en_detalle(informe.detalle) or self._espacio_modelo
        if espacio:
            barra = _texto_barra(informe.evaluaciones, espacio, self._ancho_barra, color)
            filas.append(("progreso", barra))
        filas += [
            ("segundos", f"{informe.segundos:.4f}"),
            ("estado", estado),
            ("pasos emitidos", str(informe.pasos_emitidos)),
        ]
        if informe.veredicto:
            filas.append(("veredicto", _veredicto_bonito(informe.veredicto, color)))
        normales, pendientes = _partir_detalle(informe.detalle)
        for extra in normales:
            filas.append(("", f"• {extra}"))
        if pendientes:
            filas.append(("pendientes", f"{len(pendientes)} por hacer"))
            for linea in pendientes:
                filas.append(("", f"• {linea}"))
            filas.append(("PISTA", _tinta(PISTA_PENDIENTES, "33", color)))

        ancho_clave = max([len(k) for k, _ in filas if k] or [0])
        lineas: list[str] = []
        for clave, valor in filas:
            if clave:
                lineas.append(f"{clave.rjust(ancho_clave)} : {valor}")
            else:
                lineas.append(f"{' ' * (ancho_clave + 3)}{valor}")
        anchos = [_ancho_visible(linea) for linea in lineas] + [len(informe.titulo)]
        ancho = max(anchos)
        borde = "─" * (ancho + 2)
        titulo = _tinta(informe.titulo, "1", color)
        relleno = ancho - len(informe.titulo)
        print(f"┌{borde}┐")
        print(f"│ {' ' * (relleno // 2)}{titulo}{' ' * (relleno - relleno // 2)} │")
        print(f"├{borde}┤")
        for linea in lineas:
            print(f"│ {linea}{' ' * (ancho - _ancho_visible(linea))} │")
        print(f"└{borde}┘")
