"""
Comprehensive repair script for app/app.py.
Fixes:
  1. Corrupted emoji/text in sidebar labels and mobile drawer
  2. Removes mobile filter drawer (it runs too late to affect state)
  3. Adds DuplcateWidgetID-safe sidebar that uses session_state keys correctly
  4. Fixes all mojibake label strings
Run from project root: python repair_app.py
"""
import re

SRC = "app/app.py"

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# ─── 1. Fix corrupted emoji text in sidebar section ─────────────────────────
#  The sidebar labels use mojibake because PowerShell ate the UTF-8 emojis.
#  We replace the whole sidebar block with clean text.

OLD_SIDEBAR = '''# =========================================================
# 5. SIDEBAR â€" OPERATIONS CONSOLE
# =========================================================
st.sidebar.title("ðŸš¦ Operations Console")
selected_city = st.sidebar.selectbox("ðŸŒ Target Sector", options=sorted(df['City_UI'].unique()))

st.sidebar.markdown("### ðŸŽ›ï¸ Operational Controls")

# Scenario and Live toggle are grouped â€" both are operational state controls
selected_severity = st.sidebar.selectbox(
    "ðŸš¨ Scenario",
    options=["Observed Conditions", "Low", "Moderate", "High", "Severe"]
)
if selected_severity != "Observed Conditions":
    st.sidebar.markdown("<small style='color:#FF006E; font-weight:600;'>Simulation Mode Active</small>", unsafe_allow_html=True)

live_enabled = st.sidebar.toggle("ðŸ"´ Enable Live Telemetry", key="live_toggle")

selected_region  = None
selected_sector  = None
if live_enabled:
    # Step 1 â€" Region selector (all UAE emirates)
    _live_regions = list(UAE_CORRIDORS.keys())
    selected_region = st.sidebar.selectbox(
        "ðŸ—ºï¸ Region",
        options=_live_regions,
        key="live_region"
    )
    # Step 2 â€" Corridor selector filtered to selected region only
    _region_corridors = list(UAE_CORRIDORS[selected_region].keys())
    selected_sector = st.sidebar.selectbox(
        "ðŸ" Corridor",
        options=_region_corridors,
        key="live_sector"
    )

# Time Window â€" only relevant in historical mode
# Live mode uses real-time, so the hour selector is hidden
if not live_enabled:
    st.sidebar.markdown("### â±ï¸ Time Window")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        h_clock = st.selectbox("Hour", options=[12,1,2,3,4,5,6,7,8,9,10,11],
                                format_func=lambda x: f"{x}:00", label_visibility="collapsed")
    with c2:
        period = st.selectbox("Period", options=["AM", "PM"], label_visibility="collapsed")
    target_h = h_clock + (12 if period == "PM" and h_clock != 12 else 0)
    if period == "AM" and h_clock == 12: target_h = 0
else:
    # Live mode: anchor historical context to current hour
    target_h = datetime.now().hour
    period   = "PM" if target_h >= 12 else "AM"'''

NEW_SIDEBAR = '''# =========================================================
# 5. SIDEBAR — OPERATIONS CONSOLE
# =========================================================
st.sidebar.title("UAE Mobility Intelligence")
selected_city = st.sidebar.selectbox("Target City", options=sorted(df['City_UI'].unique()))

st.sidebar.markdown("### Operational Controls")

selected_severity = st.sidebar.selectbox(
    "Scenario",
    options=["Observed Conditions", "Low", "Moderate", "High", "Severe"]
)
if selected_severity != "Observed Conditions":
    st.sidebar.markdown("<small style='color:#FF006E; font-weight:600;'>Simulation Mode Active</small>", unsafe_allow_html=True)

live_enabled = st.sidebar.toggle("Enable Live Telemetry", key="live_toggle")

selected_region  = None
selected_sector  = None
if live_enabled:
    _live_regions = list(UAE_CORRIDORS.keys())
    selected_region = st.sidebar.selectbox(
        "Region",
        options=_live_regions,
        key="live_region"
    )
    _region_corridors = list(UAE_CORRIDORS[selected_region].keys())
    selected_sector = st.sidebar.selectbox(
        "Corridor",
        options=_region_corridors,
        key="live_sector"
    )

# Time Window — only relevant in historical mode
if not live_enabled:
    st.sidebar.markdown("### Time Window")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        h_clock = st.selectbox("Hour", options=[12,1,2,3,4,5,6,7,8,9,10,11],
                                format_func=lambda x: f"{x}:00", label_visibility="collapsed")
    with c2:
        period = st.selectbox("Period", options=["AM", "PM"], label_visibility="collapsed")
    target_h = h_clock + (12 if period == "PM" and h_clock != 12 else 0)
    if period == "AM" and h_clock == 12: target_h = 0
else:
    # Live mode: anchor to current real-time hour
    target_h = datetime.now().hour
    period   = "PM" if target_h >= 12 else "AM"'''

