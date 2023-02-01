"""A MicroArchive entity"""

from datetime import date
from typing import NamedTuple, List, Union
from typing import Optional

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

    def done(self):
        return self.identity.done() and \
               self.description.done() and \
               self.contact.done()

    def slug(self) -> str:
        return slugify(self.identity.title)

    def __repr__(self):
        return f"<MicroArchive '{self.identity.title}' {self.items}>"

