import streamlit as st


def render():
    # Simple Home page showing welcome and logoff
    user = st.session_state.get('user') or st.session_state.get('enrollment', {}).get('username', '')

    # Hide default pages nav and style sidebar to match app theme
    st.markdown(
        """
        <style>div[data-testid="stSidebarNav"]{display:none;}</style>
        <style>
        .stApp { background-color: #d6f0ff; }
        h1, .css-1v3fvcr h1 { color: #1f4e79 !important; }
        section[data-testid="stSidebar"] > div, div[data-testid="stSidebar"] {
            background-color: #1f4e79 !important;
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] *{ color: #ffffff !important; }
        section[data-testid="stSidebar"] button, section[data-testid="stSidebar"] .stButton>button {
            background-color: rgba(255,255,255,0.06) !important;
            color: #ffffff !important;
        }
        .stApp .stButton>button { background-color: #d6f0ff !important; color: #000000 !important; border: none !important; }
        .stApp .stButton>button:hover { background-color: #c79e72 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(f"Welcome : {user}")
    st.divider()
    st.write("You're now logged in. Use the sidebar to navigate.")

    # Logoff handled by dashboard sidebar; do not create per-page logoff button


if __name__ == "__main__":
    render()
