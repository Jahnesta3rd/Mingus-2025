
import streamlit as st

# Set page config
st.set_page_config(page_title="Mobile Onboarding", layout="centered")

# Main container
st.markdown(
    """
    <div style='max-width: 480px; margin: auto; padding: 5vw; display: flex; flex-direction: column; align-items: center;'>
    """, unsafe_allow_html=True
)

# Inputs
email = st.text_input("Email Address")
phone = st.text_input("Phone Number")
zipcode = st.text_input("Zip Code")

# Button
if st.button("Continue"):
    if email and phone and zipcode:
        st.success("Proceeding to the next step...")
    else:
        st.error("Please fill out all fields.")

# Close container div
st.markdown("</div>", unsafe_allow_html=True)
