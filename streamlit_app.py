# app.py
# Dew Point – Analisi per scelta diluizione
# Top horizontal menu with exactly two boxes: Home (default) and Documentazione.
# When Documentazione is selected the app shows the raw HTML file (documentation.html)
# below the menu and hides the rest of the UI. To return, click Home.

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pathlib
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("Dew Point – Analisi per scelta diluizione")

# -----------------------------
# Paths and initial state
# -----------------------------
DOC_PATH = pathlib.Path(__file__).parent / "documentation.html"
has_doc = DOC_PATH.exists()

if "page" not in st.session_state:
    st.session_state.page = "Home"  # default

if "temp_margin" not in st.session_state:
    st.session_state.temp_margin = 2.0
if "humidity_margin" not in st.session_state:
    st.session_state.humidity_margin = 15
if "show_options" not in st.session_state:
    st.session_state.show_options = False

# -----------------------------
# Simple CSS to render two horizontal "boxes" that act like a menu
# -----------------------------
st.markdown(
    """
    <style>
    .menu-row { display:flex; gap:12px; align-items:center; margin-bottom:14px; }
    .menu-box {
      padding:10px 20px;
      border-radius:10px;
      cursor:pointer;
      font-weight:700;
      border:2px solid #e6e6e6;
      background:#ffffff;
      color:#0b3d91;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
      min-width:160px;
      text-align:center;
      user-select:none;
    }
    .menu-box:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(11,61,145,0.06); }
    .menu-box.active {
      background: linear-gradient(180deg,#0b5ed7,#084bb5);
      color: #fff;
      border-color: rgba(8,75,181,0.9);
    }
    @media (max-width: 640px) {
      .menu-row { flex-direction: column; gap:8px; }
      .menu-box { min-width: auto; width:100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Render the two menu boxes and wire them to session_state.page
# We use Streamlit buttons (one per box) so clicks update state reliably.
# -----------------------------
menu_cols = st.columns([1, 1, 8])
with menu_cols[0]:
    if st.button("Home"):
        st.session_state.page = "Home"
with menu_cols[1]:
    # If documentation file is missing, still show the box but disable action
    if has_doc:
        if st.button("Documentazione"):
            st.session_state.page = "Documentazione"
    else:
        # show a visually identical disabled button (no extra buttons elsewhere)
        st.button("Documentazione (manca)", disabled=True)

# Visual highlight of active box (purely cosmetic)
# We re-render a small HTML row showing which is active (keeps only two boxes visible)
active_home = "active" if st.session_state.page == "Home" else ""
active_doc  = "active" if st.session_state.page == "Documentazione" else ""
st.markdown(
    f"""
    <div class="menu-row" aria-hidden="true">
      <div class="menu-box {active_home}">Home</div>
      <div class="menu-box {active_doc}">Documentazione</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# If Documentazione selected: show raw HTML (pure) and stop further UI rendering
# The top menu remains (so user can click Home to return).
# -----------------------------
if st.session_state.page == "Documentazione":
    if has_doc:
        html = DOC_PATH.read_text(encoding="utf-8")
        # Render the HTML as-is (MathJax included in the file will work)
        components.html(html, height=900, scrolling=True)
    else:
        st.error("File documentation.html non trovato nella cartella dell'app.")
    st.stop()  # do not render any other UI when in Documentazione

# -----------------------------
# HOME: main application UI (Opzioni più in basso come richiesto)
# -----------------------------

# Opzioni (pulsante mostrato nella sezione Home, non in alto)
opt_col1, opt_col2 = st.columns([1, 8])
with opt_col1:
    if st.button("Opzioni"):
        st.session_state.show_options = not st.session_state.show_options

if st.session_state.show_options:
    with st.container():
        st.markdown("**Margini di sicurezza (persistenti)**")
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            st.session_state.temp_margin = st.number_input(
                "Margine temperatura (°C)",
                min_value=0.0, max_value=10.0,
                value=float(st.session_state.temp_margin),
                step=0.5, format="%.1f",
                key="temp_margin_input"
            )
        with col_o2:
            st.session_state.humidity_margin = st.number_input(
                "Margine umidità (%)",
                min_value=0, max_value=100,
                value=int(st.session_state.humidity_margin),
                step=1,
                key="humidity_margin_input"
            )

temp_margin = float(st.session_state.temp_margin)
humidity_margin = int(st.session_state.humidity_margin)

# -----------------------------
# Input controls
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
    Dil = st.number_input("Diluizione", min_value=1.0, max_value=10.0, value=2.0, step=0.2, format="%.1f")
    HR_min_stimata = st.number_input("Umidità minima stimata (%)", min_value=0, max_value=100, value=40, step=5)

# -----------------------------
# Dew point function and calculations
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
conform_istantanea = DP_current < T_EXT
conform_trasporto = DP_current < (T_min - temp_margin)
RH_post_dil = RH / Dil
soglia_umidita = RH_post_dil + humidity_margin
conform_umidita = HR_min_stimata >= soglia_umidita
score = int(conform_istantanea) + int(conform_trasporto) + int(conform_umidita)

# Suggeritore
def suggerisci_diluizione():
    candidates = []
    for d in np.arange(1.0, 10.01, 0.1):
        dp = dew_point(T_EXT, T_camino, RH, d)
        c1 = dp < T_EXT
        c2 = dp < (T_min - temp_margin)
        c3 = HR_min_stimata >= (RH / d + humidity_margin)
        s = int(c1) + int(c2) + int(c3)
        candidates.append((round(d, 1), int(s), float(dp)))
        if s == 3:
            return round(d, 1), int(s), float(dp)
    candidates.sort(key=lambda x: (-int(x[1]), x[0]))
    return candidates[0]

Dil_suggerita, score_suggerita, DP_suggerito = suggerisci_diluizione()

# -----------------------------
# Conformità box and suggeritore
# -----------------------------
col_box_left, col_box_right = st.columns([1, 1])
with col_box_left:
    bg_color = "#d4edda" if DP_current < T_min else ("#fff3cd" if DP_current < T_EXT else "#f8d7da")
    border_color = "#28a745" if DP_current < T_min else ("#ffc107" if DP_current < T_EXT else "#dc3545")
    conform_html = f"""
    <div style="
        padding:14px;
        border-radius:10px;
        background-color:{bg_color};
        border:2px solid {border_color};
        font-size:15px;
        line-height:1.5;">
      <h4 style="margin:0 0 8px 0;">Conformità</h4>
      <p style="margin:6px 0;"><strong>Dew Point calcolato:</strong> {DP_current:.2f} °C</p>
      <p style="margin:6px 0;"><strong>Conformità istantanea</strong> (DP &lt; T_EXT = {T_EXT} °C):
        <span style="font-weight:bold; color:{'green' if conform_istantanea else 'red'};">{'✔' if conform_istantanea else '✘'}</span>
      </p>
      <p style="margin:6px 0;"><strong>Conformità trasporto</strong> (DP &lt; T_min - {temp_margin} = {T_min - temp_margin} °C):
        <span style="font-weight:bold; color:{'green' if conform_trasporto else 'red'};">{'✔' if conform_trasporto else '✘'}</span>
      </p>
      <p style="margin:6px 0;"><strong>Conformità umidità</strong> (HR_min ≥ RH/Dil + {humidity_margin}% = {soglia_umidita:.1f}%):
        <span style="font-weight:bold; color:{'green' if conform_umidita else 'red'};">{'✔' if conform_umidita else '✘'}</span>
      </p>
      <hr style="margin:10px 0;">
      <p style="margin:6px 0;"><strong>Conformità soddisfatte:</strong> {score} / 3</p>
    </div>
    """
    st.markdown(conform_html, unsafe_allow_html=True)

with col_box_right:
    suggeritore_html = f"""
    <div style="
        padding:14px;
        border-radius:10px;
        background-color:#f7f7f7;
        border:1px solid #ddd;
        font-size:15px;
        line-height:1.5;">
      <h4 style="margin:0 0 8px 0;">Suggeritore diluizione</h4>
      <p style="margin:6px 0;"><strong>Diluizione suggerita:</strong> {Dil_suggerita:.1f}</p>
      <p style="margin:6px 0;"><strong>Dew Point previsto:</strong> {DP_suggerito:.2f} °C</p>
      <hr style="margin:10px 0;">
      <p style="margin:6px 0;"><strong>Parametri usati:</strong></p>
      <p style="margin:4px 0;">Margine temperatura: {temp_margin} °C</p>
      <p style="margin:4px 0;">Margine umidità: {humidity_margin} %</p>
    </div>
    """
    st.markdown(suggeritore_html, unsafe_allow_html=True)

# -----------------------------
# Grafico principale (asse X default = Diluizione)
# -----------------------------
green_fill  = 'rgba(40,167,69,0.25)'
yellow_fill = 'rgba(255,193,7,0.30)'
red_fill    = 'rgba(220,50,50,0.35)'

Dil_values = np.arange(1.0, 10.01, 0.2)

with st.container():
    asse_x = st.selectbox("Seleziona asse X (Grafico)", ["Diluizione", "RH", "T_camino", "T_EXT"], index=0)
    if asse_x == "Diluizione":
        X_values = Dil_values
        DP_vs_X = np.array([dew_point(T_EXT, T_camino, RH, d) for d in X_values])
        x_label = "Diluizione"
        X_current = Dil
    elif asse_x == "RH":
        X_values = np.arange(5, 100, 5)
        DP_vs_X = np.array([dew_point(T_EXT, T_camino, rh, Dil) for rh in X_values])
        x_label = "Umidità relativa (%)"
        X_current = RH
    elif asse_x == "T_camino":
        X_values = np.arange(0, 201, 5)
        DP_vs_X = np.array([dew_point(T_EXT, tcam, RH, Dil) for tcam in X_values])
        x_label = "Temperatura camino (°C)"
        X_current = T_camino
    else:
        X_values = np.arange(0, 41, 5)
        DP_vs_X = np.array([dew_point(text, T_camino, RH, Dil) for text in X_values])
        x_label = "Temperatura esterna (°C)"
        X_current = T_EXT

    y_min = min(DP_vs_X.min(), T_EXT, T_min) - 5
    y_max = max(DP_vs_X.max(), T_EXT, T_min) + 5

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.concatenate([X_values, X_values[::-1]]),
        y=np.concatenate([[T_min]*len(X_values), [y_min]*len(X_values)]),
        fill='toself', fillcolor=green_fill, line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip', name="Zona sicura (sotto T_min)"
    ))
    fig.add_trace(go.Scatter(
        x=np.concatenate([X_values, X_values[::-1]]),
        y=np.concatenate([[T_EXT]*len(X_values), [T_min]*len(X_values)]),
        fill='toself', fillcolor=yellow_fill, line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip', name="Zona rischio (tra T_min e T_EXT)"
    ))
    fig.add_trace(go.Scatter(
        x=np.concatenate([X_values, X_values[::-1]]),
        y=np.concatenate([[y_max]*len(X_values), [T_EXT]*len(X_values)]),
        fill='toself', fillcolor=red_fill, line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip', name="Zona condensa (sopra T_EXT)"
    ))
    fig.add_trace(go.Scatter(x=X_values, y=DP_vs_X, mode="lines", line=dict(color="blue", width=3), name="Curva Dew Point"))
    fig.add_trace(go.Scatter(x=[X_values.min(), X_values.max()], y=[DP_current, DP_current], mode="lines",
                             line=dict(color="blue", width=2, dash="dash"), name="Dew Point attuale (DP_current)"))
    fig.add_trace(go.Scatter(x=[X_values.min(), X_values.max()], y=[T_min, T_min], mode="lines",
                             line=dict(color="black", width=2, dash="dash"), name="Temperatura minima trasporto (T_min)"))
    fig.add_trace(go.Scatter(x=[X_values.min(), X_values.max()], y=[T_EXT, T_EXT], mode="lines",
                             line=dict(color="orange", width=2, dash="dash"), name="Temperatura esterna attuale (T_EXT)"))
    fig.add_trace(go.Scatter(x=[X_current], y=[DP_current], mode="markers", marker=dict(size=12, color="black"), name="Punto attuale"))

    fig.update_layout(xaxis_title=x_label, yaxis_title="Temperatura (°C)",
                      yaxis=dict(range=[y_min, y_max]), template="plotly_white",
                      title="Grafico", margin=dict(t=40, b=40, l=40, r=20),
                      legend=dict(title="Legenda (consultazione)", orientation="v"))

    st.plotly_chart(fig, use_container_width=True)
