/* lab_bioinspirados · TSP interactivo. Solo cliente, sin dependencias.
   Convenciones Python (ejemplos/tsp_manual.py + VistaConsola):
   - tour canónico abierto: empieza en 0; costo suma retorno orden[-1] -> orden[0]
   - orden cerrado impreso: "0 → 1 → 2 → 3 → 0"; costo con 6 cifras (%.6g)
   - espacio fase 1: (n-1)! sin podar simétricos; desempate < estricto */
"use strict";

/* ---------- registro vivo (/api/registro con fallback local) ---------- */
const REGISTRO_LOCAL = {
  solvers: ["fuerza-bruta", "vecino-cercano (pendiente)", "busqueda-local (pendiente)",
    "colonia-hormigas (pendiente)", "abejas-abc (pendiente)",
    "busqueda-tabu (pendiente)", "recocido-simulado (pendiente)"],
  problemas: ["viajero", "mochila-binaria", "n-reinas (pendiente)",
    "coloreo-grafos (pendiente)", "one-max (pendiente)", "tsp-nube (pendiente)"],
};
/* Etiqueta legible del problema: el registro expone "viajero"; se conserva
   "tsp-cuadrado" como fallback histórico si un backend viejo aún lo emite. */
const ETIQUETA_PROBLEMA = { viajero: "Viajero", "tsp-cuadrado": "Viajero" };
function etiquetaProblema(nombre) {
  return ETIQUETA_PROBLEMA[nombre] || nombre;
}
function etiquetaPendiente(nombre, pendiente) {
  return pendiente ? `${nombre} (pendiente)` : nombre;
}
function poblarDropdowns(registro) {
  const selS = document.getElementById("sel-solver");
  const selP = document.getElementById("sel-problema");
  if (!registro) registro = { solvers: [], problemas: [] };
  if (selS && registro.solvers && registro.solvers.length) {
    selS.textContent = "";
    for (const s of registro.solvers) {
      const o = document.createElement("option");
      o.value = s.nombre || s;
      o.textContent = typeof s === "string" ? s : etiquetaPendiente(s.nombre, s.pendiente);
      selS.appendChild(o);
    }
  }
  if (selP && registro.problemas && registro.problemas.length) {
    selP.textContent = "";
    for (const p of registro.problemas) {
      const o = document.createElement("option");
      o.value = p.nombre || p;
      o.textContent = typeof p === "string"
        ? etiquetaProblema(p)
        : etiquetaPendiente(etiquetaProblema(p.nombre), p.pendiente);
      selP.appendChild(o);
    }
  }
  window.__registro = registro;
}
fetch("/api/registro")
  .then((r) => (r.ok ? r.json() : Promise.reject(new Error("sin registro"))))
  .then((j) => poblarDropdowns(j))
  .catch(() => poblarDropdowns({ solvers: REGISTRO_LOCAL.solvers, problemas: REGISTRO_LOCAL.problemas }));

/* Sin tope duro: streaming vivo cancelable para cualquier n.
   Las permutas se generan lazy (next-permutation desde 0 fijo) y se pintan
   en vivo: candidato actual tenue + mejor ambar. Sin materializar tours. */

const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;

const canvas = document.getElementById("mapa");
const ctx = canvas.getContext("2d");
const aviso = document.getElementById("aviso-heuristica");
const aviso3d = document.getElementById("aviso-3d");
const $ = (id) => document.getElementById(id);
const els = {
  n: $("in-n"), semilla: $("in-semilla"),
  stN: $("st-n"), stCosto: $("st-costo"), stEvals: $("st-evals"),
  stBrecha: $("st-brecha"), stTiempo: $("st-tiempo"),
  fbCosto: $("cmp-fb-costo"), fbEvals: $("cmp-fb-evals"),
  nnCosto: $("cmp-nn-costo"), nnEvals: $("cmp-nn-evals"),
  pyOrden: $("py-orden"), pyCosto: $("py-costo"),
  play: $("btn-play"), vel: $("velocidad"),
};

/* ---------- estado ---------- */
let puntos = [];            // [{x,y} en [0,1]^2]
let solucion = null;        // {orden:[...abierto], costo, metodo, evaluaciones, ms, exacto}
let vecino = null;          // {orden, costo} comparativa
let stream = null;          // {gen, n, mejor, mejorCosto, actual, evals, t0, terminado, cancelado, timer}
let anim = { t: 0, playing: false, raf: 0, last: 0, paso: 0 };
let drag = null;            // {idx, movido}
let downPos = null;

