"""Full audit of every page in the app."""
import asyncio, os, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
DIR = "audit_screenshots"
os.makedirs(DIR, exist_ok=True)

results = []

async def login(page, user, pw):
    await page.goto(f"{BASE}/accounts/login/")
    await page.fill('input[name="username"]', user)
    await page.fill('input[name="password"]', pw)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")

async def check(page, role, name, url, wait="networkidle"):
    try:
        resp = await page.goto(f"{BASE}{url}", wait_until=wait, timeout=12000)
        status = resp.status if resp else 0
        content = await page.content()
        errors = [k for k in ["Exception Value","Server Error","OperationalError","TemplateDoesNotExist","NoReverseMatch","AttributeError","TypeError"] if k in content]
        if status >= 400 or errors:
            shot = f"{DIR}/{role}_{name}.png"
            await page.screenshot(path=shot, full_page=True)
            detail = ""
            if "Exception Value" in content:
                idx = content.find("Exception Value")
                detail = content[idx:idx+300].replace("\n"," ")[:200]
            results.append({"role": role, "name": name, "url": url, "status": "FAIL", "http": status, "detail": detail or str(errors)})
            print(f"  [FAIL] {name:45} HTTP {status} {detail[:80]}")
        else:
            results.append({"role": role, "name": name, "url": url, "status": "OK", "http": status})
            print(f"  [OK  ] {name:45} HTTP {status}")
    except Exception as e:
        results.append({"role": role, "name": name, "url": url, "status": "CRASH", "detail": str(e)[:120]})
        print(f"  [CRASH] {name:45} {str(e)[:80]}")

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()

        # ── ADMIN ──────────────────────────────────────────────────────
        print("\n=== ADMIN ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        await login(page, "admin", "mywebapp")
        for name, url in [
            ("dashboard",               "/accounts/dashboard/"),
            ("publish_sequences",        "/school/admin/publish/"),
            ("report_hub",              "/reports/hub/"),
            ("analytics_empty",         "/reports/analytics/"),
            ("analytics_form5a_seq1",   "/reports/analytics/?sequence=1&class_id=2"),
            ("analytics_form5a_seq2",   "/reports/analytics/?sequence=2&class_id=2"),
            ("report_card_view",        "/reports/view/1/2/"),
            ("report_card_view_seq2",   "/reports/view/2/2/"),
            ("pdf_download",            "/reports/pdf/1/2/"),
            ("zip_download",            "/reports/zip/1/2/"),
            ("api_enrollments",         "/reports/api/enrollments/?academic_year=1"),
            ("admin_panel",             "/school-admin-secure-2025/"),
            ("password_change_admin",   "/school-admin-secure-2025/password_change/"),
        ]:
            await check(page, "admin", name, url)
        await ctx.close()

        # ── TEACHER ────────────────────────────────────────────────────
        print("\n=== TEACHER ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        await login(page, "teacher1", "teacher123")
        for name, url in [
            ("dashboard",               "/accounts/dashboard/"),
            ("select_assignment",        "/marks/teacher/assignments/"),
            ("mark_entry_form5a_seq1",   "/marks/teacher/entry/1/1/"),
            ("mark_entry_form5a_seq2",   "/marks/teacher/entry/1/2/"),
            ("class_summary_empty",      "/marks/teacher/class-summary/"),
            ("class_summary_form5a_s1",  "/marks/teacher/class-summary/?assignment=1&sequence=1"),
            ("class_summary_form5a_s2",  "/marks/teacher/class-summary/?assignment=1&sequence=2"),
            ("password_change",          "/accounts/password_change/"),
        ]:
            await check(page, "teacher", name, url)
        await ctx.close()

        # ── TEACHER2 ────────────────────────────────────────────────────
        print("\n=== TEACHER2 ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        await login(page, "teacher2", "teacher123")
        for name, url in [
            ("dashboard",               "/accounts/dashboard/"),
            ("select_assignment",        "/marks/teacher/assignments/"),
            ("class_summary_empty",      "/marks/teacher/class-summary/"),
        ]:
            await check(page, "teacher2", name, url)
        await ctx.close()

        # ── STUDENT ────────────────────────────────────────────────────
        print("\n=== STUDENT ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        await login(page, "student1", "student123")
        for name, url in [
            ("dashboard",               "/accounts/dashboard/"),
            ("my_results_empty",        "/marks/student/results/"),
            ("my_results_seq1",         "/marks/student/results/?sequence=1"),
            ("my_results_seq2",         "/marks/student/results/?sequence=2"),
            ("analytics",               "/marks/student/analytics/"),
            ("report_cards",            "/reports/my-reports/"),
            ("report_card_seq1",        "/reports/online/1/"),
            ("report_card_seq2",        "/reports/online/2/"),
            ("password_change",         "/accounts/password_change/"),
        ]:
            await check(page, "student", name, url)
        await ctx.close()

        # ── PARENT ─────────────────────────────────────────────────────
        print("\n=== PARENT ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        await login(page, "parent1", "parent123")
        for name, url in [
            ("dashboard",               "/accounts/dashboard/"),
            ("results_empty",           "/marks/parent/results/"),
            ("results_student1_seq1",   "/marks/parent/results/?student=2&sequence=1"),
            ("results_student1_seq2",   "/marks/parent/results/?student=2&sequence=2"),
            ("report_cards_empty",      "/reports/parent-reports/"),
            ("report_cards_student1",   "/reports/parent-reports/?student=2"),
            ("report_card_online",      "/reports/online/1/2/"),
            ("password_change",         "/accounts/password_change/"),
        ]:
            await check(page, "parent", name, url)
        await ctx.close()

        # ── PARENT2 ─────────────────────────────────────────────────────
        print("\n=== PARENT2 ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        await login(page, "parent2", "parent123")
        for name, url in [
            ("dashboard",               "/accounts/dashboard/"),
            ("results_empty",           "/marks/parent/results/"),
            ("report_cards_empty",      "/reports/parent-reports/"),
        ]:
            await check(page, "parent2", name, url)
        await ctx.close()

        # ── PUBLIC ─────────────────────────────────────────────────────
        print("\n=== PUBLIC ===")
        ctx = await browser.new_context(viewport={"width":1280,"height":900})
        page = await ctx.new_page()
        for name, url in [
            ("login_page",              "/accounts/login/"),
            ("register_parent",         "/accounts/register/parent/"),
            ("pending_approval",        "/accounts/pending-approval/"),
        ]:
            await check(page, "public", name, url)
        await ctx.close()

        await browser.close()

    ok = [r for r in results if r["status"]=="OK"]
    fail = [r for r in results if r["status"]!="OK"]
    print(f"\n{'='*70}")
    print(f"TOTAL: {len(results)} pages  |  {len(ok)} OK  |  {len(fail)} FAILED")
    if fail:
        print("\nFAILED:")
        for r in fail:
            print(f"  [{r['role']:10}] {r['name']:45} {r.get('detail','')[:100]}")
    print('='*70)
    return len(fail)

if __name__ == "__main__":
    failures = asyncio.run(main())
    sys.exit(failures)
