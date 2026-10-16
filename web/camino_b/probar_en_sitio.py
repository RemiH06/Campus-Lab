"""Prueba un fragmento sobre una página real de campuslab.iteso.mx sin publicarlo: intercepta la
página, inyecta HTML/CSS/JS del fragmento (como lo pinta Liferay) y saca capturas en escritorio y celular.
Uso: python web/camino_b/probar_en_sitio.py   (requiere playwright; capturas en reestructura/salida/capturas/)
"""
import asyncio, re, json, pathlib
from playwright.async_api import async_playwright
REPO = pathlib.Path(__file__).resolve().parents[2]
F = REPO / "web" / "camino_b" / "liferay" / "fragmentos"
SALIDA = REPO / "reestructura" / "salida" / "capturas"
SALIDA.mkdir(parents=True, exist_ok=True)
U = "https://campuslab.iteso.mx/web/campuslab/temp"
async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for n in ["prototipo-plantillas", "prototipo-componentes"]:
            d = F / n; html = (d/"index.html").read_text(encoding="utf-8"); css = (d/"index.css").read_text(encoding="utf-8"); js = (d/"index.js").read_text(encoding="utf-8")
            conf = {"datos": json.loads((d/"configuration.json").read_text(encoding="utf-8"))["fieldSets"][0]["fields"][0]["defaultValue"]}
            wrap = "(function(){var fragmentElement=document.getElementById('fragment-cl');var configuration=" + json.dumps(conf) + ";\n" + js + "\n})();"
            for vp, sch in [({"width": 1280, "height": 900}, "light"), ({"width": 390, "height": 844}, "dark")]:
                pg = await b.new_page(viewport=vp, color_scheme=sch); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                async def h(route):
                    resp = await route.fetch(); body = await resp.text()
                    body = re.sub(r'<div class="lfr-layout-structure-item-com-liferay-journal-content-web-portlet-journalcontentportlet.*?(?=</div>\s*</div>\s*</section>)', "", body, count=1, flags=re.S)
                    body = body.replace("</head>", "<style>" + css + "</style></head>", 1)
                    body = body.replace('<div class="layout-content portlet-layout" id="main-content"', '<div class="layout-content portlet-layout" id="main-content"', 1)
                    i = body.find('id="main-content"'); i = body.find(">", i) + 1
                    body = body[:i] + '<div id="fragment-cl">' + html + "</div>" + body[i:]
                    k = body.rfind("</body>"); body = body[:k] + "<script>" + wrap.replace("</", "<\\/") + "</script>" + body[k:]
                    await route.fulfill(response=resp, body=body)
                await pg.route(U, h)
                await pg.goto(U, wait_until="networkidle", timeout=90000); await pg.wait_for_timeout(2500)
                await pg.screenshot(path=str(SALIDA / f"f_{n}_{vp['width']}.png"))
                ok = await pg.evaluate("document.querySelectorAll('.mos-c, .demo .stage *').length")
                ov = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                print(n, vp["width"], "elementos", ok, "overflow", ov, "errores", [e[:120] for e in errs[:3]])
        await b.close()
asyncio.run(run())
