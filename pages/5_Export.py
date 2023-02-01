
from streamlit_extras.switch_page_button import switch_page

from ead import Identity, Contact, Description, SimpleEad, EadItem
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

ead = SimpleEad(
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
    items=[EadItem(
                ident,
                Identity(value_or_default(key(ident))),
                Description(scope=value_or_default(scope(ident))), url, thumb_url, [])
           for ident, url, thumb_url in value_or_default("items", [])]
)


TEMP_NAME = "testing"

xml = ead.to_xml()
with st.expander("Show EAD XML"):
    st.code(xml, language="xml")
st.download_button("Download EAD XML", file_name=ead.slug() + ".xml", data=xml)

html = env.get_template("index.html.j2").render(name=TEMP_NAME, ead=ead)
with st.expander("Show HTML"):
    st.code(html, language="html")
st.download_button("Download HTML", file_name=ead.slug() + ".html", data=html)

manifest = ead.to_json(baseurl=st.secrets.iiif.server_url)
with st.expander("Show IIIF Manifest"):
    st.code(manifest, language="json")
st.download_button("Download IIIF Manifest", file_name=ead.slug() + ".json", data=manifest)

st.markdown("---")
if st.button("Publish Website"):
    items_html = env.get_template("items.html.j2").render(name=TEMP_NAME, ead=ead)
    url = publish(TEMP_NAME, html, items_html, xml, manifest)
    st.markdown(f"Waiting for site to be available at: [https://{url}](https://{url})")

col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")


