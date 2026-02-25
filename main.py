import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

# ================= CONFIG =================
MAX_APPLIES_PER_RUN = 10
applied_count = 0

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

SEARCH_KEYWORDS = [
    "React Developer",
    "Full Stack Developer",
    "Frontend Engineer",
    "Software Engineer",
]


# ================= HELPERS =================
def random_delay(a=8, b=18):
    time.sleep(random.uniform(a, b))


def already_applied(job_id):
    url = f"{SUPABASE_URL}/rest/v1/applied_jobs?job_id=eq.{job_id}"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200 and len(r.json()) > 0


def save_job(job):
    url = f"{SUPABASE_URL}/rest/v1/applied_jobs"
    requests.post(url, headers=HEADERS, json=job)


# ================= MAIN BOT =================
def run_bot():
    global applied_count

    print("Starting LinkedIn bot...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Kolkata",
        )

        page = context.new_page()

        # ================= LOGIN =================
        page.goto(
            "https://www.linkedin.com/login",
            wait_until="domcontentloaded",
        )

        page.wait_for_selector("#username", timeout=60000)

        page.fill("#username", LINKEDIN_EMAIL)
        page.fill("#password", LINKEDIN_PASSWORD)

        random_delay(2, 4)

        page.click('button[type="submit"]')

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # checkpoint safety
        if "checkpoint" in page.url.lower():
            print("LinkedIn checkpoint detected. Stopping run.")
            browser.close()
            return

        print("Logged in successfully")

        # ================= SEARCH LOOP =================
        for keyword in SEARCH_KEYWORDS:
            if applied_count >= MAX_APPLIES_PER_RUN:
                print("Daily apply limit reached")
                break

            print(f"Searching: {keyword}")

            search_url = (
                "https://www.linkedin.com/jobs/search/"
                f"?keywords={keyword.replace(' ', '%20')}"
                "&f_AL=true"
                "&f_TPR=r86400"
                "&f_E=2"
            )

            page.goto(search_url)
            random_delay()

            jobs = page.locator(
                ".jobs-search-results__list-item"
            ).all()[:10]

            for job in jobs:
                if applied_count >= MAX_APPLIES_PER_RUN:
                    print("Daily apply limit reached")
                    break

                try:
                    job.click()
                    random_delay(6, 12)

                    if "currentJobId=" not in page.url:
                        continue

                    job_id = page.url.split("currentJobId=")[-1].split("&")[0]

                    if already_applied(job_id):
                        print("Already applied")
                        continue

                    easy_apply = page.locator('button:has-text("Easy Apply")')

                    if easy_apply.count() == 0:
                        print("No Easy Apply")
                        continue

                    easy_apply.first.click()
                    random_delay(5, 10)

                    submit_btn = page.locator(
                        'button:has-text("Submit application")'
                    )

                    if submit_btn.count() > 0:
                        submit_btn.first.click()
                        print("Applied successfully")

                        save_job(
                            {
                                "job_id": job_id,
                                "title": keyword,
                                "company": "LinkedIn",
                                "location": "Remote",
                                "job_url": page.url,
                            }
                        )

                        applied_count += 1

                    random_delay(12, 25)

                except Exception as e:
                    print("Error:", e)
                    continue

        browser.close()
        print(f"Run finished. Applied: {applied_count}")


# ================= ENTRY =================
if __name__ == "__main__":
    run_bot()