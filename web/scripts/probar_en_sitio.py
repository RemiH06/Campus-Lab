"""Prueba un fragmento sobre una página real de campuslab.iteso.mx sin publicarlo: intercepta la
página, inyecta HTML/CSS/JS del fragmento (como lo pinta Liferay) y saca capturas en escritorio y celular,
claro y oscuro. También mide el salto al hacer scroll: cuánto se mueve el contenido de más (0 = sin salto).
Uso: python web/scripts/probar_en_sitio.py [carpeta_fragmento ...]
     (sin argumentos prueba los dos prototipos; requiere playwright; capturas en catalogo/salida/capturas/)
"""
import asyncio, re, json, sys, pathlib
from playwright.async_api import async_playwright
REPO = pathlib.Path(__file__).resolve().parents[2]
F = REPO / "web" / "fragmentos"
SALIDA = REPO / "catalogo" / "salida" / "capturas"
SALIDA.mkdir(parents=True, exist_ok=True)
U = "https://campuslab.iteso.mx/web/campuslab/temp"
CARPETAS = [pathlib.Path(a).resolve() for a in sys.argv[1:]] or [F / "prototipo-plantillas", F / "prototipo-componentes"]

def configuracion(d):
    p = d / "configuration.json"
    if not p.exists(): return {}
    return {f["name"]: f.get("defaultValue") for fs in json.loads(p.read_text(encoding="utf-8"))["fieldSets"] for f in fs["fields"]}

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for d in CARPETAS:
            n = d.name
            html, css, js = ((d / f"index.{x}").read_text(encoding="utf-8") for x in ("html", "css", "js"))
            wrap = "(function(){var fragmentElement=document.getElementById('fragment-cl');var configuration=" + json.dumps(configuracion(d)) + ";\n" + js + "\n})();"
            for vp, sch in [({"width": 1280, "height": 900}, "light"), ({"width": 1280, "height": 900}, "dark"), ({"width": 390, "height": 844}, "light"), ({"width": 390, "height": 844}, "dark")]:
                pg = await b.new_page(viewport=vp, color_scheme=sch); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                async def h(route):
                    resp = await route.fetch(); body = await resp.text()
                    body = re.sub(r'<div class="lfr-layout-structure-item-com-liferay-journal-content-web-portlet-journalcontentportlet.*?(?=</div>\s*</div>\s*</section>)', "", body, count=1, flags=re.S)
                    body = body.replace("</head>", "<style>" + css + "</style></head>", 1)
                    i = body.find('id="main-content"'); i = body.find(">", i) + 1
                    body = body[:i] + '<div id="fragment-cl">' + html + "</div>" + body[i:]
                    k = body.rfind("</body>"); body = body[:k] + "<script>" + wrap.replace("</", "<\\/") + "</script>" + body[k:]
                    await route.fulfill(response=resp, body=body)
                await pg.route(U, h)
                await pg.goto(U, wait_until="networkidle", timeout=90000); await pg.wait_for_timeout(2500)
                tag = f"{n}_{vp['width']}_{'oscuro' if sch == 'dark' else 'claro'}"
                await pg.screenshot(path=str(SALIDA / f"f_{tag}.png"))
                top = "document.getElementById('main-content').getBoundingClientRect().top"
                t0 = await pg.evaluate(top); saltos = []
                for y in (1, 60, 400):
                    await pg.evaluate(f"window.scrollTo(0,{y})"); await pg.wait_for_timeout(450)
                    saltos.append(round(t0 - y - await pg.evaluate(top)))
                await pg.screenshot(path=str(SALIDA / f"f_{tag}_scroll.png"))
                await pg.evaluate("window.scrollTo(0,document.body.scrollHeight)"); await pg.wait_for_timeout(500)
                await pg.screenshot(path=str(SALIDA / f"f_{tag}_fin.png"))
                ov = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                print(tag, "salto(1/60/400px)", saltos, "overflow", ov, "errores", [e[:120] for e in errs[:3]])
                await pg.close()
        await b.close()
asyncio.run(run())
