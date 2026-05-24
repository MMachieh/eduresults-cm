"""Take screenshots of all key pages with real data."""
import asyncio, os
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
DIR  = "test_screenshots"
os.makedirs(DIR, exist_ok=True)

SEQ_ID     = 1
CLASS_ID   = 2
STUDENT_ID = 2
AY_ID      = 1

async def shot(page, path, url, wait="networkidle"):
    await page.goto(f"{BASE}{url}", wait_until=wait, timeout=15000)
    await page.screenshot(path=f"{DIR}/{path}.png", full_page=True)
    status = "OK" if "Exception Value" not in await page.content() and "Server Error" not in await page.content() else "ERROR"
    print(f"  [{status}] {path:45} {url}")
    return status

async def login(page, user, pw):
    await page.goto(f"{BASE}/accounts/login/")
    await page.fill('input[name="username"]', user)
    await page.fill('input[name="password"]', pw)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")

async def main():
    errors = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()

        # ── ADMIN ──────────────────────────────────────────────────────
        print("\n=== ADMIN ===")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await login(page, "admin", "mywebapp")

        for name, url in [
            ("01_admin_dashboard",       "/accounts/dashboard/"),
            ("02_publish_sequences",     "/school/admin/publish/"),
            ("03_report_hub",            "/reports/hub/"),
            ("04_analytics_empty",       "/reports/analytics/"),
            ("05_analytics_with_data",   f"/reports/analytics/?sequence={SEQ_ID}&class_id={CLASS_ID}"),
            ("06_report_card_online",    f"/reports/view/{SEQ_ID}/{STUDENT_ID}/"),
            ("07_report_card_admin_view",f"/reports/view/{SEQ_ID}/{STUDENT_ID}/"),
        ]:
            s = await shot(page, name, url)
            if s == "ERROR": errors.append(name)

        await ctx.close()

        # ── TEACHER ────────────────────────────────────────────────────
        print("\n=== TEACHER ===")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await login(page, "teacher1", "teacher123")

        # Get teacher assignment id
        asgn_id = None
        await page.goto(f"{BASE}/marks/teacher/assignments/")
        content = await page.content()

        for name, url in [
            ("08_teacher_dashboard",    "/accounts/dashboard/"),
            ("09_select_assignment",    "/marks/teacher/assignments/"),
            ("10_class_summary_empty",  "/marks/teacher/class-summary/"),
            ("11_mark_entry_sheet",     f"/marks/teacher/entry/1/{SEQ_ID}/"),
        ]:
            s = await shot(page, name, url)
            if s == "ERROR": errors.append(name)

        # Try class summary with data — find first teacher assignment
        from_page = await page.goto(f"{BASE}/marks/teacher/class-summary/?assignment=1&sequence={SEQ_ID}", wait_until="networkidle")
        content = await page.content()
        if "Exception Value" not in content:
            await page.screenshot(path=f"{DIR}/12_class_summary_data.png", full_page=True)
            print(f"  [OK ] 12_class_summary_data                        /marks/teacher/class-summary/?assignment=1&sequence={SEQ_ID}")
        await ctx.close()

        # ── STUDENT ────────────────────────────────────────────────────
        print("\n=== STUDENT ===")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await login(page, "student1", "student123")

        for name, url in [
            ("13_student_dashboard",        "/accounts/dashboard/"),
            ("14_student_results_empty",    "/marks/student/results/"),
            ("15_student_results_with_data",f"/marks/student/results/?sequence={SEQ_ID}"),
            ("16_student_analytics",        "/marks/student/analytics/"),
            ("17_report_card_self",         f"/reports/online/{SEQ_ID}/"),
        ]:
            s = await shot(page, name, url)
            if s == "ERROR": errors.append(name)

        await ctx.close()

        # ── PARENT ─────────────────────────────────────────────────────
        print("\n=== PARENT ===")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await login(page, "parent1", "parent123")

        for name, url in [
            ("18_parent_dashboard",      "/accounts/dashboard/"),
            ("19_parent_results_empty",  "/marks/parent/results/"),
            ("20_parent_results_data",   f"/marks/parent/results/?student={STUDENT_ID}&sequence={SEQ_ID}"),
            ("21_report_card_parent",    f"/reports/online/{SEQ_ID}/{STUDENT_ID}/"),
        ]:
            s = await shot(page, name, url)
            if s == "ERROR": errors.append(name)

        await ctx.close()

        # ── PUBLIC ─────────────────────────────────────────────────────
        print("\n=== PUBLIC ===")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        for name, url in [
            ("22_login_page",            "/accounts/login/"),
            ("23_register_parent",       "/accounts/register/parent/"),
            ("24_pending_approval",      "/accounts/pending-approval/"),
        ]:
            s = await shot(page, name, url)
            if s == "ERROR": errors.append(name)
        await ctx.close()

        await browser.close()

    print(f"\n{'='*60}")
    print(f"Screenshots saved to: {DIR}/")
    if errors:
        print(f"ERRORS on: {errors}")
    else:
        print("All pages rendered without server errors.")
    print('='*60)

asyncio.run(main())