if OLD_SIDEBAR in content:
    content = content.replace(OLD_SIDEBAR, NEW_SIDEBAR)
    print("Fixed sidebar labels")
else:
    print("WARNING: Sidebar block not found verbatim — attempting partial fixes")
    # Partial fixes for individual corrupted strings
    corrupted_labels = [
        ('st.sidebar.title("ðŸš¦ Operations Console")', 'st.sidebar.title("UAE Mobility Intelligence")'),
        ('"ðŸŒ Target Sector"', '"Target City"'),
        ('"### ðŸŽ›ï¸ Operational Controls"', '"### Operational Controls"'),
        ('"ðŸš¨ Scenario"', '"Scenario"'),
        ('"ðŸ"´ Enable Live Telemetry"', '"Enable Live Telemetry"'),
        ('"ðŸ—ºï¸ Region"', '"Region"'),
        ('"ðŸ" Corridor"', '"Corridor"'),   # note: mojibake of 📍
        ('"### â±ï¸ Time Window"', '"### Time Window"'),
        ('# Step 1 â€" Region selector (all UAE emirates)', '# Step 1 — Region selector (all UAE emirates)'),
        ('# Step 2 â€" Corridor selector filtered to selected region only', '# Step 2 — Corridor selector filtered to selected region only'),
        ('# Scenario and Live toggle are grouped â€" both are operational state controls', '# Scenario and Live toggle are grouped — both are operational state controls'),
        ('# Time Window â€" only relevant in historical mode', '# Time Window — only relevant in historical mode'),
        ('# Live mode: anchor historical context to current hour', '# Live mode: anchor to current real-time hour'),
        ('# =========================================================\n# 5. SIDEBAR â€" OPERATIONS CONSOLE', '# =========================================================\n# 5. SIDEBAR — OPERATIONS CONSOLE'),
    ]
    for bad, good in corrupted_labels:
        if bad in content:
            content = content.replace(bad, good)
            print(f"  Fixed: {bad[:50]}")

# ─── 2. Fix mobile filter drawer labels ──────────────────────────────────────
OLD_MOBILE_SECTION = '''# =========================================================
# 7. MOBILE FILTER DRAWER (inline â€" replaces sidebar on mobile)
# =========================================================
st.markdown("<div class='mobile-filter-hint'>", unsafe_allow_html=True)
with st.expander("âš™ï¸ Filters â€" Region, Corridor & Controls", expanded=False):
    _mob_cities = sorted(df['City_UI'].unique())
    _mob_city   = st.selectbox(
        "ðŸŒ Historical City",
        options=_mob_cities,
        index=_mob_cities.index(selected_city) if selected_city in _mob_cities else 0,
        key="mob_city"
    )
    # Sync: if user changed city in mobile drawer update selected_city
    if _mob_city != selected_city:
        selected_city = _mob_city

    _mob_live = st.toggle("ðŸ"´ Live Telemetry", value=live_enabled, key="mob_live")
    if _mob_live != live_enabled:
        live_enabled = _mob_live

    if live_enabled:
        _mob_regions = list(UAE_CORRIDORS.keys())
        _mob_region = st.selectbox(
            "ðŸ—ºï¸ Region",
            options=_mob_regions,
            index=_mob_regions.index(selected_region) if selected_region in _mob_regions else 0,
            key="mob_region"
        )
        _mob_corridors = list(UAE_CORRIDORS[_mob_region].keys())
        _mob_sector = st.selectbox(
            "ðŸ" Corridor",
            options=_mob_corridors,
            index=_mob_corridors.index(selected_sector) if selected_sector in _mob_corridors else 0,
            key="mob_sector"
        )
        selected_region = _mob_region
        selected_sector = _mob_sector

    if not live_enabled:
        _mc1, _mc2 = st.columns(2)
        with _mc1:
            _mob_h = st.selectbox("Hour", options=[12,1,2,3,4,5,6,7,8,9,10,11],
                                  format_func=lambda x: f"{x}:00", key="mob_h")
        with _mc2:
            _mob_p = st.selectbox("Period", options=["AM","PM"], key="mob_p")
        target_h = _mob_h + (12 if _mob_p == "PM" and _mob_h != 12 else 0)
        if _mob_p == "AM" and _mob_h == 12: target_h = 0
st.markdown("</div>", unsafe_allow_html=True)'''

