import random
import urllib.parse

import pytest
from httpx import AsyncClient, ASGITransport

from src.app import app, activities


@pytest.mark.asyncio
async def test_root_redirect():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False) as ac:
        r = await ac.get("/")
        assert r.status_code in (301, 302, 307)
        assert r.headers.get("location") == "/static/index.html"


@pytest.mark.asyncio
async def test_get_activities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/activities")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data


@pytest.mark.asyncio
async def test_signup_and_unregister_flow():
    email = f"test+{''.join(random.choices('abcdef0123456789', k=6))}@example.com"
    activity = "Chess Club"

    # Ensure email not present before test
    if email in activities[activity]["participants"]:
        activities[activity]["participants"].remove(email)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Sign up
        r = await ac.post(f"/activities/{activity}/signup?email={urllib.parse.quote(email, safe='')}")
        assert r.status_code == 200
        assert "Signed up" in r.json().get("message", "")

        # Verify participant present via GET
        r2 = await ac.get("/activities")
        assert email in r2.json()[activity]["participants"]

        # Unregister
        r3 = await ac.post(f"/activities/{activity}/unregister?email={urllib.parse.quote(email, safe='')}")
        assert r3.status_code == 200
        assert "Unregistered" in r3.json().get("message", "")

        # Verify removed
        r4 = await ac.get("/activities")
        assert email not in r4.json()[activity]["participants"]


@pytest.mark.asyncio
async def test_unregister_nonexistent_returns_404():
    activity = "Chess Club"
    email = "not-exist@example.com"
    # Ensure not present
    activities[activity]["participants"] = [p for p in activities[activity]["participants"] if p != email]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(f"/activities/{activity}/unregister?email={urllib.parse.quote(email, safe='')}")
        assert r.status_code == 404
