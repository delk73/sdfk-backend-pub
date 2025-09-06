"""Integration tests are gated behind RUN_SLOW to keep default runs fast."""

import os
import pytest


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        os.getenv("RUN_SLOW") != "1",
        reason="set RUN_SLOW=1 to run integration tests",
    ),
]

