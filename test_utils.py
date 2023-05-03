from typing import Dict, Union

import pytest

from microarchive import MicroArchive, Identity, Description, Contact, Item, Control


@pytest.fixture
def archive():
    return MicroArchive(
        identity=Identity(
            title="Test",
            extent="1 box"
        ),
        description=Description(
            scope="Paragraph 1\n\nParagraph 2"
        ),
        contact=Contact(
            street="1 Acacia Av."
        ),
        control=Control(
          notes="Test Note"
        ),
        items=[
            Item.make(id="Dir1/Dir1-1/item1", identity=Identity(title="Item1")),
            Item.make(id="Dir1/item2", identity=Identity(title="Item2")),
            Item.make(id="Dir2/Dir2-1/item3", identity=Identity(title="Item3")),
            Item.make(id="Dir2/item4", identity=Identity(title="Item4")),
        ]
    )


def key_exists(data: Dict, *keys: Union[str, int]):
    elem = data
    for key in keys:
        try:
            elem = elem[key]
        except KeyError:
            return False
    return True


def value_of(data: Dict, *keys: Union[str, int]):
    elem = data
    for key in keys:
        try:
            elem = elem[key]
        except KeyError:
            return None
    return elem


