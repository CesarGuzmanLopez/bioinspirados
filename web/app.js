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
  stCand: $("st-cand"), stRitmo: $("st-ritmo"),
  stBrecha: $("st-brecha"), stTiempo: $("st-tiempo"),
  fbCosto: $("cmp-fb-costo"), fbEvals: $("cmp-fb-evals"),
  nnCosto: $("cmp-nn-costo"), nnEvals: $("cmp-nn-evals"),
  pyOrden: $("py-orden"), pyCosto: $("py-costo"),
  play: $("btn-play"), vel: $("velocidad"), tempoVal: $("tempo-val"),
  chkCand: $("chk-candidato"),
};

/* ---------- estado ---------- */
let puntos = [];            // [{x,y} en [0,1]^2]
let solucion = null;        // {orden:[...abierto], costo, metodo, evaluaciones, ms, exacto}
let vecino = null;          // {orden, costo} comparativa
let stream = null;          // {gen, n, total, mejor, mejorCosto, actual, actualCosto,
                            //  evals, t0, terminado, cancelado, pausado, timer,
                            //  historial:[{orden,costo}], vista, verCandidato}
let anim = { t: 0, playing: false, raf: 0, last: 0, paso: 0 };
let drag = null;            // {idx, movido}
let downPos = null;
/* Historial acotado para paso →/←: n≤8 guarda todo ((n−1)!≤5040);
   si no, ventana de los últimos 20000 candidatos. El óptimo ámbar
   nunca depende del historial: siempre visible. */
const HIST_MAX = 20000;

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
/* ---------- tempo real: ms por evaluación ---------- */
/** Slider = ms que tarda en PROBAR cada solución (500 lento … 1 rápido). */
function msPorEval() {
  const v = parseInt(els.vel.value, 10);
  return Math.min(500, Math.max(1, Number.isFinite(v) ? v : 60));
}
function pintarTempo() {
  if (els.tempoVal) els.tempoVal.textContent = `${msPorEval()} ms/eval`;
}
/** Ritmo real medido: evals / segundo desde t0. */
function ritmoReal() {
  if (!stream) return 0;
  const s = (performance.now() - stream.t0) / 1000;
  return s > 0 ? stream.evals / s : 0;
}

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
    gen: toursLazy(n), n, total: null, mejor: null, mejorCosto: Infinity,
    actual: null, actualCosto: Infinity,
    evals: 0, t0: performance.now(), terminado: false, cancelado: false,
    pausado: REDUCED, timer: 0, historial: [], vista: -1,
    verCandidato: els.chkCand ? els.chkCand.checked : true,
  };
  try {
    let f = 1;
    for (let i = 2; i <= n - 1; i++) { f *= i; if (!isFinite(f) || f > 1e15) { f = Infinity; break; } }
    stream.total = isFinite(f) ? f : null;
  } catch { stream.total = null; }
  solucion = null;
  anim.t = 0; anim.paso = 0;
  const grande = n > 10;
  aviso.hidden = false;
  aviso.textContent = grande
    ? `n=${n} → ${espacioTexto(n)} tours: streaming sin fin garantizado, puedes detener cuando quieras`
    : `explorando ${(espacioTexto(n))} tours en vivo…`;
  actualizarAviso3D();
  actualizarBotonDetener();
  pintarTempo();
  // Sin autoplay con prefers-reduced-motion: queda pausado en eval 0.
  setPlay(!REDUCED);
  if (REDUCED) { pintarPanel(0); dibujar(); }
}

/** Hook 3D: n>200 sugiere la vista 3D (web/3d-viewer/) sin bloquear la 2D.
 *  El enlace arrastra n+semilla (?n=&semilla=) para replicar la instancia. */
