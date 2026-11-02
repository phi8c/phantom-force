from importlib.metadata import PackageNotFoundError, version


def package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "unknown"
