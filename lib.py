import datetime
from typing import Any

import streamlit as st

from microarchive import MicroArchive, Identity, Contact, Description, Item, ALL_KEYS, KEYS, item_key, ALL_ITEM_KEYS
from store import StoreSettings, Store, IIIFSettings
from website import Website

EXPIRATION = 3600
SITE_ID = "siteid"

S3_SETTINGS = StoreSettings(
    bucket=st.secrets.s3_credentials.bucket,
    prefix=st.secrets.s3_credentials.prefix,
    region=st.secrets.s3_credentials.region,
    access_key=st.secrets.s3_credentials.access_key,
    secret_key=st.secrets.s3_credentials.secret_key
)

IIIF_SETTINGS = IIIFSettings(
    server_url=st.secrets.iiif.server_url,
    image_format=st.secrets.iiif.image_format
)

STORE = Store(S3_SETTINGS, IIIF_SETTINGS)
WEB = Website(S3_SETTINGS)


def load_stored_data(site_id: str):
    site_info = WEB.get_site(site_id)
    meta = STORE.get_meta("?", site_info.origin_id)
    for key in ALL_KEYS:
        if key in meta and meta[key]:
            if key == KEYS.DATE_DESC:
                st.session_state[key] = datetime.date.fromisoformat(meta[key])
            else:
                st.session_state[key] = meta[key]
    for ident, _, _ in load_files():
        for key in ALL_ITEM_KEYS:
            ikey = item_key(ident, key)
            if ikey in meta and meta[ikey]:
                st.session_state[ikey] = meta[ikey]


def value_or_default(key, default: Any = ""):
    return st.session_state[key] if key in st.session_state else default


@st.experimental_memo(ttl=EXPIRATION)
def load_files():
    return STORE.load_files()


def init_page():
    if "items" not in st.session_state:
        st.session_state.items = load_files()

    if KEYS.TITLE not in st.session_state:
        st.session_state[KEYS.TITLE] = "Default Collection Name"
    if KEYS.SCOPE not in st.session_state:
        st.session_state[KEYS.SCOPE] = "[Default collection description.]"

    st.write("# Micro Archive Publication Tool")


def make_archive():
    return MicroArchive(
        identity=Identity(
            title=value_or_default(KEYS.TITLE),
            datedesc=value_or_default(KEYS.DATE_DESC, ""),
            extent=value_or_default(KEYS.EXTENT)),
        contact=Contact(
            holder=value_or_default(KEYS.HOLDER),
            street=value_or_default(KEYS.STREET),
            postcode=value_or_default(KEYS.POSTCODE)),
        description=Description(biog=value_or_default(KEYS.BIOG_HIST),
                                scope=value_or_default(KEYS.SCOPE),
                                lang=value_or_default(KEYS.LANGS, [])),
        items=[Item(
            ident,
            Identity(value_or_default(item_key(ident, KEYS.TITLE))),
            Description(scope=value_or_default(item_key(ident, KEYS.SCOPE))), url, thumb_url, [])
            for ident, url, thumb_url in value_or_default(KEYS.ITEMS, [])]
    )
