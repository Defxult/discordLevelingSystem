"""
This local discord leveling system uses the same levels and XP needed values as MEE6.
All credit goes towards the MEE6 developers for providing the "LEVELS_AND_XP" documentation. 

MEE6 documentation can be found here: https://github.com/Mee6/Mee6-documentation
"""

from collections import namedtuple

__all__ = ('LEVELS_AND_XP', 'MAX_XP', 'MAX_LEVEL', '_next_level_details', '_find_level')

LEVELS_AND_XP = {
    "0": 0,
    "1": 100,
    "2": 255,
    "3": 475,
    "4": 770,
    "5": 1150,
    "6": 1625,
    "7": 2205,
    "8": 2900,
    "9": 3720,
    "10": 4675,
    "11": 5775,
    "12": 7030,
    "13": 8450,
    "14": 10045,
    "15": 11825,
    "16": 13800,
    "17": 15980,
    "18": 18375,
    "19": 20995,
    "20": 23850,
    "21": 26950,
    "22": 30305,
    "23": 33925,
    "24": 37820,
    "25": 42000,
    "26": 46475,
    "27": 51255,
    "28": 56350,
    "29": 61770,
    "30": 67525,
    "31": 73625,
    "32": 80080,
    "33": 86900,
    "34": 94095,
    "35": 101675,
    "36": 109650,
    "37": 118030,
    "38": 126825,
    "39": 136045,
    "40": 145700,
    "41": 155800,
    "42": 166355,
    "43": 177375,
    "44": 188870,
    "45": 200850,
    "46": 213325,
    "47": 226305,
    "48": 239800,
    "49": 253820,
    "50": 268375,
    "51": 283475,
    "52": 299130,
    "53": 315350,
    "54": 332145,
    "55": 349525,
    "56": 367500,
    "57": 386080,
    "58": 405275,
    "59": 425095,
    "60": 445550,
    "61": 466650,
    "62": 488405,
    "63": 510825,
    "64": 533920,
    "65": 557700,
    "66": 582175,
    "67": 607355,
    "68": 633250,
    "69": 659870,
    "70": 687225,
    "71": 715325,
    "72": 744180,
    "73": 773800,
    "74": 804195,
    "75": 835375,
    "76": 867350,
    "77": 900130,
    "78": 933725,
    "79": 968145,
    "80": 1003400,
    "81": 1039500,
    "82": 1076455,
    "83": 1114275,
    "84": 1152970,
    "85": 1192550,
    "86": 1233025,
    "87": 1274405,
    "88": 1316700,
    "89": 1359920,
    "90": 1404075,
    "91": 1449175,
    "92": 1495230,
    "93": 1542250,
    "94": 1590245,
    "95": 1639225,
    "96": 1689200,
    "97": 1740180,
    "98": 1792175,
    "99": 1845195,
    "100": 1899250
}

MAX_XP = LEVELS_AND_XP['100']
MAX_LEVEL = 100

def _next_level_details(current_level: int) -> tuple:
    """Returns a `namedtuple`
    
    Attributes
    ----------
    - level (:class:`int`)
    - xp_needed (:class:`int`)
    
        .. changes
            v0.0.2
                Changed return type to a namedtuple instead of tuple
    """
    temp = current_level + 1
    if temp > 100:
        temp = 100
    key = str(temp)
    val = LEVELS_AND_XP[key]
    Details = namedtuple('Details', ['level', 'xp_needed'])
    return Details(level=int(key), xp_needed=val)

def _find_level(current_total_xp: int) -> int:
    """Return the members current level based on their total XP

    NOTE: Do not use this with detecting level ups in :meth:`award_xp`. Pretty much only made for :meth:`add_xp`, :meth:`remove_xp`
    
        .. added:: v0.0.2
    """
    # check if the current xp matches the xp_needed exactly
    if current_total_xp in LEVELS_AND_XP.values():
        for level, xp_needed in LEVELS_AND_XP.items():
            if current_total_xp == xp_needed:
                return int(level)
    else:
        for level, xp_needed in LEVELS_AND_XP.items():
            if 0 <= current_total_xp <= xp_needed:
                level = int(level)
                level -= 1
                if level < 0: level = 0
                return level
