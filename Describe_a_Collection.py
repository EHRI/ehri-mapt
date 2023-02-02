#!/usr/bin/env python

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default

st.set_page_config(page_title="Describe a Collection")

init_page()

st.info("""This bit will allow the user to select a folder of images from some Cloud storage.
        For the moment I have hard-coded a set of scans on AWS:""")

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

