"""Ead document proxy"""

import os
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import date
from typing import NamedTuple, List, Dict, Union
from typing import Optional
from urllib.parse import quote_plus

import langcodes
from iiif_prezi3 import Range
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


class EadItem(NamedTuple):
    id: str
    identity: Identity
    content: Description
    url: Union[str, None]
    thumb_url: Union[str, None]
    items: List['EadItem']

    @classmethod
    def make(cls, id: str, identity: Identity):
        return cls(id, identity, Description(), None, None, [])


    def __repr__(self):
        return f"<EadItem '{self.id}' '{self.identity.title}' (children: {len(self.items)})>"


class SimpleEad(NamedTuple):
    identity: Identity
    description: Description
    contact: Contact
    items: List[EadItem]

    def done(self):
        return self.identity.done() and \
               self.description.done() and \
               self.contact.done()

    def slug(self) -> str:
        return slugify(self.identity.title)

    def nest_parents(self, parents: OrderedDict[str, EadItem]) -> OrderedDict[str, EadItem]:
        def nest(flat: OrderedDict[str, EadItem], nested: OrderedDict[str, EadItem]) -> OrderedDict[str, EadItem]:
            # break
            if not flat:
                return nested

            path, item = flat.popitem(False)
            *parts, last = path.split('/')
            if not parts:
                nested[path] = item
            else:
                p_path = '/'.join(parts)
                p = flat.get(p_path) if p_path in flat else EadItem.make(
                    id=p_path,
                    identity=Identity(title=parts[-1])
                )
                p.items.insert(0, item)
                # p.items.append(item)
                flat[p_path] = p
            return nest(flat, nested)
        return nest(parents, OrderedDict())


    def to_xml(self):
        now = date.today()
        root = ET.Element("ead", {
            'xmlns': 'urn:isbn:1-931666-22-9',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'urn:isbn:1-931666-22-9 http://www.loc.gov/ead/ead.xsd'
        })
        eadheader = ET.SubElement(root, 'eadheader', {
            'countryencoding': 'iso3166-1',
            'dateencoding': 'iso8601',
            'scriptencoding': 'iso15924', 'repositoryencoding': 'iso15511', 'relatedencoding': 'DC'
        })
        eadid = ET.SubElement(eadheader, 'eadid')
        eadid.text = self.slug()
        filedesc = ET.SubElement(eadheader, 'filedesc')
        titleproper = ET.SubElement(filedesc, 'titleproper')
        titleproper.text = self.identity.title
        publicationstmt = ET.SubElement(eadheader, 'publicationstmt')
        if self.contact.lines():
            address = ET.SubElement(publicationstmt, 'address')
            for line in self.contact.lines():
                addressline = ET.SubElement(address, 'addressline')
                addressline.text = line.strip()
        profiledesc = ET.SubElement(eadheader, 'profiledesc')
        creation = ET.SubElement(profiledesc, 'creation')
        creation.text = "This file was exported from the EHRI MicroArchives cataloguing demo"
        date_ = ET.SubElement(creation, 'date', {'normal': now.strftime('%Y%m%d')})
        date_.text = now.isoformat()
        langusage = ET.SubElement(profiledesc, 'langusage')
        language = ET.SubElement(langusage, 'language', {'langcode': 'eng'})
        language.text = "English"
        archdesc = ET.SubElement(root, 'archdesc')
        did = ET.SubElement(archdesc, 'did')
        unitid = ET.SubElement(did, 'unitid')
        unitid.text = self.slug()
        unittitle = ET.SubElement(did, 'unittitle')
        unittitle.text = self.identity.title
        if self.identity.extent:
            physdesc = ET.SubElement(did, 'physdesc', {'label': 'Extent'})
            extent = ET.SubElement(physdesc, 'extent')
            extent.text = self.identity.extent
        if self.description.lang:
            langmaterial = ET.SubElement(did, 'langmaterial')
            for lang in self.description.lang:
                langdata = langcodes.get(lang)
                language = ET.SubElement(langmaterial, 'language', {'langcode': langdata.to_alpha3()})
                language.text = langdata.display_name()
        if self.description.biog:
            scopecontent = ET.SubElement(archdesc, 'bioghist')
            scopecontentp = ET.SubElement(scopecontent, 'p')
            scopecontentp.text = self.description.biog
        if self.description.scope:
            scopecontent = ET.SubElement(archdesc, 'scopecontent')
            scopecontentp = ET.SubElement(scopecontent, 'p')
            scopecontentp.text = self.description.scope

        parents = OrderedDict()
        for item in self.items:
            *path_parts, _ = item.id.split('/')
            if len(path_parts) == 0:
                continue

            dir_path = os.path.join(path_parts[0], *path_parts[1:])
            p = parents.get(dir_path)
            if p is None:
                p = EadItem(
                    id=dir_path,
                    identity=Identity(title=path_parts[-1]),
                    content=Description(),
                    url=None,
                    thumb_url=None,
                    items=[]
                )
            p.items.append(item)
            parents[dir_path] = p

        print(f"Parents: {parents}")

        if self.items:
            dsc = ET.SubElement(archdesc, 'dsc')
            for item in self.nest_parents(parents).values():

                def make_child(child: EadItem, parent: ET.Element, num: int):
                    c = ET.SubElement(parent, f"c{num}", {'level': 'otherlevel'})
                    did = ET.SubElement(c, 'did')
                    unitid = ET.SubElement(did, 'unitid')
                    unitid.text = child.id
                    if child.identity.title:
                        unittitle = ET.SubElement(did, 'unittitle')
                        unittitle.text = child.identity.title
                    if child.content.scope:
                        scopecontent = ET.SubElement(c, "scopecontent")
                        scopecontentp = ET.SubElement(scopecontent, "p")
                        scopecontentp.text = child.content.scope
                    for cc in child.items:
                        make_child(cc, c, num + 1)

                make_child(item, dsc, 1)

        _pretty_print(root, pad='    ')
        return ET.tostring(root, encoding="unicode")

    def to_json(self, baseurl: str, prefix: str):
        from iiif_prezi3 import Manifest, Canvas, CanvasRef, Annotation, AnnotationPage, ResourceItem, Range

        manifest_items = []
        for item in self.items:
            canvas_ref = baseurl + quote_plus(prefix + item.id)
            canvas = Canvas(
                id=canvas_ref,
                label={"en": [item.identity.title or item.id]},
                thumbnail=[dict(id=f"{canvas_ref}.tif/full/!100,150/0/default.jpg", type="Image", format="image/jpeg")],
                height=1000,
                width=750,
                items=[
                    AnnotationPage(
                        id=f"{canvas_ref}/page",
                        items=[
                            Annotation(
                                id=f"{canvas_ref}/ann1",
                                motivation="painting",
                                target=canvas_ref,
                                body=ResourceItem(
                                    id=f"{canvas_ref}.tif/full/pct:50/0/default.jpg",
                                    type="Image",
                                    format="image/jpeg"
                                )
                            )
                        ]
                    )
                ]
            )
            manifest_items.append(canvas)

        manifest_structures = []
        ranges = {}

        for item in self.items:
            canvas_ref: str = baseurl + quote_plus(prefix + item.id)
            *path_parts, _ = item.id.split('/')
            if len(path_parts) == 0:
                continue

            dir_path = os.path.join(path_parts[0], *path_parts[1:])

            cr = CanvasRef(id=canvas_ref, type="Canvas", label={"en": [item.identity.title or item.id]})
            r = ranges.get(dir_path)
            if r is None:
                r = Range(
                    id=f"{baseurl}range/{dir_path}",
                    label={"en": [path_parts[-1]]},
                    items=[]
                )
                ranges[dir_path] = r
            r.items.append(cr)

        # go through the ranges, create any parents without direct item children,
        # and nest any sub-ranges
        nested_ranges = nest_ranges(baseurl, ranges)
        manifest_structures.extend(nested_ranges.values())

        manifest = Manifest(
            id=baseurl + "manifest.json",
            label={"en": [self.identity.title]},
            items=manifest_items,
            structures=manifest_structures)

        return manifest.json(indent=2)


    def __repr__(self):
        return f"<SimpleEAD '{self.identity.title}' {self.items}>"


def _pretty_print(current, parent=None, index=-1, depth=0, pad='\t'):
    for i, node in enumerate(current):
        _pretty_print(node, current, i, depth + 1, pad)
    if parent is not None:
        if index == 0:
            parent.text = '\n' + (pad * depth)
        else:
            parent[index - 1].tail = '\n' + (pad * depth)
        if index == len(parent) - 1:
            current.tail = '\n' + (pad * (depth - 1))


def nest_ranges(baseurl: str, ranges: Dict[str, Range]) -> Dict[str, Range]:
    def nest(flat: Dict[str, Range], nested: Dict[str, Range]) -> Dict[str, Range]:
        # break condition:
        if not flat:
            return nested

        path, r = flat.popitem()
        *parts, last = path.split('/')
        if not parts:
            nested[path] = r
        else:
            # create a range for the last component and
            # insert it into those to be processed
            p_path = '/'.join(parts)
            p = flat.get(p_path) if p_path in flat else Range(
                id=f"{baseurl}range/{p_path}",
                label={"en": [parts[-1]]},
                items=[]
            )
            # ranges inserted at the beginning of items
            p.items.insert(0, r)
            flat[p_path] = p
        return nest(flat, nested)

    return nest(ranges, {})
