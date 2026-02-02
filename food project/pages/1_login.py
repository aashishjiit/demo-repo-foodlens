import streamlit as st
import os
import json
import hashlib


def render():
    # Hide default pages nav (dashboard provides navigation)
    st.markdown(
        """
        <style>div[data-testid="stSidebarNav"]{display:none;}</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        div[data-testid="stSidebarNav"]{display:none;}
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
        /* Main content buttons */
        .stApp .stButton>button { background-color: #4b9bd6 !important; color: #ffffff !important; border: none !important; }
        .stApp .stButton>button:hover { background-color: #7fbce8 !important; }
        /* Stronger selector to ensure the login button matches theme */
        .stApp .stButton>button { border-color: #4ba3e0 !important; }
        .stApp .stButton>button:hover { border-color: #3a8ccc !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Load persisted credentials if present
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CRED_PATH = os.path.join(ROOT, 'credentials.json')
    file_creds = None
    if os.path.exists(CRED_PATH):
        try:
            with open(CRED_PATH, 'r', encoding='utf-8') as f:
                file_creds = json.load(f)
                # expose to session for later use
                st.session_state['credentials_file'] = file_creds
        except Exception:
            file_creds = None

    # Logoff handled by dashboard sidebar; do not create per-page logoff button

    st.title("Login")
    st.divider()

    prefill_user = file_creds.get('username') if file_creds else ''
    username = st.text_input("Username", value=prefill_user, key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    remember = st.checkbox("Remember me on this device", value=False, key="login_remember")

    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if st.button("Login", key="login_submit"):
        creds = st.session_state.get('credentials')
        # First check session credentials (freshly enrolled in this run)
        valid = False
        if creds and username == creds.get('username') and password == creds.get('password'):
            valid = True
        # Otherwise check persisted file credentials (compare hashed password)
        if not valid and file_creds:
            if username == file_creds.get('username') and hashlib.sha256(password.encode()).hexdigest() == file_creds.get('password_hash'):
                valid = True

        if valid:
            st.session_state['authenticated'] = True
            st.session_state['user'] = username
            # Persist if requested
            if remember:
                try:
                    to_save = {
                        'username': username,
                        'password_hash': hashlib.sha256(password.encode()).hexdigest(),
                        'enrollment': st.session_state.get('enrollment', {})
                    }
                    with open(CRED_PATH, 'w', encoding='utf-8') as f:
                        json.dump(to_save, f)
                except Exception as e:
                    st.warning(f"Could not save credentials: {e}")

            # Set target page and stop; dashboard will run the home page on rerun
            st.session_state['page'] = '2_home'
            # show darker blue notification instead of green success
            st.markdown(f"<div style='background:#4ba3e0;color:#ffffff;padding:10px;border-radius:6px'>Logged in as {username}</div>", unsafe_allow_html=True)
            st.stop()
        else:
            st.error("Invalid credentials. Please enroll first or check username/password.")

    if st.session_state.get('authenticated'):
        st.write(f"You are logged in as {st.session_state.get('enrollment', {}).get('username','')}")
        if st.button("Logout", key="login_logout"):
            st.session_state['authenticated'] = False
            st.success("Logged out")


if __name__ == "__main__":
    render()
