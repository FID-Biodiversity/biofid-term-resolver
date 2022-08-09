import pathlib

import pytest


@pytest.fixture
def test_directory():
    return pathlib.Path(__file__).parent


@pytest.fixture
def resources_directory_path(test_directory):
    return test_directory / 'resources'
