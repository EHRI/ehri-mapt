from datetime import date

import inflect
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import value_or_default, init_page, load_files, PREFIX
from microarchive import KEYS

p = inflect.engine()

init_page("WP11 Demo | Basic Identifying Info")

items = load_files(st.session_state.get(PREFIX))

st.write("## Identification")

st.write("**Information to identify the collection.**")

st.session_state[KEYS.TITLE] = st.text_input("Enter a descriptive name for the full collection:",
                                             help="This is equivalent to ISAD(G) 3.1.2: Title",
                                             value=value_or_default(KEYS.TITLE))

st.session_state[KEYS.EXTENT] = st.text_area("Enter a general description of the format of this material:",
                                             help="Example '127 photographs'. "
                                                  "This is equivalent to ISAD(G) 3.1.5: Extent and Medium",
                                             value=value_or_default(KEYS.EXTENT,
                                                                    f"{len(items)} "
                                                                    f"{p.plural('scanned image', len(items))}" if items else ""))

st.divider()
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Describe a Collection")

if col2.button("Next"):
    switch_page("Context Information")
