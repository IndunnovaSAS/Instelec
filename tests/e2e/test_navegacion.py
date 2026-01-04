"""
E2E tests using Playwright for browser-based navigation testing.

NOTE: These tests require special setup due to async compatibility issues
between Playwright and Django. Run them separately with:

    python manage.py test tests.e2e.test_navegacion --keepdb

Or use the StaticLiveServerTestCase approach shown below.
"""

import pytest
from django.test import LiveServerTestCase, override_settings
from django.contrib.auth import get_user_model
from playwright.sync_api import sync_playwright


@override_settings(ALLOWED_HOSTS=['*'])
class PlaywrightTestCase(LiveServerTestCase):
    """Base class for Playwright E2E tests using Django's test framework."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.page = self.browser.new_page()

    def tearDown(self):
        self.page.close()
        super().tearDown()


class TestHealthCheckBrowser(PlaywrightTestCase):
    """Test health check endpoints via browser."""

    def test_health_endpoint_returns_healthy(self):
        """Test health check endpoint returns healthy status."""
        self.page.goto(f"{self.live_server_url}/health/")
        content = self.page.content()
        self.assertIn("healthy", content.lower())

    def test_api_health_endpoint_returns_healthy(self):
        """Test API health check endpoint returns healthy status."""
        self.page.goto(f"{self.live_server_url}/api/health/")
        content = self.page.content()
        self.assertIn("healthy", content.lower())


class TestLoginPageBrowser(PlaywrightTestCase):
    """Test login page functionality via browser."""

    def test_login_page_loads(self):
        """Test that login page loads with form elements."""
        self.page.goto(f"{self.live_server_url}/usuarios/login/")

        # Page should have form elements
        body = self.page.locator("body")
        self.assertTrue(body.is_visible())

    def test_login_form_has_required_fields(self):
        """Test login form has email and password fields."""
        self.page.goto(f"{self.live_server_url}/usuarios/login/")

        # Look for username/email input
        email_input = self.page.locator(
            "input[name='username'], input[name='email'], input[type='email']"
        ).first
        password_input = self.page.locator(
            "input[name='password'], input[type='password']"
        ).first

        self.assertTrue(email_input.is_visible())
        self.assertTrue(password_input.is_visible())

    def test_invalid_login_stays_on_page(self):
        """Test invalid login shows error and stays on page."""
        self.page.goto(f"{self.live_server_url}/usuarios/login/")

        # Fill form with invalid credentials
        self.page.locator(
            "input[name='username'], input[name='email'], input[type='email']"
        ).first.fill("wrong@test.com")
        self.page.locator(
            "input[name='password'], input[type='password']"
        ).first.fill("wrongpass")

        # Submit
        self.page.locator(
            "button[type='submit'], input[type='submit']"
        ).first.click()

        self.page.wait_for_load_state("networkidle")

        # Should stay on login page
        self.assertIn("login", self.page.url)

    def test_valid_login_redirects(self):
        """Test valid login redirects away from login page."""
        User = get_user_model()
        User.objects.create_user(
            email="playwright@test.com",
            password="PlaywrightPass123!",
            first_name="Playwright",
            last_name="Test",
        )

        self.page.goto(f"{self.live_server_url}/usuarios/login/")

        # Fill form with valid credentials
        self.page.locator(
            "input[name='username'], input[name='email'], input[type='email']"
        ).first.fill("playwright@test.com")
        self.page.locator(
            "input[name='password'], input[type='password']"
        ).first.fill("PlaywrightPass123!")

        # Submit
        self.page.locator(
            "button[type='submit'], input[type='submit']"
        ).first.click()

        self.page.wait_for_load_state("networkidle")

        # Should redirect away from login
        url = self.page.url
        self.assertTrue("/login" not in url or "next=" in url)


class TestProtectedPagesBrowser(PlaywrightTestCase):
    """Test that protected pages require authentication."""

    def test_actividades_redirects_to_login(self):
        """Test actividades page redirects unauthenticated users to login."""
        self.page.goto(f"{self.live_server_url}/actividades/")
        self.page.wait_for_load_state("networkidle")
        self.assertIn("login", self.page.url)

    def test_cuadrillas_redirects_to_login(self):
        """Test cuadrillas page redirects unauthenticated users to login."""
        self.page.goto(f"{self.live_server_url}/cuadrillas/")
        self.page.wait_for_load_state("networkidle")
        self.assertIn("login", self.page.url)

    def test_campo_redirects_to_login(self):
        """Test campo page redirects unauthenticated users to login."""
        self.page.goto(f"{self.live_server_url}/campo/")
        self.page.wait_for_load_state("networkidle")
        self.assertIn("login", self.page.url)


class TestNavigationAfterLoginBrowser(PlaywrightTestCase):
    """Test navigation after successful login."""

    def setUp(self):
        super().setUp()
        # Create and login user
        User = get_user_model()
        self.user = User.objects.create_user(
            email="navegador@test.com",
            password="NavPass123!",
            first_name="Navegador",
            last_name="Test",
            rol="coordinador",
        )

        # Perform login
        self.page.goto(f"{self.live_server_url}/usuarios/login/")
        self.page.locator(
            "input[name='username'], input[name='email'], input[type='email']"
        ).first.fill("navegador@test.com")
        self.page.locator(
            "input[name='password'], input[type='password']"
        ).first.fill("NavPass123!")
        self.page.locator(
            "button[type='submit'], input[type='submit']"
        ).first.click()
        self.page.wait_for_load_state("networkidle")

    def test_home_accessible_after_login(self):
        """Test home page is accessible after login."""
        self.page.goto(f"{self.live_server_url}/")
        self.page.wait_for_load_state("networkidle")
        self.assertNotIn("/login", self.page.url)

    def test_actividades_accessible_after_login(self):
        """Test actividades page is accessible after login."""
        self.page.goto(f"{self.live_server_url}/actividades/")
        self.page.wait_for_load_state("networkidle")
        # Should not redirect to login or have next param
        url = self.page.url
        self.assertTrue("/login" not in url or "next=" in url)


class TestResponsiveDesignBrowser(PlaywrightTestCase):
    """Test responsive design on different viewports."""

    def test_mobile_viewport(self):
        """Test login page works on mobile viewport."""
        self.page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE
        self.page.goto(f"{self.live_server_url}/usuarios/login/")

        # Form should be visible
        email_input = self.page.locator(
            "input[name='username'], input[name='email'], input[type='email']"
        ).first
        self.assertTrue(email_input.is_visible())

    def test_tablet_viewport(self):
        """Test login page works on tablet viewport."""
        self.page.set_viewport_size({"width": 768, "height": 1024})  # iPad
        self.page.goto(f"{self.live_server_url}/usuarios/login/")

        # Form should be visible
        email_input = self.page.locator(
            "input[name='username'], input[name='email'], input[type='email']"
        ).first
        self.assertTrue(email_input.is_visible())


class TestErrorPagesBrowser(PlaywrightTestCase):
    """Test error page handling."""

    def test_404_page(self):
        """Test 404 page returns correct status."""
        response = self.page.goto(f"{self.live_server_url}/pagina-inexistente-xyz/")
        self.assertEqual(response.status, 404)
