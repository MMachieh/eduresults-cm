"""
Drive every app route with Playwright. Logs in as each role, visits every page,
screenshots failures, and prints a summary.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
SCREENSHOT_DIR = "test_screenshots"

import os
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

CREDENTIALS = {
    "admin":   ("admin",    "mywebapp"),
    "teacher": ("teacher1", "teacher123"),
    "student": ("student1", "student123"),
    "parent":  ("parent1",  "parent123"),
}

# Routes to test per role: (url, description)
ROUTES = {
    "admin": [
        ("/accounts/dashboard/",            "Admin dashboard"),
        ("/school/admin/publish/",          "Publish sequences"),
        ("/reports/hub/",                   "Report cards hub"),
        ("/reports/analytics/",             "Analytics (no filter)"),
        ("/reports/api/enrollments/?academic_year=1", "API enrollments"),
    ],
    "teacher": [
        ("/accounts/dashboard/",            "Teacher dashboard"),
        ("/marks/teacher/assignments/",     "Select assignment"),
        ("/marks/teacher/class-summary/",   "Class summary (no filter)"),
    ],
    "student": [
        ("/accounts/dashboard/",            "Student dashboard"),
        ("/marks/student/results/",         "Student results (no filter)"),
        ("/marks/student/analytics/",       "Student analytics"),
    ],
    "parent": [
        ("/accounts/dashboard/",            "Parent dashboard"),
        ("/marks/parent/results/",          "Parent results (no filter)"),
    ],
}

results = []

async def login(page, username, password):
    await page.goto(f"{BASE}/accounts/login/")
    await page.fill('input[name="username"]', username)
    await page.fill('input[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")

async def test_role(playwright, role, username, password, routes):
    browser = await playwright.chromium.launch()
    ctx = await browser.new_context()
    page = await ctx.new_page()

    # Collect JS errors
    js_errors = []
    page.on("pageerror", lambda e: js_errors.append(str(e)))

    # Login
    try:
        await login(page, username, password)
        if "/dashboard/" not in page.url and "login" in page.url:
            results.append({"role": role, "url": "/login", "status": "FAIL", "note": "Login failed"})
            await browser.close()
            return
    except Exception as e:
        results.append({"role": role, "url": "/login", "status": "FAIL", "note": str(e)})
        await browser.close()
        return

    for url, desc in routes:
        js_errors.clear()
        try:
            resp = await page.goto(f"{BASE}{url}", wait_until="networkidle", timeout=10000)
            status = resp.status if resp else 0
            content = await page.content()

            # Detect Django error pages
            is_error = (
                status >= 400
                or "Server Error" in content
                or "Exception Value" in content
                or "OperationalError" in content
                or "TemplateDoesNotExist" in content
                or "NoReverseMatch" in content
                or "AttributeError" in content
                or "TypeError" in content
                or ("error" in content.lower() and status >= 500)
            )

            if is_error or js_errors:
                slug = url.replace("/", "_").strip("_")
                shot = f"{SCREENSHOT_DIR}/{role}_{slug}.png"
                await page.screenshot(path=shot)
                note = f"HTTP {status}"
                if js_errors:
                    note += f" | JS: {js_errors[0][:80]}"
                if "Exception Value" in content:
                    start = content.find("Exception Value")
                    note += " | " + content[start:start+200].replace("\n", " ")[:150]
                results.append({"role": role, "url": url, "desc": desc, "status": "FAIL", "note": note, "shot": shot})
            else:
                results.append({"role": role, "url": url, "desc": desc, "status": "OK",   "note": f"HTTP {status}"})

        except Exception as e:
            results.append({"role": role, "url": url, "desc": desc, "status": "FAIL", "note": str(e)[:120]})

    await browser.close()

async def main():
    async with async_playwright() as pw:
        for role, (username, password) in CREDENTIALS.items():
            routes = ROUTES.get(role, [])
            print(f"Testing as {role} ({username})...")
            await test_role(pw, role, username, password, routes)

    print("\n" + "="*70)
    ok = [r for r in results if r["status"] == "OK"]
    fail = [r for r in results if r["status"] == "FAIL"]
    print(f"RESULTS: {len(ok)} OK  |  {len(fail)} FAILED\n")
    for r in results:
        icon = "OK" if r["status"] == "OK" else "XX"
        desc = r.get("desc", r["url"])
        print(f"  [{r['role']:8}] {icon} {desc:40} {r['note'][:80]}")
        if r["status"] == "FAIL" and "shot" in r:
            print(f"             Screenshot: {r['shot']}")
    print("="*70)
    return len(fail)

if __name__ == "__main__":
    failures = asyncio.run(main())
    sys.exit(failures)
