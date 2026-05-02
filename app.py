import streamlit as st
import requests
from PIL import Image
from openai import OpenAI
import google.generativeai as genai
import urllib.parse
import pandas as pd
import folium
from streamlit_folium import st_folium

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
st.title("🌍 Terra-AI")
st.caption("Global AI Copilot for Smart Farming")

# ================= MENU =================
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

# ================= WEATHER =================
if menu == "🌦 Weather Intelligence":
    st.header("🌦 5-Day Weather Forecast")

    city = st.text_input("Enter City")

    if st.button("Get Forecast"):
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()

        if res.get("cod") == "200":
            for i in range(0, 40, 8):
                day = res["list"][i]
                date_txt = day["dt_txt"].split(" ")[0]

                st.subheader(f"📅 {date_txt}")

                col1, col2, col3 = st.columns(3)
                col1.metric("Temp", f"{day['main']['temp']}°C")
                col2.metric("Humidity", f"{day['main']['humidity']}%")
                col3.metric("Wind", f"{day['wind']['speed']} m/s")

                st.write(day["weather"][0]["description"])

                st.divider()
        else:
            st.error("City not found")

# ================= SATELLITE =================
elif menu == "🛰 Satellite Insights":
    st.header("🛰 Satellite Insights")

    city = st.text_input("Enter City")

    if st.button("Get Data"):
        geo_url = f"https://nominatim.openstreetmap.org/search?city={city}&format=json"
        res = requests.get(geo_url).json()

        if res:
            lat = float(res[0]["lat"])
            lon = float(res[0]["lon"])

            st.success(f"{lat}, {lon}")

            m = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon]).add_to(m)
            st_folium(m, width=700, height=400)

# ================= AI ADVISORY =================
elif menu == "🤖 AI Advisory":
    st.header("🤖 Smart Advisory")

    country = st.text_input("Country")
    crop = st.text_input("Crop")
    soil = st.selectbox("Soil", ["Sandy", "Clay", "Loamy"])
    weather = st.selectbox("Weather", ["Hot", "Cold", "Rainy"])

    if st.button("Generate Advice"):

        if not country or not crop:
            st.warning("Fill all fields")
        else:
            prompt = f"""
            Country: {country}
            Crop: {crop}
            Soil: {soil}
            Weather: {weather}
            Give farming advice.
            """

            try:
                response = groq_client.responses.create(
                    model="openai/gpt-oss-20b",
                    input=prompt
                )

                st.success(response.output_text)

            except Exception as e:
                st.error("AI unavailable")
                st.error(e)

# ================= DISEASE =================
elif menu == "🦠 Disease Detection":
    st.header("🦠 Disease Detection")

    file = st.file_uploader("Upload Image")

    if file:
        img = Image.open(file)
        st.image(img)

        if GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel("models/gemini-2.5-flash")
                response = model.generate_content(["Detect disease", img])
                st.write(response.text)
            except Exception as e:
                st.error(e)

# ================= CHATBOT =================
elif menu == "💬 AI Copilot":
    st.header("💬 AI Copilot")

    user_input = st.chat_input("Ask...")

    if user_input:
        try:
            response = groq_client.responses.create(
                model="openai/gpt-oss-20b",
                input=user_input
            )

            st.write(response.output_text)

        except Exception as e:
            st.error(e)

# ================= YIELD =================
elif menu == "📈 Yield Predictor":
    st.header("📈 Yield Predictor")

    area = st.number_input("Area", 1)
    rain = st.slider("Rainfall", 0, 500, 100)

    if st.button("Predict"):
        result = area * 30 + rain * 0.2
        st.success(f"Yield: {result}")

# ================= FERTILIZER =================
elif menu == "🧪 Fertilizer AI":
    crop = st.text_input("Crop")

    if st.button("Get Recommendation"):
        st.success(f"Use NPK fertilizer for {crop}")
