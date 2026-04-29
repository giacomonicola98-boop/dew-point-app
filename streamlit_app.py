import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pathlib
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# -----------------------------
# Inizializza session_state
# -----------------------------
if "show_options" not in st.session_state:
    st.session_state.show_options = False
if "temp_margin" not in st.session_state:
    st.session_state.temp_margin = 2.0
if "humidity_margin" not in st.session_state:
    st.session_state.humidity_margin = 15

# -----------------------------
# Funzione dew point
# -----------------------------
def dew_point(T_ext, T_cam, RH, Dil):
    term = ((RH * 100 / Dil) / 100) * (
        6.11 * 10 ** (
            (7.5 * (T_cam * (100 / Dil) + T_ext * (100 - 100 / Dil)) / 100) /
            (237.7 + (T_cam * (100 / Dil) + T_ext * (100 - 100 / Dil)) / 100)
        )
    )
    return (-430.22 + 237.7 * np.log(term / 100)) / (-np.log(term / 100) + 19.08)

# -----------------------------
# Sidebar — menu di navigazione
# -----------------------------
doc_path = pathlib.Path(__file__).parent / "documentation.html"
has_doc = doc_path.exists()

with st.sidebar:
    st.markdown("## Menu")
    page = st.radio("", ["🏠 Home", "📄 Documentation"], label_visibility="collapsed")

# ==============================
# PAGINA: DOCUMENTATION
# ==============================
if page == "📄 Documentation":
    if has_doc:
        html_content = doc_path.read_text(encoding="utf-8")
        # Rimuove padding Streamlit e mostra solo l'HTML a piena pagina
        st.markdown("""
            <style>
                /* Nascondi titolo app e padding principale */
                .block-container {
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                    max-width: 100% !important;
                }
                header[data-testid="stHeader"] {
                    display: none !important;
                }
            </style>
        """, unsafe_allow_html=True)
        components.html(html_content, height=950, scrolling=True)
    else:
        st.warning("⚠️ File `documentation.html` non trovato nella stessa cartella dello script.")
        st.info("Carica il file `documentation.html` nella stessa directory di `streamlit_app.py` su GitHub.")
    st.stop()

# ==============================
# PAGINA: HOME
# ==============================
st.title("DewPoint e scelta diluizione")
st.header("Per campionamento secondo UNI EN 13725")

# -----------------------------
# Pulsante Opzioni
# -----------------------------
col_opt, _ = st.columns([1, 5])
with col_opt:
    if st.button("⚙️ Opzioni"):
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
# PARAMETRI — 6 colonne compatte
# -----------------------------
st.subheader("Parametri di calcolo")

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    T_ext = st.slider("T esterna (°C)", 0, 40, 20, 1)
with c2:
    T_min_stimata = st.slider("T min trasporto stimata(°C)", 0, 40, 5, 1)
with c3:
    T_camino = st.slider("T camino (°C)", 0, 200, 100, 1)
with c4:
    RH = st.slider("Umidità rel. (%)", 5, 99, 50, 5)
with c5:
    Dil = st.number_input("Diluizione", min_value=1.0, max_value=10.0, value=2.0, step=0.2, format="%.1f")
with c6:
    HR_min_stimata = st.number_input("UR min stimata (%)", min_value=0, max_value=100, value=40, step=5)

# -----------------------------
# CALCOLI
# -----------------------------
DP_current = dew_point(T_ext, T_camino, RH, Dil)

conform_istantanea = DP_current < T_ext
conform_trasporto  = DP_current < (T_min_stimata - temp_margin)
RH_post_dil        = RH / Dil
soglia_umidita     = RH_post_dil + humidity_margin
conform_umidita    = HR_min_stimata >= soglia_umidita
score              = int(conform_istantanea) + int(conform_trasporto) + int(conform_umidita)

# -----------------------------
# SUGGERITORE
# -----------------------------
def suggerisci_diluizione():
    candidates = []
    for d in np.arange(1.0, 10.01, 0.1):
        dp = dew_point(T_ext, T_camino, RH, d)
        c1 = dp < T_ext
        c2 = dp < (T_min_stimata - temp_margin)
        c3 = HR_min_stimata >= (RH / d + humidity_margin)
        s  = int(c1) + int(c2) + int(c3)
        candidates.append((round(d, 1), int(s), float(dp)))
        if s == 3:
            return round(d, 1), int(s), float(dp)
    candidates.sort(key=lambda x: (-x[1], x[0]))
    return candidates[0]

