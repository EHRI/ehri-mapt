import os
from dataclasses import dataclass
from typing import Optional

import boto3

from microarchive import MicroArchive
from store import StoreSettings
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    extensions=['jinja_markdown.MarkdownExtension'],
    loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__))),
    autoescape=select_autoescape()
)


def get_random_string(length: int) -> str:
    import random, string
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class DistributionNotFound(Exception):
    def __init__(self, site_id: str):
        super(DistributionNotFound, self).__init__(f"Distribution not found with id {site_id}")
        self.site_id = site_id


@dataclass
class SiteInfo:
    id: str
    domain: str
    origin_id: str
    status: str


def make_html(slug: str, desc: MicroArchive) -> str:
    return  env.get_template("index.html.j2").render(name=slug, data=desc)


class Website:
    def __init__(self, settings: StoreSettings):
        self.settings = settings
        self.client = self.client("cloudfront")

    def client(self, service: str):
        return boto3.client(service,
                            region_name=self.settings.region,
                            aws_access_key_id=self.settings.access_key,
                            aws_secret_access_key=self.settings.secret_key,)

    def get_or_create_site(self, name: str, site_id: Optional[str] = None) -> SiteInfo:
        """If site_id is given, fetch the distribution info.
        Otherwise, create the distribution."""
        if site_id:
            return self.get_site(site_id)
        else:
            return self.create_site(name)

    def get_site(self, site_id: str) -> SiteInfo:
        """Get the distribution info for the given `site_id`"""
        r = self.client.get_distribution(Id=site_id)
        return SiteInfo(
            id=r["Distribution"]["Id"],
            status=r["Distribution"]["Status"],
            domain=r["Distribution"]["DomainName"],
            origin_id=r["Distribution"]["DistributionConfig"]["Origins"]["Items"][0]["OriginPath"]
        )

    def create_site(self, name: str) -> SiteInfo:
        """Create a new site with the given name as the origin id"""
        bucket = self.settings.bucket
        region = self.settings.region
        file_prefix:str = self.settings.prefix
        file_prefix_no_slash = file_prefix[:-1] if file_prefix.endswith("/") else file_prefix

        # this is simply a reference used within the distribution and could be random,
        # but here we associate it with the given name.
        origin_id = bucket + "_" + name

        # the suffix for the uploaded material, on top of the
        # suffix for the input files
        site_suffix = get_random_string(5)
        suffix = f"_webdata_{site_suffix}/"
        key_prefix = file_prefix_no_slash + suffix

        # s3.create_origin_access_policy()
        # ref is simply a random string to ensure request cannot be replayed
        ref = get_random_string(10)

        # bucket domain
        bucket_domain = f"{bucket}.s3.{region}.amazonaws.com"

        r = self.client.create_distribution(
            DistributionConfig={
                'CallerReference': ref,
                'Enabled': True,
                'DefaultRootObject': 'index.html',
                'HttpVersion': 'http2and3',
                'Comment': 'Created by the EHRI-3 WP11 Demo tool',
                'Origins': {
                    'Quantity': 1,
                    'Items': [{
                        'Id': origin_id,
                        'OriginPath': "/" + key_prefix[:-1],  # slash must be at the start
                        'DomainName': bucket_domain,
                        # 'OriginAccessControlId': oac_id,
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }]
                },
                'DefaultCacheBehavior': {
                    # 'CachePolicyId': '658327ea-f89d-4fab-a63d-7e88639e58f6',  # CachingOptimized (from docs)
                    'CachePolicyId': '4135ea2d-6df8-44a3-9df3-4b5a84be39ad',  # CachingDisabled (from docs)
                    'ResponseHeadersPolicyId': '5cc3b908-e619-4b99-88e5-2cf7f45965bd', # Allow CORS
                    'TargetOriginId': origin_id,
                    'ViewerProtocolPolicy': 'allow-all',
                    'AllowedMethods': {
                        'Quantity': 2,
                        'Items' : ['GET', 'HEAD'],
                        'CachedMethods': {
                            'Quantity': 2,
                            'Items': ['GET', 'HEAD']
                        }
                    }
                }
            }
        )

        return SiteInfo(
            id=r["Distribution"]["Id"],
            status=r["Distribution"]["Status"],
            domain=r["Distribution"]["DomainName"],
            origin_id=r["Distribution"]["DistributionConfig"]["Origins"]["Items"][0]["OriginPath"]
        )



