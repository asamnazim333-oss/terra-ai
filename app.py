import streamlit as st
import requests
from PIL import Image
from openai import OpenAI
import google.generativeai as genai
import urllib.parse

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

# ================= SATELLITE =================


elif menu == "🛰 Satellite Insights":
    st.header("🛰 Satellite Weather Insights (NASA)")

    geo_res = None  # initialize variable

    city_name = st.text_input("Enter City Name")

    if st.button("Get Data"):
        with st.spinner("Fetching coordinates..."):
            # Encode city name safely
            city_encoded = urllib.parse.quote(city_name)
            geo_url = f"https://nominatim.openstreetmap.org/search?city={city_encoded}&format=json"

            headers = {"User-Agent": "terra-ai-hackathon-app"}

            try:
                res = requests.get(geo_url, headers=headers, timeout=10)
                geo_res = res.json()
            except requests.exceptions.JSONDecodeError:
                st.error("Error decoding location data. Nominatim may have rejected the request.")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching location: {e}")

        # Only proceed if geo_res is valid
        if geo_res and len(geo_res) > 0:
            # Convert lat/lon to float and round
            lat = round(float(geo_res[0]["lat"]), 3)
            lon = round(float(geo_res[0]["lon"]), 3)
            st.success(f"Coordinates: {lat}, {lon}")

            with st.spinner("Fetching NASA data..."):
                try:
                    nasa_url = (
                        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
                        f"parameters=T2M,PRECTOT&community=AG&longitude={lon}&latitude={lat}&format=JSON"
                    )
                    nasa_res = requests.get(nasa_url, timeout=10).json()

                    if "properties" in nasa_res and "parameter" in nasa_res["properties"]:
                        data = nasa_res["properties"]["parameter"]
                        st.write("🌡 Temperature Sample:", list(data["T2M"].values())[:5])
                        st.write("🌧 Rainfall Sample:", list(data["PRECTOT"].values())[:5])
                    else:
                        st.warning("NASA data not available for this exact location. Try a nearby city.")
                except Exception as e:
                    st.error(f"Error fetching NASA data: {e}")
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
    st.header("🦠 AI Disease Detection")

    image = st.file_uploader("Upload crop image", type=["jpg", "png"])

    if image:
        img = Image.open(image)
        st.image(img, width=250)

        if st.button("Analyze"):
            with st.spinner("Analyzing..."):
                model = genai.GenerativeModel("gemini-1.5-flash")

                response = model.generate_content([
                    "Identify disease, give confidence %, cause and treatment.",
                    img
                ])

            st.success(response.text)

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