# The mobile drawer ran AFTER the scenario engine, meaning changes never took effect.
# Replace with a clean compact version that:
#   - Uses a note explaining that controls are in the sidebar (expanded by hamburger)
#   - On mobile, shows a compact quick-access bar
NEW_MOBILE_SECTION = '''# =========================================================
# 7. MOBILE QUICK-ACCESS BAR
# =========================================================
# On mobile the sidebar is accessible via the hamburger menu (top-left).
# We show a compact status bar so the user knows what is active.
st.markdown("<div class='mobile-filter-hint'>", unsafe_allow_html=True)
_mob_mode = "LIVE" if live_enabled else "HISTORICAL"
_mob_loc  = f"{selected_sector}, {selected_region}" if live_enabled and selected_sector else selected_city
st.markdown(
    f"<div style='background:rgba(255,0,110,0.08); border:1px solid rgba(255,0,110,0.25); "
    f"border-radius:10px; padding:10px 14px; margin-bottom:12px; display:flex; "
    f"align-items:center; gap:10px; font-size:0.85rem;'>"
    f"<span style='background:#FF006E; color:white; padding:2px 8px; border-radius:4px; "
    f"font-size:0.70rem; font-weight:800; letter-spacing:0.06em;'>{_mob_mode}</span>"
    f"<span style='color:#CBD5E1; flex:1;'>{_mob_loc}</span>"
    f"<span style='color:#475569; font-size:0.72rem;'>Tap menu to change</span>"
    f"</div>",
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)'''

if OLD_MOBILE_SECTION in content:
    content = content.replace(OLD_MOBILE_SECTION, NEW_MOBILE_SECTION)
    print("Fixed mobile filter drawer -> compact status bar")
else:
    print("WARNING: Mobile drawer block not found verbatim")
    # Try to find and replace with partial match
    mob_start = content.find("# 7. MOBILE FILTER DRAWER")
    mob_end   = content.find("# =========================================================\n# 8. TITLE")
    if mob_start != -1 and mob_end != -1:
        content = content[:mob_start] + NEW_MOBILE_SECTION.lstrip("# =========================================================\n") + "\n\n" + content[mob_end:]
        print("  Applied via position-based replacement")

# ─── 3. Fix corrupted title ───────────────────────────────────────────────────
for bad, good in [
    ('st.title("ðŸš¦ UAE Mobility Intelligence")', 'st.title("UAE Mobility Intelligence")'),
    ('st.markdown("## ðŸ"¡ Network Status")', 'st.markdown("## Network Status")'),
]:
    if bad in content:
        content = content.replace(bad, good)
        print(f"Fixed: {bad[:60]}")

# ─── 4. Fix remaining corrupted emoji patterns from the markup sections ────────
# These come from inline HTML strings that got mojibake'd
emoji_fixes = [
    # Corrupted section headers in Python string literals
    ('â€"', '—'),          # em dash (most common)
    (' Â·', ' ·'),          # middle dot with preceding nbsp
    ('Â·', '·'),            # middle dot
]
for bad, good in emoji_fixes:
    if bad in content:
        count = content.count(bad)
        content = content.replace(bad, good)
        print(f"Fixed {count}x: {repr(bad)} -> {repr(good)}")

# ─── 5. Final parse check ─────────────────────────────────────────────────────
import sys
try:
    compile(content, SRC, "exec")
    print("\nPASS: File parses as valid Python")
except SyntaxError as e:
    print(f"\nFAIL: SyntaxError at line {e.lineno}: {e.msg}")
    lines = content.split("\n")
    lo = max(0, e.lineno - 4)
    hi = min(len(lines), e.lineno + 3)
    for i, l in enumerate(lines[lo:hi], lo + 1):
        print(f"  {i:4d}: {repr(l[:100])}")
    sys.exit(1)

with open(SRC, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("Saved. Done.")
