from playwright.sync_api import sync_playwright
import pathlib
u=pathlib.Path('index.html').resolve().as_uri()
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome"); pg=b.new_page(viewport={"width":1920,"height":1080})
    out=[]
    pg.goto(u); n=pg.evaluate("document.querySelectorAll('.slide').length")
    for i in range(1,n+1):
        pg.goto(f"{u}?m={i}#{i}"); pg.wait_for_timeout(150)
        t=pg.evaluate("""()=>{const s=document.querySelector('.slide.active');let m=0;
          for(const a of s.getAnimations({subtree:true})){if(a.transitionProperty)continue;const e=a.effect.getComputedTiming().endTime; if(isFinite(e)) m=Math.max(m,e);} return Math.round(m)/1000}""")
        out.append(f"{i}:{t}")
    print(" ".join(out)); b.close()
