import json
import os
import sys
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
from urllib.parse import quote_plus

import boto3
from botocore.exceptions import ClientError

THUMB_DIR = ".thumb"


@dataclass
class StoreSettings:
    bucket: str
    region: str
    prefix: str
    access_key: str
    secret_key: str


@dataclass
class IIIFSettings:
    server_url: str
    image_format: str


@dataclass
class Store:
    def __init__(self, settings: StoreSettings, iiif_settings: IIIFSettings):
        self.settings = settings
        self.iiif_settings = iiif_settings
        self.client = self.aws_client("s3")

    def aws_client(self, service: str):
        return boto3.client(service,
                        region_name=self.settings.region,
                        aws_access_key_id=self.settings.access_key,
                        aws_secret_access_key=self.settings.secret_key)

    def load_files(self) -> List[Tuple[str, str, str]]:
        r = self.client.list_objects_v2(
            Bucket=self.settings.bucket,
            Prefix=self.settings.prefix)
        file_meta = [meta for meta in r["Contents"] if not meta["Key"].endswith("/")]
        items = []
        for i, meta in enumerate(file_meta):
            key: str = meta["Key"]
            if THUMB_DIR in key:
                continue

            path_no_ext = os.path.splitext(key)[0]
            item_id = path_no_ext[len(self.settings.prefix):]
            url = self.iiif_settings.server_url + quote_plus(key) + "/full/max/0/default.jpg"
            thumb_url = self.iiif_settings.server_url + quote_plus(key) + "/full/!75,100/0/default.jpg"
            items.append((item_id, url, thumb_url))
        return items

    def get_meta(self, name: str, origin: str) -> Optional[Dict]:
        """Fetch the micro-archive manifest from existing storage"""
        import io
        buf = io.BytesIO()
        origin_no_slash = origin[1:] if origin.startswith('/') else origin
        try:
            self.client.download_fileobj(
                Bucket=self.settings.bucket,
                Key=os.path.join(origin_no_slash, f".meta.json"),
                Fileobj=buf
            )
            return json.loads(buf.getvalue().decode('utf-8'))
        except ClientError:
            print(f"Unable to find existing metadata for name {name} at origin {origin}", file=sys.stderr)
            return None

    def upload(self, name: str, origin: str, index: str, xml: str, iiif: str, meta: Dict):
        """Upload website data to storage"""
        bucket = self.settings.bucket
        origin_no_slash = origin[1:] if origin.startswith('/') else origin

        files = [
            ("index.html", "text/html", index),
            (f"{name}.xml", "text/xml", xml),
            (f"{name}.json", "application/json", iiif),
        ]

        # Upload a manifest privately
        self.client.put_object(
            Bucket=bucket,
            Key = os.path.join(origin_no_slash, f".meta.json"),
            ContentType="application/json",
            Body=json.dumps(meta, indent=2, default=str).encode('utf-8')
        )

        # Upload the rest with Public ACL
        for filename, content_type, data in files:
            self.client.put_object(
                ACL='public-read',
                Bucket=bucket,
                Key=os.path.join(origin_no_slash, filename),
                ContentType=content_type,
                Body=data.encode('utf-8')
            )
