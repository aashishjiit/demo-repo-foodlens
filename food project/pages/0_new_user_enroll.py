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
        .stApp .stButton>button { background-color: #d6f0ff !important; color: #000000 !important; border: none !important; }
        .stApp .stButton>button:hover { background-color: #7fbce8 !important; }
        /* Stronger selector to ensure buttons match theme */
        .stApp .stButton>button { border-color: #4ba3e0 !important; }
        .stApp .stButton>button:hover { border-color: #3a8ccc !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Logoff handled by dashboard sidebar; do not create per-page logoff button

    st.title("New User Enrollment")
    st.divider()

    st.write("##### User Information Form: 📝")
    st.divider()

    # Account credentials for login (moved to top of form)
    inputUsername = st.text_input("Choose a username:", key="enroll_username")
    inputPassword = st.text_input("Choose a password:", type="password", key="enroll_password")
    remember = st.checkbox("Remember me on this device", value=True, key="enroll_remember")
    st.divider()
    # Path to store credentials (hashed password)
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CRED_PATH = os.path.join(ROOT, 'credentials.json')

    inputName = st.text_input("Name: ", key="enroll_name")
    st.write("Hello ", inputName, "!")
    st.divider()

    inputAge = st.number_input("Age: ", min_value=0, max_value=120, step=1, key="enroll_age")
    st.write("You are ", inputAge, " years old!")
    st.divider()

    inputGender = st.selectbox("Select your gender:", ["Male", "Female", "Other", "Prefer Not To Say"], key="enroll_gender")
    st.write("You selected: ", inputGender)
    st.divider()

    inputHeight = st.slider("Select your height (in cm):", min_value=50, max_value=250, value=170, step=1, key="enroll_height")
    st.write("Your height is: ", inputHeight, " cm")
    st.divider()

    inputWeight = st.slider("Select your weight (in kg):", min_value=10, max_value=300, value=70, step=1, key="enroll_weight")
    st.write("Your weight is: ", inputWeight, " kg")
    st.divider()

    inputDiet = st.multiselect("Select your dietary preferences:", ["Vegetarian"], key="enroll_diet")
    st.divider()

    if st.button("Submit", key="enroll_submit"):
        st.session_state['enrollment'] = {
            'name': inputName,
            'age': inputAge,
            'gender': inputGender,
            'height': inputHeight,
            'weight': inputWeight,
            'diet': inputDiet,
            'username': inputUsername,
        }
        # store credentials in session_state for simple session-based login
        st.session_state['credentials'] = {
            'username': inputUsername,
            'password': inputPassword,
        }
        # Persist hashed credentials if user opted in
        if remember:
            to_save = {
                'username': inputUsername,
                'password_hash': hashlib.sha256(inputPassword.encode()).hexdigest(),
                'enrollment': st.session_state.get('enrollment', {})
            }
            try:
                with open(CRED_PATH, 'w', encoding='utf-8') as f:
                    json.dump(to_save, f)
            except Exception as e:
                st.warning(f"Could not save credentials: {e}")
        st.session_state['enrolled'] = True
        st.success("Thank you for submitting your information!")
    st.divider()

    st.write("Your data will be used to tailor diet recommendations specifically for you.")
    st.divider()


if __name__ == "__main__":
    render()
