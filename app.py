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
import importlib.metadata as importlib_metadata
import streamlit as st

st.write("Google GenerativeAI version:", importlib_metadata.version("google-generativeai"))


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


st.write(pkg_resources.get_distribution("google-generativeai").version)

# ================= GLOBAL MODE =================
country = st.selectbox("🌎 Select Country", ["USA", "Pakistan", "India"])

# ================= MENU =================
menu = st.sidebar.radio("Menu", [
    "🌦 Weather Intelligence",
    "🛰 Satellite Insights",
    "🤖 AI Advisory",
    "🦠 Disease Detection",
    "💬 AI Copilot",
    "📈 Yield Predictor",
])

# ================= WEATHER =================
if menu == "🌦 Weather Intelligence":
    st.header("🌦 7-Day Weather Forecast")

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
    st.header("🛰 Satellite Weather & Crop Insights (Global)")

    city_name = st.text_input("Enter City Name")

    if st.button("Get Data"):
        with st.spinner("Fetching data..."):
            try:
                geo_url = f"https://nominatim.openstreetmap.org/search?city={urllib.parse.quote(city_name)}&format=json"
                headers = {"User-Agent": "terra-ai"}
                geo_res = requests.get(geo_url, headers=headers).json()

                if geo_res:
                    lat = float(geo_res[0]["lat"])
                    lon = float(geo_res[0]["lon"])

                    st.success(f"📍 Coordinates: {lat}, {lon}")

                    m = folium.Map(location=[lat, lon], zoom_start=10)
                    folium.Marker([lat, lon]).add_to(m)
                    st_folium(m, width=700, height=400)

                    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
                    weather_res = requests.get(weather_url).json()

                    if "daily" in weather_res:
                        df = pd.DataFrame({
                            "date": weather_res["daily"]["time"],
                            "temp_max": weather_res["daily"]["temperature_2m_max"],
                            "temp_min": weather_res["daily"]["temperature_2m_min"],
                            "rain": weather_res["daily"]["precipitation_sum"]
                        })
                        df["date"] = pd.to_datetime(df["date"])
                        st.line_chart(df.set_index("date"))
                    else:
                        st.warning("Weather data not available")
                else:
                    st.error("City not found")

            except Exception as e:
                st.error(f"Error: {e}")

# ================= AI ADVISORY =================
elif menu == "🤖 AI Advisory":
    st.header("🤖 Smart Advisory")

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

        response = groq_client.responses.create(
            model="openai/gpt-oss-20b",
            input=prompt
        )

        st.success(response.output_text)

# ================= DISEASE =================
elif menu == "🦠 Disease Detection":
    st.subheader("🦠 Crop Disease Detection")
    
    with st.form("disease_form"):
        cam = st.camera_input("Camera")
        file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"])
        submit = st.form_submit_button("Analyze")

    img_file = cam if cam else file

    if img_file and submit:
        try:
            img = Image.open(img_file)
            img.thumbnail((1024, 1024))
            st.image(img, width=300)

            if not GEMINI_API_KEY:
                st.error("Gemini API key missing")
            else:
                with st.spinner("Analyzing..."):
                    prompt = "Identify plant disease, give confidence %, cause and treatment."

                    try:
                        model = genai.GenerativeModel("gemini-pro-vision")
                        response = model.generate_content([prompt, img])

                        st.success("✅ Result")
                        st.markdown(response.text)

                    except Exception as e:
                        st.warning("Gemini failed")
                        st.error(e)

        except Exception as e:
            st.error(f"Error: {e}")

# ================= CHATBOT =================
elif menu == "💬 AI Copilot":
    st.header("💬 AI Farm Copilot")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask farming question...")

    if user_input:
        st.session_state.chat.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        response = groq_client.responses.create(
            model="openai/gpt-oss-20b",
            input=user_input
        )

        reply = response.output_text

        st.session_state.chat.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

# ================= YIELD =================
elif menu == "📈 Yield Predictor":
    st.header("📈 Smart Yield Prediction")

    area = st.number_input("Land (acres)", 1)
    rainfall = st.slider("Rainfall", 0, 500, 100)
    temp = st.slider("Temperature", 0, 50, 25)

    if st.button("Predict"):
        yield_est = (area * 30) + (rainfall * 0.2) - (temp * 0.7)
        st.success(f"Estimated Yield: {round(yield_est,2)}")
