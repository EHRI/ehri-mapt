from datetime import date

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import value_or_default, init_page, load_files, PREFIX
from microarchive import KEYS

init_page("WP11 Demo | Additional Info")

items = load_files(st.session_state.get(PREFIX))

st.write("## Administration")

st.write("**Administrative information about this description.**")

st.session_state[KEYS.NOTES] = st.text_area("Enter any notes about the description of these materials:",
                                            help="This is equivalent to ISAD(G) 3.7.1: Archivist Note",
                                            value=value_or_default(KEYS.NOTES))

st.session_state[KEYS.DATE_DESC] = st.date_input("Enter the date this description was made:",
                                                 help="This is equivalent to ISAD(G) 3.7.3: Dates of Description",
                                                 value=value_or_default(KEYS.DATE_DESC, date.today()))

st.divider()
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Item Information")

if col2.button("Next"):
    switch_page("Publish")
