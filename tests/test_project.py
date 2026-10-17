
from importlib.metadata import version


def test_project_is_installed() -> None:
    assert version("helpdesk-api") == "0.1.0"


def test_python_version_is_supported() -> None:
    import sys

    assert sys.version_info >= (3, 12)
    assert sys.version_info < (3, 13)
