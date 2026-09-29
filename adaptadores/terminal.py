"""Composition root accesible: lista plugins y corre demos chicas.

Uso:
    python -m adaptadores.terminal
    python adaptadores/terminal.py

No cablea a mano: usa ``Loader.descubrir`` (cuarentena incluida), marca
pendientes como TODO y corre el cuadrado n=4 + una mochila chica con
``VistaConsola``. No borra ni rompe ``ejemplos/tsp_manual.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lab_bioinspirados.nucleo.cargador import Loader  # noqa: E402
from lab_bioinspirados.nucleo.puertos import Informe  # noqa: E402
from lab_bioinspirados.nucleo.verificacion import verificar  # noqa: E402
from lab_bioinspirados.problemas.mochila import MochilaBinaria  # noqa: E402
from lab_bioinspirados.problemas.viajero import Viajero  # noqa: E402
from lab_bioinspirados.solvers.fuerza_bruta import FuerzaBruta  # noqa: E402
from lab_bioinspirados.vistas.consola import VistaConsola  # noqa: E402

CUADRADO = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def listar(registro) -> None:
    print(f"-- registro (generación {registro.generacion}) --")
    vistos: set[str] = set()
    print("solvers:")
    for info in registro.solvers:
        if info.nombre in vistos:
            continue
        vistos.add(info.nombre)
        marca = " (pendiente)" if info.pendiente or info.error else ""
        extra = f" [{info.error}]" if info.error else ""
        print(f"  - {info.nombre}{marca}{extra}")
    vistos.clear()
    print("problemas:")
    for info in registro.problemas:
        if info.nombre in vistos:
            continue
        vistos.add(info.nombre)
        marca = " (pendiente)" if info.pendiente or info.error else ""
        extra = f" [{info.error}]" if info.error else ""
        print(f"  - {info.nombre}{marca}{extra}")


def demo_cuadrado(vista: VistaConsola, cada_n_pasos: int = 1) -> None:
    """Cuadrado n=4 imprimiendo CADA solución probada (cada_n_pasos=1).

    ``cada_n_pasos`` es el paso de emisión del observador: 1 = ver cada
    tour evaluado (modo lento docente); súbelo para ir más rápido.
    """
    print("== demo TSP cuadrado n=4 (óptimo 4.0) ==")
    problema = Viajero(coordenadas=CUADRADO)

    def _progreso(paso) -> None:
        print(
            f"   evals={paso.evaluaciones:>3} costo={paso.mejor.costo:.6g} "
            f"mejor={' → '.join(map(str, (*paso.mejor.orden, 0)))}"
        )

    resultado = FuerzaBruta(observador=_progreso, cada_n_pasos=cada_n_pasos).resolver(problema)
    ok_costo, ok_orden = verificar(problema, resultado.solucion)
    vista.mostrar(resultado)
    vista.render(
        Informe.desde_resultado(
            resultado,
            titulo="Verificación",
            veredicto=f"óptimo={'sí' if ok_costo else 'no'}, primero={'sí' if ok_orden else 'no'}",
        )
    )


def demo_mochila(vista: VistaConsola) -> None:
    print("== demo mochila chica (óptimo valor 7, costo -7) ==")
    problema = MochilaBinaria(pesos=(2, 3, 4, 5), valores=(3, 4, 5, 6), capacidad=5)
    resultado = FuerzaBruta().resolver(problema)
    assert resultado.solucion.costo == -7.0, resultado.solucion
    vista.mostrar(resultado)


def demo_grande(vista: VistaConsola) -> None:
    """Streaming vivo n=11: NO corre (n-1)! completo; corta a las 20k evals."""
    import math

    n = 11
    puntos = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    total = f"{math.factorial(n - 1):,}".replace(",", ".")
    print(f"== demo TSP n={n} en streaming vivo (corte a 20k de {total}) ==")
    problema = Viajero(coordenadas=puntos, permitir_grande=True)

    def _progreso(paso) -> None:
        print(
            f"   evals={paso.evaluaciones:>6} costo={paso.mejor.costo:.6g} "
            f"mejor={' → '.join(map(str, (*paso.mejor.orden, 0)))}"
        )

    resultado = FuerzaBruta(
        observador=_progreso, cada_n_pasos=2000, presupuesto_evaluaciones=20000
    ).resolver(problema)
    assert resultado.evaluaciones == 20000, resultado.evaluaciones
    assert not resultado.agotado, "el streaming con presupuesto debe cortar (agotado=False)"
    assert resultado.motivo_corte.startswith("presupuesto_evaluaciones"), resultado.motivo_corte
    vista.mostrar(resultado)
    print(f"   corte limpio: agotado={resultado.agotado} motivo={resultado.motivo_corte}")


def main(cada_n_pasos: int = 1) -> None:
    cargador = Loader()
    registro = cargador.descubrir()
    listar(registro)
    vista = VistaConsola()
    demo_cuadrado(vista, cada_n_pasos=cada_n_pasos)
    demo_mochila(vista)
    demo_grande(vista)
    print("== OK: terminal accesible ==")


if __name__ == "__main__":
    _cada = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    main(cada_n_pasos=_cada)
