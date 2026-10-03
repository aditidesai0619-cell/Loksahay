"""Road network seed data — ported from the frontend prototype's
`src/data/geo.ts` so both halves of the system describe the same
Uttarakhand demo geography. Coordinates are approximate real-world
locations for a believable, repeatable demo — not surveyed routing data.
"""

from __future__ import annotations

NODES = [
    ("N-DDN", "Dehradun", 30.3165, 78.0322),
    ("N-HDR", "Haridwar", 29.9457, 78.1642),
    ("N-RSK", "Rishikesh", 30.0869, 78.2676),
    ("N-KDW", "Kotdwar", 29.7475, 78.5262),
    ("N-PAU", "Pauri", 30.1462, 78.7642),
    ("N-TEH", "Tehri", 30.3783, 78.4805),
    ("N-SRI", "Srinagar (Garhwal)", 30.2298, 78.7849),
    ("N-RUD", "Rudraprayag", 30.2844, 78.981),
    ("N-UTK", "Uttarkashi", 30.7268, 78.4354),
    ("N-GOP", "Gopeshwar (Chamoli)", 30.3889, 79.3345),
    ("N-GRK", "Gaurikund", 30.6826, 79.0239),
    ("N-KED", "Kedarnath", 30.7346, 79.0669),
    ("N-JOS", "Joshimath", 30.5553, 79.5641),
    ("N-ALM", "Almora", 29.5892, 79.6467),
    ("N-BAG", "Bageshwar", 29.8406, 79.7704),
    ("N-PTG", "Pithoragarh", 29.5829, 80.2181),
    ("N-MUN", "Munsiyari", 30.0632, 80.2378),
    ("N-KRN", "Karnaprayag", 30.2627, 79.2152),
    # Extra nodes for the Scenario Simulator's "Add Affected Area" control.
    ("N-DEV", "Devprayag", 30.1460, 78.5926),
    ("N-GUP", "Guptkashi", 30.5300, 79.0730),
    ("N-MAN", "Mandal Valley", 30.4450, 79.2870),
]

# condition: OPEN | DEGRADED | BLOCKED
EDGES = [
    ("R1", "N-DDN", "N-RSK", "OPEN", None),
    ("R2", "N-DDN", "N-HDR", "OPEN", None),
    ("R3", "N-HDR", "N-RSK", "OPEN", None),
    ("R4", "N-RSK", "N-TEH", "OPEN", None),
    ("R5", "N-RSK", "N-KDW", "OPEN", None),
    ("R6", "N-KDW", "N-PAU", "DEGRADED", None),
    ("R7", "N-TEH", "N-SRI", "OPEN", None),
    ("R8", "N-PAU", "N-SRI", "OPEN", None),
    ("R9", "N-SRI", "N-RUD", "OPEN", None),
    ("R10", "N-TEH", "N-UTK", "OPEN", None),
    ("R11", "N-RUD", "N-GRK", "DEGRADED", None),
    ("R12", "N-GRK", "N-KED", "OPEN", None),
    ("R13", "N-RUD", "N-KRN", "OPEN", None),
    ("R14", "N-KRN", "N-GOP", "OPEN", None),
    ("R15", "N-GOP", "N-JOS", "BLOCKED", "Bridge washout, Alaknanda crossing"),
    ("R16", "N-KRN", "N-JOS", "DEGRADED", None),
    ("R17", "N-UTK", "N-JOS", "OPEN", None),
    ("R18", "N-SRI", "N-ALM", "OPEN", None),
    ("R19", "N-ALM", "N-BAG", "OPEN", None),
    ("R20", "N-BAG", "N-PTG", "OPEN", None),
    ("R21", "N-PTG", "N-MUN", "DEGRADED", None),
    ("R22", "N-BAG", "N-MUN", "OPEN", None),
    ("R23", "N-GOP", "N-BAG", "OPEN", None),
    ("R24", "N-RUD", "N-DEV", "OPEN", None),
    ("R25", "N-GRK", "N-GUP", "OPEN", None),
    ("R26", "N-GOP", "N-MAN", "OPEN", None),
]
