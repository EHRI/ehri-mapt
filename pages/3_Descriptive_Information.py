import langcodes.data_dicts
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default
from microarchive import KEYS

init_page("WP11 Demo | Descriptive Info")

st.write("## Content")

st.write("**Information about the content of the collection.**")

st.session_state[KEYS.BIOG_HIST] = st.text_area(
    "Provide a succinct biographical overview of the person(s) who created this collection",
    help="This is equivalent to ISAD(G) 3.2.2: Administrative/Biographical History",
    value=value_or_default(KEYS.BIOG_HIST))

st.session_state[KEYS.SCOPE] = st.text_area("Provide a general textual description of the contents of this collection:",
                                            help="e.g. such as the subject matter to which it pertains. "
                                                 "This is equivalent to ISAD(G) 3.3.1: Scope and Content",
                                            value=value_or_default(KEYS.SCOPE))

st.session_state[KEYS.LANGS] = st.multiselect("Enter the languages used in the collection's items:",
                                              options=sorted([lang for lang in langcodes.LANGUAGE_ALPHA3.keys()]),
                                              format_func=lambda code: langcodes.get(code).display_name(),
                                              default=value_or_default(KEYS.LANGS, []),
                                              help="This is equivalent to ISAD(G) 3.4.3: Languages of Material")

st.divider()
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Context Information")
if col2.button("Next"):
    switch_page("Item Information")