Dil_suggerita, score_suggerita, DP_suggerito = suggerisci_diluizione()

# -----------------------------
# COLORE BOX CONFORMITÀ
# -----------------------------
if DP_current < T_min_stimata:
    bg_color, border_color = "#d4edda", "#28a745"
elif DP_current < T_ext:
    bg_color, border_color = "#fff3cd", "#ffc107"
else:
    bg_color, border_color = "#f8d7da", "#dc3545"

# -----------------------------
# BOX CONFORMITÀ + SUGGERITORE
# -----------------------------
col_box_left, col_box_right = st.columns(2)

with col_box_left:
    st.markdown(f"""
    <div style="padding:14px;border-radius:10px;background-color:{bg_color};
                border:2px solid {border_color};font-size:15px;line-height:1.5;">
      <h4 style="margin:0 0 8px 0;">Conformità</h4>
      <p style="margin:6px 0;"><strong>Dew Point calcolato:</strong> {DP_current:.2f} °C</p>
      <p style="margin:6px 0;">
        <strong>Conformità istantanea</strong> (DP &lt; T_ext = {T_ext} °C):
        <span style="font-weight:bold;color:{'green' if conform_istantanea else 'red'};">
          {'✔' if conform_istantanea else '✘'}
        </span>
      </p>
      <p style="margin:6px 0;">
        <strong>Conformità trasporto</strong> (DP &lt; T_min_stimata − {temp_margin} = {T_min_stimata - temp_margin} °C):
        <span style="font-weight:bold;color:{'green' if conform_trasporto else 'red'};">
          {'✔' if conform_trasporto else '✘'}
        </span>
      </p>
      <p style="margin:6px 0;">
        <strong>Conformità umidità</strong> (UR_min ≥ RH/Dil + {humidity_margin}% = {soglia_umidita:.1f}%):
        <span style="font-weight:bold;color:{'green' if conform_umidita else 'red'};">
          {'✔' if conform_umidita else '✘'}
        </span>
      </p>
      <hr style="margin:10px 0;">
      <p style="margin:6px 0;"><strong>Conformità soddisfatte:</strong> {score} / 3</p>
    </div>
    """, unsafe_allow_html=True)

