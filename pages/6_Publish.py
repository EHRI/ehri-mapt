import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from ead import Ead
from iiif import IIIFManifest
from lib import make_archive, init_page, SITE_ID, PREFIX, WEB, IIIF_SETTINGS, S3_SETTINGS, STORE, MODE, FORMAT
from website import make_html


init_page("Publish")

st.write("## Publish Data")

# Build the representation...
desc = make_archive()

st.info("""Publishing this data will create a website containing the metadata for this
           collection and a browser for any images.\n\nTypically a new site will take **1-5 minutes** to become live.
            """)

if st.button("Publish Website", disabled=PREFIX not in st.session_state):
    prefix = st.session_state.get(PREFIX)
    update_id = st.session_state.get(SITE_ID) or None
    name = desc.slug()

    site_data = WEB.get_or_create_site(name, update_id)
    st.session_state[SITE_ID] = site_data.id
    st.session_state[MODE] = "edit"
    domain = site_data.domain

    st.markdown("---")
    url = f"https://{domain}"

    st.write("Generating EAD...")
    xml = Ead().to_xml(desc)

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
    STORE.upload(name, site_data.origin_id, html, xml, manifest, state)
    st.markdown("### Done!")
    st.write(f"""Save this ID for editing this site:""")
    st.markdown(f"### `{site_data.id}`")

    if update_id:
        st.markdown(f"Updated site: [{url}]({url})")
    else:
        st.markdown(f"Your site should be available after a few minutes at [{url}]({url})")



st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Additional Information")


