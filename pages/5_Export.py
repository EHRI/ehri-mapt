import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from ead import Ead
from iiif import IIIFManifest
from lib import make_archive, init_page, SITE_ID, WEB, IIIF_SETTINGS, S3_SETTINGS, STORE
from website import make_html

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

    site_data = WEB.get_or_create_site(name, update_id)
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
        service_url=IIIF_SETTINGS.server_url,
        image_format=IIIF_SETTINGS.image_format,
        prefix=S3_SETTINGS.prefix).to_json(desc)

    st.write("Generating site...")
    html = make_html(name, desc)

    st.write("Uploading data...")
    STORE.upload(name, site_data.origin_id, html, xml, manifest, desc.to_data())
    st.markdown("### Done!")
    st.write(f"Your site should be available after a few minutes at [{url}]({url})")


st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")


