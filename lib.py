import datetime
from typing import Any, Optional

import streamlit as st

from microarchive import MicroArchive, Identity, Contact, Description, Item, ALL_KEYS, KEYS, item_key, ALL_ITEM_KEYS, \
    Control
from store import StoreSettings, Store, IIIFSettings
from website import Website, SiteInfo

EXPIRATION = 3600
SITE_ID = "siteid"
PREFIX = "prefix"
FORMAT = "format"
MODE = "mode"
MODE_CREATE = "create"
MODE_EDIT = "edit"

S3_SETTINGS = StoreSettings(
    bucket=st.secrets.s3_credentials.bucket,
    region=st.secrets.s3_credentials.region,
    access_key=st.secrets.s3_credentials.access_key,
    secret_key=st.secrets.s3_credentials.secret_key
)

IIIF_SETTINGS = IIIFSettings(
    server_url=st.secrets.iiif.server_url,
)


@st.cache_resource
def storage():
    return Store(S3_SETTINGS, IIIF_SETTINGS)


@st.cache_resource
def web_builder():
    return Website(S3_SETTINGS)


def load_stored_data(site_id: str) -> SiteInfo:
    site_info = web_builder().get_site(site_id)
    meta = storage().get_meta(site_info.origin_id)
    if meta:
        for key in ALL_KEYS:
            if key in meta and meta[key]:
                if key == KEYS.DATE_DESC:
                    st.session_state[key] = datetime.date.fromisoformat(meta[key])
                else:
                    st.session_state[key] = meta[key]
        if PREFIX in meta:
            st.session_state[PREFIX] = meta[PREFIX]
            st.session_state[FORMAT] = st.secrets.datasets[meta[PREFIX]].format
        for ident, _, _ in load_files(st.session_state.get(PREFIX)):
            for key in ALL_ITEM_KEYS:
                ikey = item_key(ident, key)
                if ikey in meta and meta[ikey]:
                    st.session_state[ikey] = meta[ikey]
    return site_info


def value_or_default(key, default: Any = ""):
    return st.session_state[key] if key in st.session_state else default


@st.cache_data(ttl=EXPIRATION)
def load_files(prefix: Optional[str]):
    return storage().load_files(prefix)


def init_page(title: str = "Describe a Collection"):
    st.set_page_config(page_title=title)
    if KEYS.TITLE not in st.session_state:
        st.session_state[KEYS.TITLE] = "Default Collection Name"
    if KEYS.SCOPE not in st.session_state:
        st.session_state[KEYS.SCOPE] = ""
    if MODE not in st.session_state:
        st.session_state[MODE] = MODE_CREATE

    with st.sidebar:
        st.warning("""This tool is a proof of concept for describing and publishing
        simple websites based on scanned image datasets. The datasets shown here are
        for demonstration purposes only and need to be set up outside of this tool.""")

    st.write("# Micro Archive Publication Tool")


def make_archive():
    return MicroArchive(
        identity=Identity(
            title=value_or_default(KEYS.TITLE),
            extent=value_or_default(KEYS.EXTENT)),
        contact=Contact(
            holder=value_or_default(KEYS.HOLDER),
            street=value_or_default(KEYS.STREET),
            postcode=value_or_default(KEYS.POSTCODE)),
        description=Description(biog=value_or_default(KEYS.BIOG_HIST),
                                scope=value_or_default(KEYS.SCOPE),
                                lang=value_or_default(KEYS.LANGS, [])),
        control=Control(
            notes=value_or_default(KEYS.NOTES, ""),
            datedesc=value_or_default(KEYS.DATE_DESC, None)
        ),
        items=[Item(
            ident,
            Identity(value_or_default(item_key(ident, KEYS.TITLE))),
            Description(scope=value_or_default(item_key(ident, KEYS.SCOPE))), url, thumb_url, [])
            for ident, url, thumb_url in load_files(st.session_state.get(PREFIX))]
    )
