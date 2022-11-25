#!/usr/bin/env python

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default

st.set_page_config(page_title="Describe a Collection")

init_page()

view = """<div style="display: grid; grid-gap: 1rem; grid-template-columns: 1fr 1fr 1fr 1fr">"""
for i, (key, url) in enumerate(value_or_default("items", [])):
    view += "<div>"
    view += f"""<a href="{url}" target="_blank">
<img src="{url}" width="150" height="auto" alt="{key}"  style="border: 1px solid #ccc"/></a>
"""
    view += f"""<a href="{url}" target="_blank">
<h4>{key}</h4></a>
"""
    view += "</div>"
view += "</div>"
st.markdown(view, unsafe_allow_html=True)


if st.button("Enter Basic Identifying Information"):
    switch_page("Identifying Information")

