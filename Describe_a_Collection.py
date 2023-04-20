#!/usr/bin/env python

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default, SITE_SUFFIX, SITE_ID

st.set_page_config(page_title="Describe a Collection")

init_page()


with st.expander("Edit existing site?", expanded=SITE_SUFFIX in st.session_state):
    st.markdown("#### Add identifier key:")
    st.session_state[SITE_ID] = st.text_input("Site ID",
                                            help="Enter the site ID given when you published this site",
                                            value=value_or_default(SITE_ID, default=''))


items = value_or_default('items', [])

st.markdown(f"### Items found: {len(items)}")

view = """<div style="display: grid; grid-gap: 1rem; grid-template-columns: 1fr 1fr 1fr 1fr">"""
for i, (key, url, thumb_url) in enumerate(value_or_default("items", [])):
    view += "<div>"
    view += f"""<a href="{url}" target="_blank">
<img src="{thumb_url}" width="75" height="100" alt="{key}"  style="border: 1px solid #ccc"/></a>
"""
    view += f"""<a href="{url}" target="_blank">
<h5>{key}</h5></a>
"""
    view += "</div>"
view += "</div>"
st.markdown(view, unsafe_allow_html=True)


if st.button("Next: Enter Basic Identifying Information"):
    switch_page("Identifying Information")

