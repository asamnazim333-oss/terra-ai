import streamlit as st
import requests
import os
import base64
import datetime
from openai import OpenAI
from google import genai
from PIL import Image


# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="🌾 ZameenAI Ultra",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_KEY = st.secrets["OPENWEATHER_API_KEY"]
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
# =============================
# GROQ CLIENT (ONLY 1 API)
# =============================
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# =============================
# SYSTEM PROMPT (FARMING ONLY)
# =============================
SYSTEM_PROMPT = """
You are ZameenAI, an expert agricultural assistant for Pakistan.
You ONLY answer questions related to:
-This app ZameenAI Ultra
- Farming
- Crops
- Soil
- Fertilizers
- Irrigation
- Weather for agriculture
- Pests & diseases
- Yield, harvesting, farm management
If the question is NOT related to farming,
reply exactly:
"I can only help with farming and agriculture-related questions."
"""

FARMING_KEYWORDS = [
    "crop","wheat","rice","maize","cotton","sugarcane",
    "fertilizer","soil","irrigation","pest","disease",
    "harvest","yield","farm","agriculture","weather"
]

def is_farming_question(text):
    return any(word in text.lower() for word in FARMING_KEYWORDS)

# =============================
# HEADER
# =============================
st.title("🌾 ZameenAI Ultra")
st.caption("AI Powered Smart Farming Decision System")

# =============================
# MENU
# =============================
menu = st.radio(
    "Navigation Menu", 
    ["🌦 Weather", "🦠 Disease Detection", "💬 Chatbot","🤖 Smart Advisory","🌾 Crop Estimator", "🧪 Fertilizer AI",  "📈 Market & Profit", "📅 Crop Calendar"],
    horizontal=True,
    label_visibility="collapsed"
)

# =============================
# WEATHER
# =============================

if menu == "🌦 Weather":

    st.subheader("🌦 Live Weather")
    city = st.text_input("Enter City Name")

    if st.button("Get Weather"):

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:

            temp = data["main"]["temp"]
            wind = data["wind"]["speed"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]

            st.success(f"🌡 Temperature: {temp}°C")
            st.info(f"💨 Wind Speed: {wind} m/s")
            st.write(f"💧 Humidity: {humidity}%")
            st.write(f"🌥 Condition: {description}")

        else:
            st.error("City not found")

# =============================
# CROP ESTIMATOR
# =============================
elif menu == "🌾 Crop Estimator":

    st.subheader("🌾 Crop Cost & Yield Estimator")

    crops = {
        "Wheat": {"cost": 50000, "yield": 30},
        "Rice": {"cost": 60000, "yield": 35},
        "Maize": {"cost": 45000, "yield": 28},
        "Sugarcane": {"cost": 80000, "yield": 60},
        "Cotton": {"cost": 70000, "yield": 25}
    }

    crop = st.selectbox("Select Crop", list(crops.keys()))
    area = st.number_input("Land Area (acres)", min_value=1)

    if st.button("Calculate"):
        st.success(f"💰 Cost: Rs {crops[crop]['cost'] * area}")
        st.info(f"🌾 Yield: {crops[crop]['yield'] * area} maunds")

# =============================
# MARKET & PROFIT
# =============================
elif menu == "📈 Market & Profit":

    st.subheader("📈 Profit Predictor")

    prices = {
        "Wheat": 3900,
        "Rice": 4500,
        "Maize": 3500,
        "Sugarcane": 3000,
        "Cotton": 8500
    }

    crop = st.selectbox("Crop", list(prices.keys()))
    area = st.number_input("Land Area (acres)", min_value=1)

    if st.button("Predict"):
        revenue = prices[crop] * area * 30
        cost = 50000 * area
        st.success(f"💰 Revenue: Rs {revenue}")
        st.info(f"🏆 Profit: Rs {revenue - cost}")

# =============================
# FERTILIZER AI
# =============================
elif menu == "🧪 Fertilizer AI":

    st.subheader("🧪 Fertilizer Recommendation")
    crop = st.text_input("Crop Name")

    if st.button("Recommend"):
        if crop.lower() == "wheat":
            st.success("Use Urea + DAP in split doses")
        elif crop.lower() == "rice":
            st.success("Use NPK 20-20-20, maintain flooded field")
        else:
            st.info("Use balanced NPK with organic compost")

