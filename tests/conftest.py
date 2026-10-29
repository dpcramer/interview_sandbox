import os
import random

import pytest
from faker import Faker

# Set TEST_SEED to reproduce a run; otherwise each run uses a fresh seed.
SEED = int(os.environ.get("TEST_SEED", random.randrange(2**32)))
NAMES_PER_TEST = 5

# Faker locales for the supported greeting languages (Faker has no Urdu locale).
FAKE = Faker(
    [
        "en_US",
        "zh_CN",
        "hi_IN",
        "es_ES",
        "ar_SA",
        "fr_FR",
        "bn_BD",
        "pt_BR",
        "ru_RU",
        "id_ID",
        "de_DE",
    ]
)


def pytest_report_header():
    return f"mock data seed: TEST_SEED={SEED}"


@pytest.fixture(params=range(NAMES_PER_TEST))
def name(request) -> str:
    """A random name; each test using it runs once per generated name."""
    FAKE.seed_instance(f"{SEED}-{request.node.nodeid}")
    return FAKE.name()
