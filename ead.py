from datetime import date
from xml.etree import ElementTree as ET

import langcodes

from microarchive import MicroArchive, Item


class Ead():
    def __init__(self):
        pass

    def to_xml(self, data: MicroArchive) -> str:
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
        eadid.text = data.slug()
        filedesc = ET.SubElement(eadheader, 'filedesc')
        titlestmt = ET.SubElement(filedesc, 'titlestmt')
        titleproper = ET.SubElement(titlestmt, 'titleproper')
        titleproper.text = data.identity.title
        publicationstmt = ET.SubElement(filedesc, 'publicationstmt')
        if data.contact.lines():
            address = ET.SubElement(publicationstmt, 'address')
            for line in data.contact.lines():
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
        archdesc = ET.SubElement(root, 'archdesc', {'level': 'collection'})
        did = ET.SubElement(archdesc, 'did')
        unitid = ET.SubElement(did, 'unitid')
        unitid.text = data.slug()
        unittitle = ET.SubElement(did, 'unittitle')
        unittitle.text = data.identity.title
        if data.identity.extent:
            physdesc = ET.SubElement(did, 'physdesc', {'label': 'Extent'})
            extent = ET.SubElement(physdesc, 'extent')
            extent.text = data.identity.extent
        if data.description.lang:
            langmaterial = ET.SubElement(did, 'langmaterial')
            for lang in data.description.lang:
                langdata = langcodes.get(lang)
                language = ET.SubElement(langmaterial, 'language', {'langcode': langdata.to_alpha3()})
                language.text = langdata.display_name()
        if data.description.biog:
            scopecontent = ET.SubElement(archdesc, 'bioghist')
            scopecontentp = ET.SubElement(scopecontent, 'p')
            scopecontentp.text = data.description.biog
        if data.description.scope:
            scopecontent = ET.SubElement(archdesc, 'scopecontent')
            scopecontentp = ET.SubElement(scopecontent, 'p')
            scopecontentp.text = data.description.scope

        if data.items:
            dsc = ET.SubElement(archdesc, 'dsc')
            for item in data.hierarchical_items():
                def make_child(child: Item, parent: ET.Element, num: int):
                    c = ET.SubElement(parent, "c{:02d}".format(num), {'level': 'otherlevel'})
                    did = ET.SubElement(c, 'did')
                    unitid = ET.SubElement(did, 'unitid')
                    unitid.text = child.id
                    if child.identity.title:
                        unittitle = ET.SubElement(did, 'unittitle')
                        unittitle.text = child.identity.title
                    if child.content.scope:
                        scopecontent = ET.SubElement(c, "scopecontent")
                        scopecontent_p = ET.SubElement(scopecontent, "p")
                        scopecontent_p.text = child.content.scope
                    for cc in child.items:
                        make_child(cc, c, num + 1)

                make_child(item, dsc, 1)

        _pretty_print(root, pad='    ')
        return ET.tostring(root, encoding="unicode")


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