function actualizarAviso3D() {
  if (!aviso3d) return;
  const mostrar = puntos.length > 200;
  aviso3d.hidden = !mostrar;
  if (mostrar) {
    const a = aviso3d.querySelector("a");
    if (a) {
      const semilla = els.semilla ? els.semilla.value : "42";
      a.href = `3d-viewer/index.html?n=${puntos.length}&semilla=${encodeURIComponent(semilla)}`;
    }
  }
}

/** Guarda el candidato en el historial acotado (para paso →/←). */
function archivarCandidato(orden, costo) {
  if (!stream) return;
  stream.historial.push({ orden: [...orden], costo });
  if (stream.historial.length > HIST_MAX) stream.historial.shift();
  stream.vista = stream.historial.length - 1;
}

/** Evalúa UN tour: avanza el generador, mide costo, actualiza mejor (< estricto).
 *  Devuelve false si se agotó la enumeración. */
function evaluarUno() {
  const sig = stream.gen.next();
  if (sig.done) return false;
  const orden = sig.value;
  const c = costoDe(orden);
  stream.actual = [...orden];
  stream.actualCosto = c;
  stream.evals++;
  archivarCandidato(orden, c);
  if (c < stream.mejorCosto) { stream.mejorCosto = c; stream.mejor = [...orden]; } // < estricto
  return true;
}

function publicarMs() { return performance.now() - stream.t0; }

function terminarStream(avanzada) {
  const ms = publicarMs();
  solucion = {
    orden: stream.mejor ? [...stream.mejor] : null, costo: stream.mejorCosto,
    metodo: "fuerza bruta (vivo)", exacto: avanzada,
    evaluaciones: stream.evals, ms, detenido: false,
  };
  stream.terminado = true;
  pintarPanel(ms);
  actualizarBotonDetener();
  dibujar();
  if (avanzada) {
    aviso.textContent = `óptimo exacto tras ${stream.evals.toLocaleString("es")} evaluaciones (${ms.toFixed(0)} ms).`;
    setPlay(false);
    if (!REDUCED) setPlay(true); // terminado: solo anima la hormiga
    dibujar();
  }
}

/** Reprograma el siguiente tick según el tempo (ms por evaluación). */
function programar() {
  if (!stream || stream.cancelado || stream.terminado || stream.pausado) return;
  clearTimeout(stream.timer);
  const ms = msPorEval();
  stream.timer = setTimeout(tickEval, ms >= 16 ? ms : 16);
}

/** Tick de evaluación con tempo real: 1 tour por tick en lento (≥16 ms);
 *  en rápido (<16 ms) evalúa un chunk por frame (~16 ms de evaluaciones)
 *  para no colgar la UI. El óptimo ámbar nunca se borra; el candidato
 *  violeta tenue muestra lo que se está probando ahora. */
function tickEval() {
  if (!stream || stream.cancelado || stream.terminado || stream.pausado) return;
  const ms = msPorEval();
  if (ms >= 16) {
    if (!evaluarUno()) { terminarStream(true); return; }
  } else {
    // Rápido: chunk por frame (~16 ms de evaluaciones) para no colgar.
    const chunk = Math.min(50000, Math.max(1, Math.round(16 / ms)));
    const fin = performance.now() + 24; // presupuesto por frame
    let hechos = 0, agotado = false;
    while (hechos < chunk && performance.now() < fin) {
      if (!evaluarUno()) { agotado = true; break; }
      hechos++;
    }
    if (agotado || hechos === 0) { terminarStream(true); return; }
  }
  const t = publicarMs();
  solucion = {
    orden: stream.mejor ? [...stream.mejor] : null, costo: stream.mejorCosto,
    metodo: "fuerza bruta (vivo)", exacto: false,
    evaluaciones: stream.evals, ms: t, detenido: false,
  };
  pintarPanel(t);
  dibujar();
  programar();
}

/** Compat: el bucle antiguo se llamaba bombear(); ahora es programar(). */
function bombear() { programar(); }

