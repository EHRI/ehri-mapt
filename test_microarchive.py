from test_utils import *

@pytest.fixture
def flat_archive():
    return MicroArchive(
        identity=Identity(title="test"),
        description=Description(),
        contact=Contact(),
        items=[
            Item.make(id="item1", identity=Identity(title="Item1")),
            Item.make(id="item2", identity=Identity(title="Item2")),
        ]
    )


def test_hierarchical_items(archive: MicroArchive):
    hierarchy = archive.hierarchical_items()
    assert len(hierarchy) == 2, "unexpected number of top-level items"
    assert hierarchy[0].id == "Dir1", "first top-level item has unexpected id"
    assert hierarchy[0].items[0].id == "Dir1/Dir1-1", "first intermediate item has unexpected id"
    assert hierarchy[0].items[0].items[0].id == "Dir1/Dir1-1/item1"
    assert hierarchy[0].items[1].id == "Dir1/item2"
    assert hierarchy[1].items[0].items[0].id == "Dir2/Dir2-1/item3"
    assert hierarchy[1].items[1].id == "Dir2/item4"


def test_hierarchical_items_no_hierarchy(flat_archive: MicroArchive):
    no_hierarchy = flat_archive.hierarchical_items()
    assert len(no_hierarchy) == 2, "flat archive has unexpected number of top-level items"


def test_leaf_dirs(archive: MicroArchive):
    leaf_dirs = archive.leaf_dirs()
    assert ['Dir1/Dir1-1', 'Dir2/Dir2-1'] == [
        it.id for it in leaf_dirs], "unexpected leaf dirs"
