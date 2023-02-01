
from streamlit_extras.switch_page_button import switch_page

from ead import Ead
from microarchive import Identity, Contact, Description, MicroArchive, Item

from iiif import IIIFManifest
from lib import *
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader=FileSystemLoader(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
    autoescape=select_autoescape()
)


def key(id: str) -> str:
    return f"{id}.title"


def scope(id: str) -> str:
    return f"{id}.scope"


st.set_page_config(page_title="Export Information")

init_page()

st.write("## Export Information")

desc = MicroArchive(
    identity=Identity(
        title=value_or_default(TITLE),
        datedesc=value_or_default(DATE_DESC, None),
        extent=value_or_default(EXTENT)),
    contact=Contact(
        holder=value_or_default(HOLDER),
        street=value_or_default(STREET),
        postcode=value_or_default(POSTCODE)),
    description=Description(biog=value_or_default(BIOG_HIST),
                            scope=value_or_default(SCOPE),
                            lang=value_or_default(LANGS, [])),
    items=[Item(
                ident,
                Identity(value_or_default(key(ident))),
                Description(scope=value_or_default(scope(ident))), url, thumb_url, [])
           for ident, url, thumb_url in value_or_default("items", [])]
)


TEMP_NAME = "testing"


st.markdown("---")
if st.button("Publish Website"):
    site_id = create_site(TEMP_NAME)
    url = f"https://{site_id}"
    st.markdown(f"Waiting for site to be available at: [{url}]({url})")

    st.write("Generating EAD...")
    xml = Ead().to_xml(desc)
    with st.expander("Show EAD XML"):
        st.code(xml, language="xml")
    st.download_button("Download EAD XML", file_name=desc.slug() + ".xml", data=xml)

    st.write("Generating IIIF manifest...")
    manifest = IIIFManifest(
        baseurl=url,
        name=TEMP_NAME,
        service_url=st.secrets.iiif.server_url,
        prefix=st.secrets.s3_credentials.prefix).to_json(desc)
    with st.expander("Show IIIF Manifest"):
        st.code(manifest, language="json")
    st.download_button("Download IIIF Manifest", file_name=desc.slug() + ".json", data=manifest)

    st.write("Generating site...")
    html = env.get_template("index.html.j2").render(name=TEMP_NAME, data=desc)

    st.write("Uploading data...")
    upload(TEMP_NAME, html, xml, manifest)
    st.markdown("### Done!")
    st.write(f"Your site should be available in a few minutes at [{url}]({url})")


col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")


