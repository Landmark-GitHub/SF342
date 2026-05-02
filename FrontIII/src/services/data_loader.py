import streamlit as st
import pandas as pd
import os
import re

STORAGE_PATH = os.path.join("storage", "raw_data", "data_api.csv")

# =========================================================
# LOAD RAW DATA
# =========================================================

@st.cache_data
def load_initial_data():

    if os.path.exists(STORAGE_PATH):
        return pd.read_csv(STORAGE_PATH)

    return pd.DataFrame()


# =========================================================
# CONTINENT KEYWORDS
# =========================================================
# ══════════════════════════════════════════════════════════════════
# ตรวจจับทวีปจาก profile
# ══════════════════════════════════════════════════════════════════
CONTINENT_KEYWORDS = {
    "เอเชีย": [
        "thailand", "thai", "bangkok", "chiang mai", "chulalongkorn",
        "mahidol", "thammasat", "khon kaen", "chiang rai", "naresuan",
        "singapore", "malaysia", "kuala lumpur", "indonesia", "jakarta",
        "vietnam", "hanoi", "ho chi minh", "philippines", "manila",
        "cambodia", "phnom penh", "myanmar", "yangon", "laos", "brunei",
        "china", "beijing", "shanghai", "guangzhou", "hong kong", "macau",
        "japan", "tokyo", "osaka", "kyoto", "yokohama",
        "korea", "seoul", "busan", "south korea", "taiwan", "taipei",
        "mongolia", "ulaanbaatar",
        "india", "new delhi", "mumbai", "kolkata", "bangalore", "chennai",
        "pakistan", "islamabad", "karachi", "lahore",
        "bangladesh", "dhaka", "sri lanka", "colombo", "nepal", "kathmandu",
        "bhutan", "maldives", "kazakhstan", "uzbekistan", "kyrgyzstan",
        "iran", "tehran", "iraq", "baghdad",
        "saudi arabia", "riyadh", "jeddah",
        "turkey", "ankara", "istanbul",
        "israel", "tel aviv", "jerusalem",
        "jordan", "amman", "lebanon", "beirut",
        "uae", "dubai", "abu dhabi", "united arab emirates",
        "qatar", "doha", "kuwait", "bahrain", "oman",
        "yemen", "syria", "cyprus", "afghanistan", "Viet Nam",
    ],
    "ยุโรป": [
        "switzerland", "bern", "zurich", "geneva",
        "germany", "berlin", "munich", "hamburg", "cologne",
        "france", "paris", "lyon", "marseille",
        "uk", "united kingdom", "london", "england", "scotland", "wales",
        "netherlands", "amsterdam", "rotterdam",
        "italy", "rome", "milan", "naples",
        "spain", "madrid", "barcelona",
        "sweden", "stockholm", "norway", "oslo",
        "denmark", "copenhagen", "finland", "helsinki",
        "belgium", "brussels", "austria", "vienna",
        "poland", "warsaw", "portugal", "lisbon",
        "czech", "prague", "hungary", "budapest",
        "romania", "bucharest", "greece", "athens",
        "russia", "moscow", "saint petersburg",
        "ukraine", "kyiv", "ireland", "dublin",
        "croatia", "serbia", "slovakia", "slovenia",
        "bulgaria", "luxembourg", "malta", "iceland",
        "estonia", "latvia", "lithuania", "moldova", "belarus",
        "albania", "north macedonia", "bosnia", "montenegro", "kosovo",
    ],
    "อเมริกาเหนือ": [
        "usa", "united states", "u.s.", "u.s.a.", "america",
        "new york", "los angeles", "chicago", "houston", "phoenix",
        "philadelphia", "san antonio", "san diego", "dallas", "san jose",
        "atlanta", "boston", "seattle", "washington", "miami",
        "san francisco", "denver", "detroit", "minneapolis", "portland",
        "california", "texas", "florida", "ohio", "georgia",
        "massachusetts", "michigan", "illinois",
        "canada", "toronto", "montreal", "vancouver", "ottawa", "calgary",
        "mexico", "mexico city", "guadalajara", "monterrey",
        "cuba", "havana", "dominican republic", "puerto rico", "jamaica",
        "haiti", "honduras", "guatemala", "el salvador", "nicaragua",
        "costa rica", "panama", "belize", "bahamas", "trinidad",
    ],
    "อเมริกาใต้": [
        "brazil", "sao paulo", "rio de janeiro", "brasilia",
        "argentina", "buenos aires", "cordoba",
        "colombia", "bogota", "medellin",
        "chile", "santiago", "peru", "lima",
        "venezuela", "caracas", "ecuador", "quito",
        "bolivia", "la paz", "paraguay", "uruguay", "guyana", "suriname",
    ],
    "แอฟริกา": [
        "south africa", "johannesburg", "cape town", "pretoria", "durban",
        "nigeria", "lagos", "abuja", "kenya", "nairobi",
        "ethiopia", "addis ababa", "egypt", "cairo", "alexandria",
        "ghana", "accra", "tanzania", "dar es salaam",
        "uganda", "kampala", "senegal", "dakar",
        "morocco", "casablanca", "rabat", "algeria", "algiers",
        "tunisia", "tunis", "angola", "luanda",
        "mozambique", "zimbabwe", "zambia", "cameroon",
        "ivory coast", "sudan", "somalia", "mali", "niger",
        "rwanda", "burundi", "madagascar", "namibia", "botswana",
        "malawi", "liberia", "sierra leone", "guinea", "congo",
        "djibouti", "eritrea", "comoros", "mauritius", "seychelles",
    ],
    "โอเชียเนีย": [
        "australia", "sydney", "melbourne", "brisbane", "perth", "adelaide",
        "new zealand", "auckland", "wellington", "christchurch",
        "fiji", "suva", "papua new guinea", "port moresby",
        "samoa", "tonga", "vanuatu", "solomon islands", "pacific", "oceania",
    ],
    "แอนตาร์กติกา": [
        "antarctica", "mcmurdo", "amundsen-scott", "vostok station", 
        "palmer station", "south pole"
    ],
}


# =========================================================
# COMPILE REGEX
# =========================================================

PATTERNS = {
    continent: re.compile(
        "|".join(map(re.escape, keywords)),
        re.IGNORECASE
    )
    for continent, keywords in CONTINENT_KEYWORDS.items()
}


# =========================================================
# DETECT CONTINENT
# =========================================================

def detect_continent(profile):

    if pd.isna(profile):
        return "ไม่ทราบ"

    text = str(profile)

    for continent, pattern in PATTERNS.items():

        if pattern.search(text):
            return continent

    return "ไม่ทราบ"


# =========================================================
# ENRICH DATA
# =========================================================

@st.cache_data
def enrich_with_continent(df):

    df = df.copy()

    df["continent"] = df["profile"].apply(
        detect_continent
    )

    return df


# =========================================================
# AUTHORS
# =========================================================

@st.cache_data
def get_unique_authors(df):

    return (
        df.sort_values(
            "expertise_score",
            ascending=False
        )
        .drop_duplicates(subset="author_id")
        .reset_index(drop=True)
    )


# =========================================================
# MAIN PREPARE FUNCTION
# =========================================================

@st.cache_data
def prepare_all_data():

    df_raw = load_initial_data()

    df = enrich_with_continent(df_raw)

    authors = get_unique_authors(df)

    return {
        "df_raw": df_raw,
        "df": df,
        "authors": authors,
    }