"""Pytest configuration and shared fixtures for BDD tests."""
import pytest


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data."""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment before each test."""
    # This fixture runs automatically before each test
    # Can be used to reset global state if needed
    yield
    # Cleanup after test if needed
