from streamlit_extras.switch_page_button import switch_page

import streamlit as st

import os

from lib import make_archive, init_page, SITE_ID

from store import IIIFSettings, StoreSettings, Store
from ead import Ead

from iiif import IIIFManifest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from website import Website

env = Environment(
    extensions=['jinja_markdown.MarkdownExtension'],
    loader=FileSystemLoader(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
    autoescape=select_autoescape()
)


st.set_page_config(page_title="Export Information")

init_page()

st.write("## Export Information")

# Build the representation...
desc = make_archive()

st.info("""Publishing this data will create a website containing the metadata for this
           collection and a browser for any images.\n\nTypically the site will take **1-5 minutes** to become live.
            """)

if st.button("Publish Website"):
    update_id = st.session_state.get(SITE_ID)
    if update_id == "":
        update_id = None

    name = desc.slug()
    settings = StoreSettings(st.secrets.s3_credentials.bucket,
                             st.secrets.s3_credentials.region,
                             st.secrets.s3_credentials.prefix,
                             st.secrets.s3_credentials.access_key,
                             st.secrets.s3_credentials.secret_key)
    iiif_settings = IIIFSettings(st.secrets.iiif.server_url, st.secrets.iiif.image_format)

    maker = Website(settings)
    site_data = maker.get_or_create_site(name, update_id)
    st.session_state[SITE_ID] = site_data.id
    domain = site_data.domain

    with st.expander("View Distribution Info"):
        st.json(site_data.__dict__)

    st.write(f"""Save these values for editing this site:""")
    st.write(f"   Site ID:     `{site_data.id}`")

    url = f"https://{domain}"
    st.markdown(f"Waiting for site to be available at: [{url}]({url})")

    st.write("Generating EAD...")
    xml = Ead().to_xml(desc)

    st.write("Generating IIIF manifest...")
    manifest = IIIFManifest(
        baseurl=url,
        name=name,
        service_url=iiif_settings.server_url,
        image_format=iiif_settings.image_format,
        prefix=settings.prefix).to_json(desc)

    st.write("Generating site...")
    html = env.get_template("index.html.j2").render(name=name, data=desc)

    st.write("Uploading data...")
    store = Store(settings, iiif_settings)
    store.upload(name, site_data.origin_id, html, xml, manifest, {
        "foo":"bar",
        "bar": "baz"
    })
    st.markdown("### Done!")
    st.write(f"Your site should be available after a few minutes at [{url}]({url})")


st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")


