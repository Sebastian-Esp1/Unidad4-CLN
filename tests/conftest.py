import pytest

from cargar_csv import load_fixture


@pytest.fixture
def orders():
    """Pedidos frescos (todos DRAFT) para cada prueba."""
    return load_fixture()
