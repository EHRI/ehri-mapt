import json

from iiif import IIIFManifest
from test_utils import *


def test_to_json(archive):
    manifest = IIIFManifest(
        baseurl="http://example.com/",
        name="test",
        service_url="http://example.com/iiif/3/",
        image_format=".jpg",
        prefix="foobar/").to_json(archive)
    print(manifest)
    data = json.loads(manifest)
    assert value_of(data, "label", "en", 0) == "Test"
    assert len(data["items"]) == 4, "has the right number of canvases"
    assert value_of(data, "structures", 0, "label", "en", 0) == "Dir1"
    assert value_of(data, "structures", 0, "items", 0, "label", "en", 0) == "Dir1-1"
    assert len(value_of(data, "structures", 0, "items")) == 2
