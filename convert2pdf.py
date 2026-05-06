import csv
from fpdf import FPDF

# =========================
# CONFIGURATION
# =========================
CSV_FILE = "chinese_level1_words.csv"
OUTPUT_PDF = "chinese_level1_words.pdf"
FONT_FILE = "NotoSerifSC-Medium.ttf"

WORDS_PER_PAGE = 1

# Font sizes
CHINESE_FONT_SIZE = 100
PINYIN_FONT_SIZE = 50
MEANING_FONT_SIZE = 30

# Line heights
CHINESE_LINE_HEIGHT = 22
PINYIN_LINE_HEIGHT = 14
MEANING_LINE_HEIGHT = 12

# Spacing
CHINESE_TO_PINYIN_SPACING = 20
PINYIN_TO_MEANING_SPACING = 10
WORD_BLOCK_SPACING = 20

# Toggle
USE_COLORS = True

# Base colors
CHINESE_COLOR = (0, 0, 0)
MEANING_COLOR = (0, 0, 200)

# Tone colors
TONE_COLORS = {
    1: (220, 0, 0),
    2: (255, 140, 0),
    3: (0, 160, 0),
    4: (0, 0, 220),
    5: (120, 120, 120)
}

# =========================
# PDF CLASS
# =========================
class ChinesePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(128, 128, 128)
        self.set_y(10)
        self.cell(0, 10, f"Word {self.page_no()}", align="C")
        self.ln(20)
        pass

# =========================
# HELPERS
# =========================


def apply_color(pdf, color):
    if USE_COLORS:
        pdf.set_text_color(*color)
    else:
        pdf.set_text_color(0, 0, 0)

def get_tone(char):
    tone_map = {
        "ā":1,"ē":1,"ī":1,"ō":1,"ū":1,"ǖ":1,
        "á":2,"é":2,"í":2,"ó":2,"ú":2,"ǘ":2,
        "ǎ":3,"ě":3,"ǐ":3,"ǒ":3,"ǔ":3,"ǚ":3,
        "à":4,"è":4,"ì":4,"ò":4,"ù":4,"ǜ":4,
    }
    return tone_map.get(char, 0)

def detect_tone(syllable):
    for ch in syllable:
        t = get_tone(ch)
        if t:
            return t
    return 5

def split_pinyin_lines(pdf, text):
    """Split pinyin into wrapped lines preserving syllables"""
    pdf.set_font("CustomFont", size=PINYIN_FONT_SIZE)
    max_width = pdf.w - 2 * pdf.l_margin

    words = text.split()
    lines = []
    current_line = ""
    current_width = 0

    for word in words:
        w = pdf.get_string_width(word + " ")
        if current_width + w <= max_width:
            current_line += word + " "
            current_width += w
        else:
            lines.append(current_line.strip())
            current_line = word + " "
            current_width = w

    if current_line:
        lines.append(current_line.strip())

    return lines

def draw_colored_pinyin(pdf, text):
    lines = split_pinyin_lines(pdf, text)

    for line in lines:
        syllables = line.split()

        # compute centering
        total_width = sum(pdf.get_string_width(s + " ") for s in syllables)
        start_x = (pdf.w - total_width) / 2
        pdf.set_x(start_x)

        for syl in syllables:
            tone = detect_tone(syl)
            apply_color(pdf, TONE_COLORS[tone])
            pdf.cell(pdf.get_string_width(syl + " "), PINYIN_LINE_HEIGHT, syl + " ", border=0)

        pdf.ln(PINYIN_LINE_HEIGHT)

def get_multicell_height(pdf, text, font_size, line_height):
    pdf.set_font("CustomFont", size=font_size)
    max_width = pdf.w - 2 * pdf.l_margin

    words = text.split()
    lines = 1
    current_width = 0

    for word in words:
        w = pdf.get_string_width(word + " ")
        if current_width + w <= max_width:
            current_width += w
        else:
            lines += 1
            current_width = w

    return lines * line_height

def get_pinyin_height(pdf, text):
    lines = split_pinyin_lines(pdf, text)
    return len(lines) * PINYIN_LINE_HEIGHT

def get_block_height(pdf, chinese, pinyin, meaning):
    chinese_h = get_multicell_height(pdf, chinese, CHINESE_FONT_SIZE, CHINESE_LINE_HEIGHT)
    pinyin_h = get_pinyin_height(pdf, pinyin)
    meaning_h = get_multicell_height(pdf, meaning, MEANING_FONT_SIZE, MEANING_LINE_HEIGHT)

    return (
        chinese_h +
        CHINESE_TO_PINYIN_SPACING +
        pinyin_h +
        PINYIN_TO_MEANING_SPACING +
        meaning_h
    )

# =========================
# READ CSV
# =========================
words = []
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 4:
            continue
        _, chinese, pinyin, meaning = row
        words.append((chinese, pinyin, meaning))

# =========================
# CREATE PDF
# =========================
pdf = ChinesePDF(format="A4")
pdf.set_auto_page_break(auto=False)
pdf.add_font("CustomFont", "", FONT_FILE)

page_height = pdf.h

for i in range(0, len(words), WORDS_PER_PAGE):
    pdf.add_page()
    chunk = words[i:i + WORDS_PER_PAGE]

    # compute total height
    total_height = 0
    heights = []

    for chinese, pinyin, meaning in chunk:
        h = get_block_height(pdf, chinese, pinyin, meaning)
        heights.append(h)
        total_height += h

    total_height += (len(chunk) - 1) * WORD_BLOCK_SPACING

    start_y = (page_height - total_height) / 2
    pdf.set_y(start_y)

    # draw content
    for idx, (chinese, pinyin, meaning) in enumerate(chunk):

        # Chinese
        apply_color(pdf, CHINESE_COLOR)
        pdf.set_font("CustomFont", size=CHINESE_FONT_SIZE)
        pdf.multi_cell(0, CHINESE_LINE_HEIGHT, chinese, align='C')

        pdf.ln(CHINESE_TO_PINYIN_SPACING)

        # Pinyin (tone-colored)
        draw_colored_pinyin(pdf, pinyin)

        pdf.ln(PINYIN_TO_MEANING_SPACING)

        # Meaning
        apply_color(pdf, MEANING_COLOR)
        pdf.set_font("CustomFont", size=MEANING_FONT_SIZE)
        pdf.multi_cell(0, MEANING_LINE_HEIGHT, meaning, align='C')

        

        if idx < len(chunk) - 1:
            pdf.ln(WORD_BLOCK_SPACING)

# =========================
# SAVE
# =========================
pdf.output(OUTPUT_PDF)
print(f"Created {OUTPUT_PDF}")