/* ---------- utils ---------- */
function mulberry32(semilla) {
  let a = semilla >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
/** Espacio (n-1)! sin big-ints que cuelguen: exacto si cabe en double, si no orden de magnitud. */
function espacioTexto(n) {
  const k = n - 1;
  if (k <= 18) {
    let f = 1;
    for (let i = 2; i <= k; i++) f *= i;
    return f.toLocaleString("es");
  }
  let log10 = 0;
  for (let i = 2; i <= k; i++) log10 += Math.log10(i);
  const exp = Math.floor(log10);
  const mant = Math.pow(10, log10 - exp);
  return `≈${mant.toFixed(2)}·10^${exp}`;
}
function costoDe(orden) {
  let c = 0;
  for (let i = 0; i < orden.length; i++) c += dist(puntos[orden[i]], puntos[orden[(i + 1) % orden.length]]);
  return c;
}
/** Mismo formato que VistaConsola: "0 → 1 → 2 → 0". */
const ordenCerrado = (orden) => [...orden, orden[0]].join(" → ");
/** Mismo formato que VistaConsola: f"{costo:.6g}". */
function fmtCosto(c) {
  if (!isFinite(c)) return "—";
  const s = c.toPrecision(6);
  return String(Number(s));
}

/* ---------- solvers (JS, misma semántica que Python) ---------- */
/** Reordena `a` a la siguiente permutación lexicográfica; false si era la última. */
function siguientePermutacion(a) {
  let i = a.length - 2;
  while (i >= 0 && a[i] >= a[i + 1]) i--;
  if (i < 0) return false;
  let j = a.length - 1;
  while (a[j] <= a[i]) j--;
  [a[i], a[j]] = [a[j], a[i]];
  for (let l = i + 1, r = a.length - 1; l < r; l++, r--) [a[l], a[r]] = [a[r], a[l]];
  return true;
}
/** Generador lazy de tours canónicos abiertos (0 fijo, desempate < estricto fuera).
 *  Memoria O(1): nunca materializa el array de tours. */
function* toursLazy(n) {
  const resto = [];
  for (let i = 1; i < n; i++) resto.push(i);
  yield [0, ...resto];
  while (siguientePermutacion(resto)) yield [0, ...resto];
}
function vecinoCercano() {
  const n = puntos.length;
  const vis = new Array(n).fill(false);
  const orden = [0]; vis[0] = true;
  while (orden.length < n) {
    const u = orden[orden.length - 1];
    let best = -1, bd = Infinity;
    for (let v = 0; v < n; v++) {
      if (vis[v]) continue;
      const d = dist(puntos[u], puntos[v]);
      if (d < bd) { bd = d; best = v; }
    }
    orden.push(best); vis[best] = true;
  }
  return { orden, costo: costoDe(orden), evaluaciones: Math.max(0, n - 1) };
}

/* ---------- resolver streaming vivo + panel ---------- */
function detenerStream(motivo) {
  if (!stream || stream.terminado) return;
  stream.cancelado = true;
  stream.terminado = true;
  clearTimeout(stream.timer);
  const ms = performance.now() - stream.t0;
  solucion = {
    orden: stream.mejor, costo: stream.mejorCosto, metodo: "fuerza bruta (vivo)",
    exacto: false, evaluaciones: stream.evals, ms,
    detenido: true, motivo: motivo || "detenido",
  };
  pintarPanel(ms);
  actualizarBotonDetener();
  dibujar();
}

function resolver() {
  if (stream) { stream.cancelado = true; stream.terminado = true; clearTimeout(stream.timer); }
  stream = null;
  if (puntos.length < 2) {
    solucion = null; vecino = null;
    aviso.hidden = true;
    pintarPanelVacio();
    actualizarBotonDetener();
    dibujar();
    return;
  }
  const n = puntos.length;
  vecino = vecinoCercano();
  stream = {
    gen: toursLazy(n), n, mejor: null, mejorCosto: Infinity, actual: null,
    evals: 0, t0: performance.now(), terminado: false, cancelado: false, timer: 0,
  };
  solucion = null;
  anim.t = 0; anim.paso = 0;
  const grande = n > 10;
  aviso.hidden = false;
  aviso.textContent = grande
    ? `n=${n} → ${espacioTexto(n)} tours: streaming sin fin garantizado, puedes detener cuando quieras`
    : `explorando ${(espacioTexto(n))} tours en vivo…`;
  actualizarAviso3D();
  actualizarBotonDetener();
  bombear();
}

/** Hook 3D: n>200 sugiere vista 3D (texto + enlace) sin bloquear la 2D.
 *  No existe aún web/3d-viewer: el enlace es el hook; la 2D + LOD siguen activas. */
function actualizarAviso3D() {
  if (!aviso3d) return;
  aviso3d.hidden = !(puntos.length > 200);
}

/** Procesa un chunk acotado por tiempo (~24 ms) y reprograma: la UI nunca se cuelga. */
function bombear() {
  if (!stream || stream.cancelado) return;
  const lote = Math.round(200 + velocidad() * 8000); // autoplay con velocidad
  const fin = performance.now() + 24;
  let hechos = 0, avanzada = false;
  while (hechos < lote && performance.now() < fin) {
    const sig = stream.gen.next();
    if (sig.done) { avanzada = true; break; }
    const orden = sig.value;
    stream.actual = orden;
    const c = costoDe(orden);
    stream.evals++;
    hechos++;
    if (c < stream.mejorCosto) { stream.mejorCosto = c; stream.mejor = orden; } // < estricto
  }
  const ms = performance.now() - stream.t0;
  solucion = {
    orden: stream.mejor, costo: stream.mejorCosto, metodo: "fuerza bruta (vivo)",
    exacto: avanzada, evaluaciones: stream.evals, ms, detenido: false,
  };
  pintarPanel(ms);
  dibujar();
  if (avanzada) {
    stream.terminado = true;
    aviso.textContent = `óptimo exacto tras ${stream.evals.toLocaleString("es")} evaluaciones (${ms.toFixed(0)} ms).`;
    actualizarBotonDetener();
    const autoplay = !REDUCED;
    setPlay(autoplay);
    if (!autoplay) anim.t = 1;
    dibujar();
    return;
  }
  stream.timer = setTimeout(bombear, 0);
}

function pintarPanelVacio() {
  for (const k of ["stN", "stCosto", "stEvals", "stBrecha", "stTiempo"]) els[k].textContent = "—";
  els.fbCosto.textContent = els.fbEvals.textContent = "—";
  els.nnCosto.textContent = els.nnEvals.textContent = "—";
  els.pyOrden.textContent = "orden: —";
  els.pyCosto.textContent = "costo: —";
}

function pintarPanel(ms) {
  const n = puntos.length;
  els.stN.textContent = String(n);
  if (!solucion || !solucion.orden) {
    els.stCosto.textContent = "explorando…";
    els.stEvals.textContent = `0 en vivo / ${espacioTexto(n)}`;
    els.stBrecha.textContent = "—";
    els.stTiempo.textContent = `${ms.toFixed(0)} ms`;
  } else if (solucion.exacto) {
    els.stCosto.textContent = `${fmtCosto(solucion.costo)} (óptimo)`;
    els.stEvals.textContent = `${solucion.evaluaciones.toLocaleString("es")} = (${n}−1)!`;
    const brecha = solucion.costo > 0 ? ((vecino.costo - solucion.costo) / solucion.costo) * 100 : 0;
    els.stBrecha.textContent = `${brecha.toFixed(1)} %`;
  } else {
    const marca = solucion.detenido ? "detenido" : "mejor vivo";
    els.stCosto.textContent = `${fmtCosto(solucion.costo)} (${marca})`;
    els.stEvals.textContent = `${solucion.evaluaciones.toLocaleString("es")} en vivo / ${espacioTexto(n)}`;
    els.stBrecha.textContent = "sin fin garantizado";
  }
  els.stTiempo.textContent = `${ms.toFixed(0)} ms`;
  els.fbCosto.textContent = solucion && solucion.orden ? fmtCosto(solucion.costo) : "en vivo…";
  els.fbEvals.textContent = solucion ? solucion.evaluaciones.toLocaleString("es") : "—";
  els.nnCosto.textContent = vecino ? fmtCosto(vecino.costo) : "—";
  els.nnEvals.textContent = vecino ? `${vecino.evaluaciones} pasos` : "—";
  if (solucion && solucion.orden) {
    els.pyOrden.textContent = `orden: ${ordenCerrado(solucion.orden)}`;
    els.pyCosto.textContent = `costo: ${fmtCosto(solucion.costo)}`;
  }
}

/* ---------- canvas ---------- */
function ajustarCanvas() {
  const dpr = Math.min(2, devicePixelRatio || 1);
  const r = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.round(r.width * dpr));
  canvas.height = Math.max(1, Math.round(r.height * dpr));
  dibujar();
}
addEventListener("resize", ajustarCanvas);

