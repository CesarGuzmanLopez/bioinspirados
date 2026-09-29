# TODO — trabajo para estudiantes (fase 0+1 hecha, fase 2 pendiente)

## Fase 0+1 — hecha ✓

- Contratos aditivos: `Punto`/`LotePuntos`/`Resultado.motivo_corte`,
  `VERSION`/`CONTRATO`/`DIMENSIONES`, `stream_puntos` + `_generar_puntos`,
  `Modelo` + `VistaViva`, `cargador` (descubrir/cuarentena/recargar/vigilar).
- `Viajero` (antes `TSPCuadrado`) n>32 lanza `ProblemaDemasiadoGrande` antes de alocar.
- `MochilaBinaria` completa (sirve para validar el núcleo sin TSP).
- Terminal accesible (`adaptadores/terminal.py`) y servidor vivo
  (`adaptadores/servidor_web.py` + `/api/registro` + SSE `/api/eventos`).
- Stubs listados como TODO (la vista los marca "(pendiente)").

## Solvers (stubs PENDIENTE en `src/lab_bioinspirados/solvers/`)

- [ ] **VecinoCercano** (`vecino_cercano.py`): greedy desde el 0.
- [ ] **BusquedaLocal** (`busqueda_local.py`): vecindad 2-opt / flip.
- [ ] **ColoniaHormigas** (`colonia_hormigas.py`): ACO
      (`hormigas`, `alfa`, `beta`, `evaporacion`).
- [ ] **Abejas** (`abejas.py`): ABC (`empleadas`, `observadoras`, `limite`).
- [ ] **BusquedaTabu** (`busqueda_tabu.py`): (`tenencia`, `aspiracion`).
- [ ] **RecocidoSimulado** (`recocido.py`): (`temperatura`, `enfriamiento`).
- [ ] **ColoniaDeHormigas** (plantilla vieja en `fuerza_bruta.py`): migrar a
      `colonia_hormigas.py`.
- [ ] **Held-Karp** (programación dinámica exacta): comparar contra fuerza
      bruta hasta n=10 con el oráculo.

Cada stub: `PENDIENTE=True`, `REQUIERE_ENUMERACION=False`,
desempate `<` estricto, throttling `cada_n_pasos`, presupuestos
(`presupuesto_evaluaciones` / `iteraciones`).

## Problemas (3 TODO + 1 futuro en `src/lab_bioinspirados/problemas/`)

- [ ] **NReinas** (`n_reinas.py`): escribir `costo` = nº de pares en
      conflicto (0 = resuelto). Caso chico: n=4 → costo 0, p. ej. (1,3,0,2).
- [ ] **ColoreoGrafo** (`coloreo.py`): escribir `costo` = nº de aristas
      monocromáticas. Caso chico: triángulo k=3 → 0; k=2 → 1.
- [ ] **OneMax** (`one_max.py`): escribir `costo` = nº de ceros (n - suma).
      Caso chico: n=3 → (1,1,1) costo 0.
- [ ] **TSPNube** (`nube.py`, fase 2): streaming sin matriz densa + `costo`
      al vuelo + `_generar_candidatos` lazy.

Cada stub: `NOMBRE`, docstring con objetivo + función objetivo + caso chico;
cuerpos con `raise NotImplementedError("TODO estudiante: ...")`.

## Vista

- [ ] **Vista matplotlib**: dibujar tour usando el pull `Geometria2D.coordenadas()`
      (nuevo módulo `vistas/matplotlib.py`; la vista sigue sin importar
      problemas/solvers, solo `Informe`/`Resultado` + coordenadas opcionales).

## Pruebas

- [ ] Suite de pruebas para probar algoritmos (pedido explícito: probar
      algoritmos, no unitarios genéricos): oráculo vs cada solver en n pequeños,
      doble pasada primero-gana, `LIMITE_ENUMERACION`, poda de simétricos si se añade.
