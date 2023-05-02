import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default
from microarchive import KEYS

init_page("WP11 Demo | Contextual Info")

st.write("## Context")

st.write("**Information about where the collection is kept and who is responsible for it.**")

st.session_state[KEYS.HOLDER] = st.text_input("Enter the name of the person or organisation "
                                              "responsible for custody of this collection:",
                                              value=value_or_default(KEYS.HOLDER))

st.session_state[KEYS.STREET] = st.text_input("Enter the street address where this collection is held:",
                                              value=value_or_default(KEYS.STREET))

st.session_state[KEYS.POSTCODE] = st.text_input("Enter the postal code where this collection is located:",
                                                value=value_or_default(KEYS.POSTCODE))

st.divider()
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Identifying Information")
if col2.button("Next"):
    switch_page("Descriptive Information")
