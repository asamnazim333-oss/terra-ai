import streamlit as st
import requests
import os
from datetime import datetime
from PIL import Image
from openai import OpenAI
from google import genai

# ================= CONFIG =================
st.set_page_config(page_title="🌍 ZameenAI Global", layout="wide")

# ================= API KEYS =================
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

groq_client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ================= HEADER =================
st.title("🌍 ZameenAI Global")
st.caption("AI Copilot for Smart Farming")

# ================= SIDEBAR =================
menu = st.sidebar.radio("Navigation", [
    "🌦 Weather Intelligence",
    "📊 Market Prices",
    "🤖 AI Advisory",
    "🦠 Disease Detection",
    "💬 AI Copilot",
    "📈 Yield Predictor"
])

# ================= WEATHER =================
if menu == "🌦 Weather Intelligence":
    st.header("🌦 Smart Weather Insights")

    city = st.text_input("Enter City")

    if st.button("Get Weather"):
        with st.spinner("Fetching weather..."):
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
            res = requests.get(url).json()

            if res.get("cod") == 200:
                col1, col2, col3 = st.columns(3)

                col1.metric("🌡 Temp", f"{res['main']['temp']}°C")
                col2.metric("💧 Humidity", f"{res['main']['humidity']}%")
                col3.metric("💨 Wind", f"{res['wind']['speed']} m/s")

                st.info(f"Condition: {res['weather'][0]['description']}")

                # Smart Alerts
                if res['main']['temp'] > 35:
                    st.warning("🔥 Heat stress risk for crops!")
                if res['main']['temp'] < 5:
                    st.warning("❄️ Frost risk!")

            else:
                st.error("City not found")

# ================= MARKET =================
elif menu == "📊 Market Prices":
    st.header("📊 Market Insights")

    st.info("Demo market data (replace with USDA API later)")

    crops = ["Wheat", "Rice", "Maize", "Cotton"]
    price = [4000, 4500, 3500, 8500]

    for i in range(len(crops)):
        st.metric(crops[i], f"Rs {price[i]}")

# ================= AI ADVISORY =================
elif menu == "🤖 AI Advisory":
    st.header("🤖 Smart Farming Advisor")

    crop = st.text_input("Crop")
    soil = st.selectbox("Soil", ["Sandy", "Clay", "Loamy"])
    weather = st.selectbox("Weather", ["Hot", "Cold", "Rainy"])

    if st.button("Generate Advice"):
        prompt = f"""
        Give professional farming advice:
        Crop: {crop}
        Soil: {soil}
        Weather: {weather}
        """

        with st.spinner("Thinking..."):
            response = groq_client.responses.create(
                model="openai/gpt-oss-20b",
                input=prompt,
                max_output_tokens=500
            )

            st.success(response.output_text)

# ================= DISEASE DETECTION =================
elif menu == "🦠 Disease Detection":
    st.header("🦠 Crop Disease Detection")

    image = st.file_uploader("Upload leaf image", type=["jpg", "png"])

    if image:
        img = Image.open(image)
        st.image(img, width=250)

        if st.button("Analyze"):
            with st.spinner("Analyzing..."):
                prompt = """
                Identify plant disease, give reason and treatment.
                """

                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, img]
                )

                st.success(response.text)

# ================= AI CHATBOT =================
elif menu == "💬 AI Copilot":
    st.header("💬 AI Farming Copilot")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("Ask anything about farming...")

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

# ================= YIELD PREDICTOR =================
elif menu == "📈 Yield Predictor":
    st.header("📈 AI Yield Estimator")

    area = st.number_input("Land (acres)", 1)
    rainfall = st.slider("Rainfall (mm)", 0, 500, 100)
    temp = st.slider("Temperature (°C)", 0, 50, 25)

    if st.button("Predict Yield"):
        # Simple ML logic (replace with model later)
        yield_est = (area * 30) + (rainfall * 0.1) - (temp * 0.5)

        st.success(f"Estimated Yield: {round(yield_est,2)} units")
