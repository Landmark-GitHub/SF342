# import streamlit as st
# import pandas as pd
# import os
# import re

# # STORAGE_PATH = os.path.join("FrontIII/storage", "raw_data", "data_api.csv")
# STORAGE_PATH = [ 
# os.path.join( 
# "storage", 
# "raw_data", 
# "data_api.csv", 
# ), 
# r"FrontIII/storage/raw_data/data_api.csv", 
# ]

# # =========================================================
# # LOAD RAW DATA
# # =========================================================

# # @st.cache_data
# # def load_initial_data():
# #     # ตรวจสอบว่ามีไฟล์อยู่จริง และไฟล์มีขนาดมากกว่า 0 bytes
# #     if os.path.exists(STORAGE_PATH) and os.path.getsize(STORAGE_PATH) > 0:
# #         try:
# #             return pd.read_csv(STORAGE_PATH)
# #         except pd.errors.EmptyDataError:
# #             # กรณีไฟล์มีแต่ช่องว่าง (whitespace)
# #             return pd.DataFrame()

# #     return pd.DataFrame()

# @st.cache_data
# def load_initial_data():

#     if os.path.exists(STORAGE_PATH) and os.path.getsize(STORAGE_PATH) > 0:
#         try:
#             df = pd.read_csv(STORAGE_PATH)

#             # ล้างชื่อ column
#             df.columns = (
#                 df.columns
#                 .str.strip()
#                 .str.lower()
#             )

#             return df

#         except pd.errors.EmptyDataError:
#             return pd.DataFrame()

#     return pd.DataFrame()



import streamlit as st
import pandas as pd
import os
import re

STORAGE_PATHS = [
    os.path.join(
        "storage",
        "raw_data",
        "data_api.csv",
    ),
    r"FrontIII/storage/raw_data/data_api.csv",
]

# =========================================================
# FIND VALID PATH
# =========================================================

def get_storage_path():

    for path in STORAGE_PATHS:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path

    raise FileNotFoundError("ไม่พบไฟล์ data_api.csv")


# =========================================================
# LOAD RAW DATA
# =========================================================

@st.cache_data
def load_initial_data():

    storage_path = get_storage_path()

    try:
        df = pd.read_csv(storage_path)

        # ล้างชื่อ column
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )

        return df

    except pd.errors.EmptyDataError:
        return pd.DataFrame()