with col_box_right:
    st.markdown(f"""
    <div style="padding:14px;border-radius:10px;background-color:#f7f7f7;
                border:1px solid #ddd;font-size:15px;line-height:1.5;">
      <h4 style="margin:0 0 8px 0;">Suggeritore diluizione</h4>
      <p style="margin:6px 0;"><strong>Diluizione suggerita:</strong> {Dil_suggerita:.1f}</p>
      <p style="margin:6px 0;"><strong>Dew Point previsto:</strong> {DP_suggerito:.2f} °C</p>
      <hr style="margin:10px 0;">
      <p style="margin:6px 0;"><strong>Parametri usati:</strong></p>
      <p style="margin:4px 0;">Margine temperatura: {temp_margin} °C</p>
      <p style="margin:4px 0;">Margine umidità: {humidity_margin} %</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# COLORI ZONE
# -----------------------------
green_fill  = 'rgba(40,167,69,0.25)'
yellow_fill = 'rgba(255,193,7,0.30)'
red_fill    = 'rgba(220,50,50,0.35)'

# -----------------------------
# SELETTORE ASSE X + DATI
# -----------------------------
asse_x = st.selectbox(
    "Asse X del grafico",
    ["Diluizione", "Umidità relativa (%)", "Temperatura camino (°C)", "Temperatura esterna (°C)"],
    index=0
)

if asse_x == "Diluizione":
    X_values  = np.arange(1.0, 10.01, 0.2)
    DP_vs_X   = np.array([dew_point(T_ext, T_camino, RH, d) for d in X_values])
    x_label   = "Diluizione"
    X_current = Dil
elif asse_x == "Umidità relativa (%)":
    X_values  = np.arange(5, 100, 1)
    DP_vs_X   = np.array([dew_point(T_ext, T_camino, rh, Dil) for rh in X_values])
    x_label   = "Umidità relativa (%)"
    X_current = RH
elif asse_x == "Temperatura camino (°C)":
    X_values  = np.arange(0, 201, 2)
    DP_vs_X   = np.array([dew_point(T_ext, tcam, RH, Dil) for tcam in X_values])
    x_label   = "Temperatura camino (°C)"
    X_current = T_camino
else:
    X_values  = np.arange(0, 41, 1)
    DP_vs_X   = np.array([dew_point(text, T_camino, RH, Dil) for text in X_values])
    x_label   = "Temperatura esterna (°C)"
    X_current = T_ext

y_min = min(DP_vs_X.min(), T_ext, T_min_stimata) - 5
y_max = max(DP_vs_X.max(), T_ext, T_min_stimata) + 5

# -----------------------------
# GRAFICO con label inline
# -----------------------------
fig = go.Figure()

# Zone colorate (fasce orizzontali fisse)
fig.add_trace(go.Scatter(
    x=np.concatenate([X_values, X_values[::-1]]),
    y=np.concatenate([[T_min_stimata]*len(X_values), [y_min]*len(X_values)]),
    fill='toself', fillcolor=green_fill,
    line=dict(color='rgba(0,0,0,0)'),
    hoverinfo='skip', showlegend=False
))
fig.add_trace(go.Scatter(
    x=np.concatenate([X_values, X_values[::-1]]),
    y=np.concatenate([[T_ext]*len(X_values), [T_min_stimata]*len(X_values)]),
    fill='toself', fillcolor=yellow_fill,
    line=dict(color='rgba(0,0,0,0)'),
    hoverinfo='skip', showlegend=False
))
fig.add_trace(go.Scatter(
    x=np.concatenate([X_values, X_values[::-1]]),
    y=np.concatenate([[y_max]*len(X_values), [T_ext]*len(X_values)]),
    fill='toself', fillcolor=red_fill,
    line=dict(color='rgba(0,0,0,0)'),
    hoverinfo='skip', showlegend=False
))

# Curva Dew Point
fig.add_trace(go.Scatter(
    x=X_values, y=DP_vs_X,
    mode="lines",
    line=dict(color="royalblue", width=3),
    name="Dew Point", showlegend=False
))

# Punto attuale con label
fig.add_trace(go.Scatter(
    x=[X_current], y=[DP_current],
    mode="markers+text",
    marker=dict(size=12, color="black"),
    text=[f"  DP = {DP_current:.1f} °C"],
    textposition="middle right",
    textfont=dict(size=12, color="black"),
    showlegend=False
))

# Linee tratteggiate + annotation inline
x_end = X_values[-1]

for y_val, color, label in [
    (DP_current, "royalblue", f"DP attuale ({DP_current:.1f} °C)"),
    (T_min_stimata,      "black",     f"T min trasporto ({T_min_stimata} °C)"),
    (T_ext,      "darkorange",f"T esterna ({T_ext} °C)"),
]:
    fig.add_shape(type="line",
        x0=X_values[0], x1=x_end,
        y0=y_val, y1=y_val,
        line=dict(color=color, dash="dash", width=1.5)
    )
    fig.add_annotation(
        x=x_end, y=y_val,
        text=label, showarrow=False,
        xanchor="left", font=dict(color=color, size=11),
        bgcolor="rgba(255,255,255,0.75)", borderpad=2
    )

# Label zone (a sinistra, centrate verticalmente)
x_start = X_values[0]
for y_lo, y_hi, emoji, label, color in [
    (y_min, T_min_stimata, "✅", "Conforme",            "green"),
    (T_min_stimata, T_ext, "⚠️", "Rischio trasporto",   "#b8860b"),
    (T_ext, y_max, "❌", "Condensa immediata",  "red"),
]:
    fig.add_annotation(
        x=x_start, y=(y_lo + y_hi) / 2,
        text=f"{emoji} {label}", showarrow=False,
        xanchor="left", font=dict(color=color, size=11),
        bgcolor="rgba(255,255,255,0.7)", borderpad=2
    )

fig.update_layout(
    xaxis_title=x_label,
    yaxis_title="Temperatura (°C)",
    yaxis=dict(range=[y_min, y_max]),
    xaxis=dict(range=[X_values[0], X_values[-1] * 1.18]),
    template="plotly_white",
    margin=dict(t=30, b=40, l=50, r=150),
    showlegend=False,
    height=450
)

st.plotly_chart(fig, use_container_width=True)
