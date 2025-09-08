from __future__ import annotations
from fpdf import FPDF
import os

def export_pdf(form: ObservationForm) -> bytes:
    """PDF-Export mit Unicode-fähiger TTF-Schrift (DejaVu). 
    Fallback ohne TTF: ASCII-Normalisierung statt Crash."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- Versuche, Unicode-fähige TTF-Schriften zu laden ---
    fonts_ok = False
    regular_path = os.path.join("fonts", "DejaVuSans.ttf")
    bold_path = os.path.join("fonts", "DejaVuSans-Bold.ttf")
    try:
        if os.path.exists(regular_path):
            pdf.add_font("DejaVu", "", regular_path, uni=True)
        if os.path.exists(bold_path):
            pdf.add_font("DejaVu", "B", bold_path, uni=True)
        # Wenn mindestens Regular existiert, nutzen:
        if os.path.exists(regular_path):
            fonts_ok = True
    except Exception:
        fonts_ok = False  # falls auf Streamlit Cloud was schiefgeht

    # --- Helfer: Normalisierung falls keine Unicode-Font ---
    def ascii_norm(s: str) -> str:
        repl = {
            "ä": "ae", "ö": "oe", "ü": "ue",
            "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
            "ß": "ss", "–": "-", "—": "-", "„": '"', "“": '"', "‚": "'", "’": "'"
        }
        for k, v in repl.items():
            s = s.replace(k, v)
        return s

    def set_font_bold():
        if fonts_ok and os.path.exists(bold_path):
            pdf.set_font("DejaVu", "B", 16)
        elif fonts_ok:
            pdf.set_font("DejaVu", "", 16)  # pseudo-bold nicht nötig; Regular reicht
        else:
            pdf.set_font("Helvetica", "B", 16)

    def set_font_regular(size=11):
        if fonts_ok:
            pdf.set_font("DejaVu", "", size)
        else:
            pdf.set_font("Helvetica", "", size)

    def line(txt=""):
        if not fonts_ok:
            txt = ascii_norm(txt)
        pdf.multi_cell(0, 6, txt)

    pdf.add_page()

    # Titel
    set_font_bold()
    title = "Hospitationsbogen – BLI 3.0"
    if not fonts_ok:
        title = ascii_norm(title)
    pdf.cell(0, 10, title, ln=True, align="C")

    # Meta
    set_font_regular(11)
    line(f"Datum: {form.date}")
    line(f"Kolleg*in: {form.colleague}")
    line(f"Beobachter*in: {form.observer}")
    line(f"Fach/Klasse/Thema: {form.subject} / {form.grade} / {form.topic}")
    if form.school:
        line(f"Schule: {form.school}")
    if form.profile_focus:
        line("Profil-Fokus: " + ", ".join(form.profile_focus))
    pdf.ln(2)

    # Module + Kriterien
    for mk, mod in form.modules.items():
        set_font_bold()
        heading = f"{mk} – {BLI_DATA[mk]['title']}"
        if not fonts_ok:
            heading = ascii_norm(heading)
        line(heading)

        set_font_regular(11)
        for ck, cres in mod.criteria.items():
            crit = f"{ck} {BLI_DATA[mk]['criteria'][ck]}"
            if not fonts_ok:
                crit = ascii_norm(crit)
            line(crit)
            line(f"  Bewertung: {cres.rating}/4")
            if cres.comment:
                cmt = cres.comment if fonts_ok else ascii_norm(cres.comment)
                line(f"  Kommentar: {cmt}")
            pdf.ln(1)
        pdf.ln(2)

    # Stärken / nächste Schritte
    set_font_bold()
    line("Stärken")
    set_font_regular(11)
    line(form.strengths or "-")
    pdf.ln(2)

    set_font_bold()
    line("Nächste Schritte (konkret, terminiert)")
    set_font_regular(11)
    line(form.next_steps or "-")
    pdf.ln(2)

    # Scores
    per_module, overall = compute_scores(form)
    set_font_bold()
    line("Zusammenfassung (Scores)")
    set_font_regular(11)
    for mk, sc in per_module.items():
        line(f"{mk}: {sc:.2f} / 4")
    line(f"Gesamt (gewichtet): {overall:.2f} / 4")

    return pdf.output(dest="S").encode("latin-1", errors="ignore")
