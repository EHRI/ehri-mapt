from datetime import date

import inflect
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import value_or_default, init_page
from microarchive import KEYS

p = inflect.engine()

st.set_page_config(page_title="Basic Identifying Info")

init_page()

items = value_or_default("items", [])

st.write("## Identifying information")

st.write("Information to identify the collection")

st.session_state[KEYS.TITLE] = st.text_input("Collection Name",
              help="Enter a descriptive name for the full collection",
              value=value_or_default(KEYS.TITLE))

st.session_state[KEYS.DATE_DESC] = st.date_input("Date of description",
              help="Enter the date this description was made",
              value=value_or_default(KEYS.DATE_DESC, date.today()))

st.session_state[KEYS.EXTENT] = st.text_area("Type of material",
             help="Enter a general description of the format of this material, for example '127 "
                  "photographs'",
             value=value_or_default(KEYS.EXTENT, f"{len(items)} {p.plural('scanned image', len(items))}"))

st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Describe a Collection")

if col2.button("Next"):
    switch_page("Context Information")