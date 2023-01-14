import pytest


# This fixture enables loading custom integrations in all tests that import this fixture.
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enables custom_integrations fixture for all tests."""
    yield
