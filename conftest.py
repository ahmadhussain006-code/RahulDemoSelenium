import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default=None,
        help="Run on a single browser: chrome | firefox | edge. Omit to run all browsers."
    )


def pytest_generate_tests(metafunc):
    """
    If --browser is passed, run only that browser.
    If --browser is NOT passed, parametrize across all 3 browsers automatically.
    """
    if "browser" in metafunc.fixturenames:
        selected = metafunc.config.getoption("--browser")
        if selected:
            metafunc.parametrize("browser", [selected])
        else:
            metafunc.parametrize("browser", ["chrome", "firefox", "edge"])