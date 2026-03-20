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

#==========Crop Calendar=============
elif menu == "📅 Crop Calendar":

    st.subheader("📅 Seasonal Crop Calendar (Pakistan)")

    # Crop Data
    crops_data = {
        "Wheat": {
            "sowing": ["November", "December"],
            "harvest": ["April", "May"],
            "use": "Staple food crop (flour, roti, bread)"
        },
        "Rice": {
            "sowing": ["June", "July"],
            "harvest": ["October", "November"],
            "use": "Staple food crop (boiled rice, export)"
        },
        "Maize": {
            "sowing": ["February", "March", "July", "August"],
            "harvest": ["June", "November"],
            "use": "Food, poultry feed, industrial use"
        },
        "Cotton": {
            "sowing": ["April", "May"],
            "harvest": ["September", "October"],
            "use": "Textile industry"
        },
        "Sugarcane": {
            "sowing": ["February", "March", "September", "October"],
            "harvest": ["November", "December", "January", "February", "March"],
            "use": "Sugar production"
        },
        "Mustard": {
            "sowing": ["October", "November"],
            "harvest": ["February", "March"],
            "use": "Cooking oil"
        },
        "Gram (Chickpea)": {
            "sowing": ["October", "November"],
            "harvest": ["March", "April"],
            "use": "Pulse / protein food"
        },
        "Sunflower": {
            "sowing": ["January", "February", "June"],
            "harvest": ["May", "June", "October"],
            "use": "Cooking oil"
        }
    }

    # User selects month
    selected_month = st.selectbox(
        "Select Month",
        ["January","February","March","April","May","June",
         "July","August","September","October","November","December"]
    )

    st.info(f"📆 Selected Month: {selected_month}")

    sowing_crops = []
    harvest_crops = []

    for crop, details in crops_data.items():
        if selected_month in details["sowing"]:
            sowing_crops.append((crop, details["use"]))
        if selected_month in details["harvest"]:
            harvest_crops.append((crop, details["use"]))

    st.markdown("### 🌱 Crops to Sow")

    if sowing_crops:
        for crop, use in sowing_crops:
            st.success(f"🌾 {crop} — Use: {use}")
    else:
        st.write("No major sowing crop this month.")

    st.markdown("### 🌾 Crops to Harvest")

    if harvest_crops:
        for crop, use in harvest_crops:
            st.warning(f"🌾 {crop} — Use: {use}")
    else:
        st.write("No major harvesting crop this month.")


#=========== Market Price and estimator===



elif menu == "📈 Market & Profit":
    st.subheader("📈 Market Price & Profit Predictor")

    # 1️⃣ Select Country
    country = st.selectbox("Select Country", ["Pakistan", "USA", "India"])

    # 2️⃣ Define crop prices for each country (per acre or per unit)
    crop_prices = {
        "Pakistan": {
            "Wheat": 3900,
            "Rice": 4500,
            "Maize": 3500,
            "Sugarcane": 3000,
            "Cotton": 8500,
            "Barley": 2800,
            "Tomato": 6000,
            "Potato": 4500
        },
        "USA": {
            "Wheat": 250,      # Prices in USD
            "Rice": 300,
            "Maize": 220,
            "Sugarcane": 180,
            "Cotton": 500,
            "Barley": 150,
            "Tomato": 350,
            "Potato": 200
        },
        "India": {
            "Wheat": 2000,     # Prices in INR
            "Rice": 2500,
            "Maize": 1800,
            "Sugarcane": 1500,
            "Cotton": 4000,
            "Barley": 1200,
            "Tomato": 2500,
            "Potato": 2000
        }
    }

    # 3️⃣ Currency symbol for display
    currency = {"Pakistan": "Rs", "USA": "$", "India": "₹"}

    # 4️⃣ Select crop and area
    prices = crop_prices[country]
    crop = st.selectbox("Select Crop", list(prices.keys()))
    area = st.number_input("Enter land area (acres)", min_value=1)

    # 5️⃣ Calculate profit
    if st.button("Predict Profit"):
        avg_yield = 30  # average yield per acre
        revenue = avg_yield * area * prices[crop]
        cost = 50000 * area if country != "USA" else 2000 * area  # Example cost difference
        profit = revenue - cost

        st.success(f"💰 Revenue: {currency[country]} {revenue}")
        st.warning(f"📉 Cost: {currency[country]} {cost}")
        st.info(f"🏆 Profit: {currency[country]} {profit}")


