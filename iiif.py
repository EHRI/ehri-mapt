"""Render a MicroArchive as a IIIF manifest"""
import os
from collections import OrderedDict
from typing import Dict
from urllib.parse import quote_plus

from iiif_prezi3 import Manifest, Canvas, CanvasRef, Annotation, AnnotationPage, ResourceItem, Range

from microarchive import MicroArchive


class IIIFManifest():
    def __init__(self,
                 baseurl: str,
                 name: str,
                 service_url: str,
                 prefix: str,
                 width: int = 768,
                 height: int = 1024):
        self.baseurl = baseurl
        self.name = name
        self.service_url = service_url
        self.prefix = prefix
        self.width = width
        self.height = height

    def to_json(self, data: MicroArchive) -> str:

        manifest_items = []
        for item in data.items:
            canvas_ref = self.service_url + quote_plus(self.prefix + item.id)
            canvas = Canvas(
                id=canvas_ref,
                label={"en": [item.identity.title or item.id]},
                thumbnail=[dict(id=f"{canvas_ref}.tif/full/!100,150/0/default.jpg", type="Image", format="image/jpeg")],
                height=self.width,
                width=self.height,
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
        ranges = OrderedDict()

        for item in data.items:
            *path_parts, _ = item.id.split('/')
            if len(path_parts) == 0:
                continue

            dir_path = os.path.join(path_parts[0], *path_parts[1:])

            canvas_ref: str = self.service_url + quote_plus(self.prefix + item.id)
            cr = CanvasRef(id=canvas_ref, type="Canvas", label={"en": [item.identity.title or item.id]})
            r = ranges.get(dir_path) if dir_path in ranges else Range(
                id=f"{self.baseurl}/{self.name}/range/{dir_path}",
                label={"en": [path_parts[-1]]},
                items=[]
            )
            r.items.append(cr)
            ranges[dir_path] = r

        # go through the ranges, create any parents without direct item children,
        # and nest any sub-ranges
        print(f"Nesting ranges: {ranges.keys()}")
        nested_ranges = self.nest_ranges(ranges)
        manifest_structures.extend(nested_ranges.values())

        manifest = Manifest(
            id=f"{self.baseurl}/{self.name}.json",
            label={"en": [data.identity.title]},
            attribution="EHRI",
            right="https://creativecommons.org/licenses/by/4.0/",
            requiredStatement={
                "label": {
                    "en": ["Attribution"],
                },
                "value": {
                    "en": ["EHRI"]
                }
            },
            items=manifest_items,
            structures=manifest_structures)

        return manifest.json(indent=2)

    def nest_ranges(self, ranges: OrderedDict[str, Range]) -> OrderedDict[str, Range]:
        def nest(flat: OrderedDict[str, Range], nested: OrderedDict[str, Range]) -> OrderedDict[str, Range]:
            # break condition:
            if not flat:
                return nested

            path, r = flat.popitem(False)
            *parts, last = path.split('/')
            print(f"Nesting item {path} with {len(r.items)} children")
            if not parts:
                print("No parts, done")
                nested[path] = r
            else:
                # create a range for the last component and
                # insert it into those to be processed
                p_path = '/'.join(parts)
                print(f"Looking for parent path {p_path}")
                p = flat.get(p_path) if p_path in flat else Range(
                    id=f"{self.baseurl}/{self.name}/range/{p_path}",
                    label={"en": [parts[-1]]},
                    items=[]
                )
                # ranges inserted at the beginning of items
                #p.items.insert(0, r)
                p.items.append(r)
                flat[p_path] = p
            return nest(flat, nested)
        return nest(ranges, OrderedDict())