const aPx = (p) => ({ x: p.x * canvas.width, y: p.y * canvas.height });

function dibujar() {
  actualizarAviso3D();
  const W = canvas.width, H = canvas.height;
  const n = puntos.length;
  const lod = n > 64; // LOD: sin etiquetas ni brillos, solo puntos+líneas
  // fondo + retícula tenue
  ctx.clearRect(0, 0, W, H);
  ctx.strokeStyle = "#ffffff10";
  ctx.lineWidth = 1;
  const stepX = W / 8, stepY = H / 8;
  ctx.beginPath();
  for (let i = 1; i < 8; i++) { ctx.moveTo(i * stepX, 0); ctx.lineTo(i * stepX, H); ctx.moveTo(0, i * stepY); ctx.lineTo(W, i * stepY); }
  ctx.stroke();

  if (stream && stream.actual && n >= 2) dibujarCandidato();
  if (solucion && solucion.orden && n >= 2) dibujarTour(lod);
  // ciudades
  puntos.forEach((p, i) => {
    const { x, y } = aPx(p);
    const R = Math.max(4, W / 160);
    if (lod) {
      ctx.fillStyle = i === 0 ? "#ffe9b8" : "#ffd97a";
      ctx.beginPath(); ctx.arc(x, y, R * 0.7, 0, 7); ctx.fill();
      return;
    }
    const R2 = Math.max(10, W / 90);
    const grad = ctx.createRadialGradient(x, y, 0, x, y, R2 * 2.4);
    grad.addColorStop(0, "#ffd97a");
    grad.addColorStop(0.45, "#ffb340aa");
    grad.addColorStop(1, "#ffb34000");
    ctx.fillStyle = grad;
    ctx.beginPath(); ctx.arc(x, y, R2 * 2.4, 0, 7); ctx.fill();
    ctx.fillStyle = i === 0 ? "#ffe9b8" : "#1b1440";
    ctx.strokeStyle = "#ffd97a"; ctx.lineWidth = Math.max(2, R2 / 5);
    ctx.beginPath(); ctx.arc(x, y, R2, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = i === 0 ? "#7a4d00" : "#ffd97a";
    ctx.font = `700 ${Math.round(R2 * 1.1)}px ui-monospace, Menlo, monospace`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(String(i), x, y + 1);
  });

  if (solucion && solucion.orden && anim.playing) dibujarHormiga();
}

function rutaPx(orden) {
  const pts = orden.map((i) => aPx(puntos[i]));
  pts.push(pts[0]);
  return pts;
}

/** Candidato actual tenue: lo que se está evaluando ahora mismo. */
function dibujarCandidato() {
  if (!stream || !stream.actual) return;
  if (solucion && solucion.orden && stream.actual === solucion.orden) return;
  const pts = rutaPx(stream.actual);
  ctx.save();
  ctx.lineJoin = "round"; ctx.lineCap = "round";
  ctx.shadowBlur = 0;
  ctx.strokeStyle = "#b9a7ff"; ctx.globalAlpha = 0.28;
  ctx.lineWidth = Math.max(1, canvas.width / 700);
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let s = 1; s < pts.length; s++) ctx.lineTo(pts[s].x, pts[s].y);
  ctx.stroke();
  ctx.restore();
}

