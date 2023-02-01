"""Render a MicroArchive as a IIIF manifest"""
import os
from typing import Dict
from urllib.parse import quote_plus

from iiif_prezi3 import Manifest, Canvas, CanvasRef, Annotation, AnnotationPage, ResourceItem, Range

from microarchive import MicroArchive


class IIIFManifest():
    def __init__(self, baseurl: str, name: str, service_url: str, prefix: str):
        self.baseurl = baseurl
        self.name = name
        self.service_url = service_url
        self.prefix = prefix

    def to_json(self, data: MicroArchive) -> str:

        manifest_items = []
        for item in data.items:
            canvas_ref = self.service_url + quote_plus(self.prefix + item.id)
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

        for item in data.items:
            canvas_ref: str = self.service_url + quote_plus(self.prefix + item.id)
            *path_parts, _ = item.id.split('/')
            if len(path_parts) == 0:
                continue

            dir_path = os.path.join(path_parts[0], *path_parts[1:])

            cr = CanvasRef(id=canvas_ref, type="Canvas", label={"en": [item.identity.title or item.id]})
            r = ranges.get(dir_path)
            if r is None:
                r = Range(
                    id=f"{self.baseurl}/{self.name}/range/{dir_path}",
                    label={"en": [path_parts[-1]]},
                    items=[]
                )
                ranges[dir_path] = r
            r.items.append(cr)

        # go through the ranges, create any parents without direct item children,
        # and nest any sub-ranges
        nested_ranges = self.nest_ranges(ranges)
        manifest_structures.extend(nested_ranges.values())

        manifest = Manifest(
            id=f"{self.baseurl}/{self.name}.json",
            label={"en": [data.identity.title]},
            items=manifest_items,
            structures=manifest_structures)

        return manifest.json(indent=2)

    def nest_ranges(self, ranges: Dict[str, Range]) -> Dict[str, Range]:
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
                    id=f"{self.baseurl}/{self.name}/range/{p_path}",
                    label={"en": [parts[-1]]},
                    items=[]
                )
                # ranges inserted at the beginning of items
                p.items.insert(0, r)
                flat[p_path] = p
            return nest(flat, nested)
        return nest(ranges, {})
