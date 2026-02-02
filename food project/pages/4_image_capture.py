
import streamlit as st
import os
import shutil
import re
from datetime import datetime
from pathlib import Path
import sys


def render():
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
        .stApp .stButton>button { background-color: #3b84c2 !important; color: #ffffff !important; border: none !important; }
        .stApp .stButton>button:hover { background-color: #7fbce8 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Image Capturing 📸")
    st.divider()
    st.write("This page allows you to capture images using your device's camera. Please ensure that your camera is connected and functioning properly before proceeding.")
    st.write("To capture an image, click on the 'Capture Image' button below. The captured image will be displayed on the screen.")
    st.divider()

    #st.radio("Does this contain oil?: ", ("Yes", "No"))
    #st.radio("Does this contain butter?: ", ("Yes", "No"))
    
    #st.text_input("Please enter any other sauces the dish contains: ")
    #st.divider()
    # Logoff handled by dashboard sidebar; do not create per-page logoff button
    # Start capture flow
    if 'capturing' not in st.session_state:
        st.session_state['capturing'] = False

    # Allow uploading an image file in addition to camera capture
    uploaded_file = st.file_uploader("Or upload an image", type=['png', 'jpg', 'jpeg'], key="uploaded_image")
    if uploaded_file is not None:
        # Ensure images_data/captures folder exists in project root
        project_root = os.path.dirname(os.path.dirname(__file__))
        save_dir = os.path.join(project_root, 'images_data', 'captures')
        os.makedirs(save_dir, exist_ok=True)

        # preserve original name but add timestamp to avoid collisions
        orig_name = getattr(uploaded_file, 'name', 'upload')
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{orig_name}"
        save_path = os.path.join(save_dir, filename)
        try:
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Uploaded and saved to {save_path}")
            # persist last saved path so analysis can find it across reruns
            st.session_state['last_capture_path'] = save_path

            # If user is authenticated, also save a copy under images_data/<userid>/food_to_analyse
            if st.session_state.get('authenticated') and st.session_state.get('user'):
                try:
                    user_id = str(st.session_state.get('user'))
                    user_folder = os.path.join(project_root, 'images_data', user_id, 'food_to_analyse')
                    os.makedirs(user_folder, exist_ok=True)
                    target_path = os.path.join(user_folder, filename)
                    shutil.copy(save_path, target_path)
                    st.info(f"Copied to user folder: {target_path}")
                except Exception as e:
                    st.warning(f"Could not copy to user folder: {e}")

            # analysis button for uploaded file
            analyze_key = f"analyze_{filename}"
            if 'analyze_requested' not in st.session_state:
                st.session_state['analyze_requested'] = False
            if st.button("Analyze uploaded image (YOLOv8)", key=analyze_key):
                st.session_state['analyze_requested'] = True
            # previously-detected foods are stored in session state (display suppressed)
        except Exception as e:
            st.error(f"Could not save uploaded image: {e}")

    if st.button("Capture Image", key="capture_image"):
        st.session_state['capturing'] = True

    if st.session_state['capturing']:
        camera_file = st.camera_input("Take a photo", key="camera_input")
        if camera_file is not None:
            # Ensure images_data/captures folder exists in project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            save_dir = os.path.join(project_root, 'images_data', 'captures')
            os.makedirs(save_dir, exist_ok=True)

            # choose extension from content type
            content_type = getattr(camera_file, 'type', '') or ''
            ext = 'png' if 'png' in content_type else 'jpg'
            filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            save_path = os.path.join(save_dir, filename)

            # write bytes
            try:
                with open(save_path, 'wb') as f:
                    f.write(camera_file.getbuffer())
                # st.success(f"Image saved to {save_path}")
                # persist last saved path so analysis can find it across reruns
                st.session_state['last_capture_path'] = save_path

                # If user is authenticated, also save a copy under images_data/<userid>/food_to_analyse
                if st.session_state.get('authenticated') and st.session_state.get('user'):
                    try:
                        user_id = str(st.session_state.get('user'))
                        user_folder = os.path.join(project_root, 'images_data', user_id, 'food_to_analyse')
                        os.makedirs(user_folder, exist_ok=True)
                        target_path = os.path.join(user_folder, filename)
                        # copy saved file
                        shutil.copy(save_path, target_path)
                        # st.info(f"Copied to user folder: {target_path}")
                    except Exception as e:
                        st.warning(f"Could not copy to user folder: {e}")
                # Offer YOLOv8 analysis if ultralytics is available (or show install hint)
                analyze_key = f"analyze_{filename}"
                if 'analyze_requested' not in st.session_state:
                    st.session_state['analyze_requested'] = False
                if st.button("Analyze captured image (YOLOv8)", key=analyze_key):
                    st.session_state['analyze_requested'] = True

                # previously-detected foods are stored in session state (display suppressed)

                if st.session_state.get('analyze_requested'):
                    def _analyze(path):
                        try:
                            from ultralytics import YOLO
                        except Exception as e:
                            st.error("Package 'ultralytics' not found. Install with: pip install ultralytics")
                            return None

                        try:
                            model = YOLO('yolov8n.pt')
                        except Exception:
                            # Model file will be downloaded automatically in many setups, but fail gracefully
                            try:
                                model = YOLO('yolov8n')
                            except Exception as ex:
                                st.error(f"Could not load YOLO model: {ex}")
                                return None

                        # Debug: show model labels available (helps determine if 'avocado' is supported)
                        # try:
                        #     names = getattr(model, 'names', None)
                        #     if names is not None:
                        #         if isinstance(names, dict):
                        #             label_list = [v.lower() for v in names.values()]
                        #         else:
                        #             label_list = [str(x).lower() for x in names]
                        #         st.write('Model labels:', label_list)
                        #         if 'avocado' in label_list:
                        #             st.info("Model includes label: 'avocado'")
                        #         else:
                        #             st.info("Model does not include label 'avocado' — consider using CLIP fallback or retraining for avocado detection.")
                        # except Exception:
                        #     pass

                        try:
                            results = model.predict(source=path, conf=0.25, imgsz=640, verbose=False)
                        except Exception as ex:
                            st.error(f"YOLO inference failed: {ex}")
                            return None

                        if not results:
                            st.info('No detections')
                            return None

                        r = results[0]
                        detections = []
                        try:
                            # Collect detections along with box coordinates when available
                            boxes = []
                            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                                label = model.names[int(cls)] if hasattr(model, 'names') else str(int(cls))
                                # convert box tensor to list of coords
                                try:
                                    coords = [int(x) for x in list(box)]
                                except Exception:
                                    try:
                                        coords = [int(x) for x in box.tolist()]
                                    except Exception:
                                        coords = None
                                detections.append((label, float(conf)))
                                boxes.append(coords)
                        except Exception:
                            # Fallback if result fields differ
                            boxes = []
                            if hasattr(r, 'boxes') and len(r.boxes) > 0:
                                for b in r.boxes:
                                    c = int(getattr(b, 'cls', 0))
                                    confv = float(getattr(b, 'conf', 0.0))
                                    label = model.names[c] if hasattr(model, 'names') else str(c)
                                    detections.append((label, confv))
                                    # best-effort coords
                                    try:
                                        coords = [int(x) for x in list(getattr(b, 'xyxy', []))]
                                    except Exception:
                                        coords = None
                                    boxes.append(coords)

                        # Annotated image
                        try:
                            annotated = r.plot()
                            from PIL import Image
                            import numpy as np
                            img = Image.fromarray(annotated.astype('uint8'))
                            ann_path = str(Path(path).with_name(Path(path).stem + '_annotated' + Path(path).suffix))
                            img.save(ann_path)
                        except Exception:
                            ann_path = None

                        # If the model does not include 'avocado', run a CLIP zero-shot fallback
                        # to classify crops and detect avocado (optional, requires 'clip' package).
                        try:
                            names = getattr(model, 'names', None)
                            model_label_list = []
                            if names is not None:
                                if isinstance(names, dict):
                                    model_label_list = [v.lower() for v in names.values()]
                                else:
                                    model_label_list = [str(x).lower() for x in names]
                        except Exception:
                            model_label_list = []

                        # CLIP fallback only if 'avocado' not supported by YOLO model
                        if 'avocado' not in model_label_list and boxes:
                            try:
                                import importlib
                                clip = importlib.import_module('clip')
                                torch = importlib.import_module('torch')
                                from PIL import Image

                                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                                clip_model, clip_preprocess = clip.load('ViT-B/32', device=device)

                                # candidate labels to check (lowercase)
                                candidates = ['avocado', 'apple', 'banana', 'orange', 'rice', 'bread', 'pasta', 'egg', 'tofu', 'cheese']
                                text_tokens = clip.tokenize(candidates).to(device)

                                pil_img = Image.open(path).convert('RGB')
                                # examine each box crop
                                for i, coords in enumerate(boxes):
                                    if not coords or len(coords) < 4:
                                        continue
                                    left, top, right, bottom = coords[0], coords[1], coords[2], coords[3]
                                    try:
                                        crop = pil_img.crop((left, top, right, bottom)).resize((224,224))
                                    except Exception:
                                        continue
                                    img_input = clip_preprocess(crop).unsqueeze(0).to(device)
                                    with torch.no_grad():
                                        logits_per_image, _ = clip_model(img_input, text_tokens)
                                        probs = logits_per_image.softmax(dim=-1).cpu().numpy()[0]
                                    # choose top candidate
                                    top_idx = int(probs.argmax())
                                    top_label = candidates[top_idx]
                                    top_prob = float(probs[top_idx])
                                    # if CLIP strongly believes it's an avocado, replace/add detection
                                    if top_label == 'avocado' and top_prob > 0.35:
                                        # update detections list to mark as avocado
                                        # replace label at same index (if exists)
                                        try:
                                            detections[i] = ('avocado', detections[i][1])
                                        except Exception:
                                            detections.append(('avocado', top_prob))
                            except Exception:
                                # CLIP not available or failed; suppress UI hint
                                pass

                        return detections, ann_path

                    # prefer persisted path (survives reruns) when available
                    path_to_analyze = st.session_state.get('last_capture_path', save_path)
                    result = _analyze(path_to_analyze)
                    if result is None:
                        # analysis failed or ultralytics missing
                        pass
                    else:
                        detections, ann = result

                        # Quick check: if none of the detected labels look like food, ask user to re-capture
                        FRUIT_LABELS = {'apple', 'banana', 'orange', 'grape', 'strawberry', 'lemon', 'lime', 'pineapple', 'mango', 'pear', 'peach', 'watermelon', 'kiwi', 'blueberry'}
                        food_candidates = set(['apple','banana','orange','sandwich','pizza','rice','bread','pasta','avocado','egg','tofu','cheese']) | FRUIT_LABELS

                        if not detections or not any(lab.lower() in food_candidates for lab, _ in detections):
                            st.warning("Please re-capture image with food items")
                            st.session_state['last_summary'] = {}
                            st.session_state['last_detections'] = detections
                        else:
                            # Map raw model labels to friendly food names (extend as needed)
                            FOOD_MAP = {
                                'apple': 'Apple',
                                'banana': 'Banana',
                                'orange': 'Orange',
                                'sandwich': 'Sandwich',
                                'pizza': 'Pizza',
                                'cup': 'Cup',
                                'bottle': 'Bottle',
                                'avocado': 'Avocado',
                                'rice': 'Rice',
                                'bread': 'Bread',
                                'pasta': 'Pasta',
                                'egg': 'Egg',
                                'tofu': 'Tofu',
                                'cheese': 'Cheese',
                                # add more mappings you care about
                            }

                            # Labels to ignore (non-food objects detected by model)
                            NON_FOOD = {'person', 'car', 'truck', 'dog', 'cat'}

                            # Define allowed food labels (only include these in summary)
                            FOOD_ALLOWED = set(k.lower() for k in FOOD_MAP.keys()) | FRUIT_LABELS | {'rice', 'bread', 'pasta', 'sandwich', 'pizza', 'avocado', 'egg', 'tofu', 'cheese'}

                            # Aggregate detections into summary: count + best confidence (only foods)
                            summary = {}
                            for label, score in detections:
                                raw = label.lower()
                                if raw in NON_FOOD:
                                    continue
                                if raw not in FOOD_ALLOWED:
                                    # skip non-food detections not in allowed list
                                    continue
                                name = FOOD_MAP.get(raw, raw.replace('_', ' ').title())
                                info = summary.get(name, {'count': 0, 'top_conf': 0.0})
                                info['count'] += 1
                                info['top_conf'] = max(info['top_conf'], float(score))
                                summary[name] = info

                            # persist last summary and detections so UI fallback can use them
                            st.session_state['last_summary'] = summary
                            st.session_state['last_detections'] = detections

                            # determine fruits from raw labels (ignore non-food and non-food-like detections)
                            detected_foods = []
                            for lab, sc in detections:
                                raw = lab.lower()
                                if raw in NON_FOOD or raw not in FOOD_ALLOWED:
                                    continue
                                detected_foods.append(FOOD_MAP.get(raw, raw.replace('_', ' ').title()))
                            st.session_state['detected_foods'] = sorted(set(detected_foods), key=lambda x: x.lower())

                            # Nutrition lookup used for per-item and totals
                            NUTRITION_DB = {
                                'apple': {'calories':95, 'protein':0.5, 'carbs':25, 'fat':0.3},
                                'banana': {'calories':105, 'protein':1.3, 'carbs':27, 'fat':0.4},
                                'orange': {'calories':62, 'protein':1.2, 'carbs':15.4, 'fat':0.2},
                                'rice': {'calories':205, 'protein':4.3, 'carbs':45, 'fat':0.4},
                                'brown rice': {'calories':216, 'protein':5, 'carbs':45, 'fat':1.8},
                                'bread': {'calories':79, 'protein':4, 'carbs':14, 'fat':1},
                                'whole wheat bread': {'calories':70, 'protein':4, 'carbs':12, 'fat':1},
                                'pasta': {'calories':131, 'protein':5, 'carbs':25, 'fat':1.1},
                                'avocado': {'calories':250, 'protein':3, 'carbs':12, 'fat':23},
                                'egg': {'calories':78, 'protein':6, 'carbs':0.6, 'fat':5},
                                'tofu': {'calories':76, 'protein':8, 'carbs':1.9, 'fat':4.8},
                                'cheese': {'calories':113, 'protein':7, 'carbs':1, 'fat':9},
                                'pizza': {'calories':266, 'protein':11, 'carbs':33, 'fat':10},
                                'sandwich': {'calories':250, 'protein':12, 'carbs':30, 'fat':8},
                            }

                            st.subheader('Detected Individual Food Items With Nutrition Info')
                            rows = []
                            for name, info in summary.items():
                                # find per-item nutrition using the same lookup as totals
                                lname = name.lower()
                                nut = None
                                if lname in NUTRITION_DB:
                                    nut = NUTRITION_DB[lname]
                                else:
                                    key = lname.replace('_', ' ')
                                    for k in NUTRITION_DB:
                                        if k in key or k in lname:
                                            nut = NUTRITION_DB[k]
                                            break
                                if nut is None:
                                    st.warning(f"Could not find nutrition info for item '{name}'")

                                per_cal = nut['calories']
                                per_pro = nut['protein']
                                per_car = nut['carbs']
                                per_fat = nut['fat']
                                total_cal = per_cal * info.get('count', 1)

                                rows.append({
                                    'Item': name,
                                    'Count': info['count'],
                                    # 'Top confidence': f"{info['top_conf']:.2f}",
                                    'Calories (each)': f"{int(per_cal)}",
                                    'Protein (g each)': f"{per_pro:.1f}",
                                    'Carbs (g each)': f"{per_car:.1f}",
                                    'Fat (g each)': f"{per_fat:.1f}",                                
                                    # 'Calories (total)': f"{int(total_cal)}",
                                })
                            st.table(rows)
                            st.markdown("**Food Items Present:** " + ", ".join(summary.keys()))

                            # Estimate nutrition (per-item averages) and show totals

                            totals = {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0}
                            for name, info in summary.items():
                                count = info.get('count', 1)
                                lname = name.lower()
                                # try exact match, then token match
                                nut = None
                                if lname in NUTRITION_DB:
                                    nut = NUTRITION_DB[lname]
                                else:
                                    key = lname.replace('_', ' ')
                                    for k in NUTRITION_DB:
                                        if k in key or k in lname:
                                            nut = NUTRITION_DB[k]
                                            break
                                if nut is None:
                                    nut = {'calories':150, 'protein':5, 'carbs':20, 'fat':7}

                                totals['calories'] += nut['calories'] * count
                                totals['protein'] += nut['protein'] * count
                                totals['carbs'] += nut['carbs'] * count
                                totals['fat'] += nut['fat'] * count

                            st.divider()
                            st.subheader('Estimated total nutrition for your meal')
                            # st.markdown(f"- Calories: **{int(totals['calories'])} kcal**")
                            # st.markdown(f"- Protein: **{totals['protein']:.1f} g**")
                            # st.markdown(f"- Carbohydrates: **{totals['carbs']:.1f} g**")
                            # st.markdown(f"- Fats: **{totals['fat']:.1f} g**")

                            table = [
                                {'Nutrient': 'Calories (kcal)', 'Total': f"{int(totals['calories'])}"},
                                {'Nutrient': 'Protein (g)', 'Total': f"{totals['protein']:.1f}"},
                                {'Nutrient': 'Carbohydrates (g)', 'Total': f"{totals['carbs']:.1f}"},
                                {'Nutrient': 'Fats (g)', 'Total': f"{totals['fat']:.1f}"},
                            ]
                            st.table(table)

                            # # also show raw detections for debugging/inspection (skip non-food)
                            # st.divider()
                            # st.subheader('Raw detections')
                            # for lab, conf in detections:
                            #     if lab.lower() in NON_FOOD:
                            #         continue
                            #     st.write(f"- {lab}: {conf:.2f}")

            except Exception as e:
                st.error(f"Could not save image: {e}")

            # end capture flow
    # Nutrition suggestion fallback / manual input UI (show whenever an image exists)
    if st.session_state.get('last_capture_path'):
        st.subheader('Nutrition suggestions')

        # Local copies of the vegetarian label sets (same logic as analyzer)
        PROTEIN_LABELS = {
            'tofu', 'tempeh', 'lentil', 'lentils', 'bean', 'beans', 'chickpea', 'chickpeas',
            'egg', 'eggs', 'yogurt', 'greek_yogurt', 'cheese', 'cottage_cheese', 'paneer',
            'seitan', 'quinoa', 'edamame', 'soy', 'nuts', 'almond', 'walnut', 'peanut'
        }
        CARB_LABELS = {
            'rice', 'brown_rice', 'bread', 'wholegrain_bread', 'pita', 'pasta', 'noodle', 'noodles',
            'potato', 'potatoes', 'sweet_potato', 'tortilla', 'wrap', 'oat', 'oats', 'cereal', 'bagel'
        }
        FAT_LABELS = {
            'avocado', 'butter', 'oil', 'olive_oil', 'margarine', 'cheese', 'peanut_butter',
            'nuts', 'almond', 'walnut', 'peanut', 'seeds', 'chia', 'flax', 'tahini'
        }

        last_summary = st.session_state.get('last_summary', {})
        last_detections = st.session_state.get('last_detections', [])

        # Build suggestions input: prefer detected summary items, else basic defaults
        detected_names = list(last_summary.keys()) if last_summary else []
        defaults = detected_names or ['Tofu', 'Rice', 'Avocado', 'Lentils', 'Bread', 'Cheese', 'Egg']

        options_pool = sorted(set(defaults + [d[0].replace('_', ' ').title() for d in last_detections]))
        selected = st.multiselect('Select food items present (or edit):', options=options_pool, default=detected_names or None, key='manual_selected_items')
        typed = st.text_input('Or type food items comma-separated (e.g. tofu, rice, avocado)', key='manual_typed_items')

        def parse_items(selected_list, typed_text):
            items = []
            for s in selected_list:
                items.append(s.lower())
            if typed_text:
                for p in typed_text.split(','):
                    p = p.strip()
                    if p:
                        items.append(p.lower())
            return items

        def _nutri_card(message, border_color="#5cf0f0", bg="#7ae688"):
            html = f"<div style='background:{bg};border:1px solid {border_color};padding:10px;border-radius:6px;margin:6px 0;color:#111'>{message}</div>"
            st.markdown(html, unsafe_allow_html=True)

        if st.button('Get nutrition recommendation', key='get_nutri_reco'):
            items = parse_items(st.session_state.get('manual_selected_items', []), st.session_state.get('manual_typed_items', ''))
            protein_present = any((it in PROTEIN_LABELS) or any(p in it for p in ('tofu','tempeh','lentil','bean','chick','egg','yogurt','cheese','paneer','quinoa','edamame','soy','nut')) for it in items)
            carb_present = any((it in CARB_LABELS) or any(p in it for p in ('rice','bread','pasta','potato','oat','noodle','tortilla')) for it in items)
            fat_present = any((it in FAT_LABELS) or any(p in it for p in ('avocado','butter','oil','nut','seed','peanut_butter')) for it in items)

            # show what is present
            present_groups = []
            if protein_present:
                present_groups.append('Protein')
            if carb_present:
                present_groups.append('Carbohydrates')
            if fat_present:
                present_groups.append('Fats')
            if present_groups:
                _nutri_card(f"<strong>Present:</strong> {' ,'.join(present_groups)}")

            if not protein_present:
                # Bold any suggested protein items the user has favorited
                fav_paths = st.session_state.get('favorites', [])
                fav_tokens = set()
                for p in fav_paths:
                    b = os.path.basename(p)
                    base = os.path.splitext(b)[0].lower()
                    for t in re.split(r'[^a-z0-9]+', base):
                        if t:
                            fav_tokens.add(t)

                protein_items = ['tofu', 'tempeh', 'boiled egg', 'lentils', 'chickpeas', 'beans', 'Greek yogurt', 'cottage cheese', 'paneer', 'quinoa', 'nuts', 'seeds']

                def _format_and_join(item_list):
                    parts = []
                    for it in item_list:
                        norm = re.sub(r'[^a-z0-9]+', ' ', it.lower())
                        tokens = norm.split()
                        bold = any(t in fav_tokens for t in tokens)
                        parts.append(f"<strong>{it}</strong>" if bold else it)
                    return ', '.join(parts)

                _nutri_card(f"Add more vegetarian protein like: {_format_and_join(protein_items)}.")
            if not carb_present:
                carb_items = ['brown rice', 'quinoa', 'whole wheat bread', 'oats', 'pasta', 'potatoes', 'sweet potatoes']
                # reuse _format_and_join defined above (ensure fav_tokens defined even if protein_present)
                try:
                    _format_and_join
                except NameError:
                    fav_paths = st.session_state.get('favorites', [])
                    fav_tokens = set()
                    for p in fav_paths:
                        b = os.path.basename(p)
                        base = os.path.splitext(b)[0].lower()
                        for t in re.split(r'[^a-z0-9]+', base):
                            if t:
                                fav_tokens.add(t)
                    def _format_and_join(item_list):
                        parts = []
                        for it in item_list:
                            norm = re.sub(r'[^a-z0-9]+', ' ', it.lower())
                            tokens = norm.split()
                            bold = any(t in fav_tokens for t in tokens)
                            parts.append(f"<strong>{it}</strong>" if bold else it)
                        return ', '.join(parts)

                _nutri_card(f"Add healthy carbohydrates like: {_format_and_join(carb_items)}.")
            if not fat_present:
                fat_items = ['avocado', 'olive oil', 'nuts', 'seeds', 'peanut butter', 'tahini', 'butter']
                try:
                    _format_and_join
                except NameError:
                    fav_paths = st.session_state.get('favorites', [])
                    fav_tokens = set()
                    for p in fav_paths:
                        b = os.path.basename(p)
                        base = os.path.splitext(b)[0].lower()
                        for t in re.split(r'[^a-z0-9]+', base):
                            if t:
                                fav_tokens.add(t)
                    def _format_and_join(item_list):
                        parts = []
                        for it in item_list:
                            norm = re.sub(r'[^a-z0-9]+', ' ', it.lower())
                            tokens = norm.split()
                            bold = any(t in fav_tokens for t in tokens)
                            parts.append(f"<strong>{it}</strong>" if bold else it)
                        return ', '.join(parts)

                _nutri_card(f"Add healthy fats like: {_format_and_join(fat_items)}.")

            if protein_present and carb_present and fat_present:
                _nutri_card('Your meal contains a good balance of protein, carbohydrates, and fats! Well done! 🍽️✅', border_color='#4CAF50')

            # Also estimate totals for the selected/typed items (combine foods together)
            if items:
                # small nutrition lookup similar to YOLO block
                NUTRITION_DB = {
                    'apple': {'calories':95, 'protein':0.5, 'carbs':25, 'fat':0.3},
                    'banana': {'calories':105, 'protein':1.3, 'carbs':27, 'fat':0.4},
                    'orange': {'calories':62, 'protein':1.2, 'carbs':15.4, 'fat':0.2},
                    'rice': {'calories':205, 'protein':4.3, 'carbs':45, 'fat':0.4},
                    'brown rice': {'calories':216, 'protein':5, 'carbs':45, 'fat':1.8},
                    'bread': {'calories':79, 'protein':4, 'carbs':14, 'fat':1},
                    'whole wheat bread': {'calories':70, 'protein':4, 'carbs':12, 'fat':1},
                    'pasta': {'calories':131, 'protein':5, 'carbs':25, 'fat':1.1},
                    'avocado': {'calories':250, 'protein':3, 'carbs':12, 'fat':23},
                    'egg': {'calories':78, 'protein':6, 'carbs':0.6, 'fat':5},
                    'tofu': {'calories':76, 'protein':8, 'carbs':1.9, 'fat':4.8},
                    'cheese': {'calories':113, 'protein':7, 'carbs':1, 'fat':9},
                    'pizza': {'calories':266, 'protein':11, 'carbs':33, 'fat':10},
                    'sandwich': {'calories':250, 'protein':12, 'carbs':30, 'fat':8},
                }

                totals = {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0}
                for it in items:
                    name = it.strip().lower()
                    if not name:
                        continue
                    nut = None
                    if name in NUTRITION_DB:
                        nut = NUTRITION_DB[name]
                    else:
                        key = name.replace('_', ' ')
                        for k in NUTRITION_DB:
                            if k in key or k in name:
                                nut = NUTRITION_DB[k]
                                break
                    if nut is None:
                        nut = {'calories':150, 'protein':5, 'carbs':20, 'fat':7}
                    totals['calories'] += nut['calories']
                    totals['protein'] += nut['protein']
                    totals['carbs'] += nut['carbs']
                    totals['fat'] += nut['fat']

                st.divider()
                st.subheader('Estimated total nutrition of scanned items')
                st.markdown(f"- Calories: **{int(totals['calories'])} kcal**")
                st.markdown(f"- Protein: **{totals['protein']:.1f} g**")
                st.markdown(f"- Carbohydrates: **{totals['carbs']:.1f} g**")
                st.markdown(f"- Fats: **{totals['fat']:.1f} g**")

    st.divider()


if __name__ == "__main__":
    render()




