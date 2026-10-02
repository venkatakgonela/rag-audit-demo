import pytest

from rag_audit.db import check_vector_extension
from rag_audit.settings import Settings


@pytest.mark.integration
def test_vector_extension_is_enabled():
    assert check_vector_extension(Settings()), "The vector extension must be enabled"
