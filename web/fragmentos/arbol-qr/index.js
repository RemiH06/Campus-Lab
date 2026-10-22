/* Árbol con su QR, fijo en la esquina inferior derecha. Liferay lo envuelve en una función con fragmentElement y configuration.
   El árbol es el de la floración del sitio (la que eligió quien visita o la del mes: data-cl-flor en <html>, lo pone el
   Marco) y de noche se oscurece con el modo oscuro; en lluvias es un tabachín con hojas bajo la lluvia. Al tocarlo se
   abre; al tocar el árbol la cámara sube y la copa se vuelve el centro del QR de esta página, listo para escanear o
   descargar. Motor tomado del componente 15 de web/fuentes/prototipos/componentes_plantilla.html (si se mejora uno,
   pasar el cambio al otro). Idea de ICQR (Louis Raillé); el código es propio. */
(function () {
  var el = fragmentElement.querySelector(".cl-aqr");
  if (!el || el.dataset.listo) return;
  el.dataset.listo = "1";
  var cfg = configuration || {};
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var enEditor = !!fragmentElement.closest(".page-editor");

  /* Código QR (ISO 18004): modo byte, corrección M, versiones 1 a 10, máscara con menor penalización. Sin librerías */
  var qrCodigo = function (texto) {
    var ECC = [0, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26], BLQ = [0, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5];
    var bytes = [].slice.call(new TextEncoder().encode(texto));
    var crudos = function (v) { var r = (16 * v + 128) * v + 64; if (v >= 2) { var n = Math.floor(v / 7) + 2; r -= (25 * n - 10) * n - 55; if (v >= 7) r -= 36; } return r; };
    var ver = 1; while (ver <= 10 && 4 + (ver < 10 ? 8 : 16) + 8 * bytes.length > (Math.floor(crudos(ver) / 8) - ECC[ver] * BLQ[ver]) * 8) ver++;
    if (ver > 10) throw new Error("texto demasiado largo para el QR");
    var cap = (Math.floor(crudos(ver) / 8) - ECC[ver] * BLQ[ver]) * 8, bits = [];
    var pon = function (v, n) { for (var i = n - 1; i >= 0; i--) bits.push((v >>> i) & 1); };
    pon(4, 4); pon(bytes.length, ver < 10 ? 8 : 16); bytes.forEach(function (b) { pon(b, 8); });
    pon(0, Math.min(4, cap - bits.length)); pon(0, (8 - bits.length % 8) % 8);
    for (var p = 0xEC; bits.length < cap; p ^= 0xEC ^ 0x11) pon(p, 8);
    var datos = []; for (var i = 0; i < bits.length; i += 8) datos.push(parseInt(bits.slice(i, i + 8).join(""), 2));
    /* Reed-Solomon sobre GF(256), polinomio 0x11D */
    var mul = function (x, y) { var z = 0; for (var i = 7; i >= 0; i--) { z = (z << 1) ^ ((z >>> 7) * 0x11D); z ^= ((y >>> i) & 1) * x; } return z; };
    var grado = ECC[ver], div = []; for (i = 0; i < grado - 1; i++) div.push(0); div.push(1);
    for (var r = 1, k = 0; k < grado; k++) { for (var j = 0; j < div.length; j++) { div[j] = mul(div[j], r); if (j + 1 < div.length) div[j] ^= div[j + 1]; } r = mul(r, 2); }
    var resto = function (d) { var res = div.map(function () { return 0; }); d.forEach(function (b) { var f = b ^ res.shift(); res.push(0); div.forEach(function (c, i) { res[i] ^= mul(c, f); }); }); return res; };
    var nb = BLQ[ver], total = Math.floor(crudos(ver) / 8), cortos = nb - total % nb, largoC = Math.floor(total / nb), bloques = [];
    for (i = 0, k = 0; i < nb; i++) { var d = datos.slice(k, k + largoC - grado + (i < cortos ? 0 : 1)); k += d.length; var e = resto(d); if (i < cortos) d.push(0); bloques.push(d.concat(e)); }
    var cw = []; for (i = 0; i < bloques[0].length; i++) bloques.forEach(function (b, j) { if (i !== largoC - grado || j >= cortos) cw.push(b[i]); });
    /* matriz y patrones fijos */
    var n = ver * 4 + 17, M = [], F = [];
    for (i = 0; i < n; i++) { M.push(new Array(n).fill(false)); F.push(new Array(n).fill(false)); }
    var fija = function (x, y, v) { M[y][x] = v; F[y][x] = true; };
    for (i = 0; i < n; i++) { fija(6, i, i % 2 === 0); fija(i, 6, i % 2 === 0); }
    [[3, 3], [n - 4, 3], [3, n - 4]].forEach(function (c) { for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) { var x = c[0] + dx, y = c[1] + dy, m = Math.max(Math.abs(dx), Math.abs(dy)); if (x >= 0 && x < n && y >= 0 && y < n) fija(x, y, m !== 2 && m !== 4); } });
    var al = [];
    if (ver > 1) { var na = Math.floor(ver / 7) + 2, paso = Math.ceil((ver * 4 + 4) / (na * 2 - 2)) * 2; al = [6]; for (var q = n - 7; al.length < na; q -= paso) al.splice(1, 0, q); }
    al.forEach(function (a, ia) { al.forEach(function (b, ib) {
      if ((ia === 0 && ib === 0) || (ia === 0 && ib === al.length - 1) || (ia === al.length - 1 && ib === 0)) return;
      for (var dy = -2; dy <= 2; dy++) for (var dx = -2; dx <= 2; dx++) fija(a + dx, b + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
    }); });
    var formato = function (mask) {
      var dd = mask, rem = dd; for (var i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537); /* nivel M = 00 */
      var b = ((dd << 10) | rem) ^ 0x5412, bit = function (i) { return ((b >>> i) & 1) === 1; };
      for (i = 0; i <= 5; i++) fija(8, i, bit(i)); fija(8, 7, bit(6)); fija(8, 8, bit(7)); fija(7, 8, bit(8));
      for (i = 9; i < 15; i++) fija(14 - i, 8, bit(i));
      for (i = 0; i < 8; i++) fija(n - 1 - i, 8, bit(i)); for (i = 8; i < 15; i++) fija(8, n - 15 + i, bit(i)); fija(8, n - 8, true);
    };
    formato(0);
    if (ver >= 7) { var rv = ver; for (i = 0; i < 12; i++) rv = (rv << 1) ^ ((rv >>> 11) * 0x1F25); var vb = (ver << 12) | rv; for (i = 0; i < 18; i++) { var bv = ((vb >>> i) & 1) === 1, a2 = n - 11 + i % 3, b2 = Math.floor(i / 3); fija(a2, b2, bv); fija(b2, a2, bv); } }
    /* datos en zigzag desde la esquina de abajo a la derecha */
    for (var der = n - 1, t = 0; der >= 1; der -= 2) {
      if (der === 6) der = 5;
      for (var v = 0; v < n; v++) for (j = 0; j < 2; j++) {
        var x = der - j, y = ((der + 1) & 2) === 0 ? n - 1 - v : v;
        if (!F[y][x] && t < cw.length * 8) { M[y][x] = ((cw[t >>> 3] >>> (7 - (t & 7))) & 1) === 1; t++; }
      }
    }
    var MASC = [function (x, y) { return (x + y) % 2 === 0; }, function (x, y) { return y % 2 === 0; }, function (x) { return x % 3 === 0; }, function (x, y) { return (x + y) % 3 === 0; },
      function (x, y) { return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; }, function (x, y) { return x * y % 2 + x * y % 3 === 0; },
      function (x, y) { return (x * y % 2 + x * y % 3) % 2 === 0; }, function (x, y) { return ((x + y) % 2 + x * y % 3) % 2 === 0; }];
    var aplica = function (m) { for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) if (!F[y][x] && MASC[m](x, y)) M[y][x] = !M[y][x]; };
    /* penalización (reglas 1, 2 y 4 de la norma): racha de 5+ iguales, bloques 2×2, proporción de oscuros */
    var castigo = function () {
      var s = 0, osc = 0, y, x, c;
      for (y = 0; y < n; y++) for (x = 0, c = 1; x < n; x++) { if (M[y][x]) osc++; if (x && M[y][x] === M[y][x - 1]) { c++; if (c === 5) s += 3; else if (c > 5) s++; } else c = 1; }
      for (x = 0; x < n; x++) for (y = 0, c = 1; y < n; y++) { if (y && M[y][x] === M[y - 1][x]) { c++; if (c === 5) s += 3; else if (c > 5) s++; } else c = 1; }
      for (y = 0; y < n - 1; y++) for (x = 0; x < n - 1; x++) if (M[y][x] === M[y][x + 1] && M[y][x] === M[y + 1][x] && M[y][x] === M[y + 1][x + 1]) s += 3;
      return s + Math.floor(Math.abs(osc * 20 - n * n * 10) / (n * n)) * 10;
    };
    var mejor = 0, menor = Infinity;
    for (var m = 0; m < 8; m++) { aplica(m); formato(m); var c2 = castigo(); if (c2 < menor) { menor = c2; mejor = m; } aplica(m); }
    aplica(mejor); formato(mejor);
    return M;
  };

  function arbolQR() {
    /* especies que florecen en el campus: [id de la ficha, nombre, color de la flor, meses, forma]. Forma (en fracciones del lado del QR salvo donde se dice):
       R radio de la copa, tr alto del tronco, ry media altura de la copa, ab cuánto cuelga la copa bajo su centro (0 a 1), rt grosor del tronco (módulos),
       inc inclinación del tronco (módulos), ra ramas principales, abre apertura de las ramas (0 verticales, 1 horizontales), irr copa irregular, den flores por módulo */
    var ESP = [["tabebuia-rosea", "Rosa morada", "#e46fb2", [2], { R: .40, tr: .30, ry: .20, ab: .75, rt: .8, inc: .9, ra: 5, abre: .55, irr: 1.4, den: 1 }],
      ["jacaranda-mimosifolia", "Jacaranda", "#8d6ee0", [3], { R: .45, tr: .24, ry: .13, ab: .45, rt: .7, inc: .6, ra: 6, abre: .72, irr: .9, den: .9 }],
      ["roseodendron-donnell-smithii", "Primavera", "#f5c02a", [4], { R: .32, tr: .40, ry: .25, ab: .8, rt: .65, inc: .25, ra: 4, abre: .3, irr: .7, den: 1 }],
      ["delonix-regia", "Tabachín", "#ea4b23", [5, 6], { R: .46, tr: .25, ry: .08, ab: .25, rt: .95, inc: 1.4, ra: 6, abre: .92, irr: .5, den: 1.1 }],
      ["spathodea-campanulata", "Galeana", "#f2862a", [11], { R: .36, tr: .28, ry: .24, ab: .85, rt: .7, inc: .4, ra: 4, abre: .45, irr: .8, den: 1.15 }],
      ["pseudobombax-ellipticum", "Clavellina", "#ef6f95", [12, 1], { R: .36, tr: .26, ry: .17, ab: .6, rt: 1.3, inc: .5, ra: 3, abre: .6, irr: 1.1, den: .55, desnuda: 1 }]];
    var TEMP = [["flor", "Floración"], ["lluvias", "Lluvias"], ["secas", "Secas"]];
    var cv = el.querySelector("canvas"), fondo = document.createElement("canvas");
    var E = null, n = 0, c0 = 0, url = "", W = 0, H = 0, dpr = 1, vista = null;
    var sem = function (s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return function () { h = Math.imul(h ^ h >>> 15, 2246822507) + 0x6D2B79F5 | 0; return (h >>> 0) / 4294967296; }; };
    var rgb = function (h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; };
    var css = function (c, k) { k = k || 1; return "rgb(" + Math.round(Math.min(255, c[0] * k)) + "," + Math.round(Math.min(255, c[1] * k)) + "," + Math.round(Math.min(255, c[2] * k)) + ")"; };
    var mezcla = function (a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; };
    var por = function (c, k) { return [c[0] * k, c[1] * k, c[2] * k]; };
    var ss = function (a, b, x) { x = Math.max(0, Math.min(1, (x - a) / (b - a))); return x * x * (3 - 2 * x); };
    /* cuánto oscurecer un color para que el lector lo tome como módulo oscuro (gris final cerca de 0.3) */
    var hundir = function (c) { return Math.min(.7, 78 / Math.max(1, .299 * c[0] + .587 * c[1] + .114 * c[2])); };
    var CLARO = rgb("#f5ece0");

    /* racimos de flores u hojas, pintados una vez y estampados miles de veces */
    function racimo(base, tipo, R) {
      var c = document.createElement("canvas"), g = c.getContext("2d"), i, a, d, k;
      c.width = c.height = 40; g.scale(40 / 64, 40 / 64); g.globalAlpha = .5; g.fillStyle = css(base, .6); g.beginPath(); g.arc(32, 35, 21, 0, 7); g.fill(); g.globalAlpha = 1;
      if (tipo === "flor") for (i = 0; i < 5; i++) {
        a = i * 1.26 + R(); d = i ? 12 + R() * 3 : 0; k = .86 + R() * .26;
        var x = 32 + Math.cos(a) * d, y = 31 + Math.sin(a) * d * .8;
        for (var p = 0; p < 5; p++) { var b = p * 1.2566 + a; g.fillStyle = css(base, k * (p % 2 ? 1 : .9)); g.beginPath(); g.ellipse(x + Math.cos(b) * 4.6, y + Math.sin(b) * 4.6, 5, 3.4, b, 0, 7); g.fill(); }
        g.fillStyle = "#fff1c2"; g.beginPath(); g.arc(x, y, 1.7, 0, 7); g.fill();
      } else for (i = 0; i < 10; i++) {
        a = R() * 6.28; d = R() * 15; g.fillStyle = css(base, .8 + R() * .4); g.beginPath(); g.ellipse(32 + Math.cos(a) * d, 31 + Math.sin(a) * d * .8, 9, 5, a + 1, 0, 7); g.fill();
      }
      /* luz desde arriba a la izquierda y sombra abajo, para que cada racimo tenga volumen */
      g.globalCompositeOperation = "source-atop";
      var l = g.createLinearGradient(14, 10, 46, 56); l.addColorStop(0, "rgba(255,255,255,.28)"); l.addColorStop(.5, "rgba(255,255,255,0)"); l.addColorStop(1, "rgba(30,10,20,.3)");
      g.fillStyle = l; g.fillRect(0, 0, 64, 64);
      return c;
    }

    /* la escena: el suelo es el QR con 2 módulos de margen. Claros = camino de petatillo; oscuros fuera de la copa = pasto.
       Los oscuros bajo la copa los pone la copa misma: una columna de cubos flotando a su altura, que solo aparece al girar a la vista cenital */
    function construir() {
      var es = ESP[S.e], F = es[4], R = sem(es[0] + S.temp), flor = S.temp === "flor", secas = S.temp === "secas", Q, x, z, i, y;
      url = destino(); Q = qrCodigo(url);
      var q = Q.length, mg = 2; n = q + 2 * mg; c0 = n / 2;
      var Rc = F.R * q, Ht = F.tr * q, Ry = F.ry * q, Cy = Ht + Ry * F.ab;
      var toma = function (a) { return a[Math.floor(R() * a.length)]; };
      var pal = { camino: ["#ecd2b6", "#e6c8a9", "#f0dac3", "#e3c2a2"].map(rgb), junta: rgb("#d5c0a8"), corteza: rgb("#6b4a32"), flor: rgb(es[2]),
        pasto: (secas ? ["#6f7a33", "#5f6a2b", "#7d8a3c"] : ["#2f7d3c", "#28703a", "#3a8c45"]).map(rgb),
        hoja: (secas ? ["#b38a35", "#c49a45", "#9a7430", "#8a6a34"] : ["#3f9a4c", "#4aa857", "#358a42", "#5bb866"]).map(rgb) };
      /* cinco tonos de cada racimo, de la sombra a la luz: abajo y del lado contrario al sol, más oscuros */
      var TONOS = [.66, .78, .9, 1.02, 1.14];
      var spF = TONOS.map(function (k) { return racimo(por(pal.flor, k), "flor", R); }), spH = TONOS.map(function (k) { return racimo(por(pal.hoja[Math.floor(R() * 4)], k), "hoja", R); });
      var tono = function (y, x, z) { var h = Math.max(0, Math.min(1, (y - Ht) / (Ry * (1.6 + F.ab)))), s = ((c0 - x) + (c0 - z)) / (2.8 * Rc); return Math.max(0, Math.min(4, Math.round(h * 3.4 + s * 1.6 + R() * .8))); };
      var desnuda = flor && F.desnuda; /* la clavellina florece sin hojas */
      E = { textura: null, T: 0, suelo: [], pasto: [], briznas: [[], [], []], caidas: [], cosas: [], Rc: Rc, Ht: Ht, top: 0, colBrizna: pal.pasto.map(function (c) { return css(c, 1.18); }) };
      var bola = function (x, y, z, img, s) { E.cosas.push({ k: 0, x: x, y: y, z: z, img: img, s: s, pronto: E.cosas.length % 2 }); };
      /* cada columna crece entera (a → bb); un cubo guarda su columna para saber si lo tapan el de arriba o los vecinos */
      var cols = {}, cubo = function (x, y, z, h, c, C, arriba) { E.cosas.push({ k: 1, x: x, y: y, z: z, h: h, c: c, dk: hundir(c), C: C, arriba: arriba, tonos: [] }); };
      var columna = function (x, z, b, t, a, bb) { var C = { b: b, t: t, a: a, bb: bb }; (cols[x + "," + z] = cols[x + "," + z] || []).push(C); return C; };
      var seg = function (p, q2, r0, r1) { E.cosas.push({ k: 2, p: p, q: q2, r0: r0, r1: r1 }); };

      /* la copa no es una cúpula lisa: orilla ondulada y lóbulos que abultan la parte de arriba */
      var f1 = R() * 6.28, f2 = R() * 6.28, lob = [];
      for (i = 0; i < 6; i++) { var la = R() * 6.28, ld = Rc * (.25 + R() * .5); lob.push([c0 + Math.cos(la) * ld, c0 + Math.sin(la) * ld, Rc * (.3 + R() * .18), Ry * (.3 + R() * .35) * (.5 + F.irr * .5)]); }
      var radio = function (a) { return Rc * (1 + .07 * F.irr * Math.sin(3 * a + f1) + .04 * F.irr * Math.sin(5 * a + f2)); };
      E.radio = radio;
      for (z = 0; z < n; z++) for (x = 0; x < n; x++) {
        var osc = x >= mg && z >= mg && x < n - mg && z < n - mg && Q[z - mg][x - mg], dx = x + .5 - c0, dz = z + .5 - c0, r = Math.hypot(dx, dz), Ra = radio(Math.atan2(dz, dx)), cp = null;
        if (r < Ra) {
          var g0 = Math.sqrt(1 - r * r / (Ra * Ra)), u = (R() - .5) * .5, bulto = 0;
          lob.forEach(function (l) { var d2 = (Math.pow(x + .5 - l[0], 2) + Math.pow(z + .5 - l[1], 2)) / (l[2] * l[2]); if (d2 < 1) bulto = Math.max(bulto, l[3] * Math.sqrt(1 - d2)); });
          var t = Cy + Ry * g0 + bulto * g0 + u, b = Cy - Ry * F.ab * g0 + u * .5;
          if (t - b < 1.2) b = t - 1.2;
          cp = { t: t, b: b, g: g0 }; E.top = Math.max(E.top, t + 1);
        }
        if (osc && !cp) {
          E.pasto.push({ x: x, z: z, c: toma(pal.pasto) });
          for (i = 0; i < 4; i++) E.briznas[i % 3].push([x + .12 + R() * .76, z + .12 + R() * .76, .3 + R() * .4, (R() - .5) * .3, (R() - .5) * .3]);
        } else E.suelo.push({ x: x, z: z, v: (x + z) % 2, a: toma(pal.camino), b: toma(pal.camino) });
        if (!cp) continue;
        if ((flor || secas) && R() < .3) E.caidas.push([x + R(), z + R(), flor ? toma([por(pal.flor, .95), pal.flor]) : toma(pal.hoja)]);
        /* el QR dentro de la copa: cubos que crecen escalonados mientras la cámara sube */
        if (osc) {
          var nc = Math.max(1, Math.ceil(cp.t - .4 - cp.b)), y0 = cp.b + Math.max(0, nc - 3), a2 = .1 + R() * .22, C = columna(x, z, y0, cp.b + nc, a2, a2 + .42);
          nc = Math.min(nc, 3);
          for (i = 0; i < nc; i++) cubo(x, y0 + i, z, 1, por(flor && R() < (desnuda ? 1 : .86) ? pal.flor : toma(pal.hoja), .9 + R() * .2), C, i < nc - 1);
        }
        /* lo que se ve en la vista de árbol: racimos sobre la cúpula, algunos por debajo y por los lados de la orilla */
        var np = Math.round((.9 + 1.6 * cp.g) * F.den + R() * .8), px, py, pz;
        var pon = function (px, py, pz, pf, s) { bola(px, py, pz, (flor && R() < pf ? spF : spH)[tono(py, px, pz)], s); };
        for (i = 0; i < np; i++) { px = x + .5 + (R() - .5) * 1.3; py = cp.t - .4 + (R() - .5) * .8; pz = z + .5 + (R() - .5) * 1.3; pon(px, py, pz, desnuda ? 1 : .8, 1.45 + R() * .6); }
        if (cp.g < .75 && R() < .6 * F.den) bola(x + .5, cp.b + .3, z + .5, (desnuda ? spF : spH)[0], 1.3 + R() * .3);
        var orilla = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(function (d) { var xx = x + d[0] + .5 - c0, zz = z + d[1] + .5 - c0; return Math.hypot(xx, zz) >= radio(Math.atan2(zz, xx)); });
        if (orilla) for (y = cp.b + 1; y < cp.t - 1; y += 1.1) if (R() < F.den) pon(x + .5 + (R() - .5), y, z + .5 + (R() - .5), desnuda ? 1 : .75, 1.1 + R() * .4);
        /* tronco en cubos, solo en los módulos oscuros del centro */
        if (osc && r < 2.3) { var Ct = columna(x, z, .3, cp.b, .2, .6); for (y = .3; y < cp.b - .05; y++) cubo(x, y, z, Math.min(1, cp.b - y), por(pal.corteza, .9 + R() * .2), Ct, y + 1 < cp.b - .05); }
      }
      E.cosas.forEach(function (o) { if (o.k === 1) { o.vx = cols[(o.x + 1) + "," + o.z] || []; o.vz = cols[o.x + "," + (o.z + 1)] || []; } });

      /* tronco liso y ramas: lo que se ve en la vista de árbol */
      var a0 = R() * 6.28, tr = function (t) { var d = F.inc * (t * t + .3 * Math.sin(t * Math.PI * 1.5)); return [c0 + Math.cos(a0) * d, .3 + Ht * t, c0 + Math.sin(a0) * d]; };
      var rT = function (t) { return F.rt * (1 - .5 * t) * (F.rt > .9 ? 1 + .4 * Math.sin(t * Math.PI) : 1); };
      for (i = 0; i < 8; i++) seg(tr(i / 8), tr((i + 1) / 8), rT(i / 8), rT((i + 1) / 8));
      var rama = function (p, az, el2, L, r0, prof) {
        var e = [p[0] + Math.cos(az) * Math.cos(el2) * L, p[1] + Math.sin(el2) * L, p[2] + Math.sin(az) * Math.cos(el2) * L];
        var hx = e[0] - c0, hz = e[2] - c0, hr = Math.hypot(hx, hz);
        if (hr > .85 * Rc) { e[0] = c0 + hx * .85 * Rc / hr; e[2] = c0 + hz * .85 * Rc / hr; }
        e[1] = Math.min(e[1], Cy + Ry * .5);
        var r1 = r0 * .6, m = [(p[0] + e[0]) / 2, (p[1] + e[1]) / 2 + L * .08, (p[2] + e[2]) / 2];
        seg(p, m, r0, (r0 + r1) / 2); seg(m, e, (r0 + r1) / 2, r1);
        if (prof < 2) for (var j = 0; j < 2; j++) rama(prof ? e : m, az + (j ? 1 : -1) * (.45 + R() * .5), el2 + (R() - .3) * .5, L * .55, r1 * .8, prof + 1);
      };
      /* camino de petatillo: dos ladrillos por módulo, girados en damero, pintado una vez visto desde arriba (T px por módulo) */
      var T = 20, tx = document.createElement("canvas"), gt = tx.getContext("2d"); tx.width = tx.height = n * T;
      gt.fillStyle = css(pal.junta); gt.fillRect(0, 0, n * T, n * T);
      E.suelo.forEach(function (s) {
        var a = s.x * T, b = s.z * T, m = T * .07, h = T * .4;
        gt.fillStyle = css(s.a); if (s.v) gt.fillRect(a + m, b + m, T - 2 * m, h); else gt.fillRect(a + m, b + m, h, T - 2 * m);
        gt.fillStyle = css(s.b); if (s.v) gt.fillRect(a + m, b + T / 2 + T * .03, T - 2 * m, h); else gt.fillRect(a + T / 2 + T * .03, b + m, h, T - 2 * m);
      });
      E.textura = tx; E.T = T;
      for (i = 0; i < F.ra; i++) rama(tr(.72 + R() * .28), a0 + i * 6.283 / F.ra + (R() - .5) * .6, (1 - F.abre) * 1.15 + .18 + (R() - .5) * .2, Rc * (.5 + R() * .2), rT(.85) * .75, 0);
    }

    /* proyección ortográfica: de isométrica (giro 45°, inclinación 32°) a cenital (0°, 90°). La copa no desaparece: sus racimos se encogen
       y en su lugar crecen los cubos, que vistos desde arriba caen justo sobre los módulos oscuros del QR */
    var suave = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
    function pintar(t, rapido) {
      var e = suave(t), th = (45 - 45 * e) * Math.PI / 180, ph = (32 + 58 * e) * Math.PI / 180, qr = e * e;
      var ct = Math.cos(th), st = Math.sin(th), cp = Math.cos(ph), sp = Math.sin(ph);
      var P = function (x, y, z) { x -= c0; z -= c0; var x1 = x * ct - z * st, z1 = x * st + z * ct; return [x1, -y * cp + z1 * sp, z1 * cp + y * sp]; };
      var vB = ss(0, .6, 1 - e), vB2 = ss(.45, .85, 1 - e), vR = ss(0, .4, 1 - e), vP = ss(0, .3, 1 - e), Rc = E.Rc;
      /* encuadre: la losa y la copa caben con margen */
      var pts = [];
      [0, n].forEach(function (x) { [0, n].forEach(function (z) { pts.push(P(x, -1.4, z), P(x, .5, z)); }); });
      [c0 - Rc, c0 + Rc].forEach(function (x) { [c0 - Rc, c0 + Rc].forEach(function (z) { pts.push(P(x, E.top, z)); }); });
      var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
      var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
      var k = Math.min((W - 12) / (x1 - x0), (H - 12) / (y1 - y0)), ox = W / 2 - (x0 + x1) / 2 * k, oy = H / 2 - (y0 + y1) / 2 * k;
      vista = { P: P, k: k, ox: ox, oy: oy };
      /* en movimiento se pinta a menor resolución y sin filetes; el cuadro final sale nítido */
      var rz = rapido ? Math.min(dpr, 1.25) : dpr;
      fondo.width = Math.round(W * rz); fondo.height = Math.round(H * rz);
      var g = fondo.getContext("2d"); g.setTransform(rz, 0, 0, rz, 0, 0); g.lineJoin = "round"; g.lineCap = "round"; g.lineWidth = .7;
      var X = function (p) { return ox + p[0] * k; }, Y = function (p) { return oy + p[1] * k; };
      var cara = function (q, c) { g.beginPath(); q.forEach(function (p, i) { if (i) g.lineTo(X(p), Y(p)); else g.moveTo(X(p), Y(p)); }); g.closePath(); g.fillStyle = g.strokeStyle = c; g.fill(); if (!rapido) g.stroke(); };
      var piso = function (xa, xb, za, zb, y, c) { cara([P(xa, y, za), P(xb, y, za), P(xb, y, zb), P(xa, y, zb)], c); };
      /* cs: [arriba, lado x, lado z]; ver: qué caras pintar (bits 1 arriba, 2 lado x, 4 lado z) */
      var caja = function (x, y, z, w, h, d, cs, ver) {
        if (ver & 2 && st * cp > .02) cara([P(x + w, y, z), P(x + w, y + h, z), P(x + w, y + h, z + d), P(x + w, y, z + d)], cs[1]);
        if (ver & 4 && ct * cp > .02) cara([P(x, y, z + d), P(x, y + h, z + d), P(x + w, y + h, z + d), P(x + w, y, z + d)], cs[2]);
        if (ver & 1) piso(x, x + w, z, z + d, y + h, cs[0]);
      };
      var tres = function (c) { return [css(c), css(c, .8), css(c, .66)]; };
      /* losa: costados de piedra */
      cara([P(n, -1.4, 0), P(n, .3, 0), P(n, .3, n), P(n, -1.4, n)], "#cdbfa8"); cara([P(0, -1.4, n), P(0, .3, n), P(n, .3, n), P(n, -1.4, n)], "#b6a890");
      /* el camino: la textura cenital proyectada al plano del suelo (y = .3), y encima una capa clara que crece al llegar al QR */
      var T = E.T, ta = k * ct / T, tb = k * st * sp / T, tc = -k * st / T, td = k * ct * sp / T;
      g.setTransform(rz * ta, rz * tb, rz * tc, rz * td, rz * (ox - k * ct * c0 + k * st * c0), rz * (oy - .3 * k * cp - k * st * sp * c0 - k * ct * sp * c0));
      g.drawImage(E.textura, 0, 0);
      if (qr > .01) { g.globalAlpha = qr * .75; g.fillStyle = css(CLARO); g.fillRect(0, 0, n * T, n * T); g.globalAlpha = 1; }
      g.setTransform(rz, 0, 0, rz, 0, 0);
      /* flores u hojas caídas y la sombra de la copa, solo en la vista de árbol */
      if (vB > .01) {
        g.globalAlpha = vB; E.caidas.forEach(function (f) { var p = P(f[0], .31, f[1]); g.fillStyle = css(f[2]); g.fillRect(X(p) - k * .14, Y(p) - k * .1, k * .28, k * .2); });
        /* sombra suave: tres capas de la misma silueta de la copa, cada vez más chicas */
        g.fillStyle = "#3a2a1c";
        [1, .8, .55].forEach(function (f) {
          g.globalAlpha = .055 * vB; g.beginPath();
          for (var i = 0; i <= 40; i++) { var a = i / 40 * 6.283, rr = E.radio(a) * f, p = P(c0 + 1 + Math.cos(a) * rr, .31, c0 + 1 + Math.sin(a) * rr); if (i) g.lineTo(X(p), Y(p)); else g.moveTo(X(p), Y(p)); }
          g.fill();
        });
        g.globalAlpha = 1;
      }
      /* pasto: losetas un poco más altas que el camino, con briznas que se acuestan al girar */
      E.pasto.map(function (s) { return [P(s.x + .5, .4, s.z + .5)[2], s]; }).sort(function (a, b) { return a[0] - b[0]; }).forEach(function (o) {
        var s = o[1]; caja(s.x, .3, s.z, 1, .22, 1, tres(mezcla(s.c, por(s.c, hundir(s.c)), qr)), 7);
      });
      if (vP > .01) E.briznas.forEach(function (lote, j) {
        g.beginPath(); g.strokeStyle = E.colBrizna[j]; g.lineWidth = Math.max(.6, k * .09);
        lote.forEach(function (b) { var p = P(b[0], .52, b[1]), q2 = P(b[0] + b[3] * vP, .52 + b[2] * vP, b[1] + b[4] * vP); g.moveTo(X(p), Y(p)); g.lineTo(X(q2), Y(q2)); });
        g.stroke();
      });
      /* el árbol: racimos, ramas y cubos, de atrás hacia adelante */
      var base = [c0, .3, c0], lista = [];
      /* una cara lateral se tapa si la columna vecina ya creció completa y cubre esa altura */
      var tapa = function (L, y0, y1) { for (var i = 0; i < L.length; i++) { var C = L[i]; if (C.b <= y0 + .01 && C.t >= y1 - .01 && ss(C.a, C.bb, e) >= .999) return true; } return false; };
      var nq = Math.round(qr * 32);
      E.cosas.forEach(function (o) {
        if (o.k === 0) { var vb = o.pronto ? vB2 : vB; if (vb > .01) lista.push([P(o.x, o.y, o.z)[2], o, vb]); }
        else if (o.k === 1) {
          var v = ss(o.C.a, o.C.bb, e); if (v < .02) return;
          var ver = v < .999 ? 7 : (o.arriba ? 0 : 1) | (tapa(o.vx, o.y, o.y + o.h) ? 0 : 2) | (tapa(o.vz, o.y, o.y + o.h) ? 0 : 4);
          if (ver) lista.push([P(o.x + .5, o.y + o.h / 2, o.z + .5)[2], o, v, ver]);
        }
        else if (vR > .01) lista.push([P((o.p[0] + o.q[0]) / 2, (o.p[1] + o.q[1]) / 2, (o.p[2] + o.q[2]) / 2)[2], o]);
      });
      lista.sort(function (a, b) { return a[0] - b[0]; });
      var junto = function (p) { return [base[0] + (p[0] - base[0]) * vR, base[1] + (p[1] - base[1]) * vR, base[2] + (p[2] - base[2]) * vR]; };
      lista.forEach(function (it) {
        var o = it[1], p, s;
        if (o.k === 0) { var vb = it[2]; p = P(o.x, o.y, o.z); s = o.s * k * vb; if (vb < .62) { g.globalAlpha = vb * 1.6; g.drawImage(o.img, X(p) - s / 2, Y(p) - s / 2, s, s); g.globalAlpha = 1; } else g.drawImage(o.img, X(p) - s / 2, Y(p) - s / 2, s, s); }
        else if (o.k === 1) { var v = it[2], w = v, h = o.h * v; caja(o.x + .5 - w / 2, o.y + (o.h - h) / 2, o.z + .5 - w / 2, w, h, w, o.tonos[nq] || (o.tonos[nq] = tres(mezcla(o.c, por(o.c, o.dk), nq / 32))), it[3]); }
        else {
          var a = P.apply(null, junto(o.p)), b = P.apply(null, junto(o.q)), d = Math.max(1, (o.r0 + o.r1) * k * vR);
          g.globalAlpha = Math.min(1, vR * 1.5); g.beginPath(); g.moveTo(X(a), Y(a)); g.lineTo(X(b), Y(b));
          g.lineWidth = d; g.strokeStyle = "#563a26"; g.stroke();
          g.beginPath(); g.moveTo(X(a) - d * .2, Y(a)); g.lineTo(X(b) - d * .2, Y(b)); g.lineWidth = d * .45; g.strokeStyle = "#7d5a3e"; g.lineCap = "butt"; g.stroke(); g.lineCap = "round"; g.globalAlpha = 1;
        }
      });
      g.lineWidth = .7;
      /* de noche (modo oscuro del sitio) la escena se oscurece en la vista de árbol; el QR sale claro para que se lea */
      if (S.noche && qr < .99) { g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = "source-atop"; g.fillStyle = "rgba(12,24,48," + (.5 * (1 - qr)).toFixed(3) + ")"; g.fillRect(0, 0, fondo.width, fondo.height); g.globalCompositeOperation = "source-over"; }
      componer();
    }

    /* lo que cae de la copa (pétalos en floración, hojas en secas, lluvia en lluvias), encima de la escena ya pintada */
    var caen = [], raf = 0;
    function componer() {
      var g = cv.getContext("2d"); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cv.width, cv.height); g.drawImage(fondo, 0, 0, cv.width, cv.height);
      if (S.t || !caen.length || !abierto) return;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      var V = vista, X = function (p) { return V.ox + p[0] * V.k; }, Y = function (p) { return V.oy + p[1] * V.k; };
      if (S.temp === "lluvias") {
        g.beginPath(); g.strokeStyle = "rgba(120,160,195,.55)"; g.lineWidth = Math.max(.8, V.k * .08);
        caen.forEach(function (p) { var a = V.P(p.x, p.y, p.z), b = V.P(p.x + .12, p.y + 1.1, p.z); g.moveTo(X(a), Y(a)); g.lineTo(X(b), Y(b)); });
        g.stroke(); return;
      }
      caen.forEach(function (p) {
        var q = V.P(p.x, p.y, p.z), l = V.k * .5;
        g.save(); g.translate(X(q), Y(q)); g.rotate(p.r); g.fillStyle = p.c; g.beginPath(); g.ellipse(0, 0, l / 2, l / 3.2, 0, 0, 7); g.fill(); g.restore();
      });
    }
    function sembrar() {
      var R = sem("caen" + S.e + S.temp), es = ESP[S.e], lluvia = S.temp === "lluvias"; caen = [];
      if (reduce.matches) return;
      for (var i = 0; i < (lluvia ? 70 : 18); i++) {
        var a = R() * 6.283, d = Math.sqrt(R()) * (lluvia ? n * .7 : E.Rc * .9);
        caen.push({ x: c0 + Math.cos(a) * d, y: R() * E.top, z: c0 + Math.sin(a) * d, v: lluvia ? .5 + R() * .3 : .025 + R() * .03, r: R() * 6, vr: (R() - .5) * .08,
          c: S.temp === "flor" ? es[2] : ["#a8802f", "#c9a24a", "#8f6a2a"][i % 3] });
      }
    }
    function animar() {
      raf = 0; if (!abierto || S.t || !caen.length) return;
      var lluvia = S.temp === "lluvias";
      caen.forEach(function (p) {
        p.y -= p.v; p.r += p.vr; if (!lluvia) p.x += Math.sin(p.y * .7) * .02;
        if (p.y < .6) p.y = lluvia ? E.top + Math.random() * 4 : E.Ht + (E.top - E.Ht) * (.2 + Math.random() * .6);
      });
      componer(); raf = requestAnimationFrame(animar);
    }
    var sigue = function () { if (!raf && abierto && !S.t && caen.length) raf = requestAnimationFrame(animar); };

    function medir() { W = cv.clientWidth || 320; H = Math.round(W * 1.04); dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = W * dpr; cv.height = H * dpr; cv.style.height = H + "px"; }
    var girando = false;
    function voltear() {
      if (girando) return; girando = true;
      var desde = S.t, hacia = S.t ? 0 : 1, t0 = performance.now(), dur = reduce.matches ? 1 : 1500;
      var paso = function (ahora) { var p = Math.min((ahora - t0) / dur, 1); S.t = desde + (hacia - desde) * p; pintar(S.t, p < 1); if (p < 1) requestAnimationFrame(paso); else { S.t = hacia; girando = false; rotulo(); sigue(); } };
      requestAnimationFrame(paso);
    }
    function rehacer() { construir(); sembrar(); pintar(S.t); rotulo(); sigue(); }
    /* QR plano para imprimir: módulos de 16 px, margen de 4 módulos y el nombre debajo */
    function descargar() {
      var es = ESP[S.e], Q = qrCodigo(url), m = 16, q = 4, lado = (Q.length + 2 * q) * m, c = document.createElement("canvas"), g = c.getContext("2d"), fam = getComputedStyle(el).fontFamily;
      c.width = lado; c.height = lado + 70; g.fillStyle = "#ffffff"; g.fillRect(0, 0, c.width, c.height); g.fillStyle = "#1b2a1f";
      Q.forEach(function (fila, y) { fila.forEach(function (v, x) { if (v) g.fillRect((x + q) * m, (y + q) * m, m, m); }); });
      g.textAlign = "center"; g.font = "600 30px " + fam; g.fillText(cfg.texto || document.title, lado / 2, lado + 18);
      g.font = "20px " + fam; g.fillStyle = "#4a5d69"; g.fillText(url.replace("https://", ""), lado / 2, lado + 50);
      c.toBlob(function (b) { var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "qr-" + (location.pathname.split("/").filter(Boolean).pop() || "campuslab") + ".png"; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000); });
    }

    /* ── qué árbol toca: el de la floración del sitio y el modo del sitio ── */
    var html = document.documentElement, sistema = window.matchMedia("(prefers-color-scheme: dark)");
    var POR_FLOR = { "rosa-morada": 0, jacaranda: 1, primavera: 2, tabachin: 3, galeana: 4, clavellina: 5 };
    var POR_MES = { 12: "clavellina", 1: "clavellina", 2: "rosa-morada", 3: "jacaranda", 4: "primavera", 5: "tabachin", 6: "tabachin", 11: "galeana" };
    var S = { e: 3, temp: "lluvias", t: 0, noche: false };
    function destino() { return elegirUrl().url; }
    function tema() {
      var f = html.dataset.clFlor || POR_MES[new Date().getMonth() + 1] || "lluvias", e = POR_FLOR[f];
      var noche = html.dataset.clModo ? html.dataset.clModo === "oscuro" : sistema.matches;
      var temp = e == null ? "lluvias" : "flor";
      e = e == null ? 3 : e;
      if (E && e === S.e && temp === S.temp && noche === S.noche) return;
      var otro = !E || e !== S.e || temp !== S.temp;
      S.e = e; S.temp = temp; S.noche = noche;
      if (otro) rehacer(); else { pintar(S.t); rotulo(); }
    }

    var nombre = el.querySelector(".cl-aqr-nombre"), pista = el.querySelector(".cl-aqr-pista"), bVer = el.querySelector('[data-accion="ver"]');
    var abrir = el.querySelector(".cl-aqr-abrir"), panel = el.querySelector(".cl-aqr-panel"), lienzo = el.querySelector(".cl-aqr-lienzo"), mini = el.querySelector(".cl-aqr-mini");
    var abierto = false;
    function rotulo() {
      var es = ESP[S.e];
      nombre.textContent = es[1] + (S.temp === "lluvias" ? " en temporada de lluvias" : " en flor") + (S.noche ? ", de noche" : "");
      pista.textContent = S.t ? "Escanéalo con la cámara del celular" : "Toca el árbol: su copa se vuelve el QR de esta página";
      bVer.textContent = S.t ? "Ver el árbol" : "Ver el QR";
      cv.setAttribute("role", "img");
      cv.setAttribute("aria-label", S.t ? "Código QR que lleva a esta página (" + url.replace(/^https?:\/\//, "") + ")" : es[1] + " sobre el código QR de esta página; su copa forma el centro del código");
    }
    /* un solo lienzo: chico en el botón, grande en el panel; al moverlo, el ResizeObserver lo vuelve a medir */
    function poner(a) {
      abierto = a; el.dataset.abierto = String(a); abrir.setAttribute("aria-expanded", String(a)); panel.hidden = !a;
      (a ? lienzo : mini).appendChild(cv);
      if (a) { panel.querySelector(".cl-aqr-titulo").focus(); sigue(); }
      else { if (S.t && !girando) { S.t = 0; pintar(0); rotulo(); } abrir.focus(); }
    }
    abrir.addEventListener("click", function () { poner(!abierto); });
    cv.addEventListener("click", function () { if (abierto) voltear(); });
    panel.addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      if (b.dataset.accion === "ver") voltear();
      if (b.dataset.accion === "bajar") descargar();
      if (b.dataset.accion === "cerrar") poner(false);
    });
    el.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && abierto) poner(false); });

    new MutationObserver(tema).observe(html, { attributes: true, attributeFilter: ["data-cl-flor", "data-cl-modo"] });
    sistema.addEventListener("change", tema);
    var rt; if (window.ResizeObserver) new ResizeObserver(function () { clearTimeout(rt); rt = setTimeout(function () { var w = cv.clientWidth; if (w && Math.abs(w - W) > 1) { medir(); pintar(S.t); } }, 60); }).observe(cv);
    medir(); tema();
  }

  /* a dónde lleva el QR: la URL de la Configuración, completa (https://…) o del sitio (/web/campuslab/naturalista), o si
     está vacía, esta misma página sin ?… ni #. El QR admite unos 210 caracteres: si no cabe o está mal escrita se usa
     esta página, y quien edita ve el aviso en el editor */
  function elegirUrl() {
    var pagina = location.origin + location.pathname, t = (cfg.url || "").trim(), u;
    if (!t) return { url: pagina };
    try { u = new URL(t, location.href).href; } catch (e) { return { url: pagina, aviso: "la URL \"" + t + "\" no es válida" }; }
    try { qrCodigo(u); } catch (e) { return { url: pagina, aviso: "la URL tiene " + u.length + " caracteres y el QR admite unos 210; usa una más corta" }; }
    return { url: u };
  }

  /* el motor (unos 60 ms) espera a que la página termine de cargar; en el editor de páginas no se monta, solo dice a dónde lleva */
  if (enEditor) {
    var d = elegirUrl();
    el.querySelector(".cl-aqr-nota").textContent = "Árbol QR: en la página publicada flota en la esquina inferior derecha y lleva a " +
      ((cfg.url || "").trim() && !d.aviso ? d.url : "esta misma página") + "." + (d.aviso ? " Aviso: " + d.aviso + "." : "");
    return;
  }
  if (document.readyState === "complete") arbolQR(); else window.addEventListener("load", arbolQR, { once: true });
})();
