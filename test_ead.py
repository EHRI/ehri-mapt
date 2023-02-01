import pytest

import xml.etree.ElementTree as ET

from ead import Ead
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


def test_to_xml(archive):
    ead_xml = Ead().to_xml(archive)
    print(ead_xml)
    doc = ET.XML(ead_xml)
    item1 = doc.find('.//e:archdesc/e:dsc/e:c1/e:c2/e:c3/e:did/e:unitid', EADNS)
    assert item1 is not None, "could not find item1 'unitid' element"
    assert item1.text == "Dir1/Dir1-1/item1"

    item3 = doc.find('.//e:archdesc/e:dsc/e:c1[2]/e:c2/e:c3/e:did/e:unitid', EADNS)
    assert item3 is not None, "could not find item3 'unitid' element"
    assert item3.text == "Dir2/Dir2-1/item3"
