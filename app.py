import streamlit as st


st.set_page_config(
    page_title="Supply Chain Traceability Matrix",
    layout="wide",
)

st.title("Supply Chain Traceability Matrix")

page = st.sidebar.radio(
    "Navigation",
    ("Assessment", "Matrix / Bubble chart", "Categories admin"),
)

if page == "Assessment":
    st.header("Assessment")
    st.info("Assessment form will go here.")
elif page == "Matrix / Bubble chart":
    st.header("Matrix / Bubble chart")
    st.info("Bubble chart will go here.")
elif page == "Categories admin":
    st.header("Categories admin")
    st.info("Category management will go here.")
