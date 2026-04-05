import streamlit as st
import pandas as pd
import os
from datetime import datetime
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# ---------------------------
# configurare pagina
# ---------------------------
st.set_page_config(page_title="Sesizari urbane RM Valcea", layout="wide")

# ---------------------------
# constante
# ---------------------------
FISIER_DATE = "sesizari.csv"
FOLDER_POZE = "poze"
CENTRU_LAT = 45.1047
CENTRU_LON = 24.3756
OPTIUNI = ["Parcare neregulamentara", "Deseuri", "Gropi", "Iluminat", "Alta"]

os.makedirs(FOLDER_POZE, exist_ok=True)

# ---------------------------
# functie simpla de clasificare
# ---------------------------
def clasifica(text):
    text = text.lower()

    if "masina" in text or "parcat" in text or "trotuar" in text:
        return "Parcare neregulamentara"
    elif "gunoi" in text or "deseu" in text or "gunoaie" in text or "tomberon" in text:
        return "Deseuri"
    elif "groapa" in text or "asfalt" in text or "drum" in text:
        return "Gropi"
    elif "lumina" in text or "bec" in text or "iluminat" in text:
        return "Iluminat"
    else:
        return "Alta"

# ---------------------------
# functie salvare poza
# ---------------------------
def salveaza_fisier(uploaded_file, prefix="img"):
    if uploaded_file is None:
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nume_fisier = f"{prefix}_{timestamp}_{uploaded_file.name}"
    cale = os.path.join(FOLDER_POZE, nume_fisier)

    with open(cale, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return nume_fisier

# ---------------------------
# session state
# ---------------------------
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None

if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None

if "geo_requested" not in st.session_state:
    st.session_state.geo_requested = False

# ---------------------------
# titlu
# ---------------------------
st.title("Platforma de sesizari urbane - Rm. Valcea")
st.write("Completeaza formularul, selecteaza locatia pe harta si adauga optional o fotografie.")

# ---------------------------
# layout
# ---------------------------
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Formular sesizare")

    descriere = st.text_area("Descriere problema")

    if descriere.strip():
        categorie_sugerata = clasifica(descriere)
        st.info(f"Categorie sugerata de AI: {categorie_sugerata}")
    else:
        categorie_sugerata = "Alta"

    categorie = st.selectbox(
        "Categorie finala",
        OPTIUNI,
        index=OPTIUNI.index(categorie_sugerata)
    )

    st.markdown("### Fotografie")

    poza_upload = st.file_uploader(
        "Incarca o fotografie",
        type=["jpg", "jpeg", "png"]
    )

    poza_camera = st.camera_input("Sau fa o poza direct")

    if poza_upload is not None:
        st.image(poza_upload, caption="Fotografie incarcata", use_container_width=True)

    if poza_camera is not None:
        st.image(poza_camera, caption="Fotografie facuta cu camera", use_container_width=True)

    st.markdown("### Localizare")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Foloseste locatia mea"):
            st.session_state.geo_requested = True

    with c2:
        if st.button("Sterge punctul selectat"):
            st.session_state.selected_lat = None
            st.session_state.selected_lon = None
            st.session_state.geo_requested = False
            st.rerun()

    if st.session_state.geo_requested:
        locatie = get_geolocation()

        if locatie and "coords" in locatie:
            st.session_state.selected_lat = locatie["coords"]["latitude"]
            st.session_state.selected_lon = locatie["coords"]["longitude"]
            st.success("Locatia telefonului/browserului a fost preluata.")
            st.session_state.geo_requested = False
            st.rerun()
        else:
            st.warning("Permite accesul la locatie si apasa din nou butonul.")

    if st.session_state.selected_lat is not None and st.session_state.selected_lon is not None:
        st.success(
            f"Locatie selectata: lat {st.session_state.selected_lat:.6f}, "
            f"lon {st.session_state.selected_lon:.6f}"
        )
    else:
        st.warning("Selecteaza un punct pe harta sau foloseste locatia mea.")

with col2:
    st.subheader("Harta")

    centru_harta = [CENTRU_LAT, CENTRU_LON]
    zoom_harta = 13

    if st.session_state.selected_lat is not None and st.session_state.selected_lon is not None:
        centru_harta = [st.session_state.selected_lat, st.session_state.selected_lon]
        zoom_harta = 16

    m = folium.Map(location=centru_harta, zoom_start=zoom_harta)

    if os.path.exists(FISIER_DATE):
        df_harta = pd.read_csv(FISIER_DATE)
        for _, rand in df_harta.iterrows():
            try:
                lat = float(rand["latitudine"])
                lon = float(rand["longitudine"])
                popup_text = f"{rand['categorie_finala']} - {rand['descriere']}"
                folium.Marker(
                    [lat, lon],
                    popup=popup_text,
                    tooltip=rand["categorie_finala"]
                ).add_to(m)
            except:
                pass

    if st.session_state.selected_lat is not None and st.session_state.selected_lon is not None:
        folium.Marker(
            [st.session_state.selected_lat, st.session_state.selected_lon],
            popup="Locatia selectata",
            tooltip="Locatia selectata",
            icon=folium.Icon(icon="info-sign")
        ).add_to(m)

    map_data = st_folium(m, width=800, height=550, returned_objects=["last_clicked"])

# click pe harta
if map_data and map_data.get("last_clicked"):
    click_lat = map_data["last_clicked"]["lat"]
    click_lon = map_data["last_clicked"]["lng"]

    if (
        st.session_state.selected_lat != click_lat
        or st.session_state.selected_lon != click_lon
    ):
        st.session_state.selected_lat = click_lat
        st.session_state.selected_lon = click_lon
        st.rerun()

# trimitere sesizare
st.markdown("---")

if st.button("Trimite sesizarea"):
    if not descriere.strip():
        st.error("Completeaza descrierea problemei.")
    elif st.session_state.selected_lat is None or st.session_state.selected_lon is None:
        st.error("Selecteaza locatia pe harta sau foloseste locatia mea.")
    else:
        nume_poza = ""

        # prioritate: poza facuta cu camera, apoi poza uploadata
        if poza_camera is not None:
            nume_poza = salveaza_fisier(poza_camera, prefix="camera")
        elif poza_upload is not None:
            nume_poza = salveaza_fisier(poza_upload, prefix="upload")

        date_noi = pd.DataFrame([{
            "data_raportare": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "descriere": descriere,
            "categorie_sugerata_ai": categorie_sugerata,
            "categorie_finala": categorie,
            "latitudine": st.session_state.selected_lat,
            "longitudine": st.session_state.selected_lon,
            "fotografie": nume_poza
        }])

        if os.path.exists(FISIER_DATE):
            date_existente = pd.read_csv(FISIER_DATE)
            date_finale = pd.concat([date_existente, date_noi], ignore_index=True)
        else:
            date_finale = date_noi

        date_finale.to_csv(FISIER_DATE, index=False)

        st.success("Sesizarea a fost salvata cu succes!")

        st.session_state.selected_lat = None
        st.session_state.selected_lon = None
        st.rerun()

# tabel cu sesizari
if os.path.exists(FISIER_DATE):
    st.markdown("---")
    st.subheader("Sesizari salvate")
    df = pd.read_csv(FISIER_DATE)
    st.dataframe(df, use_container_width=True)
