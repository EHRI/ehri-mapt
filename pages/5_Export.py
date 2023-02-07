
from streamlit_extras.switch_page_button import switch_page

from ead import Ead

from iiif import IIIFManifest
from lib import *
from jinja2 import Environment, FileSystemLoader, select_autoescape
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

TEMP_NAME = "testing"

st.info("""Publishing this data will create a website containing the metadata for this
           collection and a browser for any images.\n\nTypically the site will take **1-5 minutes** to become live.
            """)
if st.button("Publish Website"):
    site_suffix = get_random_string(5)
    site_id = create_site(TEMP_NAME, site_suffix)
    url = f"https://{site_id}"
    st.markdown(f"Waiting for site to be available at: [{url}]({url})")

    st.write("Generating EAD...")
    xml = Ead().to_xml(desc)

    st.write("Generating IIIF manifest...")
    manifest = IIIFManifest(
        baseurl=url,
        name=TEMP_NAME,
        service_url=st.secrets.iiif.server_url,
        image_format=st.secrets.iiif.image_format,
        prefix=st.secrets.s3_credentials.prefix).to_json(desc)

    st.write("Generating site...")
    html = env.get_template("index.html.j2").render(name=TEMP_NAME, data=desc)

    st.write("Uploading data...")
    upload(TEMP_NAME, site_suffix, html, xml, manifest)
    st.markdown("### Done!")
    st.write(f"Your site should be available after a few minutes at [{url}]({url})")


st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")


