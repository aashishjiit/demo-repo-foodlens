
# importing necessary libraries
import streamlit as st
import os
import shutil
import re
import base64
import io
from PIL import Image, ImageOps

# displaying page content
def render():
    # Hide default pages nav (dashboard provides navigation)
    # intro to html/css for hiding sidebar
    st.markdown(
        """
        <style>div[data-testid="stSidebarNav"]{display:none;}</style>
        """,
        unsafe_allow_html=True,
    )

    # Logoff handled by dashboard sidebar; do not create per-page logoff button

    st.title(" Food Recommendation System 🍔")
    # Page background: light blue
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #d6f0ff;
        }
        /* Title/header color */
        .stApp h1, .stApp .css-1v3fvcr h1 {
            color: #1f4e79 !important;
        }
        /* Sidebar background and text color */
        section[data-testid="stSidebar"] > div, div[data-testid="stSidebar"] {
            background-color: #1f4e79 !important;
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] *{
            color: #ffffff !important;
        }
        /* Sidebar links/buttons contrast */
        section[data-testid="stSidebar"] button, section[data-testid="stSidebar"] .stButton>button {
            background-color: rgba(255,255,255,0.06) !important;
            color: #ffffff !important;
        }
        /* Main content buttons (e.g. "Select as favorite") */
        .stApp .stButton>button {
            background-color: #d6f0ff !important;
            color: #000000 !important;
            border: none !important;
            width: 171px !important;
            max-width: 171px !important;
            padding: 8px 10px !important;
            border-radius: 4px !important;
            margin: 6px auto !important;
            display: inline-block !important;
            box-sizing: border-box !important;
        }
        .stApp .stButton>button:hover {
            background-color: #7fbce8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
        /* Stronger selector to ensure the login button matches theme */
        .stApp .stButton>button { background-color: #4ba3e0 !important; border-color: #4ba3e0 !important; color: #ffffff !important; }
        .stApp .stButton>button:hover { background-color: #3a8ccc !important; border-color: #3a8ccc !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    # Introduction text
    st.write("Welcome to the Food Recommendation System! This page provides personalized food recommendations based on your dietary preferences and nutritional needs. Explore a variety of meal options tailored just for you.")
    st.write("To get started, please ensure you have completed the user enrollment process on the 'New User Enrollment' page. Your information will help us generate accurate and suitable food recommendations.")
    st.divider()

    # Show all images from a `favourites_option` directory and allow selecting favorites
    project_root = os.path.dirname(os.path.dirname(__file__))
    candidates = [
        os.path.join(project_root, 'images_data', 'favourites_option'),
        os.path.join(project_root, 'image_data', 'favourites_option'),
        os.path.join(project_root, 'images', 'favourites_option'),
        os.path.join(project_root, 'favourites_option'),
    ]
    # files and locations
    image_files = []
    for c in candidates:
        if os.path.isdir(c):
            for fname in sorted(os.listdir(c)):
                # skip bunch-bananas-6175887.webp from recommendations
                if fname.lower() == 'bunch-bananas-6175887.webp':
                    continue
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.avif')):
                    image_files.append(os.path.join(c, fname))
            if image_files:
                break
    # If no images found, show placeholder
    if not image_files:
        st.info('No recommendation images found in favourites_option — showing placeholder.')
        st.image("https://via.placeholder.com/400", caption="Recommendation 1")
        return
    # Initialize favorites list in session state
    if 'favorites' not in st.session_state:
        st.session_state['favorites'] = []

    # Helper to safely resolve and display image paths (avoid passing bare file ids to st.image)
    def _resolve_image_path(p):
        # If absolute/relative path exists, return it
        if os.path.isabs(p) and os.path.exists(p):
            return p
        alt = os.path.join(project_root, p)
        if os.path.exists(alt):
            return alt

        # Try looking under images_data folders for the basename
        base = os.path.basename(p)
        search_dirs = [
            os.path.join(project_root, 'images_data'),
            os.path.join(project_root, 'images_data', 'favourites_option'),
        ]
        # include user's folders if available
        if st.session_state.get('authenticated') and st.session_state.get('user'):
            uid = str(st.session_state.get('user'))
            search_dirs.insert(0, os.path.join(project_root, 'images_data', uid, 'favourites'))
            search_dirs.insert(0, os.path.join(project_root, 'images_data', uid, 'food_to_analyse'))

        for d in search_dirs:
            candidate = os.path.join(d, base)
            if os.path.exists(candidate):
                return candidate

        # Not found — return None
        return None

    # Helper callback to toggle favorites so button label updates immediately
    def _toggle_favorite(path):
        if 'favorites' not in st.session_state:
            st.session_state['favorites'] = []
        if path in st.session_state['favorites']:
            st.session_state['favorites'].remove(path)
            # saving favorite to user folder
            if st.session_state.get('authenticated') and st.session_state.get('user'):
                user_id = str(st.session_state.get('user'))
                user_dir = os.path.join(project_root, 'images_data', user_id, 'favourites')
                try:
                    target = os.path.join(user_dir, os.path.basename(path))
                    if os.path.exists(target):
                        os.remove(target)
                except Exception:
                    st.warning('Could not remove favorite from user folder')
        # if not favorited
        else:
            st.session_state['favorites'].append(path)
            # checks if logged in
            if st.session_state.get('authenticated') and st.session_state.get('user'):
                user_id = str(st.session_state.get('user'))
                # folder path
                user_dir = os.path.join(project_root, 'images_data', user_id, 'favourites')
                try:
                    os.makedirs(user_dir, exist_ok=True)
                    # defines where the image will be saved
                    target = os.path.join(user_dir, os.path.basename(path))
                    if not os.path.exists(target):
                        shutil.copy(path, target)
                # warning if unable to save
                except Exception:
                    st.warning('Could not save favorite to user folder')

    # Render each image in its own row with a favorite button on the left
    # Use a fixed square size so all pictures show at the same width and height
    # Reduced size so three thumbnails visually fit per row
    IMG_SIZE = (160, 160)
    THUMB_SIZE = IMG_SIZE

    def _load_thumb(path, size=IMG_SIZE):
        try:
            img = Image.open(path)
            return ImageOps.fit(img.convert('RGB'), size, Image.LANCZOS)
        except Exception:
            return None

    def _img_to_datauri(img, fmt='JPEG'):
        try:
            buff = io.BytesIO()
            img.save(buff, format=fmt)
            b64 = base64.b64encode(buff.getvalue()).decode('ascii')
            return f"data:image/{fmt.lower()};base64,{b64}"
        except Exception:
            return None

    def _render_thumb(col, thumb, label, is_fav, outline=False, gap=False):
        # background: use light blue for all thumbnails
        bg = '#eef9ff'
        outline_style = "border:2px solid #d6f0ff;" if outline else ""
        gap_style = "margin:8px;" if gap else ""
        if thumb is None:
            # use placeholder
            img_tag = f"<img src='https://via.placeholder.com/{IMG_SIZE[0]}' style='width:{IMG_SIZE[0]}px;height:{IMG_SIZE[1]}px;object-fit:cover;border-radius:6px;'/>"
        else:
            uri = _img_to_datauri(thumb)
            if uri:
                img_tag = f"<img src=\"{uri}\" style='width:{IMG_SIZE[0]}px;height:{IMG_SIZE[1]}px;object-fit:cover;border-radius:6px;'/>"
            else:
                img_tag = f"<img src='https://via.placeholder.com/{IMG_SIZE[0]}' style='width:{IMG_SIZE[0]}px;height:{IMG_SIZE[1]}px;object-fit:cover;border-radius:6px;'/>"

        html = f"<div style='background:{bg};padding:6px;border-radius:8px;display:inline-block;{outline_style}{gap_style}'>{img_tag}<div style='text-align:center;margin-top:6px;font-size:12px;color:#222'>{label}</div></div>"
        col.markdown(html, unsafe_allow_html=True)
    # Display all candidate images in rows of three with uniform thumbnails
    chunk_size = 3
    for i in range(0, len(image_files), chunk_size):
        row_cols = st.columns(chunk_size)
        for idx, img_path in enumerate(image_files[i:i+chunk_size]):
            c = row_cols[idx]
            name = os.path.basename(img_path)
            resolved = _resolve_image_path(img_path)
            is_fav = img_path in st.session_state['favorites']
            btn_key = f"fav_btn_{i+idx}_{name}"
            btn_label = "Favorited" if is_fav else "Select as favorite"

            if resolved:
                thumb = _load_thumb(resolved, THUMB_SIZE)
                _render_thumb(c, thumb, name, is_fav)
            else:
                _render_thumb(c, None, name, is_fav)

            # Favorite toggle below each image
            c.button(btn_label, key=btn_key, on_click=_toggle_favorite, args=(img_path,))

    # Show current favorites list
    if st.session_state['favorites']:
        st.divider()
        # heading section
        st.write("Your favorites:")
        favs = st.session_state['favorites']
        chunk_size = 3
        # display favorites in rows of three
        for i in range(0, len(favs), chunk_size):
            row_cols = st.columns(chunk_size)
            for idx, p in enumerate(favs[i:i+chunk_size]):
                c = row_cols[idx]
                resolved = _resolve_image_path(p)
                if resolved:
                    thumb = _load_thumb(resolved, THUMB_SIZE)
                    is_fav = p in st.session_state.get('favorites', [])
                    _render_thumb(c, thumb, os.path.basename(p), is_fav)
                else:
                    _render_thumb(c, None, os.path.basename(p), False)

    # Recommendations: suggest more foods similar to user's favorites
    # Build simple token-based similarity from filenames and recommend top matches
    try:
        favs = st.session_state.get('favorites', [])
        candidates_set = [p for p in image_files if p not in favs]
        if favs and candidates_set:
            # collect tokens from favorite filenames
            fav_tokens = set()
            for p in favs:
                base = os.path.splitext(os.path.basename(p))[0].lower()
                for t in re.split(r'[^a-z0-9]+', base):
                    if t:
                        fav_tokens.add(t)

            # score candidates by token overlap
            scores = []
            for p in candidates_set:
                base = os.path.splitext(os.path.basename(p))[0].lower()
                tokens = set([t for t in re.split(r'[^a-z0-9]+', base) if t])
                overlap = len(tokens & fav_tokens)
                scores.append((overlap, p))

            # choose top matches (overlap > 0) else fall back to first candidates
            scores.sort(reverse=True)
            recommended = [p for s, p in scores if s > 0]
            if not recommended:
                recommended = [p for _, p in scores][:3]
            recommended = recommended[:3]

            if recommended:
                st.divider()
                st.subheader('Recommended for you')
                rec_cols = st.columns(3)
                for i, p in enumerate(recommended):
                    c = rec_cols[i % 3]
                    resolved = _resolve_image_path(p)
                    label = os.path.basename(p)
                    if resolved:
                        thumb = _load_thumb(resolved, THUMB_SIZE)
                        is_fav = p in st.session_state.get('favorites', [])
                        _render_thumb(c, thumb, label, is_fav, outline=True)
                    else:
                        _render_thumb(c, None, label, False, outline=True)
                    btn_key = f"rec_add_{i}_{os.path.basename(p)}"
                    # allow adding recommended item to favorites
                    c.button('Add to favorites', key=btn_key, on_click=_toggle_favorite, args=(p,))
    except Exception:
        # non-fatal: if recommendation logic fails, silently continue
        pass

# runs fully only when the file is executed directly
if __name__ == "__main__":
    # display the render function
    render()