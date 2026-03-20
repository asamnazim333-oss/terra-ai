import streamlit as st
import requests
from PIL import Image
from openai import OpenAI
import google.generativeai as genai
import urllib.parse
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# ================= CONFIG =================
st.set_page_config(page_title="🌍 Terra-AI", layout="wide")

# ================= KEYS =================
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

groq_client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

gemini_client = genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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

# ================= WEATHER (7 DAY) =================
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

                    # Alerts
                    if day['main']['temp'] > 35:
                        st.warning("🔥 Heat Stress Alert")
                    if day['main']['temp'] < 5:
                        st.warning("❄️ Frost Alert")
                    if "rain" in day["weather"][0]["description"]:
                        st.info("🌧 Rain Expected")

                    st.divider()
            else:
                st.error("City not found")

# ================= SATELLITE===========
   

elif menu == "🛰 Satellite Insights":
    st.header("🛰 Satellite Weather & Crop Insights (Global)")

    # Initialize session_state
    if "satellite_clicked" not in st.session_state:
        st.session_state.satellite_clicked = False
    if "geo_res" not in st.session_state:
        st.session_state.geo_res = None
    if "map_data" not in st.session_state:
        st.session_state.map_data = None
    if "weather_df" not in st.session_state:
        st.session_state.weather_df = None

    city_name = st.text_input("Enter City Name", key="city_input")

    if st.button("Get Data"):
        st.session_state.satellite_clicked = True

        with st.spinner("Fetching coordinates..."):
            city_encoded = urllib.parse.quote(city_name)
            geo_url = f"https://nominatim.openstreetmap.org/search?city={city_encoded}&format=json"
            headers = {"User-Agent": "terra-ai-hackathon-app"}

            try:
                res = requests.get(geo_url, headers=headers, timeout=10)
                st.session_state.geo_res = res.json()
            except Exception as e:
                st.error(f"Error fetching location: {e}")
                st.session_state.geo_res = None

    # Only run if button clicked
    if st.session_state.satellite_clicked:

        if st.session_state.geo_res and len(st.session_state.geo_res) > 0:
            lat = round(float(st.session_state.geo_res[0]["lat"]), 3)
            lon = round(float(st.session_state.geo_res[0]["lon"]), 3)
            st.success(f"Coordinates: {lat}, {lon}")

            # Create map only once
            if st.session_state.map_data is None:
                m = folium.Map(location=[lat, lon], zoom_start=10)
                folium.Marker([lat, lon], popup=city_name).add_to(m)
                st.session_state.map_data = m

            # Display map
            st_folium(st.session_state.map_data, width=700, height=400)

            # Open-Meteo 7-day forecast
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

        Give advanced farming advice including:
        - Fertilizer
        - Irrigation
        - Risk alerts
        """

        with st.spinner("AI thinking..."):
            response = groq_client.responses.create(
                model="openai/gpt-oss-20b",
                input=prompt,
                max_output_tokens=600
            )

            st.success(response.output_text)

# ================= DISEASE =================
elif menu == "🦠 Disease Detection":
    st.subheader("🦠 Crop Disease Detection")
    st.write("Take a picture of a leaf or upload an image")

    # Form to bypass Axios / upload issues
    with st.form("disease_form", clear_on_submit=True):
        cam_image = st.camera_input("📷 Take a photo of the leaf")
        file_image = st.file_uploader("📁 Or upload a leaf image", type=["jpg", "jpeg", "png"])
        submit_button = st.form_submit_button("Check Disease")

    # Determine which image to process
    target_image = cam_image if cam_image else file_image

    if target_image is not None and submit_button:
        try:
            img = Image.open(target_image)
            img.thumbnail((1024, 1024))  # Resize for processing
            st.image(img, caption="Processing image...", width=300)

            with st.spinner("Analyzing..."):

                # -----------------------------
                # 1️⃣ Try Gemini if API key exists
                # -----------------------------
                gemini_key = os.environ.get("GEMINI_API_KEY")
                if gemini_key:
                    try:
                        from google import genai
                        import base64

                        gemini_client = genai.Client(api_key=gemini_key)
                        img_bytes = target_image.read()
                        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

                        prompt = """
                        You are an expert plant pathologist.
                        Analyze this plant leaf image.
                        1. Name the disease.
                        2. Give confidence percentage.
                        3. Explain cause briefly.
                        4. Suggest organic and chemical remedies.
                        If healthy, say so.
                        """

                        response = gemini_client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[prompt, img_base64]
                        )

                        st.success("✅ Analysis Result (Gemini):")
                        st.markdown(response.text)

                    except Exception as e:
                        st.warning(f"Gemini AI failed: {e}")
                        st.info("Falling back to Hugging Face model...")

                # -----------------------------
                # 2️⃣ Fallback to Hugging Face Plant Disease Model
                # -----------------------------
                else:
                    try:
                        from transformers import pipeline

                        classifier = pipeline(
                            "image-classification",
                            model="nateraw/plant-disease-classifier"
                        )

                        results = classifier(img)
                        # Example result: [{'label': 'Tomato___Late_blight', 'score': 0.95}]
                        st.success("✅ Analysis Result (Hugging Face):")
                        for res in results:
                            disease_name = res["label"].replace("_", " ").replace("___", " ")
                            confidence = round(res["score"] * 100, 2)
                            st.markdown(f"**Disease:** {disease_name}  \n**Confidence:** {confidence}%")
                            # Simple remedies suggestion
                            if "healthy" not in disease_name.lower():
                                st.markdown("**Remedies:** Use balanced NPK fertilizer, remove infected leaves, apply appropriate pesticide or organic compost as needed.")
                            else:
                                st.markdown("🌱 The plant looks healthy! Keep monitoring regularly.")

                    except Exception as e:
                        st.error(f"Hugging Face model failed: {e}")

        except Exception as e:
            st.error(f"Image processing error: {e}")
            st.warning("Try a different image or reduce file size.")

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

        with st.spinner("Thinking..."):
            response = groq_client.responses.create(
                model="openai/gpt-oss-20b",
                input=user_input,
                max_output_tokens=500
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