function dibujarTour(lod) {
  const pts = rutaPx(solucion.orden);
  const prog = solucion.orden.length > 0 ? anim.t : 1;
  // halo ámbar bioluminiscente
  ctx.save();
  ctx.lineJoin = "round"; ctx.lineCap = "round";
  ctx.shadowColor = "#ffb340"; ctx.shadowBlur = (REDUCED || lod) ? 0 : 18;
  ctx.strokeStyle = "#ffb340"; ctx.lineWidth = Math.max(2.5, canvas.width / 320);
  ctx.globalAlpha = 0.95;
  ctx.beginPath();
  const total = pts.length - 1;
  const upto = Math.max(1, Math.floor(prog * total) + 1);
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let s = 1; s <= upto && s < pts.length; s++) {
    if (s === upto && prog * total < s) {
      const f = prog * total - (s - 1);
      ctx.lineTo(pts[s - 1].x + (pts[s].x - pts[s - 1].x) * f, pts[s - 1].y + (pts[s].y - pts[s - 1].y) * f);
    } else ctx.lineTo(pts[s].x, pts[s].y);
  }
  ctx.stroke();
  // rastro ya recorrido, más fino y caliente
  ctx.shadowBlur = 0; ctx.strokeStyle = "#ffe6b3"; ctx.lineWidth = Math.max(1, canvas.width / 700);
  ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.restore();
}

