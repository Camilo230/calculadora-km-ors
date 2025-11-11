
import os
import requests
import streamlit as st

st.set_page_config(page_title="Calculadora de KM • OpenRouteService", page_icon="🛣️", layout="wide")
st.title("🛣️ Calculadora de Distâncias (OpenRouteService)")
st.caption("Escolha usar Endereço/CEP **ou** Coordenadas (Longitude/Latitude).")

# ---- API KEY getter
def get_api_key():
    key = os.getenv("ORS_API_KEY", "")
    if key:
        return key.strip()
    try:
        if "ORS_API_KEY" in st.secrets:
            return st.secrets["ORS_API_KEY"].strip()
    except Exception:
        pass
    return ""

ORS_API_KEY = get_api_key()

with st.expander("🔐 Como configurar a chave da API", expanded=not bool(ORS_API_KEY)):
    st.write(
        """
        **Opção A (recomendada):** crie um arquivo `.streamlit/secrets.toml` ao lado deste app com:
        ```toml
        ORS_API_KEY = "SUA_CHAVE_AQUI"
        ```
        **Opção B (sessão atual):**
        ```cmd
        set ORS_API_KEY=SUA_CHAVE_AQUI
        ```
        """
    )
if not ORS_API_KEY:
    st.warning("Informe sua ORS_API_KEY para continuar (em `secrets.toml` ou variável de ambiente).")

# ---- HTTP helpers
def http_get(url, headers=None, params=None):
    r = requests.get(url, headers=headers or {}, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def http_post(url, headers=None, json=None):
    r = requests.post(url, headers=headers or {}, json=json or {}, timeout=30)
    r.raise_for_status()
    return r.json()

# ---- Geocode
def geocode(text):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {"text": text, "size": 1, "boundary.country": "BR", "api_key": ORS_API_KEY}
    data = http_get(url, params=params)
    feats = data.get("features", [])
    if not feats:
        raise ValueError(f"Endereço não encontrado: {text}")
    coords = feats[0]["geometry"]["coordinates"]  # [lon, lat]
    display_name = feats[0]["properties"].get("label", text)
    return coords[0], coords[1], display_name

# ---- Routing
def directions(coords_pair, profile="driving-hgv"):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    payload = {"coordinates": coords_pair}
    data = http_post(url, headers=headers, json=payload)
    route = data["routes"][0]["summary"]
    km = round(route["distance"] / 1000, 1)
    mins = int(round(route["duration"] / 60, 0))
    return km, mins

# ---- UI mode
modo = st.radio("🔀 Modo de entrada", ["Endereço/CEP", "Coordenadas (lon/lat)"], index=1, horizontal=True)

perfil = st.selectbox(
    "🚚 Perfil do veículo",
    [
        ("driving-hgv", "Caminhão (pesado) – driving-hgv"),
        ("driving-car", "Carro/Leve – driving-car"),
    ],
    index=0,
    format_func=lambda x: x[1]
)[0]

if modo == "Endereço/CEP":
    col1, col2 = st.columns([1,1])
    with col1:
        origem_txt = st.text_input("📍 Origem (ex.: 'Uberlândia, MG' ou CEP)", "Uberlândia, MG")
    with col2:
        destino_txt = st.text_input("🏁 Destino (ex.: 'Campinas, SP' ou CEP)", "Campinas, SP")

    disabled_btn = not bool(ORS_API_KEY)
    if st.button("Calcular distância", type="primary", use_container_width=True, disabled=disabled_btn):
        try:
            o_lon, o_lat, o_label = geocode(origem_txt)
            d_lon, d_lat, d_label = geocode(destino_txt)
            km, mins = directions([[o_lon, o_lat], [d_lon, d_lat]], profile=perfil)
            st.success(f"🔎 Rota: **{o_label} → {d_label}**")
            st.metric("Distância (km)", f"{km:,}".replace(",", "."))
            st.metric("Duração (min)", f"{mins:,}".replace(",", "."))
        except Exception as e:
            st.error(f"Não foi possível calcular: {e}")

else:
    st.markdown("Informe as **coordenadas** em **Longitude, Latitude** (padrão WGS84). Ex.: `-48.2772` e `-18.9186`")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        o_lon = st.number_input("📍 Origem — Longitude", value=-48.2772, format="%.6f")
    with c2:
        o_lat = st.number_input("📍 Origem — Latitude", value=-18.918600, format="%.6f")
    with c3:
        st.write("")

    d1, d2, d3 = st.columns([1,1,1])
    with d1:
        d_lon = st.number_input("🏁 Destino — Longitude", value=-47.060800, format="%.6f")
    with d2:
        d_lat = st.number_input("🏁 Destino — Latitude", value=-22.905600, format="%.6f")
    with d3:
        st.write("")

    disabled_btn = not bool(ORS_API_KEY)
    if st.button("Calcular distância", type="primary", use_container_width=True, disabled=disabled_btn):
        try:
            km, mins = directions([[float(o_lon), float(o_lat)], [float(d_lon), float(d_lat)]], profile=perfil)
            st.success("🔎 Rota calculada com coordenadas (lon/lat).")
            st.metric("Distância (km)", f"{km:,}".replace(",", "."))
            st.metric("Duração (min)", f"{mins:,}".replace(",", "."))
        except Exception as e:
            st.error(f"Não foi possível calcular: {e}")

st.divider()
st.caption("© Alli Log • Calculadora de KM via OpenRouteService — modo Endereço ou Coordenadas")
