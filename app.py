import streamlit as st
import requests
from PIL import Image
from openai import OpenAI
import google.generativeai as genai
import urllib.parse
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# ================= CONFIG =================
st.set_page_config(page_title="🌍 Terra-AI", layout="wide")

# ================= KEYS =================
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
groq_client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ================= HEADER =================
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between">
    <h1>🌍 Terra-AI</h1>
    <span style="font-size:16px;color:gray;">Global AI Copilot for Smart Farming</span>
</div>
""", unsafe_allow_html=True)

# ================= SIDEBAR MENU =================
menu = st.sidebar.radio("Menu", [
    "🌦 Weather Intelligence",
    "🛰 Satellite Insights",
    "🤖 AI Advisory",
    "🦠 Disease Detection",
    "💬 AI Copilot",
    "📈 Yield Predictor",
    "📅 Crop Calendar",
    "📈 Market & Profit",
    "🌾 Crop Estimator",
    "🧪 Fertilizer AI",
])

# ================= FUNCTION TO CREATE CARD =================
def card(title, content_func):
    with st.container():
        st.markdown(f"""
        <div style="
            background-color:#f9f9f9;
            padding:15px;
            border-radius:10px;
            box-shadow:0px 2px 5px rgba(0,0,0,0.1);
            margin-bottom:15px;">
            <h3>{title}</h3>
        """, unsafe_allow_html=True)
        content_func()
        st.markdown("</div>", unsafe_allow_html=True)

# ================= WEATHER =================
if menu == "🌦 Weather Intelligence":
    def weather_card():
        city = st.text_input("Enter City")
        if st.button("Get Forecast"):
            with st.spinner("Fetching data..."):
                url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
                res = requests.get(url).json()
                if res.get("cod") == "200":
                    for i in range(0, 40, 8):
                        day = res["list"][i]
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Temp", f"{day['main']['temp']}°C")
                        col2.metric("Humidity", f"{day['main']['humidity']}%")
                        col3.metric("Wind", f"{day['wind']['speed']} m/s")
                        st.write(day["weather"][0]["description"])
                        # Alerts
                        if day['main']['temp'] > 35: st.warning("🔥 Heat Stress Alert")
                        if day['main']['temp'] < 5: st.warning("❄️ Frost Alert")
                        if "rain" in day["weather"][0]["description"]: st.info("🌧 Rain Expected")
                        st.divider()
                else:
                    st.error("City not found")
    card("🌦 7-Day Weather Forecast", weather_card)

# ================= SATELLITE INSIGHTS =================
elif menu == "🛰 Satellite Insights":
    def satellite_card():
        if "satellite_clicked" not in st.session_state:
            st.session_state.satellite_clicked = False
            st.session_state.geo_res = None
            st.session_state.map_data = None
            st.session_state.weather_df = None
            st.session_state.city_input = ""

        city_name = st.text_input("Enter City Name", st.session_state.city_input)
        st.session_state.city_input = city_name
        if st.button("Get Data"):
            st.session_state.satellite_clicked = True
            with st.spinner("Fetching coordinates..."):
                try:
                    geo_url = f"https://nominatim.openstreetmap.org/search?city={urllib.parse.quote(city_name)}&format=json"
                    headers = {"User-Agent": "terra-ai-hackathon-app"}
                    st.session_state.geo_res = requests.get(geo_url, headers=headers, timeout=10).json()
                except Exception as e:
                    st.error(f"Error fetching location: {e}")
                    st.session_state.geo_res = None

        if st.session_state.satellite_clicked:
            if st.session_state.geo_res and len(st.session_state.geo_res) > 0:
                lat, lon = float(st.session_state.geo_res[0]["lat"]), float(st.session_state.geo_res[0]["lon"])
                st.success(f"Coordinates: {lat:.3f}, {lon:.3f}")
                if st.session_state.map_data is None:
                    m = folium.Map(location=[lat, lon], zoom_start=10)
                    folium.Marker([lat, lon], popup=city_name).add_to(m)
                    st.session_state.map_data = m
                st_folium(st.session_state.map_data, width=700, height=400)
            else:
                st.error("City not found or invalid response from location service.")
    card("🛰 Satellite Weather & Crop Insights", satellite_card)

# ================= AI ADVISORY =================
elif menu == "🤖 AI Advisory":
    def advisory_card():
        country = st.text_input("Country")
        crop = st.text_input("Crop")
        soil = st.selectbox("Soil", ["Sandy", "Clay", "Loamy"])
        weather = st.selectbox("Weather", ["Hot", "Cold", "Rainy"])
        if st.button("Generate Advice"):
            prompt = f"Country: {country}\nCrop: {crop}\nSoil: {soil}\nWeather: {weather}\nGive farming advice."
            response = groq_client.responses.create(model="openai/gpt-oss-20b", input=prompt)
            st.success(response.output_text)
    card("🤖 Smart Advisory", advisory_card)

# ================= DISEASE DETECTION =================
elif menu == "🦠 Disease Detection":
    def disease_card():
        st.write("Upload or capture a leaf image")
        with st.form("disease_form"):
            cam = st.camera_input("Camera")
            file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"])
            submit = st.form_submit_button("Analyze")
        img_file = cam if cam else file
        if img_file and submit:
            img = Image.open(img_file)
            img.thumbnail((1024,1024))
            st.image(img, width=300)
            if GEMINI_API_KEY:
                with st.spinner("Analyzing..."):
                    try:
                        model = genai.GenerativeModel("models/gemini-2.5-flash")
                        prompt = "Identify plant disease with name, confidence, cause, treatment."
                        response = model.generate_content([prompt, img])
                        st.success("✅ Disease Analysis Result")
                        st.markdown(response.text)
                    except Exception as e:
                        st.warning("⚠ Gemini model failed")
                        st.error(e)
            else:
                st.error("Gemini API key missing")
    card("🦠 Crop Disease Detection", disease_card)

# ==================== Rest of your modules ====================
# You can wrap each other menu item in the same card(title, func) pattern
# For example:
# card("💬 AI Farm Copilot", copilot_func)
# card("📈 Smart Yield Prediction", yield_func)
# card("📅 Seasonal Crop Calendar", crop_calendar_func)
# etc.