# =========================================================
# CONTINENT KEYWORDS
# =========================================================
# ══════════════════════════════════════════════════════════════════
# ตรวจจับทวีปจาก profile
# ══════════════════════════════════════════════════════════════════
CONTINENT_KEYWORDS = {
    "เอเชีย": [
        "thailand", "bangkok", "chiang mai", "phuket", "singapore", 
        "malaysia", "kuala lumpur", "indonesia", "jakarta", "bali",
        "vietnam", "hanoi", "ho chi minh", "philippines", "manila",
        "cambodia", "phnom penh", "myanmar", "naypyidaw", "yangon", 
        "laos", "vientiane", "brunei", "bandar seri begawan",
        "china", "beijing", "shanghai", "guangzhou", "hong kong", "macau",
        "japan", "tokyo", "osaka", "kyoto", "yokohama", "nagoya",
        "south korea", "seoul", "busan", "incheon", "north korea", "pyongyang",
        "taiwan", "taipei", "mongolia", "ulaanbaatar",
        "india", "new delhi", "mumbai", "kolkata", "bangalore",
        "pakistan", "islamabad", "karachi", "bangladesh", "dhaka", 
        "sri lanka", "colombo", "sri jayawardenepura kotte", "nepal", "kathmandu",
        "bhutan", "thimphu", "maldives", "male", "kazakhstan", "astana", 
        "uzbekistan", "tashkent", "turkmenistan", "ashgabat", "kyrgyzstan", "bishkek", 
        "tajikistan", "dushanbe", "iran", "tehran", "iraq", "baghdad",
        "saudi arabia", "riyadh", "jeddah", "mecca", "medina",
        "turkey", "ankara", "istanbul", "israel", "tel aviv", "jerusalem",
        "jordan", "amman", "lebanon", "beirut", "syria", "damascus",
        "uae", "united arab emirates", "dubai", "abu dhabi", 
        "qatar", "doha", "kuwait", "kuwait city", "bahrain", "manama", 
        "oman", "muscat", "yemen", "sana'a", "cyprus", "nicosia", 
        "afghanistan", "kabul", "armenia", "yerevan", "azerbaijan", "baku", "georgia", "tbilisi"
    ],
    "ยุโรป": [
        "switzerland", "bern", "zurich", "geneva",
        "germany", "berlin", "munich", "hamburg", "frankfurt",
        "france", "paris", "lyon", "marseille", "nice",
        "uk", "united kingdom", "london", "manchester", "birmingham", "edinburgh", "glasgow",
        "netherlands", "amsterdam", "the hague", "rotterdam",
        "italy", "rome", "milan", "naples", "venice", "florence",
        "spain", "madrid", "barcelona", "valencia", "seville",
        "sweden", "stockholm", "norway", "oslo", "denmark", "copenhagen", 
        "finland", "helsinki", "iceland", "reykjavik",
        "belgium", "brussels", "austria", "vienna", "poland", "warsaw", 
        "portugal", "lisbon", "czech republic", "prague", "hungary", "budapest",
        "romania", "bucharest", "greece", "athens", "russia", "moscow", "saint petersburg",
        "ukraine", "kyiv", "ireland", "dublin", "croatia", "zagreb", 
        "serbia", "belgrade", "slovakia", "bratislava", "slovenia", "ljubljana",
        "bulgaria", "sofia", "luxembourg", "malta", "valletta",
        "estonia", "tallinn", "latvia", "riga", "lithuania", "vilnius", 
        "moldova", "chisinau", "belarus", "minsk", "albania", "tirana", 
        "north macedonia", "skopje", "bosnia", "sarajevo", "montenegro", "podgorica", 
        "kosovo", "pristina", "monaco", "san marino", "vatican city", "andorra", "andorra la vella"
    ],
    "อเมริกาเหนือ": [
        "usa", "united states", "america", "washington d.c.", "new york", "los angeles", 
        "chicago", "houston", "san francisco", "miami", "seattle", "boston",
        "canada", "ottawa", "toronto", "vancouver", "montreal", "calgary",
        "mexico", "mexico city", "cancun", "guadalajara",
        "cuba", "havana", "dominican republic", "santo domingo", "puerto rico", "san juan", 
        "jamaica", "kingston", "haiti", "port-au-prince", "honduras", "tegucigalpa", 
        "guatemala", "guatemala city", "el salvador", "san salvador", "nicaragua", "managua",
        "costa rica", "san jose", "panama", "panama city", "belize", "belmopan", 
        "bahamas", "nassau", "trinidad and tobago", "port of spain", "barbados", "bridgetown"
    ],
    "อเมริกาใต้": [
        "brazil", "brasilia", "sao paulo", "rio de janeiro",
        "argentina", "buenos aires", "colombia", "bogota",
        "chile", "santiago", "peru", "lima", "venezuela", "caracas", 
        "ecuador", "quito", "bolivia", "la paz", "sucre",
        "paraguay", "asuncion", "uruguay", "montevideo", 
        "guyana", "georgetown", "suriname", "paramaribo", "french guiana", "cayenne"
    ],
    "แอฟริกา": [
        "egypt", "cairo", "alexandria", "south africa", "pretoria", "cape town", "johannesburg",
        "nigeria", "abuja", "lagos", "kenya", "nairobi", "ethiopia", "addis ababa",
        "morocco", "rabat", "casablanca", "marrakesh", "algeria", "algiers",
        "tunisia", "tunis", "libya", "tripoli", "ghana", "accra", 
        "tanzania", "dodoma", "dar es salaam", "uganda", "kampala", 
        "senegal", "dakar", "angola", "luanda", "mozambique", "maputo",
        "zimbabwe", "harare", "zambia", "lusaka", "cameroon", "yaounde",
        "ivory coast", "yamoussoukro", "abidjan", "sudan", "khartoum", 
        "somalia", "mogadishu", "mali", "bamako", "niger", "niamey",
        "rwanda", "kigali", "burundi", "gitega", "madagascar", "antananarivo",
        "namibia", "windhoek", "botswana", "gaborone", "malawi", "lilongwe",
        "liberia", "monrovia", "sierra leone", "freetown", "congo", "brazzaville", 
        "drc", "kinshasa", "djibouti", "eritrea", "asmara", "mauritius", "port louis", "seychelles", "victoria"
    ],
    "โอเชียเนีย": [
        "australia", "canberra", "sydney", "melbourne", "brisbane", "perth",
        "new zealand", "wellington", "auckland", "fiji", "suva", 
        "papua new guinea", "port moresby", "samoa", "apia", 
        "tonga", "nuku'alofa", "vanuatu", "port vila", "solomon islands", "honiara",
        "kiribati", "palau", "micronesia", "marshall islands", "nauru", "tuvalu"
    ],
    "แอนตาร์กติกา": [
        "antarctica", "mcmurdo station", "amundsen-scott", "vostok station", 
        "palmer station", "south pole", "esperanza base", "mawson station"
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

    # ตรวจสอบว่ามี column profile หรือไม่
    if "profile" not in df.columns:
        df["profile"] = ""

    df["continent"] = df["profile"].apply(
        detect_continent
    )

    return df


# =========================================================
# AUTHORS
# =========================================================

@st.cache_data
# def get_unique_authors(df):

#     return (
#         df.sort_values(
#             "expertise_score",
#             ascending=False
#         )
#         .drop_duplicates(subset="author_id")
#         .reset_index(drop=True)
#     )
def get_unique_authors(df):

    df = df.copy()

    # กันไม่มี column
    if "expertise_score" not in df.columns:
        df["expertise_score"] = 0

    if "author_id" not in df.columns:
        df["author_id"] = range(len(df))

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
