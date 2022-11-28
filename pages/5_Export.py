
from streamlit_extras.switch_page_button import switch_page

from ead import Identity, Contact, Description, SimpleEad, EadItem
from lib import *


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
                Description(scope=value_or_default(scope(ident))), url) \
           for ident, url in value_or_default("items", [])]
)


xml = ead.to_xml()
st.code(xml, language="xml")
st.download_button("Download EAD XML", file_name=ead.slug() + ".xml", data=xml, disabled=not ead.done())

col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")
