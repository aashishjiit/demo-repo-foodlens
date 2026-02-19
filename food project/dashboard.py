import streamlit as st
import importlib.util
import os
from st_compat import rerun

# Hide Streamlit's default pages navigation so we can show a custom, minimal sidebar
st.markdown(
	"""
	<style>div[data-testid="stSidebarNav"]{display:none;}</style>
	""",
	unsafe_allow_html=True,
)

# Global styling: page background, sidebar and button colors
st.markdown(
	"""
	<style>
	.stApp { background-color: #d6f0ff; }
	/* Sidebar background and text color */
	section[data-testid="stSidebar"] > div, div[data-testid="stSidebar"] {
		background-color: #1f4e79 !important;
		color: #ffffff !important;
	}
	section[data-testid="stSidebar"] * { color: #ffffff !important; }
	/* Sidebar buttons: fixed equal width, square-ish with a small curb */
	section[data-testid="stSidebar"] .stButton>button {
		width: 220px !important;
		min-width: 220px !important;
		max-width: 220px !important;
		height: 44px !important;
		padding: 8px 12px !important;
		border-radius: 3px !important;
		display: block !important;
		margin: 8px auto !important;
		box-sizing: border-box !important;
		text-align: center !important;
		background-color: rgba(255,255,255,0.06) !important;
		color: #ffffff !important;
		border: none !important;
		white-space: nowrap !important;
		overflow: hidden !important;
		text-overflow: ellipsis !important;
	}
	section[data-testid="stSidebar"] .stButton>button:hover {
		background-color: rgba(255,255,255,0.09) !important;
	}
	/* Main content buttons */
	.stApp .stButton>button { background-color: #d6f0ff !important; color: #ffffff !important; border: none !important; }
	.stApp .stButton>button:hover { background-color: #7fbce8 !important; }
	/* Header/title color */
	h1, .css-1v3fvcr h1 { color: #1f4e79 !important; }
	</style>
	""",
	unsafe_allow_html=True,
)

# Custom minimal sidebar: only Login and New User Enrollment
st.sidebar.title("Navigation")
# Store selected page in session_state so it persists across reruns
if 'page' not in st.session_state:
	st.session_state['page'] = None

# Only show login/enroll when not authenticated
if not st.session_state.get('authenticated'):
	if st.sidebar.button("Login", key="dashboard_login"):
		st.session_state['page'] = '1_login'
	if st.sidebar.button("New User Enrollment", key="dashboard_enroll"):
		st.session_state['page'] = '0_new_user_enroll'
else:
	# When authenticated show app pages + Log off
	if st.sidebar.button("Home", key="dashboard_home"):
		st.session_state['page'] = '2_home'
	if st.sidebar.button("Food Recommendation", key="dashboard_food"):
		st.session_state['page'] = '3_food_recommend'
	if st.sidebar.button("Image Capture", key="dashboard_image"):
		st.session_state['page'] = '4_image_capture'
	st.sidebar.divider()
	if st.sidebar.button("Log off", key="dashboard_logoff"):
		# Clear authentication and related session state so sidebar shows only Login/Enroll
		for k in ['authenticated', 'user', 'page', 'credentials', 'credentials_file', 'enrollment', 'enrolled', 'favorited']:
			if k in st.session_state:
				del st.session_state[k]
		st.success("Logged out")
		rerun()

# If a page is selected, run its script on every rerun so forms keep state
selected = st.session_state.get('page')
if selected:
	page_file = None
	if selected == '1_login':
		page_file = os.path.join(os.path.dirname(__file__), "pages", "1_login.py")
	elif selected == '0_new_user_enroll':
		page_file = os.path.join(os.path.dirname(__file__), "pages", "0_new_user_enroll.py")
	elif selected == '2_home':
			page_file = os.path.join(os.path.dirname(__file__), "pages", "2_home.py")
	elif selected == '3_food_recommend':
			page_file = os.path.join(os.path.dirname(__file__), "pages", "3_food_recommend.py")
	elif selected == '4_image_capture':
			page_file = os.path.join(os.path.dirname(__file__), "pages", "4_image_capture.py")

	if page_file and os.path.exists(page_file):
		# import the page module dynamically and call its render() function
		spec = importlib.util.spec_from_file_location("page_module", page_file)
		page_mod = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(page_mod)
		if hasattr(page_mod, 'render'):
			page_mod.render()
		st.stop()

st.write("# Welcome To DietLens🔎🍽️! ")
st.divider()

st.write("DietLens is an AI-powered diet recommendation system designed to help you achieve your health and fitness goals. Whether you're looking to lose weight, gain muscle, or simply maintain a healthy lifestyle, DietLens provides personalized meal plans and dietary advice tailored to your unique needs.")
st.divider()
st.write("Navigate through the available pages using the sidebar — only Login and New User Enrollment are shown until you authenticate.")
st.divider()

st.write("Get started today and take the first step towards a healthier you with DietLens!")
st.divider()