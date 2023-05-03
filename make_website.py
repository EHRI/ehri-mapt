#!/usr/bin/env python3

import argparse
import json
import os
import sys
from datetime import date

from slugify import slugify

from ead import Ead
from iiif import IIIFManifest
from microarchive import MicroArchive, KEYS
from store import StoreSettings, IIIFSettings, Store
from website import Website, SiteInfo, make_html

PREFIX = "prefix"
FORMAT = "format"
DEFAULT_DATA = {
    KEYS.TITLE: "Default Title",
    KEYS.HOLDER: "Default Holder",
    KEYS.DATE_DESC: date.today(),
}


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='SiteMaker',
        description='Create a basic website',
        epilog='For testing purposes only')

    parser.add_argument('--prefix', dest="prefix", type=str,
                        help='the prefix for the input files')
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
    parser.add_argument('--wait', action="store_true", default=False,
                        help='wait for the site to become available')
    parser.add_argument('--get-info', action="store_true", default=False,
                        help='get info about the given key and exit')
    parser.add_argument('--ead', action="store_true", default=False,
                        help='print the EAD file and exit')
    parser.add_argument('--title', type=str, required=False, dest="title",
                        help='set the site title')
    parser.add_argument('--data-from-file', type=str, dest="data_file",
                        help='set data from supplied JSON file')
    args = parser.parse_args()

    store_settings = StoreSettings(
        bucket=args.bucket,
        region=args.region,
        access_key=args.access_key,
        secret_key=args.secret_key
    )
    iiif_settings = IIIFSettings(
        server_url=args.iiif_url,
    )

    # Default values
    raw_data = DEFAULT_DATA.copy()

    if args.data_file:
        with open(args.data_file, 'r') as f:
            from_file = json.load(f)
            for k, v in from_file.items():
                raw_data[k] = v

    store = Store(store_settings, iiif_settings)
    site_maker = Website(store_settings)
    if args.key:
        print("Loading data...", file=sys.stderr)
        existing_data = site_maker.get_site(args.key)
        meta = store.get_meta(existing_data.origin_id)
        if args.get_info:
            json.dump(meta, fp=sys.stdout, indent=2, default=str)
            sys.exit(1)
        for k, v in meta.items():
            if k == KEYS.DATE_DESC and v:
                raw_data[k] = date.fromisoformat(v)
            else:
                raw_data[k] = v
        if not args.prefix and PREFIX in meta:
            args.prefix = meta[PREFIX]
        if not args.iiif_ext and FORMAT in meta:
            args.iiif_ext = meta[FORMAT]
        elif not args.prefix and os.environ.get("S3_PREFIX"):
            args.prefix = os.environ.get("S3_PREFIX")

        print(f"Meta: {meta}", file=sys.stderr)

    # Now update the data from command args
    if args.title:
        raw_data[KEYS.TITLE] = args.title

    try:
        slug = slugify(raw_data[KEYS.TITLE])
    except KeyError:
        print("Argument --title [TITLE] required")
        sys.exit(1)

    # Load the files...
    files = store.load_files(args.prefix)

    print("Creating document model...", file=sys.stderr)
    desc = MicroArchive.from_data(raw_data, files)

    # If we just want to check the XML, print it and bail
    if args.ead:
        print(Ead().to_xml(desc))
        sys.exit()

    print("Creating site...", file=sys.stderr)
    site_data = site_maker.get_or_create_site(slug, args.key)
    print(json.dumps(site_data, indent=2, default=str), file=sys.stderr)

    # Now upload some data...
    url = f"https://{site_data.domain}"
    print(f"Site will be available at: {url}...", file=sys.stderr)

    print("Generating EAD...", file=sys.stderr)
    xml = Ead().to_xml(desc, os.path.join(url, f"{slug}.xml"))

    print("Generating IIIF manifest...", file=sys.stderr)
    manifest = IIIFManifest(
        baseurl=url,
        name=slug,
        service_url=iiif_settings.server_url,
        image_format=args.iiif_ext,
        prefix=args.prefix).to_json(desc)

    print("Generating site...", file=sys.stderr)
    html = make_html(slug, desc, site_data.id)

    print(f"Uploading data to origin path: {site_data.origin_id}...", file=sys.stderr)
    state = desc.to_data() | {PREFIX: args.prefix, FORMAT: args.iiif_ext}
    store.upload(slug, site_data.origin_id, html, xml, manifest, state)

    print(f"Key: {site_data.id}", file=sys.stderr)

    if args.wait:
        import polling2

        def check(data: SiteInfo) -> bool:
            if data.status != 'Deployed':
                print(f"Waiting... {data}" , file=sys.stderr)
                return False
            return True


        polling2.poll(
            lambda: site_maker.get_site(site_data.id),
            check_success=check,
            step=5,
            timeout=10*60
        )
    print("Done", file=sys.stderr)
