"""Servidor web mínimo (solo stdlib): sirve web/ + registro + SSE.

Uso:
    python -m adaptadores.servidor_web [puerto]
    python adaptadores/servidor_web.py [puerto]

Rutas:
- ``/`` y archivos de ``web/`` (estáticos).
- ``GET /api/registro`` → JSON {generacion, solvers, problemas}.
- ``GET /api/eventos`` → SSE: evento ``hola`` + ``recarga`` al vigilar.
Escucha en 127.0.0.1, puerto 8030 por defecto. Sin dependencias externas.
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / "src"
WEB = RAIZ / "web"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lab_bioinspirados.nucleo.cargador import Loader  # noqa: E402

PUERTO_DEFECTO = 8030

_cargador = Loader()
_registro = _cargador.descubrir()
_suscriptores: list[object] = []
_candado = threading.Lock()


def _al_cambiar(nuevo) -> None:
    global _registro
    _registro = nuevo
    with _candado:
        vivos = list(_suscriptores)
    for cola in vivos:
        try:
            cola.append(nuevo.generacion)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - suscriptor roto, se ignora
            continue


def _registro_json() -> dict:
    return {
        "generacion": _registro.generacion,
        "solvers": [
            {
                "nombre": i.nombre,
                "modulo": i.modulo,
                "clase": i.clase,
                "pendiente": i.pendiente,
                "version": i.version,
                "contrato": i.contrato,
                "error": i.error,
            }
            for i in _registro.solvers
        ],
        "problemas": [
            {
                "nombre": i.nombre,
                "modulo": i.modulo,
                "clase": i.clase,
                "pendiente": i.pendiente,
                "version": i.version,
                "contrato": i.contrato,
                "error": i.error,
            }
            for i in _registro.problemas
        ],
    }


class Manejador(SimpleHTTPRequestHandler):
    """Sirve web/ y las dos rutas /api/*."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, formato: str, *args: object) -> None:
        sys.stderr.write(f"[web] {formato % args}\n")

    def do_GET(self) -> None:  # noqa: N802
        ruta = urlparse(self.path).path
        if ruta == "/api/registro":
            cuerpo = json.dumps(_registro_json()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        elif ruta == "/api/eventos":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                self.wfile.write(b"event: hola\ndata: listo\n\n")
                self.wfile.flush()
                gen_previa = _registro.generacion
                while True:
                    actual = _registro.generacion
                    if actual != gen_previa:
                        gen_previa = actual
                        mensaje = f"event: recarga\ndata: {actual}\n\n".encode("utf-8")
                        self.wfile.write(mensaje)
                        self.wfile.flush()
                    threading.Event().wait(1.0)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            super().do_GET()


def servir(puerto: int = PUERTO_DEFECTO) -> ThreadingHTTPServer:
    """Arranca el servidor + vigilancia y devuelve el servidor."""
    _cargador.vigilar(_al_cambiar, intervalo=1.0)
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    print(f"sirviendo web/ en http://127.0.0.1:{puerto} (Ctrl+C para parar)")
    return servidor


def main() -> None:
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO_DEFECTO
    servidor = servir(puerto)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _cargador.detener()
        servidor.server_close()


if __name__ == "__main__":
    main()
