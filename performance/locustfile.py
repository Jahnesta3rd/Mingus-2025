import os
import random
import uuid
from datetime import datetime

from locust import HttpUser, task, between, events


MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0 Mobile Safari/537.36",
]

DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]


def pick_user_agent():
    pct_mobile = float(os.getenv("PCT_MOBILE", "0.6"))
    if random.random() < pct_mobile:
        return random.choice(MOBILE_USER_AGENTS)
    return random.choice(DESKTOP_USER_AGENTS)


def build_registration_payload():
    first_names = ["Marcus", "Alicia", "Darius", "Tanya", "Jamal", "Imani", "Andre", "Keisha"]
    last_names = ["Johnson", "Brown", "Williams", "Harris", "Davis", "Robinson", "Jackson", "Thomas"]
    metros = [
        ("30309", "Atlanta", "GA"),
        ("77002", "Houston", "TX"),
        ("20001", "Washington", "DC"),
        ("75201", "Dallas", "TX"),
        ("60601", "Chicago", "IL"),
        ("90012", "Los Angeles", "CA"),
    ]
    first = random.choice(first_names)
    last = random.choice(last_names)
    z, city, state = random.choice(metros)
    email = f"{first.lower()}.{last.lower()}.{uuid.uuid4().hex[:6]}@example.com"
    return {
        "email": email,
        "password": "StrongPass!123",
        "first_name": first,
        "last_name": last,
        "phone_number": "+14045551234",
        "zip_code": z,
        "city": city,
        "state": state,
        "industry": random.choice(["Technology", "Healthcare", "Finance", "Consulting"]),
        "job_title": random.choice(["Software Developer", "Analyst", "Consultant", "Project Manager"]),
        "monthly_income": random.choice([55000, 65000, 75000, 90000, 100000]),
    }


class ApiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.headers = {
            "User-Agent": pick_user_agent(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.email = None
        self.password = "StrongPass!123"

    @task(3)
    def landing_and_health(self):
        self.client.get("/", headers={"User-Agent": self.headers["User-Agent"]}, name="GET /")
        self.client.get("/health", headers=self.headers, name="GET /health")
        self.client.get("/api/system/health", headers=self.headers, name="GET /api/system/health")

    @task(2)
    def register_login_dashboard(self):
        # Registration
        payload = build_registration_payload()
        self.email = payload["email"]
        reg = self.client.post("/api/auth/register", json=payload, headers=self.headers, name="POST /api/auth/register")
        if reg.status_code in (200, 201, 302):
            # Login
            login = self.client.post("/api/auth/login", json={"email": self.email, "password": self.password}, headers=self.headers, name="POST /api/auth/login")
            # Dashboard/profile fetches (session cookie maintained by locust)
            self.client.get("/api/auth/profile", headers=self.headers, name="GET /api/auth/profile")
            self.client.get("/api/user/onboarding", headers=self.headers, name="GET /api/user/onboarding")

    @task(1)
    def heavy_profile_updates(self):
        # Requires login/session; do a no-op if not set
        if not self.email:
            return
        update = {
            "dependents": random.randint(0, 3),
            "marital_status": random.choice(["single", "married"]),
            "education_level": random.choice(["bachelors", "masters"]),
            "current_savings_balance": random.choice([5000, 10000, 25000, 50000]),
            "total_debt_amount": random.choice([10000, 20000, 40000]),
        }
        self.client.post("/api/user-profile/update", json=update, headers=self.headers, name="POST /api/user-profile/update")


@events.init.add_listener
def _on_locust_init(environment, **_kwargs):
    # Configure environment defaults from env vars for CI and scripts
    environment.process_exit_code = 0
    target_p95 = float(os.getenv("TARGET_P95_MS", "800"))

    @events.quitting.add_listener
    def _(environment, **__kwargs):
        stats = environment.runner.stats.total
        p95 = stats.get_response_time_percentile(0.95)
        fail_ratio = stats.fail_ratio
        if p95 and p95 > target_p95 or fail_ratio > 0.02:
            environment.process_exit_code = 1


