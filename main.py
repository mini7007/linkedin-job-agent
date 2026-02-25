import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

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


def random_delay(a=3, b=7):
    time.sleep(random.uniform(a, b))


def already_applied(job_id):
    url = f"{SUPABASE_URL}/rest/v1/applied_jobs?job_id=eq.{job_id}"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200 and len(r.json()) > 0


def save_job(job):
    url = f"{SUPABASE_URL}/rest/v1/applied_jobs"
    requests.post(url, headers=HEADERS, json=job)


def run_bot():
    print("🚀 Starting LinkedIn bot...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 🔐 Login
        page.goto("https://www.linkedin.com/login")
        page.fill("#username", LINKEDIN_EMAIL)
        page.fill("#password", LINKEDIN_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_timeout(8000)

        print("✅ Logged in")

        for keyword in SEARCH_KEYWORDS:
            print(f"🔍 Searching: {keyword}")

            search_url = (
                "https://www.linkedin.com/jobs/search/"
                f"?keywords={keyword.replace(' ', '%20')}&f_TPR=r86400&f_E=2"
            )

            page.goto(search_url)
            random_delay(5, 8)

            jobs = page.locator(".jobs-search-results__list-item").all()[:10]

            for job in jobs:
                try:
                    job.click()
                    random_delay(4, 6)

                    job_id = page.url.split("currentJobId=")[-1].split("&")[0]

                    if already_applied(job_id):
                        print("⏭️ Already applied")
                        continue

                    easy_apply = page.locator(
                        'button:has-text("Easy Apply")'
                    )

                    if easy_apply.count() == 0:
                        print("❌ No Easy Apply")
                        continue

                    easy_apply.first.click()
                    random_delay(3, 5)

                    submit_btn = page.locator(
                        'button:has-text("Submit application")'
                    )

                    if submit_btn.count() > 0:
                        submit_btn.first.click()
                        print("✅ Applied")

                        save_job(
                            {
                                "job_id": job_id,
                                "title": keyword,
                                "company": "LinkedIn",
                                "location": "Remote",
                                "job_url": page.url,
                            }
                        )

                    random_delay(10, 20)

                except Exception as e:
                    print("⚠️ Error:", e)
                    continue

        browser.close()


if __name__ == "__main__":
    run_bot()
