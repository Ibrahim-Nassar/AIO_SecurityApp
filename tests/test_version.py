import re

def test_version_is_semver():
    from ioc_core.version import __version__
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__) is not None 