function dibujarHormiga() {
  const pts = rutaPx(solucion.orden);
  const total = pts.length - 1;
  const ft = (anim.t * total) % total;
  const s = Math.floor(ft), f = ft - s;
  const x = pts[s].x + (pts[s + 1].x - pts[s].x) * f;
  const y = pts[s].y + (pts[s + 1].y - pts[s].y) * f;
  ctx.save();
  ctx.shadowColor = "#ffd97a"; ctx.shadowBlur = REDUCED ? 0 : 22;
  ctx.fillStyle = "#fff3d6";
  ctx.beginPath(); ctx.arc(x, y, Math.max(4, canvas.width / 160), 0, 7); ctx.fill();
  ctx.restore();
}

/* ---------- animación ---------- */
function velocidad() { return els.vel.value / 100; } // 0.01..1
function tick(now) {
  if (!anim.playing) return;
  const dt = Math.min(0.1, (now - anim.last) / 1000);
  anim.last = now;
  const vueltasPorSeg = 0.06 + velocidad() * 0.5; // tour completo en ~2–16 s
  anim.t = (anim.t + dt * vueltasPorSeg) % 1;
  dibujar();
  anim.raf = requestAnimationFrame(tick);
}
function setPlay(on) {
  if (!solucion) on = false;
  anim.playing = on;
  els.play.textContent = on ? "❚❚ pausar" : "▶ reproducir";
  els.play.setAttribute("aria-pressed", String(on));
  cancelAnimationFrame(anim.raf);
  if (on) { anim.last = performance.now(); anim.raf = requestAnimationFrame(tick); }
  else dibujar();
}
function paso() {
  if (!solucion || !solucion.orden) return;
  setPlay(false);
  const total = solucion.orden.length;
  anim.paso = (anim.paso + 1) % total;
  anim.t = anim.paso / total;
  dibujar();
}
function pasoAtras() {
  if (!solucion || !solucion.orden) return;
  setPlay(false);
  const total = solucion.orden.length;
  anim.paso = (anim.paso - 1 + total) % total;
  anim.t = anim.paso / total;
  dibujar();
}

/* ---------- interacción: clic / drag / doble-clic ---------- */
function eventoAPunto(ev) {
  const r = canvas.getBoundingClientRect();
  return {
    x: Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width)),
    y: Math.min(1, Math.max(0, (ev.clientY - r.top) / r.height)),
  };
}
function indiceCercano(p, radioPx = 22) {
  const r = canvas.getBoundingClientRect();
  let best = -1, bd = Infinity;
  puntos.forEach((q, i) => {
    const d = Math.hypot((q.x - p.x) * r.width, (q.y - p.y) * r.height);
    if (d < radioPx && d < bd) { bd = d; best = i; }
  });
  return best;
}

