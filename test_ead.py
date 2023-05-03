import xml.etree.ElementTree as ET

from ead import Ead
# noinspection PyUnresolvedReferences
from test_utils import *

# NB: can't figure out how to use a default namespace here without
# xpath things breaking, e.g. positional ([1]) arguments?
EAD_NS = {'e': 'urn:isbn:1-931666-22-9'}


def test_to_xml(archive):
    ead_xml = Ead().to_xml(archive)
    print(ead_xml)
    doc = ET.XML(ead_xml)
    item1 = doc.find('./e:archdesc/e:dsc/e:c01/e:c02/e:c03/e:did/e:unitid', EAD_NS)
    assert item1 is not None, "could not find item1 'unitid' element"
    assert item1.text == "Dir1/Dir1-1/item1"

    item2 = doc.find('./e:archdesc/e:dsc/e:c01[2]/e:c02/e:c03/e:did/e:unitid', EAD_NS)
    assert item2 is not None, "could not find item3 'unitid' element"
    assert item2.text == "Dir2/Dir2-1/item3"

    item3 = doc.find('./e:archdesc/e:scopecontent/e:p[1]', EAD_NS)
    assert item3 is not None, "could not find item2 'scopecontent/p[1]' element"
    assert item3.text == "Paragraph 1"

    item4 = doc.find('./e:archdesc/e:scopecontent/e:p[2]', EAD_NS)
    assert item4 is not None, "could not find item2 'scopecontent/p[2]' element"
    assert item4.text == "Paragraph 2"
