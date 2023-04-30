"""Render a MicroArchive as a IIIF manifest"""
from dataclasses import dataclass
from typing import Union
from urllib.parse import quote_plus

from iiif_prezi3 import Manifest, Canvas, CanvasRef, Annotation, AnnotationPage, ResourceItem, Range

from microarchive import MicroArchive, Item


@dataclass
class IIIFManifest:
    baseurl: str
    name: str
    service_url: str
    image_format: str
    prefix: str
    width: int = 768
    height: int = 1024

    def to_json(self, data: MicroArchive) -> str:

        manifest_items = []
        for item in data.items:
            canvas_ref = self.service_url + quote_plus(self.prefix + item.id)
            canvas = Canvas(
                id=canvas_ref,
                label={"en": [item.identity.title or item.id]},
                thumbnail=[dict(id=f"{canvas_ref}{self.image_format}/full/!100,150/0/default.jpg", type="Image", format="image/jpeg")],
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
                                    id=f"{canvas_ref}{self.image_format}/full/max/0/default.jpg",
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
        for item in data.hierarchical_items():
            def make_range(item: Item) -> Union[Range, CanvasRef]:
                if item.items:
                    return Range(id=f"{self.baseurl}/{self.name}/range/{item.id}",
                                  label={"en": [item.identity.title]},
                                  items=[make_range(i) for i in item.items])
                else:
                    return CanvasRef(id=self.service_url + quote_plus(self.prefix + item.id),
                                     type="Canvas", label={"en": [item.identity.title or item.id]})
            if item.items:
                manifest_structures.append(make_range(item))

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
                    "en": [data.contact.holder or "EHRI"]
                }
            },
            items=manifest_items,
            structures=manifest_structures)

        return manifest.json(indent=2)
