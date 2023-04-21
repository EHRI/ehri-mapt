import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from lib import init_page, value_or_default, PREFIX, load_files
from microarchive import item_key, KEYS

st.set_page_config(page_title="Enter Descriptive Info")

init_page()

st.write("## Item information")

st.write("Information about items in this collection.")


if PREFIX in st.session_state and st.session_state[PREFIX]:
    items = enumerate(load_files(st.session_state.get(PREFIX)))
    if items:
        for i, (ident, url, thumb_url) in items:
            col1, col2 = st.columns(2)
            col1.markdown(f"""<a href="{url}" target="_blank" tabindex="-1">
                            <img src="{thumb_url}" width="75" height="100" alt="{ident}"  
                                style="border: 1px solid #ccc"/></a>
                                """, unsafe_allow_html=True)
            col1.caption(ident)
            ead_title = item_key(ident, KEYS.TITLE)
            st.session_state[ead_title] = col2.text_input(f"Name {i + 1}",
                                                          value=value_or_default(ead_title),
                                                          placeholder="Title",
                                                          label_visibility="hidden")
            ead_scope = item_key(ident, KEYS.SCOPE)
            st.session_state[ead_scope] = col2.text_area(f"Scope {i + 1}",
                                                          value=value_or_default(ead_scope),
                                                          placeholder="Description",
                                                          label_visibility="hidden",
                                                          height=30)
            st.markdown("---")
    else:
        st.write("### No files available")
else:
    st.write("### No dataset selected")

st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("Back"):
    switch_page("Descriptive Information")
if col2.button("Next"):
    switch_page("Export")
