"""Record a TraceIT walkthrough.

Run backend + static frontend first, then:
  python scripts/record_demo.py http://localhost:5500

Requires Playwright with Chromium in the recording environment.
"""
from __future__ import annotations
import shutil, sys, time, uuid
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE=sys.argv[1] if len(sys.argv)>1 else "http://localhost:5500"
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo'; FRAMES=OUT/'frames'; FRAMES.mkdir(parents=True,exist_ok=True)
email=f"demo-{uuid.uuid4().hex[:8]}@example.com"; password="TraceITDemo123!"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(viewport={"width":1440,"height":1000},device_scale_factor=1,record_video_dir=str(OUT))
    page=context.new_page()
    page.goto(BASE+'/index.html',wait_until='networkidle',timeout=30000); page.screenshot(path=str(FRAMES/'01-landing.png'),full_page=True)
    page.goto(BASE+'/dashboard.html',wait_until='networkidle',timeout=30000); page.screenshot(path=str(FRAMES/'02-record.png'),full_page=True)
    page.locator('[data-key="do_mg_l"]').click(); time.sleep(.3); page.screenshot(path=str(FRAMES/'03-do-graph.png'),full_page=True)
    page.goto(BASE+'/auth.html?mode=signup&next=dashboard.html',wait_until='networkidle',timeout=30000)
    page.locator('#signupName').fill('TraceIT Demo'); page.locator('#signupEmail').fill(email); page.locator('#signupPassword').fill(password); page.locator('#signupForm button[type="submit"]').click(); page.wait_for_url('**/dashboard.html',timeout=30000)
    page.locator('#observe').click(); time.sleep(.4); page.screenshot(path=str(FRAMES/'04-observation.png'),full_page=True); page.locator('#close').click()
    video_path=page.video.path()
    context.close()
    browser.close()
video=OUT/'traceit-walkthrough.webm'; shutil.move(video_path,video)
print(video)