#========Crop Estimator =======


elif menu == "🌾 Crop Estimator":
    st.subheader("🌾 Crop Cost & Yield Estimator")

    # 1️⃣ Select Country
    country = st.selectbox("Select Country", ["Pakistan", "USA", "India"])

    # 2️⃣ Currency symbols for display
    currency = {"Pakistan": "Rs", "USA": "$", "India": "₹"}

    # 3️⃣ Crop data per country (cost per acre, yield per acre)
    crop_data = {
        "Pakistan": {
            "Wheat": {"cost": 50000, "yield": 30},
            "Rice": {"cost": 60000, "yield": 35},
            "Maize": {"cost": 45000, "yield": 28},
            "Sugarcane": {"cost": 80000, "yield": 60},
            "Cotton": {"cost": 70000, "yield": 25},
            "Barley": {"cost": 40000, "yield": 20},
            "Tomato": {"cost": 35000, "yield": 15},
            "Potato": {"cost": 30000, "yield": 18},
            "Onion": {"cost": 25000, "yield": 12},
            "Chili": {"cost": 20000, "yield": 10},
            "Mustard": {"cost": 22000, "yield": 14},
            "Soybean": {"cost": 28000, "yield": 16},
            "Sugar beet": {"cost": 50000, "yield": 50},
            "Carrot": {"cost": 18000, "yield": 10},
            "Peas": {"cost": 24000, "yield": 12}
        },
        "USA": {
            "Wheat": {"cost": 2000, "yield": 30},
            "Rice": {"cost": 2500, "yield": 35},
            "Maize": {"cost": 1800, "yield": 28},
            "Sugarcane": {"cost": 4000, "yield": 60},
            "Cotton": {"cost": 3500, "yield": 25},
            "Barley": {"cost": 1500, "yield": 20},
            "Tomato": {"cost": 1200, "yield": 15},
            "Potato": {"cost": 1000, "yield": 18},
            "Onion": {"cost": 900, "yield": 12},
            "Chili": {"cost": 800, "yield": 10},
            "Mustard": {"cost": 850, "yield": 14},
            "Soybean": {"cost": 1100, "yield": 16},
            "Sugar beet": {"cost": 2000, "yield": 50},
            "Carrot": {"cost": 700, "yield": 10},
            "Peas": {"cost": 900, "yield": 12}
        },
        "India": {
            "Wheat": {"cost": 30000, "yield": 30},
            "Rice": {"cost": 35000, "yield": 35},
            "Maize": {"cost": 25000, "yield": 28},
            "Sugarcane": {"cost": 50000, "yield": 60},
            "Cotton": {"cost": 40000, "yield": 25},
            "Barley": {"cost": 20000, "yield": 20},
            "Tomato": {"cost": 18000, "yield": 15},
            "Potato": {"cost": 15000, "yield": 18},
            "Onion": {"cost": 12000, "yield": 12},
            "Chili": {"cost": 10000, "yield": 10},
            "Mustard": {"cost": 11000, "yield": 14},
            "Soybean": {"cost": 15000, "yield": 16},
            "Sugar beet": {"cost": 30000, "yield": 50},
            "Carrot": {"cost": 9000, "yield": 10},
            "Peas": {"cost": 12000, "yield": 12}
        }
    }

    # 4️⃣ Select crop and area
    crops = crop_data[country]
    crop = st.selectbox("Select Crop", list(crops.keys()))
    area = st.number_input("Enter land area (acres)", min_value=1)

    # 5️⃣ Calculate total cost and yield
    if st.button("Calculate"):
        total_cost = crops[crop]["cost"] * area
        total_yield = crops[crop]["yield"] * area

        st.success(f"💰 Estimated Cost: {currency[country]} {total_cost}")
        st.info(f"🌾 Expected Yield: {total_yield} maunds")




