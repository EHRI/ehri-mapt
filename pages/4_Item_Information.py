import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default

st.set_page_config(page_title="Enter Descriptive Info")

init_page()

st.write("## Item information")

st.write("Information about items in this collection.")

for i, (key, url) in enumerate(value_or_default("items", [])):
    col1, col2 = st.columns(2)
    col1.write(f"#### {key}")
    col1.markdown(f"""<a href="{url}" target="_blank" tabindex="-1">
                    <img src="{url}" width="150" height="auto" alt="{key}"  
                        style="border: 1px solid #ccc"/></a>
                        """, unsafe_allow_html=True)
    key = f"{key}.title"
    st.session_state[key] = col2.text_input(f"Name {i + 1}",
                                            value=value_or_default(key, ""),
                                            placeholder="Title",
                                            label_visibility="hidden")
    st.markdown("---")

col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Descriptive Information")
if col2.button("Next"):
    switch_page("Export")
