
from datetime import date
from typing import Optional, List
import xml.etree.ElementTree as ET

import langcodes
from slugify import slugify
from typing import NamedTuple, List
from urllib.parse import quote_plus
from lib import IIIF_SERVER


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
    url: str
    thumb_url: str

    def __repr__(self):
        return f"<EadItem '{self.id}' '{self.identity.title}'>"


class SimpleEad(NamedTuple):
    identity: Identity = Identity()
    description: Description = Description()
    contact: Contact = Contact()
    items: List[EadItem] = []


    def done(self):
        return self.identity.done() and \
               self.description.done() and \
               self.contact.done()

    def slug(self) -> str:
        return slugify(self.identity.title)

    def to_json(self):
        from iiif_prezi3 import Manifest, Canvas, Annotation, AnnotationPage, ResourceItem

        manifest_items = []
        for item in self.items:
            baseurl = f"https://iiif.ehri-project-test.eu/iiif/3/"
            imgref = baseurl + quote_plus(item.id)
            canvas = Canvas(
                id=imgref,
                label={"en": [item.identity.title or item.id]},
                thumbnail=[dict(id=item.thumb_url, type="Image", format="image/jpeg")],
                height=1000,
                width=750,
                items=[
                  AnnotationPage(
                      id=f"{imgref}/page",
                      items=[
                          Annotation(
                              id=f"{imgref}/ann1",
                              motivation="painting",
                              target=imgref,
                              body=ResourceItem(
                                id=f"{imgref}.tif/full/pct:50/0/default.jpg",
                                type="Image",
                                format="image/jpeg"
                              )
                          )
                      ]
                  )
                ]
            )
            manifest_items.append(canvas)
        manifest = Manifest(
            id=IIIF_SERVER + "manifest.json",
            label={"en": [self.identity.title]},
            items=manifest_items)

        return manifest.json(indent=2)

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

        if self.items:
            dsc = ET.SubElement(archdesc, 'dsc')
            for item in self.items:
                c1 = ET.SubElement(dsc, 'c1', {'level': 'item'})
                did = ET.SubElement(c1, 'did')
                unitid = ET.SubElement(did, 'unitid')
                unitid.text = item.id
                if item.identity.title:
                    unittitle = ET.SubElement(did, 'unittitle')
                    unittitle.text = item.identity.title
                if item.content.scope:
                    scopecontent = ET.SubElement(c1, "scopecontent")
                    scopecontentp = ET.SubElement(scopecontent, "p")
                    scopecontentp.text = item.content.scope
        _pretty_print(root, pad='    ')
        return ET.tostring(root, encoding="unicode")

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
