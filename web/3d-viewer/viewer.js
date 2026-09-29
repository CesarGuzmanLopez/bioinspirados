/* lab_bioinspirados · visor 3D experimental. WebGL2 crudo, sin three.js ni build.
   100% cliente. Lee la misma nube que web/app.js: mulberry32(semilla),
   puntos en [0.12, 0.88]^3. Dibuja gl.POINTS + gl.LINE_STRIP del mejor tour
   (candidato tenue violeta + óptimo/mejor fijo ámbar, igual que el 2D).
   Órbita con drag, zoom con rueda. LOD: n>5000 solo puntos + meta-tour.
   Sin WebGL2: mensaje claro + enlace de vuelta a ../index.html (nunca negro). */
"use strict";

const $ = (id) => document.getElementById(id);
const els = {
  canvas: $("visor"), sin: $("sin-webgl"), lod: $("aviso-lod"),
  n: $("in-n"), semilla: $("in-semilla"),
  stN: $("st-n"), stCosto: $("st-costo"), stEvals: $("st-evals"),
  stCand: $("st-cand"), stRitmo: $("st-ritmo"), stTiempo: $("st-tiempo"),
  play: $("btn-play"), vel: $("velocidad"), tempoVal: $("tempo-val"),
  chkCand: $("chk-candidato"),
};

const LOD_N = 5000;      // LOD: a partir de aquí solo puntos + meta-tour
const META_K = 256;      // centros del meta-tour en modo LOD
const NN_EXACTO_MAX = 2000; // vecino-cercano exacto hasta aquí; luego muestreado
const MUESTRA_NN = 512;  // candidatos por paso en NN muestreado

/* ---------- datos: mismo PRNG y rango que web/app.js ---------- */
function mulberry32(semilla) {
  let a = semilla >>> 0;
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const dist3 = (a, b) =>
  Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
function costoDe(pts, orden) {
  let c = 0;
  for (let i = 0; i < orden.length; i++)
    c += dist3(pts[orden[i]], pts[orden[(i + 1) % orden.length]]);
  return c;
}
const ordenCerrado = (orden) => [...orden, orden[0]].join(" → ");
function fmtCosto(c) {
  if (!isFinite(c)) return "—";
  return String(Number(c.toPrecision(6)));
}

/* ---------- estado ---------- */
let puntos = [];        // [{x,y,z} en [0.12,0.88]^3]
let solucion = null;    // {orden, costo, metodo, exacto, evaluaciones, ms}
let stream = null;      // animación del solver (FB o NN incremental)
let cam = { yaw: 0.6, pitch: 0.5, dist: 3.2 };

function msPorEval() {
  const v = parseInt(els.vel.value, 10);
  return Math.min(500, Math.max(1, Number.isFinite(v) ? v : 60));
}
function pintarTempo() {
  if (els.tempoVal) els.tempoVal.textContent = `${msPorEval()} ms/eval`;
}

/* ---------- solvers (misma semántica que app.js / Python) ---------- */
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
function* toursLazy(n) {
  const resto = [];
  for (let i = 1; i < n; i++) resto.push(i);
  yield [0, ...resto];
  while (siguientePermutacion(resto)) yield [0, ...resto];
}
/** Un paso de vecino-cercano desde el parcial `st`. Devuelve el elegido. */
function pasoNN(st) {
  const { pts, orden, vis } = st;
  const n = pts.length;
  const u = orden[orden.length - 1];
  // Recuento de no visitados para decidir escaneo exacto o muestreado.
  let pendientes = 0;
  for (let v = 0; v < n; v++) if (!vis[v]) pendientes++;
  let best = -1, bd = Infinity;
  const probar = (v) => {
    const d = dist3(pts[u], pts[v]);
    if (d < bd) { bd = d; best = v; } // < estricto: el primero gana
  };
  if (pendientes <= NN_EXACTO_MAX) {
    for (let v = 0; v < n; v++) if (!vis[v]) probar(v);
  } else {
    // Muestreado: 512 candidatos al azar (rng propio, no toca la nube).
    let v = (st.cursor * 7919) % n;
    for (let k = 0; k < MUESTRA_NN; k++) {
      v = (v * 1103515245 + 12345) & 0x7fffffff;
      const c = v % n;
      if (!vis[c]) probar(c);
    }
    // El cursor evita repetir el mismo subconjunto cada paso.
    st.cursor = (st.cursor * 1103515245 + 12345) & 0x7fffffff;
    if (best < 0) for (let c = 0; c < n; c++) if (!vis[c]) { best = c; break; }
  }
  orden.push(best); vis[best] = true;
  return best;
}
/** Tour completo válido con el parcial NN + resto en orden de índice. */
function candidatoNN(st) {
  const resto = [];
  for (let v = 0; v < st.pts.length; v++) if (!st.vis[v]) resto.push(v);
  return [...st.orden, ...resto];
}

/* ---------- WebGL2 (fallo → mensaje + vuelta al 2D, nunca negro) ---------- */
let gl = null, prog = null, loc = null, bufPos = null;
function initGL() {
  try {
    gl = els.canvas.getContext("webgl2", { antialias: true });
  } catch {
    gl = null;
  }
  if (!gl) {
    els.canvas.hidden = true;
    els.sin.hidden = false;
    return false;
  }
  const vs = `#version 300 es
    layout(location=0) in vec3 a_pos;
    uniform mat4 u_mvp;
    uniform float u_px;
    void main(){ gl_Position = u_mvp * vec4(a_pos, 1.0); gl_PointSize = u_px; }`;
  const fs = `#version 300 es
    precision mediump float;
    uniform vec4 u_color;
    uniform float u_circle;
    out vec4 o;
    void main(){
      if (u_circle > 0.5) {
        vec2 c = gl_PointCoord - 0.5;
        if (dot(c, c) > 0.25) discard;
      }
      o = u_color;
    }`;
  const compilar = (tipo, src) => {
    const s = gl.createShader(tipo);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) return null;
    return s;
  };
  const v = compilar(gl.VERTEX_SHADER, vs);
  const f = compilar(gl.FRAGMENT_SHADER, fs);
  if (!v || !f) return falloGL();
  prog = gl.createProgram();
  gl.attachShader(prog, v);
  gl.attachShader(prog, f);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return falloGL();
  gl.useProgram(prog);
  loc = {
    mvp: gl.getUniformLocation(prog, "u_mvp"),
    px: gl.getUniformLocation(prog, "u_px"),
    color: gl.getUniformLocation(prog, "u_color"),
    circle: gl.getUniformLocation(prog, "u_circle"),
  };
  bufPos = gl.createBuffer();
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  gl.enable(gl.DEPTH_TEST);
  return true;
}
function falloGL() {
  gl = null;
  els.canvas.hidden = true;
  els.sin.hidden = false;
  return false;
}

