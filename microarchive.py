"""A MicroArchive entity"""
import os.path
from collections import OrderedDict
from datetime import date
from typing import NamedTuple, List, Union, Callable
from typing import Optional

import langcodes
from slugify import slugify


class Identity(NamedTuple):
    # Section 1: identification
    title: str = ""
    datedesc: Optional[date] = None
    extent: str = ""

    def done(self) -> bool:
        return self.title.strip() != "" and \
               self.datedesc is not None and \
               self.extent.strip() != ""


class Description(NamedTuple):
    # Section 2: description
    biog: str = ""
    scope: str = ""
    lang: List[str] = []

    def languages(self):
        return [langcodes.get(code).display_name() for code in self.lang]

    def done(self) -> bool:
        return self.biog.strip() != "" or \
               self.scope.strip() != ""


class Contact(NamedTuple):
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


class Item(NamedTuple):
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


class MicroArchive(NamedTuple):
    identity: Identity
    description: Description
    contact: Contact
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
        return sorted(nest(ordered, OrderedDict()).values())

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



