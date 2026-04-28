import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pathlib
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("Dew Point – Analisi per scelta diluizione")

# -----------------------------
# Stato iniziale
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "show_options" not in st.session_state:
    st.session_state.show_options = False

if "temp_margin" not in st.session_state:
    st.session_state.temp_margin = 2.0

if "humidity_margin" not in st.session_state:
    st.session_state.humidity_margin = 15

DOC_PATH = pathlib.Path(__file__).parent / "documentation.html"
has_doc = DOC_PATH.exists()

# -----------------------------
# MENU A SINISTRA (sidebar)
# -----------------------------
page = st.sidebar.radio(
    "Menu",
    ["Home", "Documentazione"],
    index=0 if st.session_state.page == "Home" else 1,
)

st.session_state.page = page

# -----------------------------
# DOCUMENTAZIONE (pura)
# -----------------------------
if st.session_state.page == "Documentazione":
    if has_doc:
        html = DOC_PATH.read_text(encoding="utf-8")
        components.html(html, height=900, scrolling=True)
    else:
        st.error("File documentation.html non trovato.")
    st.stop()

# -----------------------------
# HOME — DA QUI IN POI LA TUA APP RESTA IDENTICA
# -----------------------------

# Pulsante Opzioni
if st.button("Opzioni"):
    st.session_state.show_options = not st.session_state.show_options

if st.session_state.show_options:
    st.markdown("### Margini di sicurezza")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.temp_margin = st.number_input(
            "Margine temperatura (°C)",
            0.0, 10.0,
            float(st.session_state.temp_margin),
            0.5
        )
    with col2:
        st.session_state.humidity_margin = st.number_input(
            "Margine umidità (%)",
            0, 100,
            int(st.session_state.humidity_margin),
            1
        )

temp_margin = float(st.session_state.temp_margin)
humidity_margin = int(st.session_state.humidity_margin)

# -----------------------------
# Parametri di calcolo (TUOI, INVARIATI)
# -----------------------------
st.subheader("Parametri di calcolo")

col1, col2, col3 = st.columns(3)
with col1:
    T_EXT = st.slider("Temperatura esterna (°C)", 0, 40, 20, 1)
    T_min = st.slider("Temperatura minima trasporto (°C)", 0, 40, 5, 1)
with col2:
    T_camino = st.slider("Temperatura camino (°C)", 0, 200, 100, 5)
    RH = st.slider("Umidità relativa (%)", 5, 99, 50, 5)
with col3:
    Dil = st.number_input("Diluizione", 1.0, 10.0, 2.0, 0.2)
    HR_min_stimata = st.number_input("Umidità minima stimata (%)", 0, 100, 40, 5)

# -----------------------------
# Funzione dew point (TUA, INVARIATA)
# -----------------------------
def dew_point(T_ext, T_cam, RH, Dil):
    term = ((RH * 100 / Dil) / 100) * (
        6.11 * 10 ** (
            (7.5 * (T_cam * (100 / Dil) + T_ext * (100 - 100 / Dil)) / 100) /
            (237.7 + (T_cam * (100 / Dil) + T_ext * (100 - 100 / Dil)) / 100)
        )
    )
    return (-430.22 + 237.7 * np.log(term / 100)) / (-np.log(term / 100) + 19.08)

DP_current = dew_point(T_EXT, T_camino, RH, Dil)

# -----------------------------
# Conformità (TUA, INVARIATA)
# -----------------------------
conform_istantanea = DP_current < T_EXT
conform_trasporto = DP_current < (T_min - temp_margin)
RH_post_dil = RH / Dil
soglia_umidita = RH_post_dil + humidity_margin
conform_umidita = HR_min_stimata >= soglia_umidita
score = int(conform_istantanea) + int(conform_trasporto) + int(conform_umidita)

# -----------------------------
# Suggeritore (TUO, INVARIATO)
# -----------------------------
def suggerisci_diluizione():
    best = None
    for d in np.arange(1.0, 10.01, 0.1):
        dp = dew_point(T_EXT, T_camino, RH, d)
        s = int(dp < T_EXT) + int(dp < (T_min - temp_margin)) + int(HR_min_stimata >= (RH / d + humidity_margin))
        if s == 3:
            return round(d, 1), s, dp
        if best is None or s > best[1]:
            best = (round(d, 1), s, dp)
    return best

Dil_suggerita, score_suggerita, DP_suggerito = suggerisci_diluizione()

# -----------------------------
# Box conformità e suggeritore (TUO, INVARIATO)
# -----------------------------
colA, colB = st.columns(2)

with colA:
    st.markdown(f"""
    ### Conformità
    **Dew Point calcolato:** {DP_current:.2f} °C  
    **Conformità istantanea:** {'✔' if conform_istantanea else '✘'}  
    **Conformità trasporto:** {'✔' if conform_trasporto else '✘'}  
    **Conformità umidità:** {'✔' if conform_umidita else '✘'}  
    **Totale:** {score}/3
    """)

with colB:
    st.markdown(f"""
    ### Suggeritore diluizione
    **Diluizione suggerita:** {Dil_suggerita}  
    **Dew Point previsto:** {DP_suggerito:.2f} °C  
    """)

# -----------------------------
# Grafico (TUO, INVARIATO)
# -----------------------------
Dil_values = np.arange(1.0, 10.01, 0.2)

asse_x = st.selectbox("Seleziona asse X (Grafico)", ["Diluizione", "RH", "T_camino", "T_EXT"])

if asse_x == "Diluizione":
    X_values = Dil_values
    DP_vs_X = np.array([dew_point(T_EXT, T_camino, RH, d) for d in X_values])
    x_label = "Diluizione"
    X_current = Dil
elif asse_x == "RH":
    X_values = np.arange(5, 100, 5)
    DP_vs_X = np.array([dew_point(T_EXT, T_camino, rh, Dil) for rh in X_values])
    x_label = "Umidità (%)"
    X_current = RH
elif asse_x == "T_camino":
    X_values = np.arange(0, 200, 5)
    DP_vs_X = np.array([dew_point(T_EXT, t, RH, Dil) for t in X_values])
    x_label = "T camino (°C)"
    X_current = T_camino
else:
    X_values = np.arange(0, 40, 5)
    DP_vs_X = np.array([dew_point(t, T_camino, RH, Dil) for t in X_values])
    x_label = "T esterna (°C)"
    X_current = T_EXT

fig = go.Figure()
fig.add_trace(go.Scatter(x=X_values, y=DP_vs_X, mode="lines", line=dict(color="blue", width=3)))
fig.add_trace(go.Scatter(x=[X_current], y=[DP_current], mode="markers", marker=dict(size=12, color="black")))

fig.update_layout(
    xaxis_title=x_label,
    yaxis_title="Temperatura (°C)",
    template="plotly_white",
    height=500
)

st.plotly_chart(fig, use_container_width=True)
