import langcodes.data_dicts
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default
from microarchive import KEYS


init_page("Descriptive Info")

st.write("## Descriptive information")

st.write("Information about the content of the collection.")

st.session_state[KEYS.BIOG_HIST] = st.text_area("Biographical information",
             help="Provide a succinct biographical overview of the person or persons who created this "
                  "collection",
             value=value_or_default(KEYS.BIOG_HIST))

st.session_state[KEYS.SCOPE] = st.text_area("Content information",
             help="Provide a general textual description of the contents of this collection, such as the "
                  "subject matter to which it pertains",
             value=value_or_default(KEYS.SCOPE))

st.session_state[KEYS.LANGS] = st.multiselect("Languages Used",
               options=sorted([lang for lang in langcodes.LANGUAGE_ALPHA3.keys()]),
               format_func=lambda code: langcodes.get(code).display_name(),
               default=value_or_default(KEYS.LANGS, []),
               help="Language or languages used in the collection's items")

st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Context Information")
if col2.button("Next"):
    switch_page("Item Information")