function pintarPanelVacio() {
  for (const k of ["stN", "stCosto", "stEvals", "stCand", "stRitmo", "stBrecha", "stTiempo"]) {
    if (els[k]) els[k].textContent = "—";
  }
  els.fbCosto.textContent = els.fbEvals.textContent = "—";
  els.nnCosto.textContent = els.nnEvals.textContent = "—";
  els.pyOrden.textContent = "orden: —";
  els.pyCosto.textContent = "costo: —";
}

function fmtEval(i, n) {
  const total = stream && stream.total != null
    ? stream.total.toLocaleString("es")
    : espacioTexto(n);
  return `${i.toLocaleString("es")} / ${total}`;
}

function pintarPanel(ms) {
  const n = puntos.length;
  els.stN.textContent = String(n);
  if (!solucion || !solucion.orden) {
    els.stCosto.textContent = "explorando…";
    els.stEvals.textContent = stream ? fmtEval(stream.evals, n) : `0 en vivo / ${espacioTexto(n)}`;
    els.stBrecha.textContent = "—";
    els.stTiempo.textContent = `${ms.toFixed(0)} ms`;
    if (els.stCand) {
      els.stCand.textContent = stream && stream.actual
        ? `${ordenCerrado(stream.actual)} · ${fmtCosto(stream.actualCosto)}`
        : "—";
    }
    if (els.stRitmo) els.stRitmo.textContent = stream ? `${ritmoReal().toFixed(1)} tours/s` : "—";
  } else if (solucion.exacto) {
    els.stCosto.textContent = `${fmtCosto(solucion.costo)} (óptimo)`;
    els.stEvals.textContent = `${solucion.evaluaciones.toLocaleString("es")} = (${n}−1)!`;
    const brecha = solucion.costo > 0 ? ((vecino.costo - solucion.costo) / solucion.costo) * 100 : 0;
    els.stBrecha.textContent = `${brecha.toFixed(1)} %`;
    if (els.stCand) {
      els.stCand.textContent = stream && stream.actual
        ? `${ordenCerrado(stream.actual)} · ${fmtCosto(stream.actualCosto)}`
        : `óptimo ${ordenCerrado(solucion.orden)}`;
    }
    if (els.stRitmo) {
      els.stRitmo.textContent = stream
        ? `${ritmoReal().toFixed(1)} tours/s`
        : `${solucion.evaluaciones.toLocaleString("es")} evals`;
    }  } else {
    const marca = solucion.detenido ? "detenido" : "mejor vivo";
    els.stCosto.textContent = `${fmtCosto(solucion.costo)} (${marca})`;
    els.stEvals.textContent = stream ? fmtEval(stream.evals, n)
      : `${solucion.evaluaciones.toLocaleString("es")} en vivo / ${espacioTexto(n)}`;
    els.stBrecha.textContent = "sin fin garantizado";
    if (els.stCand) {
      els.stCand.textContent = stream && stream.actual
        ? `${ordenCerrado(stream.actual)} · ${fmtCosto(stream.actualCosto)}`
        : "—";
    }
    if (els.stRitmo) {
      els.stRitmo.textContent = stream
        ? `${ritmoReal().toFixed(1)} tours/s · ${msPorEval()} ms/eval`
        : `${solucion.evaluaciones.toLocaleString("es")} evals`;
    }
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

/** Candidato actual tenue (violeta): lo que se está probando ahora mismo.
 *  El óptimo ámbar (dibujarTour) siempre se pinta encima: nunca se borra. */
function dibujarCandidato() {
  if (!stream || !stream.actual) return;
  if (els.chkCand && !els.chkCand.checked) return;
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
  // Óptimo fijo siempre completo; solo se revela por tramos mientras anima.
  const prog = anim.playing ? anim.t : 1;
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

/* ---------- animación (hormiga sobre el óptimo; el tempo lo da el slider) ---------- */
function tick(now) {
  if (!anim.playing) return;
  const dt = Math.min(0.1, (now - anim.last) / 1000);
  anim.last = now;
  const vueltasPorSeg = 0.25; // una vuelta cada ~4 s; la velocidad de
  anim.t = (anim.t + dt * vueltasPorSeg) % 1; // evaluación la marca ms/eval
  dibujar();
  anim.raf = requestAnimationFrame(tick);
}
/** Reproducir = reanuda la evaluación con tempo + anima la hormiga.
 *  Pausar = congela la evaluación (el óptimo y el candidato quedan fijos). */
function setPlay(on) {
  if (on && !stream) on = false;
  if (on && stream && (stream.terminado || stream.cancelado)) {
    // Stream agotado/detenido: solo anima la hormiga sobre el óptimo.
    anim.playing = !REDUCED ? true : false;
    els.play.textContent = anim.playing ? "❚❚ pausar" : "▶ reproducir";
    els.play.setAttribute("aria-pressed", String(anim.playing));
    cancelAnimationFrame(anim.raf);
    if (anim.playing) { anim.last = performance.now(); anim.raf = requestAnimationFrame(tick); }
    else dibujar();
    return;
  }
  if (stream) {
    stream.pausado = !on;
    clearTimeout(stream.timer);
  }
  anim.playing = on && !REDUCED;
  els.play.textContent = on ? "❚❚ pausar" : "▶ reproducir";
  els.play.setAttribute("aria-pressed", String(on));
  cancelAnimationFrame(anim.raf);
  if (anim.playing) { anim.last = performance.now(); anim.raf = requestAnimationFrame(tick); }
  else dibujar();
  if (on && stream && !stream.terminado && !stream.cancelado) programar();
  actualizarBotonDetener();
}
/** Paso →: avanza un candidato en el historial (pausa primero).
 *  El óptimo ámbar se mantiene; solo cambia el violeta tenue. */
function paso() {
  if (!stream || !stream.historial.length) return;
  if (!stream.pausado && !stream.terminado) setPlay(false);
  if (stream.vista < stream.historial.length - 1) stream.vista++;
  mostrarVista();
}
/** ← paso: retrocede un candidato en el historial (pausa primero). */
function pasoAtras() {
  if (!stream || !stream.historial.length) return;
  if (!stream.pausado && !stream.terminado) setPlay(false);
  if (stream.vista > 0) stream.vista--;
  mostrarVista();
}
function mostrarVista() {
  const h = stream.historial[stream.vista];
  if (!h) return;
  stream.actual = [...h.orden];
  stream.actualCosto = h.costo;
  pintarPanel(publicarMs());
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
  } else if (ev.key === " ") {
    ev.preventDefault();
    const enMarcha = stream ? !stream.pausado && !stream.terminado : anim.playing;
    setPlay(!enMarcha);
  }
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
/** El botón Detener solo tiene sentido mientras el stream bombea o está pausado. */
function actualizarBotonDetener() {
  const btn = $("btn-detener");
  if (!btn) return;
  const vivo = Boolean(stream && !stream.terminado && !stream.cancelado);
  btn.disabled = !vivo;
  btn.setAttribute("aria-disabled", String(!vivo));
}
els.play.addEventListener("click", () => {
  const enMarcha = stream ? !stream.pausado && !stream.terminado : anim.playing;
  setPlay(!enMarcha);
});
$("btn-paso").addEventListener("click", paso);
$("btn-paso-atras").addEventListener("click", pasoAtras);
if (els.vel) els.vel.addEventListener("input", pintarTempo);
const tempo = (ms) => { if (els.vel) { els.vel.value = String(ms); pintarTempo(); } };
$("btn-lento").addEventListener("click", () => tempo(500));
$("btn-normal").addEventListener("click", () => tempo(60));
$("btn-rapido").addEventListener("click", () => tempo(1));
if (els.chkCand) els.chkCand.addEventListener("change", dibujar);
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
pintarTempo();
ajustarCanvas();
requestAnimationFrame(() => ajustarCanvas());
