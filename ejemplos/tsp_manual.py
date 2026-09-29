"""Composition root: único lugar que cablea TSP + solver + oráculo + vista.

Orden del guion:
  1) solver vs doble verificación (n=4, óptimo 4.0 conocido),
  2) chequeo del TSP sin solver (conteo (n-1)!, validar todo, costo idempotente),
  3) integración vs oráculo (n=8),
  4) render elegante.

Uso:  pip install -e .  &&  python ejemplos/tsp_manual.py
"""

from __future__ import annotations

from lab_bioinspirados.nucleo.puertos import Informe
from lab_bioinspirados.nucleo.verificacion import optimo_por_oraculo, verificar
from lab_bioinspirados.problemas.viajero import Viajero
from lab_bioinspirados.solvers.fuerza_bruta import FuerzaBruta
from lab_bioinspirados.vistas.consola import VistaConsola

CUADRADO_UNITARIO = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
N8 = [
    (0.0, 0.0),
    (2.0, 0.0),
    (4.0, 0.0),
    (4.0, 2.0),
    (4.0, 4.0),
    (2.0, 4.0),
    (0.0, 4.0),
    (0.0, 2.0),
]


def paso_solver_vs_doble() -> None:
    print("== 1) solver vs doble verificación (n=4, óptimo 4.0) ==")
    problema = Viajero(coordenadas=CUADRADO_UNITARIO)
    resultado = FuerzaBruta().resolver(problema)
    assert resultado.solucion.costo == 4.0, resultado.solucion
    ok_costo, ok_orden = verificar(problema, resultado.solucion)
    assert ok_costo and ok_orden, (ok_costo, ok_orden)
    print(f"   costo={resultado.solucion.costo} orden={resultado.solucion.orden} ✓ doble=(1, 1)")


def paso_chequeo_sin_solver() -> None:
    print("== 2) TSP sin solver: conteo (n-1)!, validar todo, costo idempotente ==")
    problema = Viajero(coordenadas=CUADRADO_UNITARIO)
    assert problema.espacio() == 6  # (4-1)! ; fase 1 sin podar simétricos
    candidatos = list(problema.enumerar())
    assert len(candidatos) == problema.espacio() == 6
    for orden in candidatos:
        problema.validar(orden)  # lanza si no es canónico
        assert orden[0] == 0 and len(orden) == 4
        assert problema.costo(orden) == problema.costo(orden)  # puro/idempotente
        assert problema.costo(list(orden)) == problema.costo(tuple(orden))
    print(f"   6/6 tours canónicos, costos idempotentes ✓ espacio={problema.espacio()}")


def paso_integracion_vs_oraculo() -> None:
    print("== 3) integración vs oráculo (n=8) ==")
    problema = Viajero(coordenadas=N8)
    assert problema.espacio() == 5040  # 7!
    vistos: list = []
    solver = FuerzaBruta(observador=visto_append(vistos), cada_n_pasos=1000)
    resultado = solver.resolver(problema)
    oraculo = optimo_por_oraculo(problema)
    assert resultado.solucion == oraculo, (resultado.solucion, oraculo)
    assert resultado.evaluaciones == 5040 and resultado.agotado
    assert resultado.pasos_emitidos == 5 and len(vistos) == 5  # throttling 5040//1000
    print(f"   solver == oráculo: costo={oraculo.costo:.4f} ✓ pasos={resultado.pasos_emitidos}")


def visto_append(vistos: list):
    def _guardar(paso):
        vistos.append(paso)

    return _guardar


def paso_render() -> None:
    print("== 4) render ==")
    vista = VistaConsola()
    resultado = FuerzaBruta().resolver(Viajero(coordenadas=CUADRADO_UNITARIO))
    ok_costo, ok_orden = verificar(Viajero(coordenadas=CUADRADO_UNITARIO), resultado.solucion)
    vista.mostrar(resultado)
    veredicto = f"óptimo={'sí' if ok_costo else 'no'}, primero={'sí' if ok_orden else 'no'}"
    vista.render(Informe.desde_resultado(resultado, titulo="Verificación", veredicto=veredicto))


def main() -> None:
    paso_solver_vs_doble()
    paso_chequeo_sin_solver()
    paso_integracion_vs_oraculo()
    paso_render()
    print("== OK: ejemplo manual completo ==")


if __name__ == "__main__":
    main()