# =============================
# CROP CALENDAR
# =============================
# =============================
# CROP CALENDAR (WITH DROPDOWN)
# =============================
elif menu == "📅 Crop Calendar":
    st.subheader("📅 Pakistan Crop Calendar")
    st.write("Select a month to see the recommended agricultural activities.")

    # List of months for the dropdown
    months_list = [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Get current month to set as default index
    current_month_str = datetime.datetime.now().strftime("%B")
    default_index = months_list.index(current_month_str)
    
    # Expanded Calendar Data
    calendar_data = {
        "January": "🌾 **Wheat:** Apply second irrigation and urea. Prepare land for spring vegetables like gourds.",
        "February": "🥔 **Potato:** Harvesting begins. **Sugarcane:** Ideal time for spring planting.",
        "March": "☁️ **Cotton:** Start land preparation. **Sunflower:** Sowing should be completed this month.",
        "April": "🌾 **Rice:** Prepare nurseries for Basmati. **Wheat:** Harvesting starts in Sindh and Southern Punjab.",
        "May": "🎋 **Sugarcane:** Focus on irrigation and hoeing. **Cotton:** Peak sowing time in Punjab.",
        "June": "🌱 **Rice:** Transplantation to main fields. **Maize:** Sowing for the autumn crop begins.",
        "July": "🌽 **Monsoon Crops:** Maintenance of Maize and Sugarcane. Ensure proper drainage for rain.",
        "August": "🐛 **Cotton:** Critical month for pest scouting (Whitefly/Bollworms). **Pulses:** Sowing of Mung and Mash beans.",
        "September": "🌾 **Rice:** Early varieties (like KS-282) are ready for harvest. **Mustard:** Start sowing Toria.",
        "October": "🚜 **Wheat Prep:** Land preparation is key. **Oilseeds:** Best time for sowing Mustard and Canola.",
        "November": "🌾 **Wheat:** Peak sowing time for maximum yield. **Sugarcane:** Harvesting and crushing season begins.",
        "December": "🥦 **Vegetables:** Care for winter crops (Cabbage, Radish). **Wheat:** Apply first irrigation (Kor) 20-25 days after sowing."
    }

    # Month Selection Dropdown
    selected_month = st.selectbox("Select Month:", months_list, index=default_index)

    # Displaying the Result
    st.markdown(f"---")
    st.markdown(f"### 🗓️ Agricultural Activities for **{selected_month}**")
    st.success(calendar_data.get(selected_month))
    
    # Highlight if it's the current month
    if selected_month == current_month_str:
        st.info(f"✨ **Note:** This is the current month. Prioritize these tasks for your farm.")
# =============================
# SMART ADVISORY (AI)
# =============================
elif menu == "🤖 Smart Advisory":

    st.subheader("🤖 AI Farming Advisory")

    crop = st.text_input("Crop")
    soil = st.selectbox("Soil Type", ["Sandy", "Clay", "Loamy"])
    season = st.selectbox("Season", ["Summer", "Winter", "Monsoon", "Spring"])

    if st.button("Generate Advisory"):
        prompt = f"""
        Crop: {crop}
        Soil: {soil}
        Season: {season}
        Give farming advice.
        """
        response = client.responses.create(
            model="openai/gpt-oss-20b",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_output_tokens=1000
        )
        st.write(response.output_text)

# =============================
# CHATBOT (FARMING ONLY)
# =============================
elif menu == "💬 Chatbot":

    st.subheader("💬 Farming Assistant Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input("Ask farming question..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        if not is_farming_question(user_input):
            reply = "🌾 I can only help with farming and agriculture-related questions."
        else:
            response = client.responses.create(
                model="openai/gpt-oss-20b",
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                max_output_tokens=1000
            )
            reply = response.output_text

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)


# =============================
# DISEASE DETECTION (BYPASS 403)
# =============================
elif menu == "🦠 Disease Detection":
    st.subheader("🦠 Crop Disease Detection")
    st.write("Take a picture of crop or upload")

    # Form use karne se Axios error bypass ho jata hai
    with st.form("disease_form", clear_on_submit=True):
        # Option 1: Mobile Camera (Best for farmers)
        cam_image = st.camera_input("Take a photo of the leaf")
        
        # Option 2: File Upload (If camera not available)
        file_image = st.file_uploader("Select File", type=["jpg", "jpeg", "png"])
        
        submit_button = st.form_submit_button("Check Disease")

    # Image processing logic
    target_image = cam_image if cam_image is not None else file_image

    if target_image is not None and submit_button:
        try:
            # Step 1: Image ko open aur compress karein
            img = Image.open(target_image)
            
            # AI ke liye 1024px kafi hai, is se Axios crash nahi hota
            img.thumbnail((1024, 1024))
            
            # st.image(img, caption="Processing Image...", width=300)

            with st.spinner("Checking..."):
                # prompt
                prompt = """
                    You are an expert plant pathologist for Pakistan's crops. 
                    Analyze this image of a  plant. 
                    1. Name the disease.
                    2. Give a brief explanation of why it happened.
                    3. Suggest organic (desi) and chemical remedies.
                    4.Answer briefly in 200 words max.
                    If the plant is healthy, congratulate the farmer.
                    """
                
                # Gemini Client Call
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt, img]
                )
                
                st.success("✅ Analysis Result:")
                st.markdown(response.text)

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Agar Axios 403 aaye, toh photo ka size kam karein ya camera input use karein.")