#======/Fertilizer AI =========

elif menu == "🧪 Fertilizer AI":
    st.subheader("🧪 Smart Fertilizer Recommendation")

    # 1️⃣ Crop input
    crop = st.text_input("Enter crop name")

    # 2️⃣ Fertilizer recommendations dictionary
    fertilizer_recs = {
        "wheat": "Use Urea + DAP. Apply Nitrogen in split doses.",
        "rice": "Apply NPK 20-20-20 and maintain flooded field.",
        "maize": "Use NPK 16-16-16 and apply Zinc if deficient.",
        "cotton": "Apply Nitrogen + Potash; add gypsum for soil health.",
        "sugarcane": "Use NPK 10-10-20 with organic manure.",
        "barley": "Apply Urea + NPK 12-12-17; ensure proper irrigation.",
        "tomato": "Use NPK 10-10-10 with compost; foliar feeding recommended.",
        "potato": "Apply NPK 15-15-15 and maintain soil moisture.",
        "onion": "Use Nitrogen + Potash; apply Boron if needed.",
        "chili": "Apply NPK 20-20-20 with organic mulch.",
        "mustard": "Use DAP + Urea; apply Sulphur if soil deficient.",
        "soybean": "Apply Rhizobium inoculant and balanced NPK.",
        "sugar beet": "Use NPK 15-15-15; monitor pH for best yield.",
        "carrot": "Apply NPK 10-20-10; compost helps root growth.",
        "peas": "Apply Rhizobium + NPK 12-12-12 for better pods.",
        "maize-sorghum": "Use Urea + NPK 16-16-16; ensure irrigation.",
        "sunflower": "Apply NPK 20-10-10; add Boron for flowering.",
        "cabbage": "Use NPK 15-15-15 and organic compost.",
        "okra": "Apply NPK 10-10-20 with compost; split Nitrogen doses.",
        "millet": "Use NPK 12-12-12; apply Potash for better grain."
    }

    # 3️⃣ Button click
    if st.button("Get Recommendation"):
        crop_lower = crop.strip().lower()
        rec = fertilizer_recs.get(
            crop_lower,
            "Use balanced NPK fertilizer with organic compost for this crop."
        )
        st.success(rec)
# ================= YIELD =================
elif menu == "📈 Yield Predictor":
    st.header("📈 Smart Yield Prediction")

    # 1️⃣ Select country
    country = st.selectbox("Select Country", ["Pakistan", "USA", "India"])

    # 2️⃣ Crop selection with base yield per acre
    crop_base_yield = {
        "Wheat": 30,
        "Rice": 35,
        "Maize": 28,
        "Sugarcane": 60,
        "Cotton": 25,
        "Barley": 20,
        "Tomato": 15,
        "Potato": 18,
        "Onion": 12,
        "Chili": 10,
        "Mustard": 14,
        "Soybean": 16,
        "Sugar beet": 50,
        "Carrot": 10,
        "Peas": 12
    }

    crop = st.selectbox("Select Crop", list(crop_base_yield.keys()))
    area = st.number_input("Land Area (acres)", min_value=1)
    rainfall = st.slider("Rainfall (mm)", 0, 500, 100)
    temp = st.slider("Temperature (°C)", 0, 50, 25)
    soil_quality = st.slider("Soil Quality (1-10)", 1, 10, 5)

    # 3️⃣ Yield Prediction formula
    if st.button("Predict"):
        base_yield = crop_base_yield[crop]
        # Simple predictive formula (can adjust with AI later)
        yield_est = (base_yield * area) + (rainfall * 0.25) - (temp * 0.5) + (soil_quality * 2)

        # Adjust units based on country
        unit = "maunds" if country in ["Pakistan", "India"] else "tons"
        if country in ["USA"]:
            yield_est = yield_est * 0.025  # simple conversion to tons (example)

        st.success(f"🌾 Estimated Yield for {crop}: {round(yield_est,2)} {unit}")