/* ---------- mates mínimas (sin librerías) ---------- */
function mvp() {
  const a = els.canvas.width / Math.max(1, els.canvas.height);
  const f = 1 / Math.tan((45 * Math.PI) / 360);
  const near = 0.1, far = 100;
  // Proyección perspectiva.
  const P = [f / a, 0, 0, 0, 0, f, 0, 0, 0, 0,
    (far + near) / (near - far), -1, 0, 0, (2 * far * near) / (near - far), 0];
  const cy = Math.cos(cam.yaw), sy = Math.sin(cam.yaw);
  const cx = Math.cos(cam.pitch), sx = Math.sin(cam.pitch);
  // Modelo: R = Ry(yaw) * Rx(pitch), luego traslación -dist en z.
  const R = [
    cy, sy * sx, -sy * cx, 0,
    0, cx, sx, 0,
    sy, -cy * sx, cy * cx, 0,
    0, 0, -cam.dist, 1,
  ];
  // M = P * R (column-major).
  const M = new Float32Array(16);
  for (let c = 0; c < 4; c++)
    for (let r = 0; r < 4; r++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += P[k * 4 + r] * R[c * 4 + k];
      M[c * 4 + r] = s;
    }
  return M;
}
const aXYZ = (p) => [(p.x * 2 - 1) * 1.2, (p.y * 2 - 1) * 1.2, (p.z * 2 - 1) * 1.2];
function subir(arr) {
  gl.bindBuffer(gl.ARRAY_BUFFER, bufPos);
  gl.bufferData(gl.ARRAY_BUFFER, arr, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
}
function dibujar() {
  if (!gl) return;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  const r = els.canvas.getBoundingClientRect();
  const W = Math.max(1, Math.round(r.width * dpr));
  const H = Math.max(1, Math.round(r.height * dpr));
  if (els.canvas.width !== W || els.canvas.height !== H) {
    els.canvas.width = W; els.canvas.height = H;
  }
  gl.viewport(0, 0, els.canvas.width, els.canvas.height);
  gl.clearColor(0.06, 0.07, 0.23, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.uniformMatrix4fv(loc.mvp, false, mvp());
  const n = puntos.length;
  if (!n) return;
  const lod = n > LOD_N;

  // 1) Puntos.
  const pos = new Float32Array(n * 3);
  puntos.forEach((p, i) => {
    const [x, y, z] = aXYZ(p);
    pos[i * 3] = x; pos[i * 3 + 1] = y; pos[i * 3 + 2] = z;
  });
  subir(pos);
  gl.uniform1f(loc.px, n > 2000 ? 2.0 : 5.0);
  gl.uniform1f(loc.circle, 1);
  gl.uniform4f(loc.color, 1.0, 0.85, 0.48, 1);
  gl.drawArrays(gl.POINTS, 0, n);

  // 2) Candidato tenue (violeta): lo que se está probando ahora.
  const verCand = els.chkCand ? els.chkCand.checked : true;
  const cand = stream && stream.actual;
  if (!lod && verCand && cand && cand.length >= 2) {
    const lp = new Float32Array((cand.length + 1) * 3);
    cand.forEach((idx, k) => {
      const [x, y, z] = aXYZ(puntos[idx]);
      lp[k * 3] = x; lp[k * 3 + 1] = y; lp[k * 3 + 2] = z;
    });
    const [x0, y0, z0] = aXYZ(puntos[cand[0]]);
    lp[cand.length * 3] = x0; lp[cand.length * 3 + 1] = y0; lp[cand.length * 3 + 2] = z0;
    subir(lp);
    gl.uniform1f(loc.px, 1);
    gl.uniform1f(loc.circle, 0);
    gl.uniform4f(loc.color, 0.73, 0.65, 1.0, 0.28);
    gl.drawArrays(gl.LINE_STRIP, 0, cand.length + 1);
  }

  // 3) Mejor tour fijo (ámbar): completo, o meta-tour en modo LOD.
  const mejor = solucion && solucion.orden;
  if (mejor && mejor.length >= 2) {
    let seq = mejor;
    if (lod) seq = metaTour();
    if (seq.length >= 2) {
      const lp = new Float32Array((seq.length + 1) * 3);
      seq.forEach((idx, k) => {
        const [x, y, z] = typeof idx === "number" ? aXYZ(puntos[idx]) : idx;
        lp[k * 3] = x; lp[k * 3 + 1] = y; lp[k * 3 + 2] = z;
      });
      lp[seq.length * 3] = lp[0]; lp[seq.length * 3 + 1] = lp[1]; lp[seq.length * 3 + 2] = lp[2];
      subir(lp);
      gl.uniform1f(loc.px, 1);
      gl.uniform1f(loc.circle, 0);
      gl.uniform4f(loc.color, 1.0, 0.7, 0.25, 0.95);
      gl.drawArrays(gl.LINE_STRIP, 0, seq.length + 1);
    }
  }
}
/** Meta-tour LOD: ≤256 centros (media por bloques) ordenados por NN. */
function metaTour() {
  const n = puntos.length;
  const bloque = Math.ceil(n / META_K);
  const centros = [];
  for (let b = 0; b * bloque < n; b++) {
    let sx = 0, sy = 0, sz = 0, m = 0;
    for (let i = b * bloque; i < Math.min(n, (b + 1) * bloque); i++) {
      sx += puntos[i].x; sy += puntos[i].y; sz += puntos[i].z; m++;
    }
    if (m) centros.push({ x: sx / m, y: sy / m, z: sz / m });
  }
  // NN sobre centros (≤256²: barato).
  const vis = new Array(centros.length).fill(false);
  const ord = [0]; vis[0] = true;
  while (ord.length < centros.length) {
    const u = ord[ord.length - 1];
    let bi = -1, bd = Infinity;
    for (let v = 0; v < centros.length; v++) {
      if (vis[v]) continue;
      const d = dist3(centros[u], centros[v]);
      if (d < bd) { bd = d; bi = v; }
    }
    ord.push(bi); vis[bi] = true;
  }
  return ord.map((i) => [centros[i].x * 2 * 1.2 - 1.2, centros[i].y * 2 * 1.2 - 1.2, centros[i].z * 2 * 1.2 - 1.2]);
}

/* ---------- resolver en streaming + panel ---------- */
function pintarPanel(ms) {
  const n = puntos.length;
  els.stN.textContent = String(n);
  if (!solucion || !solucion.orden) {
    els.stCosto.textContent = "explorando…";
    els.stEvals.textContent = stream ? `${stream.evals.toLocaleString("es")} en vivo` : "—";
    els.stCand.textContent = stream && stream.actual ? `${ordenCerrado(stream.actual).slice(0, 72)}…` : "—";
    els.stRitmo.textContent = stream ? `${ritmo().toFixed(1)} evals/s` : "—";
  } else {
    const marca = solucion.exacto ? "óptimo" : (solucion.detenido ? "detenido" : "mejor vivo");
    els.stCosto.textContent = `${fmtCosto(solucion.costo)} (${marca})`;
    els.stEvals.textContent = solucion.evaluaciones.toLocaleString("es");
    els.stCand.textContent = stream && stream.actual
      ? `${ordenCerrado(stream.actual).slice(0, 72)}… · ${fmtCosto(stream.actualCosto)}`
      : `óptimo ${ordenCerrado(solucion.orden).slice(0, 72)}…`;
    els.stRitmo.textContent = stream ? `${ritmo().toFixed(1)} evals/s · ${msPorEval()} ms/eval` : "—";
  }
  els.stTiempo.textContent = `${ms.toFixed(0)} ms`;
}
function ritmo() {
  if (!stream) return 0;
  const s = (performance.now() - stream.t0) / 1000;
  return s > 0 ? stream.evals / s : 0;
}
function evaluarFB() {
  // Un tour FB; false si se agotó.
  const sig = stream.gen.next();
  if (sig.done) return false;
  const orden = sig.value;
  const c = costoDe(puntos, orden);
  stream.actual = [...orden];
  stream.actualCosto = c;
  stream.evals++;
  if (c < stream.mejorCosto) { stream.mejorCosto = c; stream.mejor = [...orden]; }
  return true;
}
function evaluarNN() {
  // Un paso NN; false si el tour ya está completo.
  if (stream.nn.orden.length >= puntos.length) return false;
  pasoNN(stream.nn);
  stream.actual = candidatoNN(stream.nn);
  stream.actualCosto = costoDe(puntos, stream.actual);
  stream.evals++;
  if (stream.actualCosto < stream.mejorCosto) {
    stream.mejorCosto = stream.actualCosto;
    stream.mejor = [...stream.actual];
  }
  return stream.nn.orden.length < puntos.length;
}
function terminar(exacto) {
  const ms = performance.now() - stream.t0;
  solucion = {
    orden: stream.mejor ? [...stream.mejor] : null,
    costo: stream.mejorCosto, metodo: stream.modo, exacto,
    evaluaciones: stream.evals, ms, detenido: false,
  };
  stream.terminado = true;
  clearTimeout(stream.timer);
  pintarPanel(ms);
  setPlay(false);
  dibujar();
  els.lod.hidden = !(puntos.length > LOD_N);
  if (puntos.length > LOD_N)
    els.lod.textContent = `n=${puntos.length}: LOD activo — puntos + meta-tour de ${META_K} centros (el tour completo sería ilegible)`;
}
function tickEval() {
  if (!stream || stream.cancelado || stream.terminado || stream.pausado) return;
  const ms = msPorEval();
  const paso = stream.modo === "FB" ? evaluarFB : evaluarNN;
  if (ms >= 16) {
    if (!paso()) { terminar(stream.modo === "FB"); return; }
  } else {
    const chunk = Math.min(50000, Math.max(1, Math.round(16 / ms)));
    const fin = performance.now() + 24;
    let hechos = 0, vivo = true;
    while (hechos < chunk && performance.now() < fin) {
      if (!paso()) { vivo = false; break; }
      hechos++;
    }
    if (!vivo || hechos === 0) { terminar(stream.modo === "FB"); return; }
  }
  const t = performance.now() - stream.t0;
  solucion = {
    orden: stream.mejor ? [...stream.mejor] : null,
    costo: stream.mejorCosto, metodo: stream.modo, exacto: false,
    evaluaciones: stream.evals, ms: t, detenido: false,
  };
  pintarPanel(t);
  dibujar();
  programar();
}
function programar() {
  if (!stream || stream.cancelado || stream.terminado || stream.pausado) return;
  clearTimeout(stream.timer);
  const ms = msPorEval();
  stream.timer = setTimeout(tickEval, ms >= 16 ? ms : 16);
}
function resolver() {
  if (stream) { stream.cancelado = true; clearTimeout(stream.timer); }
  stream = null;
  if (puntos.length < 2) {
    solucion = null; pintarVacio(); dibujar(); return;
  }
  const n = puntos.length;
  const modo = n <= 8 ? "FB" : "NN";
  stream = {
    modo, evals: 0, t0: performance.now(), mejor: null, mejorCosto: Infinity,
    actual: null, actualCosto: Infinity, terminado: false, cancelado: false,
    pausado: false, timer: 0,
    gen: modo === "FB" ? toursLazy(n) : null,
    nn: modo === "NN"
      ? { pts: puntos, orden: [0], vis: Object.assign(new Array(n).fill(false), { 0: true }), cursor: 1 }
      : null,
  };
  solucion = null;
  els.lod.hidden = true;
  setPlay(true);
}
function pintarVacio() {
  for (const k of ["stN", "stCosto", "stEvals", "stCand", "stRitmo", "stTiempo"])
    if (els[k]) els[k].textContent = k === "stN" ? String(puntos.length) : "—";
}
function setPlay(on) {
  if (on && !stream) on = false;
  if (on && stream && stream.terminado) on = false;
  if (stream) {
    stream.pausado = !on;
    clearTimeout(stream.timer);
  }
  els.play.textContent = on ? "❚❚ pausar" : "▶ reproducir";
  els.play.setAttribute("aria-pressed", String(on));
  if (on) programar();
}

/* ---------- controles ---------- */
function generar() {
  if (stream) { stream.cancelado = true; clearTimeout(stream.timer); }
  stream = null;
  const n = Math.min(100000, Math.max(2, parseInt(els.n.value, 10) || 200));
  els.n.value = String(n);
  const rng = mulberry32(parseInt(els.semilla.value, 10) || 0);
  puntos = Array.from({ length: n }, () => ({
    x: 0.12 + rng() * 0.76,
    y: 0.12 + rng() * 0.76,
    z: 0.12 + rng() * 0.76,
  }));
  solucion = null;
  els.lod.hidden = true;
  setPlay(false);
  pintarVacio();
  els.stN.textContent = String(n);
  dibujar();
}
$("btn-generar").addEventListener("click", generar);
$("btn-resolver").addEventListener("click", resolver);
els.play.addEventListener("click", () => {
  const enMarcha = stream ? !stream.pausado && !stream.terminado : false;
  setPlay(!enMarcha);
});
if (els.vel) els.vel.addEventListener("input", pintarTempo);
if (els.chkCand) els.chkCand.addEventListener("change", dibujar);

/* ---------- órbita + zoom ---------- */
let drag = null;
els.canvas.addEventListener("pointerdown", (ev) => {
  drag = { x: ev.clientX, y: ev.clientY };
  els.canvas.setPointerCapture(ev.pointerId);
});
els.canvas.addEventListener("pointermove", (ev) => {
  if (!drag) return;
  cam.yaw += (ev.clientX - drag.x) * 0.008;
  cam.pitch = Math.min(1.4, Math.max(-1.4, cam.pitch + (ev.clientY - drag.y) * 0.008));
  drag = { x: ev.clientX, y: ev.clientY };
  dibujar();
});
els.canvas.addEventListener("pointerup", () => { drag = null; });
els.canvas.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  cam.dist = Math.min(9, Math.max(1.4, cam.dist * Math.exp(ev.deltaY * 0.001)));
  dibujar();
}, { passive: false });
window.addEventListener("resize", dibujar);

/* ---------- init (?n= ?semilla= para enlazar desde la 2D) ---------- */
(function init() {
  const q = new URLSearchParams(location.search);
  if (q.has("n")) els.n.value = q.get("n");
  if (q.has("semilla")) els.semilla.value = q.get("semilla");
  pintarTempo();
  if (!initGL()) return; // fallback visible, nada más que hacer
  generar();
})();
