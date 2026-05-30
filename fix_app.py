import re, sys

SRC = "app/app.py"

with open(SRC, "rb") as f:
    raw = f.read()

if raw[:3] == b"\xef\xbb\xbf":
    enc = "utf-8-sig"
    print("Detected: UTF-8 with BOM")
elif raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
    enc = "utf-16"
    print("Detected: UTF-16")
else:
    enc = "utf-8"
    print("Detected: UTF-8")

content = raw.decode(enc, errors="replace")
lines = content.split("\n")
print("Total lines: %d" % len(lines))
print("Line 299 repr: %s" % repr(lines[298][:80]))
print("Line 304 repr: %s" % repr(lines[303][:80]))

# Fix broken section header (may already be fixed from previous run)
BROKEN = "# =============================st.markdown(\"\"\"" 
FIXED  = "# =========================================================\nst.markdown(\"\"\""
if BROKEN in content:
    content = content.replace(BROKEN, FIXED)
    print("Fixed broken header")
else:
    print("Header already clean")

# Replace ALL non-ASCII replacement chars + common mojibake sequences
# Strategy: inside the CSS string block, strip every non-ASCII char to its
# closest ASCII equivalent.  We identify the block by markers.
CSS_START = 'st.markdown("""\n<meta name="viewport"'
CSS_END   = '""", unsafe_allow_html=True)\n\n# ===\n# 3.'

idx_s = content.find(CSS_START)
idx_e = content.find(CSS_END, idx_s)

if idx_s == -1:
    print("WARNING: CSS block start marker not found - trying fallback")
    idx_s = content.find('<meta name="viewport"')
    idx_e = content.find('# 3. DATA INGESTION', idx_s)

if idx_s != -1 and idx_e != -1:
    css_block = content[idx_s:idx_e]
    # Replace unicode replacement chars
    css_block = css_block.replace("\ufffd", "")
    # Replace any remaining non-ASCII in the CSS (they're only in comments)
    cleaned = ""
    for ch in css_block:
        if ord(ch) < 128:
            cleaned += ch
        elif ch in "\U0001F000-\U0001FFFF":  # emoji range - keep in template strings outside CSS
            cleaned += ch
        else:
            # In CSS comments, replace with "-"
            cleaned += "-"
    content = content[:idx_s] + cleaned + content[idx_e:]
    print("CSS block cleaned: %d chars -> %d chars" % (len(css_block), len(cleaned)))
else:
    print("WARNING: Could not isolate CSS block, applying global cleanup")
    content = content.replace("\ufffd", "")

# Verify
try:
    compile(content, SRC, "exec")
    print("PASS: File parses as valid Python")
except SyntaxError as e:
    print("FAIL: SyntaxError at line %d: %s" % (e.lineno, e.msg))
    if e.lineno:
        ls = content.split("\n")
        lo = max(0, e.lineno - 3)
        hi = min(len(ls), e.lineno + 3)
        for i, l in enumerate(ls[lo:hi], lo + 1):
            print("  %4d: %s" % (i, repr(l[:120])))
    sys.exit(1)

with open(SRC, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("Saved as clean UTF-8. Done.")
