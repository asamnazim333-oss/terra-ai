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
        with st.spinner("Fetching data..."):
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
            res = requests.get(url).json()

            if res.get("cod") == "200":
                for i in range(0, 40, 8):
                    day = res["list"][i]
                    date_txt = day["dt_txt"].split(" ")[0]

                    st.subheader(f"📅 Date: {date_txt}")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("🌡 Temp", f"{day['main']['temp']}°C")
                    col2.metric("💧 Humidity", f"{day['main']['humidity']}%")
                    col3.metric("💨 Wind", f"{day['wind']['speed']} m/s")

                    st.write(f"Weather: {day['weather'][0]['description'].title()}")

                    if day['main']['temp'] > 35:
                        st.warning("🔥 Heat Stress Alert")
                    if day['main']['temp'] < 5:
                        st.warning("❄️ Frost Alert")
                    if "rain" in day["weather"][0]["description"]:
                        st.info("🌧 Rain Expected")

                    st.divider()
            else:
                st.error("City not found")

# ================= SATELLITE =================
elif menu == "🛰 Satellite Insights":
    st.header("🛰 Satellite Weather & Crop Insights")

    city_name = st.text_input("Enter City")

    if st.button("Get Data"):
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?city={city_name}&format=json"
            res = requests.get(geo_url, headers={"User-Agent": "terra-ai"}, timeout=10).json()

            if res:
                lat = float(res[0]["lat"])
                lon = float(res[0]["lon"])

                st.success(f"Coordinates: {lat}, {lon}")

                m = folium.Map(location=[lat, lon], zoom_start=10)
                folium.Marker([lat, lon]).add_to(m)
                st_folium(m, width=700, height=400)

                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
                weather = requests.get(weather_url).json()

                if "daily" in weather:
                    df = pd.DataFrame({
                        "date": weather["daily"]["time"],
                        "temp_max": weather["daily"]["temperature_2m_max"],
                        "temp_min": weather["daily"]["temperature_2m_min"],
                        "rainfall": weather["daily"]["precipitation_sum"]
                    })
                    df["date"] = pd.to_datetime(df["date"])
                    st.line_chart(df.set_index("date"))

            else:
                st.error("City not found")

        except Exception as e:
            st.error("Error fetching data")

# ================= AI ADVISORY =================
elif menu == "🤖 AI Advisory":
    st.header("🤖 Smart Advisory")

    country = st.text_input("Country")
    crop = st.text_input("Crop")
    soil = st.selectbox("Soil", ["Sandy", "Clay", "Loamy"])
    weather = st.selectbox("Weather", ["Hot", "Cold", "Rainy"])

    if st.button("Generate Advice"):
        prompt = f"""
        Country: {country}
        Crop: {crop}
        Soil: {soil}
        Weather: {weather}
        Give farming advice.
        """

        try:
            response = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            st.success(response.choices[0].message.content)

        except Exception:
            st.error("AI service unavailable")

# ================= DISEASE =================
elif menu == "🦠 Disease Detection":
    st.subheader("🦠 Crop Disease Detection")

    cam = st.camera_input("Camera")
    file = st.file_uploader("Upload", type=["jpg", "png"])

    img_file = cam if cam else file

    if img_file:
        img = Image.open(img_file)
        st.image(img, width=300)

        if st.button("Analyze"):
            if not GEMINI_API_KEY:
                st.error("Gemini key missing")
            else:
                try:
                    model = genai.GenerativeModel("models/gemini-2.5-flash")
                    response = model.generate_content(["Identify disease", img])
                    st.success(response.text)
                except Exception:
                    st.error("Gemini failed")

# ================= CHATBOT =================
elif menu == "💬 AI Copilot":
    st.header("💬 AI Copilot")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask...")

    if user_input:
        st.session_state.chat.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        try:
            response = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": user_input}]
            )
            reply = response.choices[0].message.content
        except:
            reply = "AI unavailable"

        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

# ================= SIMPLE FEATURES =================
elif menu == "📅 Crop Calendar":
    st.write("Crop calendar working")

elif menu == "📈 Market & Profit":
    st.write("Profit module working")

elif menu == "🌾 Crop Estimator":
    st.write("Estimator working")

elif menu == "🧪 Fertilizer AI":
    st.write("Fertilizer module working")

elif menu == "📈 Yield Predictor":
    st.write("Yield predictor working")
