#!/usr/bin/env python3
import argparse
import json
import os
from datetime import date
from typing import List, Tuple, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from slugify import slugify

from ead import Ead
from iiif import IIIFManifest
from microarchive import MicroArchive, Identity, Contact, Description, Item
from store import StoreSettings, IIIFSettings, Store
from website import Website

env = Environment(
    extensions=['jinja_markdown.MarkdownExtension'],
    loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__))),
    autoescape=select_autoescape()
)

TITLE = "Mike's Test Site"
HOLDER = "EHRI"
DATE_DESC = date.today()
LANGS = ["en", "da", "it", "ja"]
EXTENT = "231 digital images"
STREET = "The Strand"
POSTCODE = "ab12 3cd"
BIOG_HIST = "Testing"
SCOPE = "Diplomatic Reports"

ITEM_DATA = {
}


def make_archive(items: List[Tuple[str, str, str]], title: str) -> MicroArchive:
    def key(ident: str) -> str:
        return f"{ident}.title"

    def scope(ident: str) -> str:
        return f"{ident}.scope"

    desc = MicroArchive(
        identity=Identity(
            title=title,
            datedesc=DATE_DESC,
            extent=EXTENT),
        contact=Contact(
            holder=HOLDER,
            street=STREET,
            postcode=POSTCODE),
        description=Description(biog=BIOG_HIST,
                                scope=SCOPE,
                                lang=LANGS),
        items=[Item(
            ident,
            Identity(ITEM_DATA.get(key(ident), "")),
            Description(scope=ITEM_DATA.get(scope(ident), "")), url, thumb_url, [])
            for ident, url, thumb_url in items]
    )

    return desc


def encode_meta() -> Dict:
    return dict(
        title=TITLE,
        datedesc=DATE_DESC,
        extent=EXTENT,
        holder=HOLDER,
        street=STREET,
        postcode=POSTCODE,
        biog=BIOG_HIST,
        scope=SCOPE,
        lang=LANGS,
        items={}
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='SiteMaker',
        description='Create a basic website',
        epilog='For testing purposes only')

    parser.add_argument('--store-prefix', dest="prefix", type=str, nargs='?', default=os.environ.get("S3_PREFIX"),
                        help='the store prefix for the input files')
    parser.add_argument('--store-bucket', dest="bucket", type=str, nargs='?', default=os.environ.get("S3_BUCKET"),
                        help='the storage bucket')
    parser.add_argument('--store-region', dest="region", type=str, nargs='?', default=os.environ.get("S3_REGION"),
                        help='the storage region')
    parser.add_argument('--access-key', dest="access_key", type=str, nargs='?', default=os.environ.get("S3_ACCESS_KEY"),
                        help='the storage access key')
    parser.add_argument('--secret-key', dest="secret_key", type=str, nargs='?', default=os.environ.get("S3_SECRET_KEY"),
                        help='the storage secret key')
    parser.add_argument('--iiif-url', dest="iiif_url", type=str, nargs='?', default=os.environ.get("IIIF_SERVER_URL"),
                        help='the IIIF server URL')
    parser.add_argument('--iiif-ext', dest="iiif_ext", type=str, nargs='?', default=".jpg",
                        help='the IIIF image extension')
    parser.add_argument('--key', type=str, nargs='?', default=None,
                        help='the site key, for updating an existing site')
    parser.add_argument('--title', type=str, required=False, default=TITLE, dest="title",
                        help='the site title')
    args = parser.parse_args()

    slug = slugify(args.title)

    print("Loading data...")
    store_settings = StoreSettings(
        prefix=args.prefix,
        bucket=args.bucket,
        region=args.region,
        access_key=args.access_key,
        secret_key=args.secret_key
    )
    iiif_settings = IIIFSettings(
        server_url=args.iiif_url,
        image_format=args.iiif_ext
    )

    store = Store(store_settings, iiif_settings)
    files = store.load_files()

    print("Creating document model...")
    desc = make_archive(files, title=args.title)

    site_maker = Website(store_settings)
    if args.key:
        existing_data = site_maker.get_site(args.key)
        meta = store.get_meta(slug, existing_data.origin_id)
        print(f"Meta: {meta}")

    site_data = site_maker.get_or_create_site(slug, args.key)
    print(json.dumps(site_data, indent=2, default=str))

    # Now upload some data...
    url = f"https://{site_data.domain}"
    print(f"Waiting for site to be available at: {url}")

    print("Generating EAD...")
    xml = Ead().to_xml(desc)

    print("Generating IIIF manifest...")
    manifest = IIIFManifest(
        baseurl=url,
        name=slug,
        service_url=iiif_settings.server_url,
        image_format=iiif_settings.image_format,
        prefix=store_settings.prefix).to_json(desc)

    print("Generating site...")
    html = env.get_template("index.html.j2").render(name=slug, data=desc)

    print(f"Uploading data to origin path: {site_data.origin_id}...")
    store.upload(slug, site_data.origin_id, html, xml, manifest, encode_meta())

    print(f"Key: {site_data.id}")
