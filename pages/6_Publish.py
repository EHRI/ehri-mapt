import os

import requests
import streamlit as st
from polling2 import TimeoutException
from streamlit_extras.switch_page_button import switch_page

from ead import Ead
from iiif import IIIFManifest
from lib import make_archive, init_page, SITE_ID, PREFIX, IIIF_SETTINGS, MODE, FORMAT, web_builder, storage
from website import make_html


def wait_for_url(url: str):
    import polling2

    def step():
        try:
            r = requests.get(url)
            return r.status_code == 200
        except requests.ConnectionError:
            return False

    try:
        polling2.poll(
            step,
            step=5,
            timeout=10 * 60
        )
    except TimeoutException:
        pass


def preparing_site(ident: str):
    """Poll Cloudfront distribution deployment. This is typically much
    slower than waiting for the local edge location to be available."""
    import polling2

    def check(data):
        return data.status == 'Deployed'

    polling2.poll(
        lambda: web_builder().get_site(ident),
        check_success=check,
        step=5,
        timeout=10 * 60
    )


init_page("Publish")
st.write("## Publish Data")

st.write("**Create a website using this description.**")

# Build the representation...
desc = make_archive()

update_id = st.session_state.get(SITE_ID, None)
if update_id:
    st.info(f"Update site with code: {update_id}")
else:
    st.info("""Publishing this data will create a website containing the metadata for this
               collection and a browser for any images.""")

if st.button("Publish Website", disabled=PREFIX not in st.session_state):
    prefix = st.session_state.get(PREFIX)
    name = desc.slug()

    site_data = web_builder().get_or_create_site(name, update_id)
    st.session_state[SITE_ID] = site_data.id
    st.session_state[MODE] = "edit"
    domain = site_data.domain

    st.divider()
    url = f"https://{domain}"

    st.write("Generating EAD...")
    xml = Ead().to_xml(desc, os.path.join(url, f"{name}.xml"))

    st.write("Generating IIIF manifest...")
    manifest = IIIFManifest(
        baseurl=url,
        name=name,
        service_url=IIIF_SETTINGS.server_url,
        image_format=st.session_state.get(FORMAT),
        prefix=prefix).to_json(desc)

    st.write("Generating website...")
    html = make_html(name, desc, site_data.id)

    st.write("Uploading data...")
    state = desc.to_data() | {
        PREFIX: st.session_state.get(PREFIX),
        FORMAT: st.session_state.get(FORMAT)
    }
    storage().upload(name, site_data.origin_id, html, xml, manifest, state)

    with st.spinner("Preparing site..."):
        if not update_id:
            st.info(f"Typically a new site will take **1-5 minutes** to become [live]({url})...")
        #preparing_site(site_data.id)
        wait_for_url(url)

    st.markdown("### Done!")
    st.write(f"""Save this ID for editing this site:""")
    st.markdown(f"### `{site_data.id}`")

    if update_id:
        st.markdown(f"Updated site: [{url}]({url})")
    else:
        st.markdown(f"Your site is available at: [{url}]({url})")

st.divider()
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Additional Information")
