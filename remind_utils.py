import re

COLORS = {  "🟥": 14495300,
            "🟧": 16027660,
            "🟨": 16632664,
            "🟩": 7909721,
            "🟦":5614830,
            "🟪": 11177686,
            "🟫":12675407,
            "⬛":3225405,
            "⬜":15132648}

REV_COLORS = {item : key for key, item in COLORS.items()}

DEFAULT_SERVER_SETTINGS = {"allowed_roles" : ["admin", "owner", "Admin", "Owner"],
                           "admin_roles" : ["admin", "owner", "Admin", "Owner"],
                           "react_emojis" : ["👍", "🤞", "👎"],
                           "color" : COLORS["🟩"]
                           }




def time_to_seconds(string:str):
    days = re.findall(r"[\d]+d",string)
    weeks = re.findall(r"[\d]+w",string)
    hours = re.findall(r"[\d+]+h",string)
    minutes = re.findall(r"[\d]+m",string)

    list = [days,weeks,hours,minutes]

    def refine(i):
        if len(i) == 0 :
            return 0
        else:
            return int(i[0][0:-1])

    days = refine(days)
    weeks = refine(weeks)
    hours = refine(hours)
    minutes = refine(minutes)


    return minutes * 60 + hours * 3600 + weeks * 604800 + days * 86400

