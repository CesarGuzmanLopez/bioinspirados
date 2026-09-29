# bioinspirados (laboratorio)

Laboratorio docente de algoritmos bioinspirados para muchos problemas:
viajero (TSP), mochila, n-reinas, coloreo, one-max y más. Desacoplo
estricto **Problemas / Solvers / Vista**. Lógica primero, elegante y
simple. (Paquete Python: `lab_bioinspirados`.)

## Ejemplo mínimo (copiable)

Instalación y demo en terminal:

```bash
pip install -e .
python -m adaptadores.terminal
```

Uso desde Python (4 ciudades en un cuadrado unidad):

```python
from lab_bioinspirados.problemas.viajero import Viajero
from lab_bioinspirados.solvers.fuerza_bruta import FuerzaBruta

p = Viajero(coordenadas=[(0, 0), (1, 0), (1, 1), (0, 1)])
r = FuerzaBruta().resolver(p)
print(r.solucion.orden, r.solucion.costo)   # (0, 1, 2, 3) 4.0
```

UI web estática (servida desde `web/`):

```bash
cd web && python3 -m http.server 8030      # http://localhost:8030
```

## Entorno (Ubuntu sin root)

Sin `sudo` y sin `--break-system-packages`: todo vive en `.venv` local.
Puertos >1024 (la web usa el 8030).

```bash
bash scripts/setup.sh          # crea .venv e instala con pip install -e .
. .venv/bin/activate           # activar en cada terminal nueva
cd web && python3 -m http.server 8030      # http://localhost:8030
```

## Instalar y correr

```bash
pip install -e .
python ejemplos/tsp_manual.py
python -m adaptadores.terminal
python -m adaptadores.servidor_web 8030
```

## Capas

- `nucleo/`: ABCs (`problema`, `solver`), tipos inmutables (`tipos`),
  errores con código (`errores`), puertos + `Informe` + `Modelo`/`VistaViva`
  (`puertos`), cargador de plugins (`cargador`), oráculo (`verificacion`).
  Solo stdlib.
- `problemas/`: `Viajero` (TSP; alias de compatibilidad `TSPCuadrado`),
  `MochilaBinaria` (completa) + stubs TODO
  (`n_reinas`, `coloreo`, `one_max`, `nube`).
- `solvers/`: `FuerzaBruta` exacta + 6 plantillas TODO
  (vecino, local, hormigas, abejas, tabú, recocido).
- `vistas/`: `VistaConsola` elegante y `VistaNula` silenciosa.
- `adaptadores/`: `terminal` (lista plugins + demos) y `servidor_web`
  (sirve `web/` + `/api/registro` + SSE `/api/eventos`).
- `ejemplos/tsp_manual.py`: composition root original (sigue verde).

## Convenciones

- Tour canónico **abierto**: `tuple[int, ...]`, empieza en 0, sin repetir el 0
  al final. `costo` suma el retorno `orden[-1] -> orden[0]`.
- Desempate `<` estricto: el primero gana (el oráculo lo verifica en doble pasada).
- Espacio fase 1: `(n-1)!` sin podar simétricos; `LIMITE_ENUMERACION = 10`.
- Identificadores en español, tecnología en inglés.

## Qué falta → ver `TODO.md`

## Añadir un problema o solver en 5 pasos

1. Copia el stub más cercano (`problemas/one_max.py` o
   `solvers/busqueda_local.py`) con tu `NOMBRE` en español.
2. Declara `PARAMETROS` (`Param("mi_param", defecto, "qué hace")`) y valida
   rangos en `_validar_parametro` (lanza `ParametroInvalido`).
3. Escribe la función objetivo (`costo` puro + `validar` estricta) o el
   `_resolver` (`<` estricto, throttling `cada_n_pasos`, presupuestos).
4. Pon `PENDIENTE = False` y verifica contra el oráculo en n chico
   (`verificacion.verificar` debe dar `(True, True)`).
5. Corre `python -m adaptadores.terminal` y `ruff check`: tu plugin aparece
   sin "(pendiente)" y sin errores.
