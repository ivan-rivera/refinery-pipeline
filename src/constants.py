"""Project-wide constants."""

from pathlib import Path

REDDIT_USER_AGENT = "refinery-pipeline/0.6.0"
REDDIT_BASE_URL = "https://www.reddit.com"
REDDIT_MAX_THREADS = 10
REDDIT_MAX_COMMENTS = 15
REDDIT_MAX_COMMENT_CHARS = 300
REDDIT_MAX_BODY_CHARS = 500
REDDIT_THROTTLE_SECONDS = 1.0
PRECIOUS_METALS_SUBREDDITS = ["wallstreetsilver", "goldsilver", "mining", "investing"]

EDGAR_THROTTLE_SECONDS = 0.2
EDGAR_CACHE_FILE = Path("data/cache/edgar_13f_cache.json")

EDGAR_INSTITUTIONAL_CIKS: dict[str, int] = {
    # Precious metals specialists
    "VAN ECK ASSOCIATES CORP": 869178,
    "SPROTT INC.": 1512920,
    "U S GLOBAL INVESTORS INC": 754811,
    "TOCQUEVILLE ASSET MANAGEMENT L.P.": 883961,
    "Merk Investments LLC": 1302842,
    "GAMCO INVESTORS, INC.": 807249,
    "GABELLI FUNDS LLC": 1081407,
    "First Eagle Investment Management, LLC": 1325447,
    "PAULSON & CO. INC.": 1035674,
    "Ruffer LLP": 1426859,
    "STANSBERRY ASSET MANAGEMENT, LLC": 1725910,
    "MIRAE ASSET GLOBAL ETFS HOLDINGS Ltd.": 1705339,
    # Sector-active managers
    "ALTRINSIC GLOBAL ADVISORS LLC": 1167388,
    "Orbis Allan Gray Ltd": 1663865,
    "Nexus Investment Management ULC": 1476329,
    "SCHRODER INVESTMENT MANAGEMENT GROUP": 1086619,
    "AGF MANAGEMENT LTD": 1003518,
    "Epoch Investment Partners, Inc.": 1305841,
    # Large passive / index
    "VANGUARD GROUP INC": 102909,
    "STATE STREET CORP": 93751,
    "BlackRock, Inc.": 2012383,
    "FMR LLC": 315066,
    "DIMENSIONAL FUND ADVISORS LP": 354204,
    "PRICE T ROWE ASSOCIATES INC /MD/": 80255,
    "FRANKLIN RESOURCES INC": 38777,
    "Capital Research Global Investors": 1422848,
    "WELLINGTON MANAGEMENT GROUP LLP": 902219,
    "Invesco Ltd.": 914208,
    "MORGAN STANLEY": 895421,
    "GOLDMAN SACHS GROUP INC": 886982,
    "JPMORGAN CHASE & CO": 19617,
    "BANK OF AMERICA CORP /DE/": 70858,
    "CITIGROUP INC": 831001,
    "UBS AM": 861177,
    "DEUTSCHE BANK AG": 948046,
    "BNP Paribas Asset Management Holding S.A.": 1520354,
    "BARCLAYS PLC": 312069,
    "Nuveen Asset Management, LLC": 1521019,
    "Pictet Asset Management Holding SA": 1993888,
    # Canadian pension funds / banks
    "TORONTO DOMINION BANK": 947263,
    "CAISSE DE DEPOT ET PLACEMENT DU QUEBEC": 898286,
    "ONTARIO TEACHERS PENSION PLAN BOARD": 937567,
    "MACKENZIE FINANCIAL CORP": 919859,
    "PUBLIC SECTOR PENSION INVESTMENT BOARD": 1396318,
    "BRITISH COLUMBIA INVESTMENT MANAGEMENT Corp": 1228242,
    "Alberta Investment Management Corp": 1463559,
    "CIBC Asset Management Inc": 1021926,
    # Sovereign wealth
    "NORGES BANK": 1374170,
}
