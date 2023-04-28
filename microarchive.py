"""A MicroArchive entity"""
import os.path
import types
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from typing import List, Union, Callable, Dict, Tuple
from typing import Optional

import langcodes
from slugify import slugify


KEYS = types.SimpleNamespace()
KEYS.TITLE = "title"
KEYS.HOLDER = "holder"
KEYS.DATE_DESC = "datedesc"
KEYS.LANGS = "langs"
KEYS.EXTENT = "extent"
KEYS.STREET = "street"
KEYS.POSTCODE = "postcode"
KEYS.BIOG_HIST = "bioghist"
KEYS.SCOPE = "scope"
KEYS.ITEMS = "items"
KEYS.NOTES = "archnotes"

ALL_KEYS = list(KEYS.__dict__.values())
ALL_ITEM_KEYS = [KEYS.TITLE, KEYS.SCOPE]


def item_key(ident: str, key: str):
    """Get a key for an item-scoped value in the flat data dictionary"""
    return f"{KEYS.ITEMS}.{ident}.{key}"


@dataclass
class Identity:
    # Section 1: identification
    title: str = ""
    extent: str = ""

    def done(self) -> bool:
        return self.title.strip() != "" and \
               self.extent.strip() != ""


@dataclass
class Description:
    # Section 2: description
    biog: str = ""
    scope: str = ""
    lang: List[str] = field(default_factory=list)

    def languages(self):
        return [langcodes.get(code).display_name() for code in self.lang]

    def done(self) -> bool:
        return self.biog.strip() != "" or \
               self.scope.strip() != ""


@dataclass
class Contact:
    # Section 3: context
    holder: str = ""
    street: str = ""
    postcode: str = ""
    phone: str = ""
    fax: str = ""
    website: str = ""
    email: str = ""

    def lines(self) -> List[str]:
        return [s for s in [self.holder,
                            self.street,
                            self.postcode,
                            self.phone,
                            self.fax,
                            self.website,
                            self.email] if s.strip() != ""]

    def done(self) -> bool:
        return self.holder.strip() != ""


@dataclass
class Control:
    notes: str = ""
    datedesc: Optional[date] = None


@dataclass
class Item:
    id: str
    identity: Identity
    content: Description
    url: Union[str, None]
    thumb_url: Union[str, None]
    items: List['Item']

    def is_dir(self):
        return bool(self.items)

    def is_leaf_dir(self):
        if self.items and len([i for i in self.items if i.items]) == 0:
            return True
        return False

    @classmethod
    def make(cls, id: str, identity: Identity):
        return cls(id, identity, Description(), None, None, [])

    def __repr__(self):
        return f"<Item '{self.id}' '{self.identity.title}' (children: {len(self.items)})>"


@dataclass
class MicroArchive:
    identity: Identity
    description: Description
    contact: Contact
    control: Control
    items: List[Item]

    def hierarchical_items(self) -> List[Item]:
        """Return items in a hierarchical structure, creating
            and intermediate level items in between."""
        # NB: this algorithm is order-sensitive, which is not so great

        # Create intermediate items for all id path sections
        lookup = OrderedDict()
        for item in sorted(self.items, key=lambda it: it.id):
            lookup[item.id] = item
            path = os.path.dirname(item.id)
            if not path:
                continue
            parts = path.split('/')
            for i in reversed(range(0, len(parts))):
                p_parts = parts[0:i+1]
                p_path = '/'.join(p_parts)
                p = lookup.get(p_path) if p_path in lookup else Item.make(
                    id=p_path, identity=Identity(title=p_parts[-1]))
                lookup[p_path] = p

        # With the set of items sorted by deepest item first, go
        # through and add each item to it's parent's children until
        # we reach an item with no parents of its own.
        def nest(flat: OrderedDict[str, Item], nested: OrderedDict[str, Item]) -> OrderedDict[str, Item]:
            if not flat:
                return nested

            path, this = flat.popitem(False)
            *parts, last = path.split('/')
            if not parts:
                nested[path] = this
            else:
                p_path = '/'.join(parts)
                p = flat.get(p_path)
                p.items.insert(0, this)
            return nest(flat, nested)

        ordered = OrderedDict([(it.id, it) for it in reversed(sorted(lookup.values(), key=lambda it: it.id))])
        return sorted(nest(ordered, OrderedDict()).values(), key=lambda it: it.id)

    def leaf_dirs(self) -> List[Item]:
        """Return a list of directories containing only items (no child directories)"""
        def walk(item: Item, f: Callable):
            for child in item.items:
                walk(child, f)
            f(item)

        leaf_dirs = []

        def test(item: Item):
            if item.is_leaf_dir():
                leaf_dirs.append(item)

        for item in self.hierarchical_items():
            walk(item, test)
        return leaf_dirs

    def done(self):
        return self.identity.done() and \
               self.description.done() and \
               self.contact.done()

    def slug(self) -> str:
        return slugify(self.identity.title)

    def __repr__(self):
        return f"<MicroArchive '{self.identity.title}' {self.items}>"

    def print_tree(self):
        def print_items(item: Item, indent: int):
            space = ' ' * 4 * indent
            print(f"{space}{item.id}")
            for i in item.items:
                print_items(i, indent + 1)
        for item in self.hierarchical_items():
            print_items(item, 0)

    @classmethod
    def from_data(cls, data: Dict, items: List[Tuple[str, str, str]]) -> 'MicroArchive':
        """Make a micro-archive from a flat dictionary and a list of items"""
        return cls(
            identity=Identity(
                title=data.get(KEYS.TITLE, ""),
                extent=data.get(KEYS.EXTENT, "")),
            contact=Contact(
                holder=data.get(KEYS.HOLDER, ""),
                street=data.get(KEYS.STREET, ""),
                postcode=data.get(KEYS.POSTCODE, "")),
            control=Control(
                notes=data.get(KEYS.NOTES, ""),
                datedesc=data.get(KEYS.DATE_DESC, date.today())
            ),
            description=Description(biog=data.get(KEYS.BIOG_HIST, ""),
                                    scope=data.get(KEYS.SCOPE, ""),
                                    lang=data.get(KEYS.LANGS, [])),
            items=[Item(
                ident,
                Identity(data.get(item_key(ident, KEYS.TITLE), "")),
                Description(scope=data.get(item_key(ident, KEYS.SCOPE), "")), web_url, thumb_url, [])
                for ident, web_url, thumb_url in items]
        )

    def to_data(self) -> Dict:
        """Turn a micro-archive into a flat dictionary, containing only
        populated values"""
        item_data = {}
        for item in self.items:
            item_data[item_key(item.id, KEYS.TITLE)] = item.identity.title
            item_data[item_key(item.id, KEYS.SCOPE)] = item.content.scope

        data = item_data | {
            KEYS.TITLE: self.identity.title,
            KEYS.EXTENT: self.identity.extent,
            KEYS.HOLDER: self.contact.holder,
            KEYS.STREET: self.contact.street,
            KEYS.POSTCODE: self.contact.postcode,
            KEYS.BIOG_HIST: self.description.biog,
            KEYS.SCOPE: self.description.scope,
            KEYS.LANGS: self.description.lang,
            KEYS.DATE_DESC: self.control.datedesc.isoformat(),
            KEYS.NOTES: self.control.notes
        }
        # Remove empty values
        return {key: value for key, value in data.items() if value}


