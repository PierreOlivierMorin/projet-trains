#!/usr/bin/env python3
"""Génère un visualiseur CAO 3D autonome (03-cao-3d/visualiseur-assemblage.html)
embarquant en Base64 les 11 fichiers .STL binaires du dossier 03-cao-3d/stl/.

Ouvrable directement par double-clic dans Safari, Chrome ou Firefox sans serveur.
"""

import base64
from pathlib import Path

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Projet Trains V1 — Inspecteur CAO 3D (11 STL)</title>
  <style>
    :root {
      --bg: #0f131a;
      --panel: #171d27;
      --panel-2: #1f2735;
      --border: #2c374b;
      --text: #e6ecf5;
      --muted: #93a1b8;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      height: 100vh;
      display: grid;
      grid-template-columns: 310px 1fr;
      overflow: hidden;
    }
    aside {
      background: var(--panel);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .header {
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
    }
    .header h1 {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
    }
    .header p {
      margin: 4px 0 0;
      font-size: 12px;
      color: var(--muted);
    }
    .section {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
    }
    .section-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin-bottom: 8px;
      font-weight: 600;
    }
    .btn-row {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    button {
      background: var(--panel-2);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }
    button:hover { border-color: var(--accent); }
    button.active {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      font-weight: 600;
    }
    .slider-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      margin-top: 8px;
    }
    .slider-row input[type="range"] { flex: 1; accent-color: var(--accent); }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .parts-list {
      flex: 1;
      overflow-y: auto;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .part-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 7px 9px;
      border-radius: 6px;
      background: var(--panel-2);
      border: 1px solid transparent;
      cursor: pointer;
      font-size: 12px;
    }
    .part-item:hover { border-color: var(--border); }
    .part-item.active { border-color: var(--accent); background: #1e2d47; }
    .swatch {
      width: 11px;
      height: 11px;
      border-radius: 3px;
      flex-shrink: 0;
    }
    .part-meta {
      flex: 1;
      min-width: 0;
    }
    .part-name {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-weight: 500;
    }
    .part-dims {
      font-size: 11px;
      color: var(--muted);
    }
    main {
      position: relative;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    canvas {
      width: 100%;
      height: 100%;
      display: block;
      cursor: grab;
    }
    canvas:active { cursor: grabbing; }
    .hud-top {
      position: absolute;
      top: 12px;
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      pointer-events: none;
      gap: 12px;
    }
    .hud-card {
      pointer-events: auto;
      background: rgba(23, 29, 39, 0.88);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 12px;
    }
    .hud-bottom {
      position: absolute;
      bottom: 12px;
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      pointer-events: none;
    }
    .drop-banner {
      position: absolute;
      inset: 16px;
      border: 2px dashed var(--accent);
      border-radius: 12px;
      background: rgba(15, 19, 26, 0.85);
      display: none;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      font-weight: 600;
      pointer-events: none;
      z-index: 20;
    }
    .drop-banner.visible { display: flex; }
  </style>
</head>
<body>
  <aside>
    <div class="header">
      <h1>Projet Trains V1 — Inspecteur STL</h1>
      <p>11 maillages réels embarqués (échelle 1:1 en mm)</p>
    </div>

    <div class="section">
      <div class="section-title">Scènes d'inspection</div>
      <div class="btn-row" id="modeBtns">
        <button data-mode="assembly" class="active">Assemblage Complet</button>
        <button data-mode="circuit">Circuit + Courbe</button>
        <button data-mode="single">Pièce seule</button>
      </div>
      <div class="btn-row" style="margin-top:8px">
        <button data-view="iso">Iso</button>
        <button data-view="side">Profil (X-Z)</button>
        <button data-view="front">Coupe Face (Y-Z)</button>
        <button data-view="top">Dessus (X-Y)</button>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Outils CAO (Éclaté & Coupe)</div>
      <div class="slider-row">
        <span style="width:52px">Éclaté</span>
        <input id="explodeRange" type="range" min="0" max="100" value="0" />
        <span id="explodeOut" class="mono" style="width:36px;text-align:right">0%</span>
      </div>
      <div class="slider-row">
        <button id="clipBtn" style="min-width:74px">Coupe: Off</button>
        <input id="clipRange" type="range" min="-100" max="100" value="0" disabled />
        <span id="clipOut" class="mono" style="width:46px;text-align:right">--</span>
      </div>
      <div class="btn-row" style="margin-top:10px">
        <button id="wireBtn">Filaire: Off</button>
        <button id="bboxBtn">Cotes BBox: On</button>
      </div>
    </div>

    <div class="section-title" style="padding:10px 16px 2px;margin:0">Pièces STL (cliquer ou cocher)</div>
    <div class="parts-list" id="partsList"></div>
  </aside>

  <main id="viewport">
    <canvas id="glCanvas"></canvas>
    <div class="hud-top">
      <div class="hud-card" id="statsCard">Chargement des 11 STL...</div>
      <div class="hud-card" style="color:var(--muted)">
        Glisser : orbiter · Shift+Glisser : déplacer · Molette : zoomer · Déposer un .STL
      </div>
    </div>
    <div class="hud-bottom">
      <div class="hud-card mono" id="dimsCard">Dimensions : --</div>
      <div class="hud-card" id="clearanceCard">Essieu Z=21,0 mm · Garde pignon +0,6 mm · Prise crémaillère 1,4 mm</div>
    </div>
    <div class="drop-banner" id="dropBanner">Déposez votre fichier .STL binaire pour l'inspecter</div>
  </main>

  <script>
  const STL_B64 = __STL_DATA_JSON__;

  const PART_META = {
    'loco_chassis_inferieur.stl': { label: 'Châssis inférieur', color: [0.23, 0.53, 0.92] },
    'loco_coque_superieure_monobloc.stl': { label: 'Coque supérieure', color: [0.92, 0.28, 0.23] },
    'loco_roue_25_5mm.stl': { label: 'Roue Ø24 / Boudin Ø27,6', color: [0.22, 0.24, 0.28] },
    'loco_pignon_central_essieu.stl': { label: 'Pignon 12 dents Ø16,8', color: [0.96, 0.68, 0.14] },
    'rail_droit_100mm_snapfit.stl': { label: 'Rail droit 100mm Snap-Fit', color: [0.22, 0.68, 0.50] },
    'rail_courbe_45deg_snapfit.stl': { label: 'Rail courbe 45° R=180', color: [0.18, 0.60, 0.66] },
    'rail_cote_100mm_strie.stl': { label: 'Rail côte micro-strié', color: [0.35, 0.72, 0.34] },
    'rail_funky_cremaillere_captif.stl': { label: 'Rail Funky crémaillère 14mm', color: [0.60, 0.36, 0.88] },
    'adaptateur_rail_bois.stl': { label: 'Adaptateur rail bois', color: [0.78, 0.60, 0.36] },
    'pilier_verrouillable_duplo.stl': { label: 'Pilier H=50mm gros blocs', color: [0.92, 0.52, 0.18] },
    'tuile_action_clipsable.stl': { label: "Tuile d'action clipsable", color: [0.14, 0.80, 0.46] },
  };

  function decodeBinarySTL(uint8) {
    const dv = new DataView(uint8.buffer, uint8.byteOffset, uint8.byteLength);
    const count = dv.getUint32(80, true);
    const pos = new Float32Array(count * 9);
    const norm = new Float32Array(count * 9);
    const linePos = new Float32Array(count * 18);
    let minX = Infinity, minY = Infinity, minZ = Infinity;
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;

    for (let i = 0; i < count; i++) {
      const off = 84 + i * 50;
      const nx = dv.getFloat32(off, true);
      const ny = dv.getFloat32(off + 4, true);
      const nz = dv.getFloat32(off + 8, true);
      const pBase = i * 9;
      const lBase = i * 18;
      const pts = [];
      for (let v = 0; v < 3; v++) {
        const vo = off + 12 + v * 12;
        const x = dv.getFloat32(vo, true);
        const y = dv.getFloat32(vo + 4, true);
        const z = dv.getFloat32(vo + 8, true);
        pos[pBase + v * 3] = x;
        pos[pBase + v * 3 + 1] = y;
        pos[pBase + v * 3 + 2] = z;
        norm[pBase + v * 3] = nx;
        norm[pBase + v * 3 + 1] = ny;
        norm[pBase + v * 3 + 2] = nz;
        pts.push([x, y, z]);
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
        if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
      }
      // 3 arêtes pour mode filaire
      const pairs = [[0,1],[1,2],[2,0]];
      for (let e = 0; e < 3; e++) {
        const a = pts[pairs[e][0]], b = pts[pairs[e][1]];
        linePos[lBase + e*6] = a[0]; linePos[lBase + e*6 + 1] = a[1]; linePos[lBase + e*6 + 2] = a[2];
        linePos[lBase + e*6 + 3] = b[0]; linePos[lBase + e*6 + 4] = b[1]; linePos[lBase + e*6 + 5] = b[2];
      }
    }
    return {
      positions: pos,
      normals: norm,
      linePositions: linePos,
      triCount: count,
      vertCount: count * 3,
      bbox: { minX, minY, minZ, maxX, maxY, maxZ, dx: maxX-minX, dy: maxY-minY, dz: maxZ-minZ }
    };
  }

  function b64ToUint8(b64) {
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  }

  const models = {};
  for (const [name, b64] of Object.entries(STL_B64)) {
    models[name] = decodeBinarySTL(b64ToUint8(b64));
  }

  // --- Initialisation WebGL1 ---
  const canvas = document.getElementById('glCanvas');
  const gl = canvas.getContext('webgl', { antialias: true });
  const vs = `
    attribute vec3 aPos;
    attribute vec3 aNorm;
    uniform mat4 uMVP;
    uniform mat4 uModel;
    varying vec3 vNorm;
    varying vec3 vWPos;
    void main() {
      vec4 wp = uModel * vec4(aPos, 1.0);
      vWPos = wp.xyz;
      vNorm = mat3(uModel) * aNorm;
      gl_Position = uMVP * wp;
    }
  `;
  const fs = `
    precision mediump float;
    uniform vec3 uColor;
    uniform int uClipAxis;
    uniform float uClipVal;
    uniform float uFlatLine;
    varying vec3 vNorm;
    varying vec3 vWPos;
    void main() {
      if (uClipAxis == 1 && vWPos.x > uClipVal) discard;
      if (uClipAxis == 2 && vWPos.y > uClipVal) discard;
      if (uClipAxis == 3 && vWPos.z > uClipVal) discard;
      if (uFlatLine > 0.5) {
        gl_FragColor = vec4(uColor, 1.0);
        return;
      }
      vec3 n = normalize(vNorm) * (gl_FrontFacing ? 1.0 : -1.0);
      vec3 l1 = normalize(vec3(0.5, 0.4, 0.75));
      vec3 l2 = normalize(vec3(-0.6, -0.5, 0.35));
      float diff = max(dot(n, l1), 0.0) * 0.65 + max(dot(n, l2), 0.0) * 0.30 + 0.24;
      vec3 col = gl_FrontFacing ? uColor * diff : mix(uColor, vec3(1.0, 0.42, 0.22), 0.40) * diff;
      gl_FragColor = vec4(col, 1.0);
    }
  `;
  function compile(t, src) {
    const s = gl.createShader(t);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, vs));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  const aPos = gl.getAttribLocation(prog, 'aPos');
  const aNorm = gl.getAttribLocation(prog, 'aNorm');
  const uMVP = gl.getUniformLocation(prog, 'uMVP');
  const uModel = gl.getUniformLocation(prog, 'uModel');
  const uColor = gl.getUniformLocation(prog, 'uColor');
  const uClipAxis = gl.getUniformLocation(prog, 'uClipAxis');
  const uClipVal = gl.getUniformLocation(prog, 'uClipVal');
  const uFlatLine = gl.getUniformLocation(prog, 'uFlatLine');
  gl.enableVertexAttribArray(aPos);
  gl.enable(gl.DEPTH_TEST);

  const gpuCache = new Map();
  function getGpu(name, m) {
    if (!gpuCache.has(name)) {
      const pb = gl.createBuffer(), nb = gl.createBuffer(), lb = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, pb); gl.bufferData(gl.ARRAY_BUFFER, m.positions, gl.STATIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, nb); gl.bufferData(gl.ARRAY_BUFFER, m.normals, gl.STATIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER, lb); gl.bufferData(gl.ARRAY_BUFFER, m.linePositions, gl.STATIC_DRAW);
      gpuCache.set(name, { pb, nb, lb, m });
    }
    return gpuCache.get(name);
  }

  function makeModelMat(tx, ty, tz, rxDeg = 0, rzDeg = 0) {
    const rx = rxDeg * Math.PI / 180, rz = rzDeg * Math.PI / 180;
    const cx = Math.cos(rx), sx = Math.sin(rx);
    const cz = Math.cos(rz), sz = Math.sin(rz);
    // M = T * Rz * Rx (col-major)
    return new Float32Array([
      cz,       sz,       0,  0,
      -sz*cx,   cz*cx,    sx, 0,
      sz*sx,   -cz*sx,    cx, 0,
      tx,       ty,       tz, 1
    ]);
  }

  function mulMat(A, B) {
    const C = new Float32Array(16);
    for (let r = 0; r < 4; r++)
      for (let c = 0; c < 4; c++)
        C[c*4+r] = A[r]*B[c*4] + A[4+r]*B[c*4+1] + A[8+r]*B[c*4+2] + A[12+r]*B[c*4+3];
    return C;
  }

  // --- État ---
  let mode = 'assembly';
  let activePart = 'loco_chassis_inferieur.stl';
  let hiddenParts = new Set();
  let explode = 0;
  let clipAxis = 0;
  let clipNorm = 0;
  let wireframe = false;
  let showBBox = true;
  let yaw = -0.68, pitch = 0.42, dist = 280;
  let pan = [0, 0, 0];

  function getSceneInstances() {
    const e = explode;
    if (mode === 'single') {
      const m = models[activePart];
      const b = m.bbox;
      return [{
        key: activePart,
        mat: makeModelMat(-(b.minX+b.maxX)/2, -(b.minY+b.maxY)/2, -(b.minZ+b.maxZ)/2, 0, 0),
        color: (PART_META[activePart] && PART_META[activePart].color) || [0.4, 0.7, 0.95]
      }];
    }
    if (mode === 'circuit') {
      return [
        { key: 'pilier_verrouillable_duplo.stl', mat: makeModelMat(-50, 0, -50 - e*20, 0, 0), color: PART_META['pilier_verrouillable_duplo.stl'].color },
        { key: 'rail_droit_100mm_snapfit.stl', mat: makeModelMat(-150 - e*18, 0, 0, 0, 0), color: PART_META['rail_droit_100mm_snapfit.stl'].color },
        { key: 'rail_cote_100mm_strie.stl', mat: makeModelMat(-50, 0, 0, 0, 0), color: PART_META['rail_cote_100mm_strie.stl'].color },
        { key: 'rail_courbe_45deg_snapfit.stl', mat: makeModelMat(50 + e*18, 0, 0, 0, 0), color: PART_META['rail_courbe_45deg_snapfit.stl'].color },
        { key: 'tuile_action_clipsable.stl', mat: makeModelMat(-115 - e*18, 0, 13.8 + e*15, 180, 0), color: PART_META['tuile_action_clipsable.stl'].color },
      ];
    }
    // Assemblage Complet centré autour de x = 135 -> décalage cx = -135, cz = -55
    const cx = -135, cz = -55;
    return [
      { key: 'pilier_verrouillable_duplo.stl', mat: makeModelMat(100+cx, 0, 0+cz - e*24, 0, 0), color: PART_META['pilier_verrouillable_duplo.stl'].color },
      { key: 'rail_droit_100mm_snapfit.stl', mat: makeModelMat(0+cx - e*18, 0, 50+cz, 0, 0), color: PART_META['rail_droit_100mm_snapfit.stl'].color },
      { key: 'tuile_action_clipsable.stl', mat: makeModelMat(35+cx - e*18, 0, 63.8+cz + e*14, 180, 0), color: PART_META['tuile_action_clipsable.stl'].color },
      { key: 'rail_funky_cremaillere_captif.stl', mat: makeModelMat(100+cx, 0, 50+cz, 0, 0), color: PART_META['rail_funky_cremaillere_captif.stl'].color },
      { key: 'adaptateur_rail_bois.stl', mat: makeModelMat(200+cx + e*18, 0, 50+cz, 0, 0), color: PART_META['adaptateur_rail_bois.stl'].color },
      { key: 'loco_chassis_inferieur.stl', mat: makeModelMat(115+cx, 0, 54.5+cz + e*22, 0, 0), color: PART_META['loco_chassis_inferieur.stl'].color },
      { key: 'loco_coque_superieure_monobloc.stl', mat: makeModelMat(115+cx, 0, 69.5+cz + e*56, 0, 0), color: PART_META['loco_coque_superieure_monobloc.stl'].color },
      { key: 'loco_pignon_central_essieu.stl', mat: makeModelMat(135+cx, -1.5, 71.0+cz + e*10, -90, 0), color: PART_META['loco_pignon_central_essieu.stl'].color },
      { key: 'loco_roue_25_5mm.stl', mat: makeModelMat(135+cx, 10.05 + e*16, 71.0+cz + e*10, -90, 0), color: PART_META['loco_roue_25_5mm.stl'].color },
      { key: 'loco_roue_25_5mm.stl', mat: makeModelMat(135+cx, -10.05 - e*16, 71.0+cz + e*10, 90, 0), color: PART_META['loco_roue_25_5mm.stl'].color },
      { key: 'loco_roue_25_5mm.stl', mat: makeModelMat(181+cx, 10.05 + e*16, 71.0+cz + e*10, -90, 0), color: PART_META['loco_roue_25_5mm.stl'].color },
      { key: 'loco_roue_25_5mm.stl', mat: makeModelMat(181+cx, -10.05 - e*16, 71.0+cz + e*10, 90, 0), color: PART_META['loco_roue_25_5mm.stl'].color },
    ];
  }

  // --- Grille & BBox ---
  const gridBuf = gl.createBuffer();
  const gridVerts = [];
  for (let i = -160; i <= 160; i += 20) {
    gridVerts.push(i, -160, -55, i, 160, -55, -160, i, -55, 160, i, -55);
  }
  gl.bindBuffer(gl.ARRAY_BUFFER, gridBuf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(gridVerts), gl.STATIC_DRAW);

  const bboxBuf = gl.createBuffer();
  function drawBBox(b, mat, mvp) {
    const corners = [
      [b.minX,b.minY,b.minZ],[b.maxX,b.minY,b.minZ],[b.maxX,b.maxY,b.minZ],[b.minX,b.maxY,b.minZ],
      [b.minX,b.minY,b.maxZ],[b.maxX,b.minY,b.maxZ],[b.maxX,b.maxY,b.maxZ],[b.minX,b.maxY,b.maxZ],
    ];
    const idx = [0,1, 1,2, 2,3, 3,0, 4,5, 5,6, 6,7, 7,4, 0,4, 1,5, 2,6, 3,7];
    const verts = new Float32Array(idx.length * 3);
    idx.forEach((ci, k) => {
      verts[k*3] = corners[ci][0]; verts[k*3+1] = corners[ci][1]; verts[k*3+2] = corners[ci][2];
    });
    gl.bindBuffer(gl.ARRAY_BUFFER, bboxBuf);
    gl.bufferData(gl.ARRAY_BUFFER, verts, gl.DYNAMIC_DRAW);
    gl.disableVertexAttribArray(aNorm);
    gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(uMVP, false, mvp);
    gl.uniformMatrix4fv(uModel, false, mat);
    gl.uniform1f(uFlatLine, 1.0);
    gl.uniform3fv(uColor, [0.35, 0.72, 1.0]);
    gl.drawArrays(gl.LINES, 0, idx.length);
    gl.enableVertexAttribArray(aNorm);
  }

  function lookAtProj(aspect) {
    const t = pan;
    const eye = [
      t[0] + dist * Math.cos(pitch) * Math.cos(yaw),
      t[1] + dist * Math.cos(pitch) * Math.sin(yaw),
      t[2] + dist * Math.sin(pitch)
    ];
    const f = [t[0]-eye[0], t[1]-eye[1], t[2]-eye[2]];
    const fl = Math.hypot(...f); f[0]/=fl; f[1]/=fl; f[2]/=fl;
    const up = [0, 0, 1];
    let s = [f[1]*up[2]-f[2]*up[1], f[2]*up[0]-f[0]*up[2], f[0]*up[1]-f[1]*up[0]];
    const sl = Math.hypot(...s) || 1; s[0]/=sl; s[1]/=sl; s[2]/=sl;
    const u = [s[1]*f[2]-s[2]*f[1], s[2]*f[0]-s[0]*f[2], s[0]*f[1]-s[1]*f[0]];
    const V = new Float32Array([
      s[0], u[0], -f[0], 0,
      s[1], u[1], -f[1], 0,
      s[2], u[2], -f[2], 0,
      -(s[0]*eye[0]+s[1]*eye[1]+s[2]*eye[2]),
      -(u[0]*eye[0]+u[1]*eye[1]+u[2]*eye[2]),
       (f[0]*eye[0]+f[1]*eye[1]+f[2]*eye[2]), 1
    ]);
    const fov = 0.72, near = 2, far = 2500, tan = 1/Math.tan(fov/2);
    const P = new Float32Array([
      tan/aspect, 0, 0, 0,
      0, tan, 0, 0,
      0, 0, (far+near)/(near-far), -1,
      0, 0, (2*far*near)/(near-far), 0
    ]);
    return mulMat(P, V);
  }

  function draw() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(w*dpr) || canvas.height !== Math.round(h*dpr)) {
      canvas.width = Math.round(w*dpr); canvas.height = Math.round(h*dpr);
    }
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0.06, 0.075, 0.10, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    const mvp = lookAtProj(w / Math.max(h, 1));
    gl.uniformMatrix4fv(uMVP, false, mvp);
    gl.uniform1i(uClipAxis, clipAxis);
    const span = clipAxis === 1 ? 150 : clipAxis === 2 ? 40 : 60;
    const clipVal = (clipNorm / 100) * span;
    gl.uniform1f(uClipVal, clipVal);
    document.getElementById('clipOut').textContent = clipAxis ? clipVal.toFixed(1) : '--';

    // Grille de sol (uniquement en assemblage)
    if (mode !== 'single') {
      gl.disableVertexAttribArray(aNorm);
      gl.bindBuffer(gl.ARRAY_BUFFER, gridBuf);
      gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
      gl.uniformMatrix4fv(uModel, false, makeModelMat(0, 0, mode === 'circuit' ? 5 : 0));
      gl.uniform1f(uFlatLine, 1.0);
      gl.uniform3fv(uColor, [0.18, 0.22, 0.30]);
      gl.drawArrays(gl.LINES, 0, gridVerts.length / 3);
      gl.enableVertexAttribArray(aNorm);
    }

    let totalTris = 0;
    const instances = getSceneInstances();
    for (const inst of instances) {
      if (mode !== 'single' && hiddenParts.has(inst.key)) continue;
      const m = models[inst.key];
      if (!m) continue;
      totalTris += m.triCount;
      const g = getGpu(inst.key, m);
      gl.uniformMatrix4fv(uModel, false, inst.mat);
      gl.uniform1f(uFlatLine, 0.0);
      gl.uniform3fv(uColor, inst.color);
      gl.bindBuffer(gl.ARRAY_BUFFER, g.pb); gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, g.nb); gl.vertexAttribPointer(aNorm, 3, gl.FLOAT, false, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, m.vertCount);

      if (wireframe) {
        gl.disableVertexAttribArray(aNorm);
        gl.bindBuffer(gl.ARRAY_BUFFER, g.lb); gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
        gl.uniform1f(uFlatLine, 1.0);
        gl.uniform3fv(uColor, [0.05, 0.07, 0.10]);
        gl.drawArrays(gl.LINES, 0, m.triCount * 6);
        gl.enableVertexAttribArray(aNorm);
      }
      if (showBBox && mode === 'single') {
        drawBBox(m.bbox, inst.mat, mvp);
      }
    }

    document.getElementById('statsCard').textContent =
      `${instances.length} objet(s) · ${totalTris.toLocaleString('fr-CA')} triangles STL rendus`;
    if (mode === 'single') {
      const b = models[activePart].bbox;
      document.getElementById('dimsCard').textContent =
        `${activePart} : ${b.dx.toFixed(2)} × ${b.dy.toFixed(2)} × ${b.dz.toFixed(2)} mm (${models[activePart].triCount} tris)`;
    } else {
      document.getElementById('dimsCard').textContent =
        mode === 'assembly'
          ? 'Assemblage complet (échelle 1:1 mm) : Pilier + 3 Rails + Tuile + Locomotive'
          : 'Circuit test : Pilier + Rail droit + Rail côte + Rail courbe 45° + Tuile';
    }
  }

  // --- Liste des pièces ---
  const partsList = document.getElementById('partsList');
  function renderPartsList() {
    partsList.innerHTML = '';
    for (const [key, m] of Object.entries(models)) {
      const meta = PART_META[key] || { label: key, color: [0.5, 0.7, 0.9] };
      const div = document.createElement('div');
      div.className = 'part-item' + (mode === 'single' && activePart === key ? ' active' : '');
      const rgb = meta.color.map(v => Math.round(v*255)).join(',');
      const b = m.bbox;
      div.innerHTML = `
        <input type="checkbox" ${hiddenParts.has(key) ? '' : 'checked'} title="Afficher/Masquer en assemblage" />
        <span class="swatch" style="background:rgb(${rgb})"></span>
        <div class="part-meta">
          <div class="part-name">${meta.label}</div>
          <div class="part-dims mono">${b.dx.toFixed(1)}×${b.dy.toFixed(1)}×${b.dz.toFixed(1)} mm · ${m.triCount} tris</div>
        </div>
      `;
      const cb = div.querySelector('input');
      cb.addEventListener('click', ev => {
        ev.stopPropagation();
        if (cb.checked) hiddenParts.delete(key); else hiddenParts.add(key);
        draw();
      });
      div.addEventListener('click', () => {
        activePart = key;
        mode = 'single';
        pan = [0, 0, 0];
        dist = Math.max(85, Math.max(b.dx, b.dy, b.dz) * 1.9);
        updateModeButtons();
        renderPartsList();
        draw();
      });
      partsList.appendChild(div);
    }
  }

  function updateModeButtons() {
    document.querySelectorAll('#modeBtns button').forEach(b => {
      b.classList.toggle('active', b.dataset.mode === mode);
    });
  }

  document.querySelectorAll('#modeBtns button').forEach(btn => {
    btn.addEventListener('click', () => {
      mode = btn.dataset.mode;
      pan = [0, 0, 0];
      dist = mode === 'single' ? 120 : mode === 'circuit' ? 320 : 280;
      updateModeButtons();
      renderPartsList();
      draw();
    });
  });

  const viewPresets = {
    iso: [-0.68, 0.42],
    side: [-Math.PI/2, 0.04],
    front: [0.0, 0.04],
    top: [-0.01, 1.48],
  };
  document.querySelectorAll('[data-view]').forEach(btn => {
    btn.addEventListener('click', () => {
      [yaw, pitch] = viewPresets[btn.dataset.view];
      draw();
    });
  });

  document.getElementById('explodeRange').addEventListener('input', e => {
    explode = Number(e.target.value) / 100;
    document.getElementById('explodeOut').textContent = e.target.value + '%';
    draw();
  });

  const clipBtn = document.getElementById('clipBtn');
  const clipRange = document.getElementById('clipRange');
  const clipLabels = ['Coupe: Off', 'Coupe: X', 'Coupe: Y', 'Coupe: Z'];
  clipBtn.addEventListener('click', () => {
    clipAxis = (clipAxis + 1) % 4;
    clipBtn.textContent = clipLabels[clipAxis];
    clipBtn.classList.toggle('active', clipAxis > 0);
    clipRange.disabled = clipAxis === 0;
    draw();
  });
  clipRange.addEventListener('input', e => { clipNorm = Number(e.target.value); draw(); });

  const wireBtn = document.getElementById('wireBtn');
  wireBtn.addEventListener('click', () => {
    wireframe = !wireframe;
    wireBtn.textContent = 'Filaire: ' + (wireframe ? 'On' : 'Off');
    wireBtn.classList.toggle('active', wireframe);
    draw();
  });

  const bboxBtn = document.getElementById('bboxBtn');
  bboxBtn.classList.add('active');
  bboxBtn.addEventListener('click', () => {
    showBBox = !showBBox;
    bboxBtn.textContent = 'Cotes BBox: ' + (showBBox ? 'On' : 'Off');
    bboxBtn.classList.toggle('active', showBBox);
    draw();
  });

  // --- Contrôles caméra souris & Drag-Drop STL ---
  let drag = false, panDrag = false, lx = 0, ly = 0;
  canvas.addEventListener('pointerdown', e => {
    drag = true; panDrag = e.shiftKey || e.button === 2;
    lx = e.clientX; ly = e.clientY;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('contextmenu', e => e.preventDefault());
  canvas.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - lx, dy = e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    if (panDrag) {
      const scale = dist * 0.0018;
      pan[0] -= (-Math.sin(yaw)*dx - Math.cos(yaw)*Math.sin(pitch)*dy) * scale;
      pan[1] -= ( Math.cos(yaw)*dx - Math.sin(yaw)*Math.sin(pitch)*dy) * scale;
      pan[2] += Math.cos(pitch) * dy * scale;
    } else {
      yaw -= dx * 0.008;
      pitch = Math.max(-1.50, Math.min(1.52, pitch + dy * 0.008));
    }
    draw();
  });
  canvas.addEventListener('pointerup', () => { drag = false; });
  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    dist = Math.max(30, Math.min(1200, dist * (1 + e.deltaY * 0.001)));
    draw();
  }, { passive: false });

  const viewport = document.getElementById('viewport');
  const dropBanner = document.getElementById('dropBanner');
  viewport.addEventListener('dragover', e => { e.preventDefault(); dropBanner.classList.add('visible'); });
  viewport.addEventListener('dragleave', () => dropBanner.classList.remove('visible'));
  viewport.addEventListener('drop', async e => {
    e.preventDefault();
    dropBanner.classList.remove('visible');
    const file = e.dataTransfer.files[0];
    if (!file || !file.name.toLowerCase().endsWith('.stl')) return;
    const buf = new Uint8Array(await file.arrayBuffer());
    models[file.name] = decodeBinarySTL(buf);
    PART_META[file.name] = { label: file.name, color: [0.3, 0.8, 0.9] };
    activePart = file.name;
    mode = 'single';
    pan = [0, 0, 0];
    updateModeButtons();
    renderPartsList();
    draw();
  });

  window.addEventListener('resize', draw);
  renderPartsList();
  draw();
  })();
  </script>
</body>
</html>
"""


def main() -> None:
    stl_dir = Path(__file__).resolve().parent / "stl"
    out_html = Path(__file__).resolve().parent / "visualiseur-assemblage.html"
    stl_files = sorted(stl_dir.glob("*.stl"))
    if not stl_files:
        raise FileNotFoundError(f"Aucun fichier .stl trouvé dans {stl_dir}")

    entries = []
    for p in stl_files:
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        entries.append(f'"{p.name}": "{b64}"')
    json_obj = "{\n    " + ",\n    ".join(entries) + "\n  }"

    html = HTML_TEMPLATE.replace("__STL_DATA_JSON__", json_obj)
    out_html.write_text(html, encoding="utf-8")
    size_kb = out_html.stat().st_size / 1024.0
    print(f"[OK] {out_html.name}: {len(stl_files)} STL embarqués | {size_kb:.1f} Ko")


if __name__ == "__main__":
    main()