canvas.addEventListener("pointerdown", (ev) => {
  canvas.focus();
  const p = eventoAPunto(ev);
  const idx = indiceCercano(p);
  downPos = p;
  if (idx >= 0) { drag = { idx, movido: false }; canvas.setPointerCapture(ev.pointerId); }
});
canvas.addEventListener("pointermove", (ev) => {
  if (!drag) return;
  const p = eventoAPunto(ev);
  if (Math.hypot(p.x - downPos.x, p.y - downPos.y) > 0.005) drag.movido = true;
  puntos[drag.idx] = p;
  dibujar();
});
canvas.addEventListener("pointerup", (ev) => {
  const p = eventoAPunto(ev);
  if (drag) {
    if (!drag.movido) {
      // clic sobre ciudad = seleccionar (re-centra hormiga); nada más
    } else {
      puntos[drag.idx] = p;
      cancelarSilencioso();
      solucion = null; vecino = null; pintarPanelVacio(); aviso.hidden = true;
    }
    drag = null;
    dibujar();
    return;
  }
  // clic en vacío = añadir ciudad (sin tope de nodos: el stream es lazy)
  cancelarSilencioso();
  puntos.push(p);
  solucion = null; vecino = null; pintarPanelVacio(); aviso.hidden = true;
  anim.t = 0;
  dibujar();
});
canvas.addEventListener("dblclick", (ev) => {
  const idx = indiceCercano(eventoAPunto(ev));
  if (idx >= 0) {
    puntos.splice(idx, 1);
    cancelarSilencioso();
    solucion = null; vecino = null; pintarPanelVacio(); aviso.hidden = true;
    setPlay(false); dibujar();
  }
});
canvas.addEventListener("keydown", (ev) => {
  if (ev.key === "Delete" || ev.key === "Backspace") {
    puntos.pop();
    cancelarSilencioso();
    solucion = null; pintarPanelVacio(); setPlay(false); dibujar();
  } else if (ev.key === " ") { ev.preventDefault(); setPlay(!anim.playing); }
});

/* ---------- controles ---------- */
/** Corta un stream en curso sin tocar el panel (al editar puntos). */
function cancelarSilencioso() {
  if (stream) { stream.cancelado = true; stream.terminado = true; clearTimeout(stream.timer); }
  stream = null;
  actualizarBotonDetener();
}
function generar() {
  cancelarSilencioso();
  const n = Math.max(2, parseInt(els.n.value, 10) || 5); // sin tope: streaming lazy
  els.n.value = String(n);
  const rng = mulberry32(parseInt(els.semilla.value, 10) || 0);
  puntos = Array.from({ length: n }, () => ({
    x: 0.12 + rng() * 0.76,
    y: 0.12 + rng() * 0.76,
  }));
  solucion = null; vecino = null; anim.t = 0;
  pintarPanelVacio(); aviso.hidden = true; setPlay(false); dibujar();
}

$("btn-generar").addEventListener("click", generar);
$("btn-cuadrado").addEventListener("click", () => {
  cancelarSilencioso();
  els.n.value = "4";
  puntos = [{ x: 0.2, y: 0.2 }, { x: 0.8, y: 0.2 }, { x: 0.8, y: 0.8 }, { x: 0.2, y: 0.8 }];
  solucion = null; vecino = null; anim.t = 0;
  pintarPanelVacio(); aviso.hidden = true; setPlay(false); dibujar();
});
$("btn-resolver").addEventListener("click", resolver);
$("btn-detener").addEventListener("click", () => detenerStream("detenido por el usuario"));
/** El botón Detener solo tiene sentido mientras el stream bombea. */
function actualizarBotonDetener() {
  const btn = $("btn-detener");
  if (!btn) return;
  const vivo = Boolean(stream && !stream.terminado);
  btn.disabled = !vivo;
  btn.setAttribute("aria-disabled", String(!vivo));
}
els.play.addEventListener("click", () => setPlay(!anim.playing));
$("btn-paso").addEventListener("click", paso);
$("btn-paso-atras").addEventListener("click", pasoAtras);
$("btn-limpiar").addEventListener("click", () => { anim.t = 0; anim.paso = 0; setPlay(false); });
$("btn-copiar").addEventListener("click", async () => {
  if (!solucion || !solucion.orden) return;
  const txt = `orden: ${ordenCerrado(solucion.orden)}\ncosto: ${fmtCosto(solucion.costo)}`;
  try { await navigator.clipboard.writeText(txt); $("btn-copiar").textContent = "¡copiado!"; }
  catch { $("btn-copiar").textContent = "copia manual ↑"; }
  setTimeout(() => { $("btn-copiar").textContent = "copiar para corregir"; }, 1600);
});

/* ---------- init ---------- */
generar();
ajustarCanvas();
requestAnimationFrame(() => ajustarCanvas());
