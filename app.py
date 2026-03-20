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
# ================= SATELLITE INSIGHTS =================
elif menu == "🛰 Satellite Insights":
    st.header("🛰 Satellite Weather & Crop Insights (Global)")

    # Initialize session_state variables
    if "satellite_clicked" not in st.session_state:
        st.session_state.satellite_clicked = False
    if "geo_res" not in st.session_state:
        st.session_state.geo_res = None
    if "map_data" not in st.session_state:
        st.session_state.map_data = None
    if "weather_df" not in st.session_state:
        st.session_state.weather_df = None
    if "city_input" not in st.session_state:
        st.session_state.city_input = ""

    # Input field
    city_name = st.text_input("Enter City Name", st.session_state.city_input)
    st.session_state.city_input = city_name  # Preserve input across reruns

    if st.button("Get Data"):
        st.session_state.satellite_clicked = True

        with st.spinner("Fetching coordinates..."):
            try:
                city_encoded = urllib.parse.quote(city_name)
                geo_url = f"https://nominatim.openstreetmap.org/search?city={city_encoded}&format=json"
                headers = {"User-Agent": "terra-ai-hackathon-app"}
                res = requests.get(geo_url, headers=headers, timeout=10)
                st.session_state.geo_res = res.json()
            except Exception as e:
                st.error(f"Error fetching location: {e}")
                st.session_state.geo_res = None

    # Only display map and weather if button clicked or previously clicked
    if st.session_state.satellite_clicked:
        if st.session_state.geo_res and len(st.session_state.geo_res) > 0:
            lat = round(float(st.session_state.geo_res[0]["lat"]), 3)
            lon = round(float(st.session_state.geo_res[0]["lon"]), 3)
            st.success(f"Coordinates: {lat}, {lon}")

            # Display map
            if st.session_state.map_data is None:
                m = folium.Map(location=[lat, lon], zoom_start=10)
                folium.Marker([lat, lon], popup=city_name).add_to(m)
                st.session_state.map_data = m

            st_folium(st.session_state.map_data, width=700, height=400)

            # Fetch 7-day weather
            with st.spinner("Fetching 7-day weather forecast..."):
                try:
                    open_meteo_url = (
                        f"https://api.open-meteo.com/v1/forecast?"
                        f"latitude={lat}&longitude={lon}"
                        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
                        f"&timezone=auto"
                    )
                    weather_res = requests.get(open_meteo_url, timeout=10).json()

                    if "daily" in weather_res:
                        df = pd.DataFrame({
                            "date": weather_res["daily"]["time"],
                            "temp_max": weather_res["daily"]["temperature_2m_max"],
                            "temp_min": weather_res["daily"]["temperature_2m_min"],
                            "rainfall": weather_res["daily"]["precipitation_sum"]
                        })
                        df["date"] = pd.to_datetime(df["date"])
                        st.subheader("📊 7-Day Weather Forecast")
                        st.line_chart(df.set_index("date")[["temp_max", "temp_min", "rainfall"]])
                        st.session_state.weather_df = df
                    else:
                        st.warning("Weather data not available for this location.")
                except Exception as e:
                    st.error(f"Error fetching weather data: {e}")
        else:
            st.error("City not found or invalid response from location service.")

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
# ================= DISEASE DETECTION =================
elif menu == "🦠 Disease Detection":
    st.subheader("🦠 Crop Disease Detection")
    st.write("Upload or capture a leaf image")

    with st.form("disease_form"):
        cam = st.camera_input("Camera")
        file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"])
        submit = st.form_submit_button("Analyze")

    img_file = cam if cam else file

    if img_file and submit:
        try:
            # Open and resize image
            img = Image.open(img_file)
            img.thumbnail((1024, 1024))
            st.image(img, width=300)

            if not GEMINI_API_KEY:
                st.error("Gemini API key missing")
            else:
                with st.spinner("Analyzing..."):
                    # Prompt for disease detection
                    prompt = """
                    Identify the plant disease in the image.
                    Provide:
                    - Disease Name
                    - Confidence %
                    - Possible Cause
                    - Treatment/Remedy
                    """

                    try:
                        # Use the correct model
                        model = genai.GenerativeModel("models/gemini-2.5-flash")
                        response = model.generate_content([prompt, img])

                        st.success("✅ Disease Analysis Result")
                        st.markdown(response.text)

                    except Exception as e:
                        st.warning("⚠ Gemini model failed")
                        st.error(e)

        except Exception as e:
            st.error(f"Error processing image: {e}")
                        

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
