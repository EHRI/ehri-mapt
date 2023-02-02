import json
from typing import Dict, Union

import pytest

import xml.etree.ElementTree as ET

from ead import Ead
from iiif import IIIFManifest
from microarchive import MicroArchive, Identity, Description, Contact, Item

# NB: can't figure out how to use a default namespace here without
# xpath things breaking, e.g. positional ([1]) arguments?
EADNS = {'e': 'urn:isbn:1-931666-22-9'}

@pytest.fixture
def archive():
    return MicroArchive(
        identity=Identity(
            title="Test",
            extent="1 box"
        ),
        description=Description(
            scope="Test"
        ),
        contact=Contact(
            street="1 Acacia Av."
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


def test_to_json(archive):
    manifest = IIIFManifest(
        baseurl="http://example.com/",
        name="test",
        service_url="http://example.com/iiif/3/",
        prefix="foobar/").to_json(archive)
    print(manifest)
    data = json.loads(manifest)
    assert value_of(data, "label", "en", 0) == "Test"
    assert len(data["items"]) == 4, "has the right number of canvases"
    assert value_of(data, "structures", 0, "label", "en", 0) == "Dir1"
    assert value_of(data, "structures", 0, "items", 1, "label", "en", 0) == "Dir1-1"
    assert len(value_of(data, "structures", 0, "items")) == 2
