import re

from bs4 import BeautifulSoup


# ISO 3166-1 alpha-2 -> country name
ISO_TO_COUNTRY: dict[str, str] = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AR": "Argentina",
    "AM": "Armenia", "AU": "Australia", "AT": "Austria", "AZ": "Azerbaijan",
    "BH": "Bahrain", "BD": "Bangladesh", "BY": "Belarus", "BE": "Belgium",
    "BO": "Bolivia", "BA": "Bosnia and Herzegovina", "BR": "Brazil",
    "BG": "Bulgaria", "CM": "Cameroon", "CA": "Canada", "CL": "Chile",
    "CN": "China", "CO": "Colombia", "CD": "DR Congo", "CG": "Republic of the Congo",
    "CR": "Costa Rica", "HR": "Croatia", "CU": "Cuba", "CY": "Cyprus",
    "CZ": "Czech Republic", "DK": "Denmark", "DO": "Dominican Republic",
    "EC": "Ecuador", "EG": "Egypt", "SV": "El Salvador", "EE": "Estonia",
    "FI": "Finland", "FR": "France", "GE": "Georgia", "DE": "Germany",
    "GH": "Ghana", "GR": "Greece", "GU": "Guam", "GT": "Guatemala",
    "GY": "Guyana", "HN": "Honduras", "HK": "Hong Kong", "HU": "Hungary",
    "IS": "Iceland", "IN": "India", "ID": "Indonesia", "IR": "Iran",
    "IQ": "Iraq", "IE": "Ireland", "IL": "Israel", "IT": "Italy",
    "JM": "Jamaica", "JP": "Japan", "JO": "Jordan", "KZ": "Kazakhstan",
    "KE": "Kenya", "XK": "Kosovo", "KW": "Kuwait", "KG": "Kyrgyzstan",
    "LV": "Latvia", "LB": "Lebanon", "LT": "Lithuania", "LU": "Luxembourg",
    "MK": "North Macedonia", "MY": "Malaysia", "MX": "Mexico", "MD": "Moldova",
    "MN": "Mongolia", "ME": "Montenegro", "MA": "Morocco", "MM": "Myanmar",
    "NP": "Nepal", "NL": "Netherlands", "NZ": "New Zealand", "NI": "Nicaragua",
    "NG": "Nigeria", "NO": "Norway", "PK": "Pakistan", "PS": "Palestine",
    "PA": "Panama", "PY": "Paraguay", "PE": "Peru", "PH": "Philippines",
    "PL": "Poland", "PT": "Portugal", "PR": "Puerto Rico", "RO": "Romania",
    "RU": "Russia", "SA": "Saudi Arabia", "SN": "Senegal", "RS": "Serbia",
    "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia", "ZA": "South Africa",
    "KR": "South Korea", "ES": "Spain", "LK": "Sri Lanka", "SE": "Sweden",
    "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan", "TJ": "Tajikistan",
    "TH": "Thailand", "TN": "Tunisia", "TR": "Turkey", "TM": "Turkmenistan",
    "UA": "Ukraine", "AE": "United Arab Emirates", "GB": "United Kingdom",
    "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan",
    "VE": "Venezuela", "VN": "Vietnam", "TT": "Trinidad and Tobago",
    "SR": "Suriname", "EN": "England", "SC": "Scotland", "WA": "Wales",
}


def extract_nationality_from_tapology_profile(detail_html: str) -> str | None:
    soup = BeautifulSoup(detail_html, "html.parser")
    flag_img = soup.select_one('img[src*="/flags/"]')
    if not flag_img:
        return None

    match = re.search(r"/flags/([A-Z]{2})", flag_img["src"])
    if not match:
        return None

    return ISO_TO_COUNTRY.get(match.group(1))
