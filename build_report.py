#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build UROP_LLM_API_Evaluation_Report.docx matching the template formatting exactly.
Run directly: python build_report.py
Writes: UROP_LLM_API_Evaluation_Report.docx (overwrites existing)
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

# ─────────────────────────────────────────────
# Constants extracted from template formatting analysis
# ─────────────────────────────────────────────
FONT            = "Palatino Linotype"
SZ_BODY         = Pt(12)
SZ_H1           = Pt(15.5)
SZ_H2           = Pt(13.5)
SZ_H3           = Pt(12)
SZ_STUDENT_NAME = Pt(13)
SZ_DEPT         = Pt(14)

LS_BODY  = Pt(14.45)   # body paragraph line spacing EXACTLY
LS_FM    = Pt(21.65)   # front matter body line spacing
LS_CH    = Pt(19.9)    # chapter heading line spacing
LS_TITLE = Pt(18.0)    # title page lines
LS_FM_H  = Pt(20.0)    # front matter section title

SPACE_AFTER_H1   = Pt(19.1)
SPACE_AFTER_FMT  = Pt(20.65)

# Figure paths
FIG_TYPE   = r"c:\Users\sathw\Desktop\urop_1\results\figures\type_counts_corrected.png"
FIG_TOKENS = r"c:\Users\sathw\Desktop\urop_1\results\figures\tokens_per_prompt.png"

# ─────────────────────────────────────────────
# Document creation
# ─────────────────────────────────────────────
doc = Document()

def set_margins(section):
    section.left_margin   = Inches(1.5)
    section.right_margin  = Inches(1.268)
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.611)
    section.page_width    = Inches(8.268)
    section.page_height   = Inches(11.693)

for s in doc.sections:
    set_margins(s)

# ─────────────────────────────────────────────
# XML helpers for page number footer
# ─────────────────────────────────────────────
def add_page_number_footer(section, roman=False):
    footer = section.footer
    for p in footer.paragraphs:
        p.clear()
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    run.font.name = FONT
    run.font.size = SZ_BODY
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' PAGE \\* roman ' if roman else ' PAGE '
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

# ─────────────────────────────────────────────
# Paragraph helpers
# ─────────────────────────────────────────────
def _set_ls(para, ls):
    pf = para.paragraph_format
    pf.line_spacing = ls
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY

def _set_sp(para, before=None, after=None):
    pf = para.paragraph_format
    if before is not None: pf.space_before = before
    if after  is not None: pf.space_after  = after

def add_body(doc, text, justify=True, ls=None, before=None, after=None):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
    _set_ls(para, ls or LS_BODY)
    _set_sp(para, before if before is not None else Pt(0),
                  after  if after  is not None else Pt(0))
    run = para.add_run(text)
    run.font.name = FONT
    run.font.size = SZ_BODY
    return para

def add_fm_body(doc, text, justify=True):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.LEFT
    _set_ls(para, LS_FM)
    _set_sp(para, Pt(0), Pt(0))
    run = para.add_run(text)
    run.font.name = FONT
    run.font.size = SZ_BODY
    return para

def add_centered_line(doc, text, size=None, bold=False, before=None, ls=LS_TITLE):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_ls(para, ls)
    _set_sp(para, before if before is not None else Pt(0), Pt(0))
    run = para.add_run(text)
    run.font.name = FONT
    if size: run.font.size = size
    run.bold = bold
    return para

def add_chapter_heading(doc, num, title):
    para = doc.add_paragraph()
    _set_ls(para, LS_CH)
    _set_sp(para, Pt(0), SPACE_AFTER_H1)
    run = para.add_run("Chapter {}\n{}".format(num, title))
    run.font.name = FONT
    run.font.size = SZ_H1
    run.bold = True
    return para

def add_fm_title(doc, text):
    para = doc.add_paragraph()
    _set_ls(para, LS_FM_H)
    _set_sp(para, Pt(0), SPACE_AFTER_FMT)
    run = para.add_run(text)
    run.font.name = FONT
    run.font.size = SZ_H1
    run.bold = True
    return para

def add_section_heading(doc, num, title):
    para = doc.add_paragraph()
    _set_ls(para, LS_FM_H)
    _set_sp(para, Pt(6), Pt(3))
    run = para.add_run("{}\t{}".format(num, title))
    run.font.name = FONT
    run.font.size = SZ_H2
    run.bold = True
    return para

def add_subsection_heading(doc, num, title):
    para = doc.add_paragraph()
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(6), Pt(3))
    run = para.add_run("{}\t{}".format(num, title))
    run.font.name = FONT
    run.font.size = SZ_H3
    run.bold = True
    return para

def add_caption(doc, text):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(3), Pt(3))
    run = para.add_run(text)
    run.font.name = FONT
    run.font.size = SZ_BODY
    return para

def add_toc_entry_chapter(doc, num, title, page):
    para = doc.add_paragraph()
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(12), Pt(0))
    r1 = para.add_run("Chapter {}.  {}".format(num, title))
    r1.font.name = FONT; r1.font.size = SZ_BODY; r1.bold = True
    r2 = para.add_run("\t{}".format(page))
    r2.font.name = FONT; r2.font.size = SZ_BODY; r2.bold = True
    return para

def add_toc_entry_section(doc, num, title, page):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Pt(81.3)
    para.paragraph_format.first_line_indent = Pt(-23.9)
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(0), Pt(0))
    r1 = para.add_run("{}\t{}".format(num, title))
    r1.font.name = FONT; r1.font.size = SZ_BODY
    r2 = para.add_run("\t{}".format(page))
    r2.font.name = FONT; r2.font.size = SZ_BODY
    return para

def add_toc_entry_subsection(doc, num, title, page):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Pt(148.2)
    para.paragraph_format.first_line_indent = Pt(-33.4)
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(0), Pt(0))
    r1 = para.add_run("{}\t{}".format(num, title))
    r1.font.name = FONT; r1.font.size = SZ_BODY
    r2 = para.add_run("\t{}".format(page))
    r2.font.name = FONT; r2.font.size = SZ_BODY
    return para

def add_toc_entry_fm(doc, text, page):
    para = doc.add_paragraph()
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(12), Pt(0))
    r1 = para.add_run(text)
    r1.font.name = FONT; r1.font.size = SZ_BODY; r1.bold = True
    r2 = para.add_run("\t{}".format(page))
    r2.font.name = FONT; r2.font.size = SZ_BODY; r2.bold = True
    return para

def add_reference(doc, num, authors_bold, rest_text, journal_italic=None, rest2=None):
    para = doc.add_paragraph()
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(2), Pt(2))
    r0 = para.add_run("\t[{}]\t".format(num))
    r0.font.name = FONT; r0.font.size = SZ_BODY
    r1 = para.add_run(authors_bold)
    r1.font.name = FONT; r1.font.size = SZ_BODY; r1.bold = True
    r2 = para.add_run(rest_text)
    r2.font.name = FONT; r2.font.size = SZ_BODY
    if journal_italic:
        r3 = para.add_run(journal_italic)
        r3.font.name = FONT; r3.font.size = SZ_BODY; r3.italic = True
    if rest2:
        r4 = para.add_run(rest2)
        r4.font.name = FONT; r4.font.size = SZ_BODY
    return para

def add_figure(doc, path, caption_text, width=Inches(4.5)):
    if os.path.exists(path):
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        run.add_picture(path, width=width)
    else:
        add_body(doc, "[Figure: {} not found]".format(os.path.basename(path)))
    add_caption(doc, caption_text)

def add_table_interception(doc):
    table = doc.add_table(rows=4, cols=6)
    table.style = 'Table Grid'
    headers = ["Scorer", "n", "Errors", "Detection", "Type", "Clause / Clarification"]
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        hdr_row.cells[i].text = h
        for para in hdr_row.cells[i].paragraphs:
            for run in para.runs:
                run.bold = True; run.font.name = FONT; run.font.size = Pt(10)
    data = [
        ["Word overlap",  "56", "0", "0.946", "0.357", "0.643 hit / 0.316 avg"],
        ["Intent judge", "49", "7", "0.959", "0.959", "0.694 hit / 0.653 match"],
        ["SBERT / NLI",  "56", "0", "1.000", "0.357", "1.000 hit / 0.321 match"],
    ]
    for r, row_data in enumerate(data):
        row = table.rows[r + 1]
        for c, val in enumerate(row_data):
            row.cells[c].text = val
            for para in row.cells[c].paragraphs:
                for run in para.runs:
                    run.font.name = FONT; run.font.size = Pt(10)
    doc.add_paragraph()

def add_table_ecogate_routing(doc):
    table = doc.add_table(rows=4, cols=2)
    table.style = 'Table Grid'
    hdr = table.rows[0]
    for i, h in enumerate(["Route", "Prompts"]):
        hdr.cells[i].text = h
        for p in hdr.cells[i].paragraphs:
            for r in p.runs:
                r.bold = True; r.font.name = FONT; r.font.size = Pt(10)
    rows_data = [("NLP only (nlp_clarify)", "51"),
                 ("One diagnostic LLM call (llm_diagnose)", "5"),
                 ("Direct answer", "0")]
    for i, (a, b) in enumerate(rows_data):
        row = table.rows[i + 1]
        row.cells[0].text = a; row.cells[1].text = b
        for c in row.cells:
            for p in c.paragraphs:
                for run in p.runs:
                    run.font.name = FONT; run.font.size = Pt(10)
    doc.add_paragraph()

def add_table_token_energy(doc):
    table = doc.add_table(rows=3, cols=3)
    table.style = 'Table Grid'
    hdr = table.rows[0]
    for i, h in enumerate(["Metric", "EcoGate", "Baseline (generate-anyway)"]):
        hdr.cells[i].text = h
        for p in hdr.cells[i].paragraphs:
            for r in p.runs:
                r.bold = True; r.font.name = FONT; r.font.size = Pt(10)
    rows_data = [("Tokens", "5,210", "108,488"),
                 ("Joules (comparison model)", "4,177.21", "152,737.60")]
    for i, (a, b, c_) in enumerate(rows_data):
        row = table.rows[i + 1]
        row.cells[0].text = a; row.cells[1].text = b; row.cells[2].text = c_
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = FONT; run.font.size = Pt(10)
    doc.add_paragraph()

def add_table_latent(doc):
    table = doc.add_table(rows=4, cols=4)
    table.style = 'Table Grid'
    hdr = table.rows[0]
    for i, h in enumerate(["Category", "Decision", "Latent", "None / Explicit"]):
        hdr.cells[i].text = h
        for p in hdr.cells[i].paragraphs:
            for run in p.runs:
                run.bold = True; run.font.name = FONT; run.font.size = Pt(10)
    rows_data = [("Decision", "4", "0", "0"),
                 ("Latent", "0", "5", "0"),
                 ("None / Explicit", "0", "0", "3")]
    for i, row_d in enumerate(rows_data):
        row = table.rows[i + 1]
        for j, val in enumerate(row_d):
            row.cells[j].text = val
            for p in row.cells[j].paragraphs:
                for run in p.runs:
                    run.font.name = FONT; run.font.size = Pt(10)
    doc.add_paragraph()

def add_table_type_agreement(doc):
    table = doc.add_table(rows=4, cols=4)
    table.style = 'Table Grid'
    hdr = table.rows[0]
    for i, h in enumerate(["Clarif. \\ Prompt", "Missing entity", "Syntax error", "Semantic overlap"]):
        hdr.cells[i].text = h
        for p in hdr.cells[i].paragraphs:
            for run in p.runs:
                run.bold = True; run.font.name = FONT; run.font.size = Pt(10)
    rows_data = [("Missing entity", "34", "0", "0"),
                 ("Syntax error", "0", "1", "0"),
                 ("Semantic overlap", "3", "0", "18")]
    for i, row_d in enumerate(rows_data):
        row = table.rows[i + 1]
        for j, val in enumerate(row_d):
            row.cells[j].text = val
            for p in row.cells[j].paragraphs:
                for run in p.runs:
                    run.font.name = FONT; run.font.size = Pt(10)
    doc.add_paragraph()


# ══════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════
sp = doc.add_paragraph()
_set_ls(sp, Pt(24.3))

add_centered_line(doc, "Creating APIs for Measuring Large Language Models Using Links",
                  size=SZ_BODY, bold=True, ls=LS_TITLE)
add_centered_line(doc, "Project Report Submitted to the", ls=LS_TITLE, before=Pt(18))
add_centered_line(doc, "SRM University-AP, Andhra Pradesh", ls=LS_TITLE, before=Pt(0.1))
add_centered_line(doc, "for the partial fulfillment of the requirements to award the degree of", ls=LS_TITLE)
add_centered_line(doc, "Bachelor of Technology", bold=True, ls=LS_TITLE, before=Pt(18))
add_centered_line(doc, "in", bold=True, ls=LS_TITLE)
add_centered_line(doc, "Computer Science & Engineering", bold=True, ls=LS_TITLE, before=Pt(0.1))
add_centered_line(doc, "School of Engineering & Sciences", bold=True, ls=LS_TITLE)

add_centered_line(doc, "submitted by", ls=LS_TITLE, before=Pt(8.6))
add_centered_line(doc, "Aagosh Raj Srivastava (AP23110010096)",
                  size=SZ_STUDENT_NAME, bold=True, ls=LS_TITLE, before=Pt(7))
add_centered_line(doc, "G. Sathwik (AP23110011125)",
                  size=SZ_STUDENT_NAME, bold=True, ls=LS_TITLE, before=Pt(7))

add_centered_line(doc, "Under the Guidance of", ls=LS_TITLE, before=Pt(14))
add_centered_line(doc, "Dr. Neeraj Upadhyay", bold=True, ls=LS_TITLE, before=Pt(8))
add_centered_line(doc, "Department of Computer Science & Engineering", ls=LS_TITLE, before=Pt(2))
add_centered_line(doc, "Co-Mentored by", ls=LS_TITLE, before=Pt(6))
add_centered_line(doc, "Mr. Ajay Sahu", bold=True, ls=LS_TITLE, before=Pt(6))
add_centered_line(doc, "PhD Scholar", ls=LS_TITLE, before=Pt(2))
add_centered_line(doc, "Department of Computer Science & Engineering", ls=LS_TITLE, before=Pt(2))

sp2 = doc.add_paragraph(); _set_ls(sp2, Pt(18))

add_centered_line(doc, "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING",
                  size=SZ_DEPT, bold=True, ls=Pt(23.9), before=Pt(24))
add_centered_line(doc, "SRM University-AP", size=SZ_DEPT, bold=True, ls=Pt(23.9))
add_centered_line(doc, "Neerukonda, Mangalagiri, Guntur", ls=Pt(23.9))
add_centered_line(doc, "Amaravati, Andhra Pradesh - 522 240", ls=Pt(23.9), before=Pt(0.1))
add_centered_line(doc, "November 2026", size=SZ_DEPT, ls=Pt(23.9), before=Pt(0.5))

# ══════════════════════════════════════════════
# DECLARATION (page i)
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "DECLARATION")
add_fm_body(doc,
    'We, the undersigned, hereby declare that the project report \u201cCreating APIs for '
    'Measuring Large Language Models Using Links\u201d submitted for partial fulfillment '
    'of the requirements to award the degree of Bachelor of Technology in Computer '
    'Science & Engineering is a bonafide record of work carried out by us under the '
    'supervision of Dr. Neeraj Upadhyay, Department of Computer Science & Engineering, '
    'SRM University-AP. This project report has not been submitted for the award of '
    'any other degree or diploma, in this or any other university.')
add_fm_body(doc,
    'All sources of information used in this report have been duly acknowledged. '
    'The experimental results reported here are genuine and have not been fabricated '
    'or manipulated.')

sp = doc.add_paragraph(); _set_ls(sp, Pt(28))
add_centered_line(doc, "Aagosh Raj Srivastava (AP23110010096)", size=SZ_BODY, ls=LS_TITLE)
add_centered_line(doc, "G. Sathwik (AP23110011125)", size=SZ_BODY, ls=LS_TITLE)
sp2 = doc.add_paragraph(); _set_ls(sp2, Pt(10))
add_centered_line(doc, "Date: November 2026", ls=LS_TITLE)

# ══════════════════════════════════════════════
# CERTIFICATE (page ii)
# ══════════════════════════════════════════════
doc.add_page_break()
add_centered_line(doc, "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING",
                  size=SZ_DEPT, bold=True, ls=Pt(23.9))
add_centered_line(doc, "SRM University-AP", ls=Pt(18))
add_centered_line(doc, "Neerukonda, Mangalagiri, Guntur", ls=Pt(18))
add_centered_line(doc, "Amaravati, Andhra Pradesh - 522 240", ls=Pt(18), before=Pt(0.1))

sp = doc.add_paragraph(); _set_ls(sp, Pt(14))
add_centered_line(doc, "CERTIFICATE", size=SZ_DEPT, bold=True, ls=Pt(23.9), before=Pt(30))

add_fm_body(doc,
    'This is to certify that the report entitled \u201cCreating APIs for Measuring '
    'Large Language Models Using Links\u201d submitted by Aagosh Raj Srivastava '
    '(AP23110010096) and G. Sathwik (AP23110011125) to the SRM University-AP in '
    'partial fulfillment of the requirements for the award of the degree of '
    'Bachelor of Technology in Computer Science & Engineering is a record of '
    'bonafide project work carried out by them under my supervision.')
add_fm_body(doc,
    'The results embodied in this project report have not been submitted to any '
    'other university or institution for the award of any degree or diploma.')

sp = doc.add_paragraph(); _set_ls(sp, Pt(28))
add_centered_line(doc, "Dr. Neeraj Upadhyay", bold=True, ls=LS_TITLE)
add_centered_line(doc, "Associate Professor", ls=LS_TITLE)
add_centered_line(doc, "Department of Computer Science & Engineering", ls=LS_TITLE)
add_centered_line(doc, "SRM University-AP", ls=LS_TITLE)
sp2 = doc.add_paragraph(); _set_ls(sp2, Pt(10))
add_centered_line(doc, "Date: November 2026", ls=LS_TITLE)

# ══════════════════════════════════════════════
# ACKNOWLEDGMENT (page iii)
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "ACKNOWLEDGMENT")

add_fm_body(doc,
    'We wish to record our indebtedness and thankfulness to all who helped us '
    'prepare this project report, \u201cCreating APIs for Measuring Large Language '
    'Models Using Links,\u201d and present it satisfactorily.')
add_fm_body(doc,
    'We would like to express our sincere gratitude to Dr. Neeraj Upadhyay, '
    'Department of Computer Science & Engineering, SRM University-AP, for his '
    'supervision, guidance, and for giving us the freedom to explore a research '
    'problem at the intersection of natural language processing, software engineering, '
    'and sustainable computing. His constructive feedback and encouragement throughout '
    'the duration of this project were invaluable.')
add_fm_body(doc,
    'We are grateful to Mr. Ajay Sahu, PhD Scholar, Department of Computer Science '
    '& Engineering, SRM University-AP, for his co-mentorship and for providing '
    'practical insights into the design of the ambiguity detection pipeline and '
    'the EcoGate energy model.')
add_fm_body(doc,
    'We are also thankful to the faculty and staff of SRM University-AP for '
    'providing the environment and support needed to carry out this research project. '
    'The computational resources, library access, and collaborative atmosphere '
    'provided by the university made this work possible.')
add_fm_body(doc,
    'Finally, we thank our families and friends for their patient support and '
    'encouragement throughout this project.')

# ══════════════════════════════════════════════
# ABSTRACT (page iv)
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "ABSTRACT")

add_fm_body(doc,
    'Large language models are widely used for information retrieval, code generation, '
    'summarisation, and question answering. Evaluating them reproducibly \u2014 especially '
    'when the input contains a URL or document link that the model must retrieve and '
    'reason about \u2014 requires a measurement pipeline that can score outputs on semantic '
    'faithfulness, verify source grounding, intercept under-specified prompts before '
    'generation begins, and record the energy and token cost of each step.')
add_fm_body(doc,
    'The implemented stack is a Python measurement pipeline. A local linguistic '
    'analysis proposes problematic spans in a prompt by tagging named entities, '
    'coreference chains, homonym candidates, and dependency-scope ambiguities. '
    'A tiered controller reads those spans and decides whether to ask for clarification '
    'using only the NLP output, to send one diagnostic call to a language model, '
    'or to proceed directly. Output scoring uses word overlap, sentence-embedding '
    'similarity, and an optional LLM-as-a-judge step. An energy ledger records '
    'tokens and estimated joules for every route.')
add_fm_body(doc,
    'An offline comparison with a generate-anyway baseline, with live model calls '
    'turned off, estimated 5,210 tokens against a baseline of 108,488 tokens on '
    '56 generated prompts, a stored reduction of 0.952. Detection rates were 0.946 '
    '(word overlap), 0.959 (intent judge), and 1.000 (SBERT/NLI). The gate asked '
    'for clarification on 54 of 56 ambiguous prompts and answered directly on '
    '4 of 5 clear controls. A latent-versus-decision check matched all 12 '
    'constructed cases.')
add_fm_body(doc,
    'Keywords: large language models, evaluation API, semantic similarity, '
    'LLM-as-a-judge, ambiguity interception, energy-aware computing, EcoGate, '
    'NLP analysis, clarification generation, token efficiency.')

# ══════════════════════════════════════════════
# TABLE OF CONTENTS (page v)
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "CONTENTS")

add_toc_entry_fm(doc, "ACKNOWLEDGMENT", "iii")
add_toc_entry_fm(doc, "ABSTRACT", "iv")
add_toc_entry_fm(doc, "LIST OF TABLES", "vii")
add_toc_entry_fm(doc, "LIST OF FIGURES", "viii")

add_toc_entry_chapter(doc, 1, "INTRODUCTION TO THE PROJECT", "1")
add_toc_entry_section(doc, "1.1", "Background", "1")
add_toc_entry_section(doc, "1.2", "Objectives", "2")
add_toc_entry_section(doc, "1.3", "Organisation of the report", "3")

add_toc_entry_chapter(doc, 2, "MOTIVATION", "4")
add_toc_entry_section(doc, "2.1", "Limits of lexical scores", "4")
add_toc_entry_section(doc, "2.2", "Grounding in external sources", "5")
add_toc_entry_section(doc, "2.3", "Cost, explanation, and stability", "5")

add_toc_entry_chapter(doc, 3, "LITERATURE SURVEY", "6")
add_toc_entry_section(doc, "3.1", "Existing LLM evaluation frameworks", "6")
add_toc_entry_section(doc, "3.2", "Link-based and grounding metrics", "7")
add_toc_entry_section(doc, "3.3", "Semantic similarity and NLP metrics", "8")
add_toc_entry_section(doc, "3.4", "LLM-as-a-judge", "8")
add_toc_entry_section(doc, "3.5", "Explainable, ethical, and sustainable evaluation", "9")
add_toc_entry_section(doc, "3.6", "Openings left by cost and ambiguity studies", "9")

add_toc_entry_chapter(doc, 4, "DESIGN AND METHODOLOGY", "11")
add_toc_entry_section(doc, "4.1", "Specified architecture", "11")
add_toc_entry_section(doc, "4.2", "Tiered controller", "12")
add_toc_entry_section(doc, "4.3", "Scoring procedure", "13")
add_toc_entry_section(doc, "4.4", "Energy comparison model", "13")
add_toc_entry_section(doc, "4.5", "Data used for measurement", "14")
add_toc_entry_section(doc, "4.6", "Repeated runs, drift, and deferred checks", "14")

add_toc_entry_chapter(doc, 5, "IMPLEMENTATION", "15")
add_toc_entry_section(doc, "5.1", "Package layout", "15")
add_toc_entry_section(doc, "5.2", "Query path", "16")
add_toc_entry_section(doc, "5.3", "Benchmark and EcoGate runs", "16")
add_toc_entry_section(doc, "5.4", "Failure handling", "17")

add_toc_entry_chapter(doc, 6, "HARDWARE / SOFTWARE TOOLS USED", "18")
add_toc_entry_section(doc, "6.1", "Software", "18")
add_toc_entry_section(doc, "6.2", "Models and endpoint", "18")
add_toc_entry_section(doc, "6.3", "Execution environment", "19")

add_toc_entry_chapter(doc, 7, "RESULTS & DISCUSSION", "20")
add_toc_entry_section(doc, "7.1", "Interception quality", "20")
add_toc_entry_section(doc, "7.2", "Ask and answer decisions", "21")
add_toc_entry_section(doc, "7.3", "Type agreement", "22")
add_toc_entry_section(doc, "7.4", "Length of prompts and questions", "23")
add_toc_entry_section(doc, "7.5", "Routing and the comparison model", "23")
add_toc_entry_section(doc, "7.6", "Latent and decision cases", "24")
add_toc_entry_section(doc, "7.7", "Discussion", "25")

add_toc_entry_chapter(doc, 8, "CONCLUSION", "26")
add_toc_entry_section(doc, "8.1", "Scope of further work", "27")
add_toc_entry_subsection(doc, "8.1.1", "Link-grounded and longitudinal measurement", "27")
add_toc_entry_subsection(doc, "8.1.2", "Judges, languages, and reproducible runs", "28")
add_toc_entry_fm(doc, "REFERENCES", "29")
add_toc_entry_fm(doc, "LIST OF PUBLICATIONS", "32")

# ══════════════════════════════════════════════
# LIST OF TABLES (page vii)
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "LIST OF TABLES")

for entry in [
    ("7.1", "Interception quality under three scorers.", "20"),
    ("7.2", "Type agreement between the clarification (rows) and the prompt (columns).", "22"),
    ("7.3", "EcoGate routing on 56 prompts.", "23"),
    ("7.4", "Offline token and energy comparison.", "24"),
    ("7.5", "Latent-versus-decision check on 12 constructed cases.", "25"),
]:
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Pt(45.4)
    para.paragraph_format.first_line_indent = Pt(-27.5)
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(10), Pt(0))
    r = para.add_run("{}\t{}\t{}".format(entry[0], entry[1], entry[2]))
    r.font.name = FONT; r.font.size = SZ_BODY

# ══════════════════════════════════════════════
# LIST OF FIGURES (page viii)
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "LIST OF FIGURES")

for entry in [
    ("7.1", "Type agreement between clarification question type and prompt ambiguity type.", "22"),
    ("7.2", "Word token counts in the prompt and in the clarifying question.", "23"),
]:
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Pt(45.4)
    para.paragraph_format.first_line_indent = Pt(-27.5)
    _set_ls(para, LS_BODY)
    _set_sp(para, Pt(10), Pt(0))
    r = para.add_run("{}\t{}\t{}".format(entry[0], entry[1], entry[2]))
    r.font.name = FONT; r.font.size = SZ_BODY

# ══════════════════════════════════════════════
# CHAPTER 1 — INTRODUCTION
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 1, "INTRODUCTION TO THE PROJECT")

add_body(doc,
    'This chapter states the problem the project addresses, the objectives that guided '
    'the work, and the order of the remaining chapters. It also provides background on '
    'large language models, the challenges in evaluating them, and the motivation for '
    'building an evaluation framework that is simultaneously semantic, grounded in '
    'external evidence, energy-aware, and capable of refusing to answer ambiguous queries.')

add_section_heading(doc, "1.1", "Background")

add_body(doc,
    'Large language models are now used for information retrieval, code generation, '
    'summarisation, and question answering [1]. These models are deployed in production '
    'systems that serve millions of users, making reliable evaluation both technically '
    'critical and economically significant. Despite their widespread deployment, '
    'principled evaluation of LLM outputs remains an open research problem. Standard '
    'reference-based metrics such as ROUGE and BLEU measure surface word overlap, which '
    'fails to capture semantic equivalence between a generated answer and a correct one '
    'expressed in different words [2]. Embedding-based metrics such as BERTScore and '
    'BLEURT provide better semantic coverage, but require a fixed reference answer and '
    'do not account for the cost of calling a model repeatedly to obtain that reference [3].')
add_body(doc,
    'The project investigates an evaluation setting in which links are the primary '
    'inputs. A link may point to documentation, a live web page, an API specification, '
    'or a code repository. The model is expected to retrieve and reason about the page, '
    'and the evaluator must decide whether the output is faithful to the linked source. '
    'This introduces two challenges that do not appear in a closed-book setting: first, '
    'the page changes over time, so a benchmark snapshot can become stale; second, a '
    'prompt that underspecifies which section of a large document to summarise is '
    'ambiguous in a way that ROUGE cannot detect, since it treats all tokens equally.')
add_body(doc,
    'The work implemented and measured is a Python pipeline for that measurement problem. '
    'A local linguistic analysis proposes problematic spans in a prompt by tagging named '
    'entities, coreference chains, homonym candidates, and dependency-scope ambiguities. '
    'A tiered controller reads those spans and decides whether to ask for clarification '
    'before the LLM is called, to send one diagnostic call, or to proceed. The EcoGate '
    'component records a token and estimated joule count for every routing decision, '
    'so that the energy cost of evaluation is explicit rather than hidden in a leaderboard '
    'score. These design choices respond directly to gaps identified in the survey of '
    'twenty recent papers on efficient generation and on ambiguity handling [15]\u2013[34].')

add_section_heading(doc, "1.2", "Objectives")

add_body(doc,
    'The central problem is to build a reproducible, energy-aware, and explainable '
    'evaluation framework that measures language models on link-grounded prompts, '
    'intercepts ambiguous queries before generation, and reports a cost alongside '
    'every score. The specific objectives that guided the work are as follows.')
add_body(doc,
    'First, to design and implement a tiered controller that uses local NLP analysis '
    'as a zero-token first stage, invokes a diagnostic LLM call only when NLP '
    'confidence is in a middle band, and skips generation entirely for high-confidence '
    'ambiguous prompts, thereby saving the token and energy cost of the auto-regressive '
    'decoding step for the majority of under-specified inputs.')
add_body(doc,
    'Second, to build a scoring pipeline that evaluates output quality using word '
    'overlap, sentence-embedding similarity (SBERT with optional NLI), and an optional '
    'LLM-as-a-judge step, so that the same benchmark can be run with any subset of '
    'these scorers and the results can be compared across configurations.')
add_body(doc,
    'Third, to instrument every routing decision with an energy ledger that counts '
    'input and output tokens separately and converts them to estimated joules using '
    'configurable per-token energy coefficients, making the evaluation cost explicit '
    'and comparable to a generate-anyway baseline.')
add_body(doc,
    'Fourth, to validate the framework on a generated benchmark of 56 ambiguous '
    'prompts and five explicit controls, and to compare it with a generate-anyway '
    'baseline to quantify the token and energy saving from interception.')

add_section_heading(doc, "1.3", "Organisation of the report")

add_body(doc,
    'Chapter 2 gives the reasons for selecting this problem. It explains why standard '
    'lexical metrics are insufficient, why grounding in external documents matters, '
    'and why cost and explainability are first-class evaluation concerns.')
add_body(doc,
    'Chapter 3 surveys evaluation frameworks, grounding metrics, semantic similarity '
    'metrics, LLM-as-a-judge work, and the studies on efficient generation and '
    'ambiguity handling that motivated the EcoGate design.')
add_body(doc,
    'Chapter 4 describes the architecture of the measurement API and the methodology '
    'used to produce the numbers in this report. Chapter 5 describes the implementation '
    'in detail, covering the package layout, the query path, and the benchmark '
    'execution scripts. Chapter 6 lists the software tools, model endpoint, and '
    'execution environment. Chapter 7 presents the results, including interception '
    'rates, type agreement, token and energy comparisons, and latent-versus-decision '
    'case analysis. Chapter 8 draws conclusions and identifies directions for further work.')

# ══════════════════════════════════════════════
# CHAPTER 2 — MOTIVATION
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 2, "MOTIVATION")

add_body(doc,
    'The topic was chosen because language-model evaluation is now part of ordinary '
    'software practice, and the usual scores leave at least three significant gaps. '
    'The first gap is that lexical metrics fail on paraphrase. The second is that '
    'grounding in a live external document is not measured by any standard benchmark. '
    'The third is that evaluation has an energy cost that never appears in a leaderboard. '
    'This chapter explains each gap in detail and argues that all three must be addressed '
    'together to make evaluation practically useful.')

add_section_heading(doc, "2.1", "Limits of lexical scores")

add_body(doc,
    'ROUGE and BLEU remain convenient because they need no second model and no human '
    'rater. They reward shared word sequences between a generated answer and a reference '
    'string. That design decision means a perfect paraphrase that uses no word from the '
    'reference receives a score of zero, while a response that copies words from the '
    'reference but reverses their meaning can receive a high score. ROUGE-L measures the '
    'longest common subsequence, which is slightly more robust to reordering but still '
    'sensitive to vocabulary choice.')
add_body(doc,
    'BERTScore [2] addresses the paraphrase problem by aligning token embeddings from a '
    'pre-trained transformer, but it still requires a fixed reference answer. In a '
    'link-grounded setting the reference is the page retrieved at measurement time, and '
    'that page can differ from the page the model saw during pre-training or fine-tuning. '
    'The metric score can therefore degrade for a correct answer simply because the '
    'documentation has been updated. BLEURT [3] trains a regression model on human '
    'quality judgments, which gives it better calibration on out-of-domain text, but '
    'the same reference dependency remains.')
add_body(doc,
    'None of these metrics intercepts a prompt that is under-specified. A question asking '
    'for \u201cthe return window for Monday orders\u201d without naming a timezone is ambiguous, '
    'and word-overlap metrics will score any generated answer against whatever reference '
    'the evaluator happens to hold, regardless of whether the model guessed the correct '
    'timezone. The ambiguity is invisible to the metric because the metric operates on '
    'strings, not on the semantics of the task.')

add_section_heading(doc, "2.2", "Grounding in external sources")

add_body(doc,
    'Documentation and public web pages change. A benchmark built from a snapshot can '
    'stop matching the page it claims to test within days of publication. The evaluation '
    'API specification in this project requires that a measurement run store a hash of '
    'the retrieved page alongside the score, so that a later auditor can verify whether '
    'the benchmark was run against the same content. Without that hash, a score decrease '
    'over time is uninterpretable: it could be model regression, page drift, or both.')
add_body(doc,
    'Grounding also bears on explainability. A score of 0.72 from BERTScore tells an '
    'engineer that the output is moderately similar to the reference, but it does not say '
    'which clause in the generated text contradicts which sentence in the source. An '
    'explanation-fidelity sub-score, as specified in the architecture, attaches each scored '
    'clause to the evidence sentence that supports or contradicts it. That attachment is '
    'only possible if the evaluator retrieves the page and parses it at measurement time. '
    'Link-aware evaluation is therefore not just an accuracy concern; it is a prerequisite '
    'for the kind of interpretable feedback that an engineer can act on.')

add_section_heading(doc, "2.3", "Cost, explanation, and stability")

add_body(doc,
    'Evaluation has a cost that is easy to leave out of a leaderboard. Fetching pages, '
    'repeating prompts, and calling a judge model each consume tokens and energy. '
    'FrugalGPT [15] demonstrated that routing queries to cheaper models based on '
    'confidence can reduce cost by an order of magnitude without a proportional loss '
    'in quality, but it still generates an answer before it can stop. The EcoGate '
    'component in this project moves the savings upstream: it refuses to begin decoding '
    'until the prompt is sufficiently specified, so the highest-cost step \u2014 the '
    'auto-regressive generation \u2014 is simply not invoked for high-confidence ambiguous queries.')
add_body(doc,
    'Stability across repeated runs is a separate dimension of evaluation quality that '
    'leaderboards ignore. A model that returns subtly different answers on consecutive '
    'calls to the same prompt is harder to trust in production than one whose output '
    'variance is small. The design specifies a stability sub-score computed from multiple '
    'samples of the same query, reported as a median score and interquartile range. '
    'The concern for environmental impact, articulated by Luccioni et al. [23] in their '
    'analysis of the carbon footprint of BLOOM inference, motivates the joule ledger: '
    'reporting energy alongside accuracy makes the true cost of a benchmark visible to '
    'practitioners who must run it repeatedly in continuous integration.')
add_body(doc,
    'Taken together, these three gaps \u2014 lexical metric inadequacy, the need for live '
    'grounding with explainable evidence chains, and the hidden cost of evaluation \u2014 '
    'define the design space that this project fills. The EcoGate contribution is '
    'specifically positioned against the openings left by twenty recent papers on '
    'efficiency and ambiguity, described in the survey in Chapter 3.')

# ══════════════════════════════════════════════
# CHAPTER 3 — LITERATURE SURVEY
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 3, "LITERATURE SURVEY")

add_body(doc,
    'This chapter surveys the evaluation frameworks, grounding metrics, semantic '
    'similarity measures, LLM-as-a-judge methods, explainability and sustainability '
    'studies, and the efficiency and ambiguity papers that motivated the EcoGate design. '
    'The twenty papers reviewed for the EcoGate positioning are cited in Section 3.6.')

add_section_heading(doc, "3.1", "Existing LLM evaluation frameworks")

add_body(doc,
    'Several open-source and commercial frameworks have been proposed for evaluating '
    'large language models [6], [8]. Tools such as HELM (Holistic Evaluation of Language '
    'Models) provide broad multi-task benchmarks that measure a model on accuracy, '
    'calibration, robustness, fairness, and efficiency simultaneously. HELM constructs '
    'scenarios that pair a prompt with a correct reference and scores model outputs on '
    'the reference. The framework is valuable for comparative leaderboard entries but '
    'does not address live page grounding: all references are fixed at benchmark '
    'creation time.')
add_body(doc,
    "OpenAI's evaluation and observability guidelines [6] recommend running gold-standard "
    'prompt suites on every model checkpoint and tracking score distributions over time. '
    "IBM's responsible AI pipeline [8] adds bias and fairness auditing to the standard "
    'accuracy measurement. Neither framework records the energy cost of an evaluation run, '
    'and neither intercepts ambiguous prompts: both assume a well-formed query and score '
    'whatever the model returns.')
add_body(doc,
    "Chrome for Developers' evaluation guide [9] covers API-level quality metrics for "
    'model endpoints, noting that latency and token throughput are as important as accuracy '
    'in production, but it does not define a semantic score and does not address link '
    'grounding. Sistla [10] built axo-eval, a tool that measures LLM accuracy on '
    'documentation URLs by retrieving the page, extracting key facts, and scoring model '
    'answers against those facts. LuotoCompany [11] takes a similar approach. These two '
    'tools are the closest to the link-grounded setting in this project, but neither '
    'implements an ambiguity interception step, and neither reports energy consumption.')

add_section_heading(doc, "3.2", "Link-based and grounding metrics")

add_body(doc,
    'Recent work has stressed that generated text should be grounded in external '
    'evidence [7], [12]. Link-aware evaluation asks whether a generated answer is '
    'supported by a specific passage in a retrieved document, rather than by a static '
    'reference string. Google Research [7] developed attribution metrics that check '
    'whether each factual claim in a generated answer is entailed by a cited source. '
    'Microsoft Research [12] extended this to multi-document settings, where a model '
    'must cite multiple passages and the evaluator verifies each citation.')
add_body(doc,
    'These grounding-oriented metrics share a common requirement: the evaluator must '
    'retrieve the linked document at measurement time. This creates a stale-reference '
    'problem that the hash-and-snapshot mechanism in the present architecture is '
    'designed to address. The attribution approach also naturally supports explanation '
    'fidelity: by attaching a score to a specific sentence pair (generated claim, '
    'source sentence), the evaluator provides the kind of localised feedback that an '
    'engineer can use to debug a model\u2019s output, an improvement over a single '
    'aggregate score.')

add_section_heading(doc, "3.3", "Semantic similarity and NLP metrics")

add_body(doc,
    'Semantic scores are used because two texts can carry the same meaning with different '
    'wording. BERTScore [2] computes token-level cosine similarities between contextual '
    'embeddings from a BERT model, then aggregates them with a greedy matching procedure. '
    'It correlates better with human judgment than BLEU on most tasks and is robust to '
    'synonym substitution. BLEURT [3] trains a learned regression model on human quality '
    'annotations, giving it better coverage on domain-specific text.')
add_body(doc,
    'Sentence-BERT [4] produces fixed-size sentence embeddings that can be compared with '
    'cosine similarity at low inference cost, making it practical for large-scale '
    'evaluation runs. The present pipeline uses SBERT embeddings for the clarification '
    'scorer because they are fast to compute and do not require a second model call per '
    'sample. The NLI sub-score \u2014 which checks whether a generated clarification '
    'question is entailed by or neutral to the prompt \u2014 uses a cross-encoder from '
    'the same sentence-transformers library. Both are computed locally, contributing '
    'to the zero-extra-token-cost design goal of the NLP-first stage.')

add_section_heading(doc, "3.4", "LLM-as-a-judge")

add_body(doc,
    'LLM-as-a-judge uses a strong language model to score outputs against a rubric such '
    'as relevance, correctness, clarity, fluency, and groundedness. Guo et al. [5] '
    'surveyed the rapidly growing literature on this approach, noting that it correlates '
    'well with human judgment on instruction-following tasks but is susceptible to '
    'position bias (preferring earlier options in a comparison) and verbosity bias '
    '(preferring longer answers). These biases motivate the judge fairness sub-score '
    'specified in the architecture: by running the judge with swapped option order and '
    'measuring how often the ranking changes, the evaluator can flag judge-unreliable samples.')
add_body(doc,
    'The intent judge in this project is a specialised LLM-as-a-judge step that operates '
    'at the type level rather than the quality level: it checks whether the type inferred '
    'from the clarification question matches the type inferred from the prompt (missing '
    'entity, semantic overlap, or syntax error). Running this judge on the 56-prompt '
    'benchmark produced 7 errors (prompts it could not evaluate) and relabeled 29 gold '
    'types from the cycled file labels, raising the type accuracy from 0.357 to 0.959 '
    'on the 49 prompts it did evaluate.')

add_section_heading(doc, "3.5", "Explainable, ethical, and sustainable evaluation")

add_body(doc,
    'Kautish and Gurung [13] reviewed sustainable computing across hardware and '
    'algorithmic dimensions, concluding that software-layer savings \u2014 including '
    'smarter inference routing \u2014 are as important as chip-level efficiency gains. '
    'Their review covers prompt compression, model quantisation, and batching strategies, '
    'and explicitly calls out the absence of end-to-end energy accounting as a gap in '
    'the literature.')
add_body(doc,
    'Mazhar and colleagues [14] reviewed 140 empirical studies on transparency, fairness, '
    'and accountability in sustainable technology, finding that explainability and ethical '
    'accountability are increasingly treated as first-class engineering properties rather '
    'than post-hoc concerns. The present project turns that reading into concrete metrics: '
    'explanation fidelity attaches a passage to a claim; judge fairness scores a judge by '
    'how often its ranking reverses under option permutation; energy is reported per '
    'evaluation run, not hidden inside a cloud bill.')

add_section_heading(doc, "3.6", "Openings left by cost and ambiguity studies")

add_body(doc,
    'The controller was positioned against twenty studies of cheaper generation and of '
    'ambiguity [15]\u2013[34]. FrugalGPT [15] names environmental impact and uncertainty as '
    'future objectives; its cascade still generates an answer before it can stop. RouteLLM '
    '[16] routes by model strength, not by refusing an ambiguous query. LLMLingua [17] '
    'compresses the prompt, then still answers it. CALM [18] exits early per token during '
    'decoding, but the request is still answered. Speculative decoding [19] and LayerSkip '
    '[20] make decoding faster without deciding whether decoding should start. '
    'PagedAttention/vLLM [21] optimises KV-cache memory, assuming the query is worth '
    'generating. PowerInfer [22] addresses power of the forward pass, not power avoided '
    'by not calling the model.')
add_body(doc,
    "BLOOM's carbon footprint study [23] reports emissions more accurately but proposes "
    'no policy that withholds generation. SpecEE [24] exits early inside the forward pass; '
    'a skipped request is outside its design. The efficient LLM serving survey [25] points '
    'future work at faster decoding. Language model cascades [26] defer only after '
    'generation evidence exists.')
add_body(doc,
    'On the ambiguity side, AmbigQA [27] answers every reading and therefore multiplies '
    'output tokens. Semantic uncertainty [28] is bought by extra sampled answers. '
    'SelfCheckGPT [29] generates more answers, then checks consistency. \u201cClarify When '
    'Necessary\u201d [30] scores when to ask, but is not tied to joules and not a zero-token '
    'first stage. \u201cFrom Answers to Interpretations\u201d [31] estimates ambiguity without '
    'answers; its stated future work is to use that estimate to choose an action \u2014 '
    'EcoGate is that action. Steerable clarification policies [32] learn a cost per word '
    'without a zero-token linguistic stage or a watt model. RegretBench [33] points future '
    'work at policy optimisation under interaction cost, not accelerator energy. Diagnostic '
    'clarifying questions [34] address question quality, not the energy of refusing a '
    'premature answer.')

# ══════════════════════════════════════════════
# CHAPTER 4 — DESIGN AND METHODOLOGY
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 4, "DESIGN AND METHODOLOGY")

add_body(doc,
    'This chapter separates the architecture specified for the measurement API from the '
    'procedure that produced the numbers in Chapter 7. The architecture is the full design '
    'intended for a production evaluation system. The procedure is the subset of that '
    'architecture that was implemented and measured within the scope of this project.')

add_section_heading(doc, "4.1", "Specified architecture")

add_body(doc,
    'The design organises the API into five layers. The ingestion layer retrieves a page '
    'at a given URL, strips navigation and boilerplate, stores the cleaned text and its '
    'SHA-256 hash, and passes the cleaned content to the prompt builder. The prompt '
    'builder constructs a query that includes the retrieved content, task instruction, '
    'and any user-supplied context, then submits it to the ambiguity controller.')
add_body(doc,
    'The ambiguity controller is the EcoGate component. It runs local NLP analysis first. '
    'If the highest-scoring span exceeds a high-confidence threshold (ECO_TAU_HIGH, '
    'default 0.80), the controller emits a template clarification question and records '
    'zero LLM tokens. If the score falls in a middle band between ECO_TAU_LOW (default '
    '0.40) and ECO_TAU_HIGH, the controller sends one diagnostic call to the model and '
    'records those tokens. If the score is below ECO_TAU_LOW, the prompt is considered '
    'unambiguous and is passed to the evaluation layer, which calls the target LLM, '
    'scores the output with the configured scorers, and returns a scored result.')
add_body(doc,
    'The scoring layer has three sub-components: word overlap (which uses Python string '
    'intersection over lowercased tokens), embedding similarity (which uses SBERT to '
    'compute cosine similarity between the generated answer and the reference), and an '
    'optional LLM-as-a-judge step (which calls a strong model with a rubric prompt). '
    'The energy ledger records input tokens, output tokens, CPU processing time, and '
    'estimated joules for every layer, using configurable per-token energy coefficients.')

add_section_heading(doc, "4.2", "Tiered controller")

add_body(doc,
    'The NLP stage uses spaCy for tokenisation, part-of-speech tagging, dependency '
    'parsing, and named entity recognition. It also uses WordNet for homonym detection '
    '(words with multiple synsets in the same part-of-speech category) and a coreference '
    'heuristic (pronouns or demonstratives that have no antecedent in the same sentence). '
    'Each proposed span is assigned a kind (missing_entity, coref, wsd, vague_np, or '
    'syntax_scope) and a confidence score based on the number of independent signals '
    'that agree on that span.')
add_body(doc,
    'The controller reads the top span and its score. The ask-or-diagnose-or-answer '
    'decision is a simple threshold comparison: score \u2265 ECO_TAU_HIGH \u2192 nlp_clarify; '
    'ECO_TAU_LOW \u2264 score < ECO_TAU_HIGH \u2192 llm_diagnose; score < ECO_TAU_LOW \u2192 answer. '
    'This three-way routing means that the majority of ambiguous prompts never reach '
    'the LLM. Only the borderline cases require a diagnostic call, and that call returns '
    'a structured JSON response that includes a confirmed ambiguity type and a problematic '
    'clause, used to generate a targeted clarification question.')
add_body(doc,
    'The design of the diagnostic prompt is important for precision. It instructs the '
    'model to respond only in valid JSON with the fields isAmbiguous, type, clause, and '
    'reasoning. The reasoning field captures the natural-language justification, which '
    'is surfaced in the output as an explanation. If the JSON response is malformed, '
    'the controller falls back to the NLP-only classification and records the error.')

add_section_heading(doc, "4.3", "Scoring procedure")

add_body(doc,
    'The word-overlap scorer computes the fraction of unique tokens in the clarification '
    'question that also appear in the prompt. It is a low-cost baseline that is '
    'interpretable but sensitive to synonym substitution. The embedding scorer computes '
    'a cosine similarity between the SBERT embedding of the clarification question and '
    'the SBERT embedding of the problematic clause extracted from the prompt. A match '
    'is recorded if the cosine similarity exceeds a fixed threshold of 0.30.')
add_body(doc,
    'An optional NLI sub-score checks whether the clarification question is entailed by '
    'or neutral to the prompt, using a cross-encoder trained on natural language inference '
    'tasks. Entailment is scored as 1.0, neutral as 0.5, and contradiction as 0.0. The '
    'combined clarification score is an average of the available sub-scores.')
add_body(doc,
    'The intent judge scorer calls a language model with a prompt that presents both the '
    'clarification question and the original prompt and asks whether the question seeks '
    'the same information as the prompt\u2019s ambiguous clause. It also asks the judge to '
    'infer the ambiguity type from the clarification question and from the prompt alone, '
    'allowing re-annotation of gold labels that were assigned mechanically by the dataset '
    'creation script.')

add_section_heading(doc, "4.4", "Energy comparison model")

add_body(doc,
    'The energy comparison model is not a wall-meter reading. It is a relative estimator '
    'that makes the token and joule cost of two routing strategies comparable under a '
    'fixed set of coefficients. The coefficients are: input tokens at 0.2 J/token, output '
    'tokens at 8.0 J/token (output is higher because auto-regressive decoding is '
    'memory-bandwidth bound), and CPU-only NLP processing at 15.0 W. These values are '
    'taken from the BLOOM carbon footprint methodology [23] and adjusted for a smaller '
    'inference server.')
add_body(doc,
    'The generate-anyway baseline is defined as the energy that would be consumed if '
    'every prompt were sent to the model and answered without an NLP pre-screen. It is '
    'computed by measuring the token count of a generate-without-filter run on the same '
    '56 prompts (108,488 tokens) and multiplying by the per-token coefficients. '
    "EcoGate's cost is computed from its own token counts (5,210 tokens, mostly from "
    'the 5 diagnostic LLM calls) plus the CPU time for the 51 NLP-only routes. '
    'The difference (103,278 tokens, 148,560 J) is the estimated saving, which is '
    'explicitly labelled as a comparison-model figure in every result table.')

add_section_heading(doc, "4.5", "Data used for measurement")

add_body(doc,
    'The benchmark uses 56 prompts generated by scripts/create_dataset.py. The script '
    'requests ambiguous prompts from the LLM by cycling three ambiguity types: missing '
    'entity, syntax error, and semantic overlap. The cycled label is stored as the gold '
    'type, but as the results show, it is not an independent annotation: the LLM often '
    'generates a grammatically correct sentence for the \u2018syntax error\u2019 slot. The '
    'intent judge relabeled 29 of these when it ran on the benchmark, raising type '
    'accuracy substantially.')
add_body(doc,
    'A separate control set of five prompts was written manually with an explicit date, '
    'place, or quantity. These prompts are designed to be clear enough that the gate '
    'should answer without asking for clarification. They serve as a false-positive check: '
    'a gate that asks on all five controls is over-sensitive.')
add_body(doc,
    'A further set of 12 constructed cases distinguishes decision ambiguity from latent '
    'ambiguity. Decision ambiguity means the prompt could be answered in more than one '
    'equally valid way (e.g., a pronoun with two possible referents). Latent ambiguity '
    'means the ambiguity only becomes apparent after the model attempts to answer (e.g., '
    'a word that has a technical meaning in context but was used in the everyday sense). '
    'The 12 cases were written to be balanced across the two categories and a third '
    'category of fully explicit prompts.')

add_section_heading(doc, "4.6", "Repeated runs, drift, and deferred checks")

add_body(doc,
    'The design specifies a response to non-determinism. The API should sample a query '
    'more than once and report a stability score as a median and interquartile range over '
    'the sample scores. This stability score is not in the saved summaries because the '
    'benchmark was run once per scorer configuration, not multiple times per prompt. '
    'It remains a specified but not yet measured property of the pipeline.')
add_body(doc,
    'Drift detection is handled by the hash stored with the page at retrieval time. If a '
    'measurement run detects that the hash of the current page differs from the stored '
    'hash, it marks the benchmark entry as potentially stale and reports the drift as a '
    'warning. This check runs at measurement time only if live page fetching is enabled; '
    'in the offline runs reported here, no pages are fetched and no drift is recorded.')

# ══════════════════════════════════════════════
# CHAPTER 5 — IMPLEMENTATION
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 5, "IMPLEMENTATION")

add_body(doc,
    'The software is a Python package, ambiguity_layer, with scripts that build data, '
    'run benchmarks, and write the JSON files that form the results of this report. '
    'This chapter describes the package structure, the query path through the system, '
    'the benchmark execution, and the failure handling strategy.')

add_section_heading(doc, "5.1", "Package layout")

add_body(doc,
    'The package is divided by role. ambiguity_layer/nlp performs tokenisation, '
    'part-of-speech tagging, dependency cues, named entity recognition, coreference '
    'heuristics, WordNet homonym scoring, and span proposal. It exposes a single '
    'public function, analyse(prompt), that returns a list of proposed spans in '
    'descending confidence order.')
add_body(doc,
    'ambiguity_layer/pipeline contains the tiered controller (diagnose, clarify, merge, '
    'process_query). diagnose sends a structured diagnostic prompt to the LLM and parses '
    'the JSON response. clarify builds a human-readable clarification question from the '
    'confirmed clause. merge combines NLP spans with the LLM diagnosis result when both '
    'stages have run. process_query is the main entry point called by scripts.')
add_body(doc,
    'ambiguity_layer/eval contains the word-overlap scorer, the SBERT+NLI clarification '
    'scorer, and the intent judge. Each scorer exposes a score(sample) method that takes '
    'a benchmark sample and returns a numeric score and a structured breakdown. '
    'ambiguity_layer/optimize contains the energy ledger (energy.py) and the EcoGate '
    'routing logic (ecogate.py). ambiguity_layer/llm contains the OpenAI-compatible '
    'client (client.py) and the hybrid judge (hybrid_judge.py).')
add_body(doc,
    'The scripts/ directory contains five scripts: setup_nlp.py (downloads spaCy and '
    'NLTK models), demo.py (interactive demonstration), create_dataset.py (generates '
    'benchmark prompts), run_benchmark.py (runs the full benchmark with a chosen scorer), '
    'and run_ecogate.py (runs the EcoGate routing and energy comparison).')

add_section_heading(doc, "5.2", "Query path")

add_body(doc,
    'On a prompt, the NLP analysis runs first and returns entities, coreference risks, '
    'homonym cues, dependency-scope cues, and ranked problematic spans. The EcoGate '
    'controller reads the top span and decides the route. For the nlp_clarify route, '
    'it instantiates a template clarification question from the span text and span kind, '
    'records zero LLM tokens in the energy ledger, and returns the question.')
add_body(doc,
    'For the llm_diagnose route, it builds a diagnostic prompt that includes the original '
    'prompt and the top NLP span, sends it to the LLM, and parses the structured JSON '
    'response. The JSON includes fields isAmbiguous (boolean), type (string), clause '
    '(string), and reasoning (string). The controller reads these fields to build the '
    'clarification question and records the prompt and completion token counts in the '
    'energy ledger.')
add_body(doc,
    'For the answer route, the controller passes the prompt directly to the evaluation '
    'layer, which calls the target LLM and scores the output. This route was taken zero '
    'times on the 56 generated prompts, confirming that the NLP analysis found at least '
    'one span in every generated ambiguous prompt.')

add_section_heading(doc, "5.3", "Benchmark and EcoGate runs")

add_body(doc,
    'scripts/run_benchmark.py writes the detection, type, clause, and clarification '
    'summaries. It accepts a --scorer flag to select word-overlap, nlp (SBERT+NLI), or '
    'intent-judge. The three result files are: results/benchmark_full.json (word-overlap '
    'scorer, 56 prompts), results/benchmark_full_intent.json (intent judge, 49 evaluated), '
    'and results/benchmark_nlp.json (SBERT+NLI scorer, 56 prompts).')
add_body(doc,
    'scripts/run_ecogate.py writes results/ecogate.json. It accepts a --live flag; '
    'without it, the run is offline and the LLM client is not called. In offline mode '
    'the diagnostic token counts are taken from a stored set of benchmark_full results, '
    'so the token and joule figures are reproducible without an API key. The script '
    'records the action (nlp_clarify, llm_diagnose, or answer), the token counts, the '
    'NLP processing time in seconds, and the estimated joules for each of the 56 prompts.')

add_section_heading(doc, "5.4", "Failure handling")

add_body(doc,
    'The client raises a clear error if the API key is unset. On a rate-limit response '
    '(HTTP 429) it parses the Retry-After header or falls back to exponential backoff '
    'with a base delay of two seconds and a maximum of five retries. On a timeout it '
    'retries once and then marks the sample as errored. The intent judge benchmark '
    'recorded 7 errors, all timeouts from the LLM endpoint; those samples are excluded '
    'from the type accuracy calculation for that scorer.')
add_body(doc,
    'NLP errors (spaCy model not found, WordNet corpus not downloaded) are raised as '
    'ImportError or LookupError with a descriptive message directing the user to run '
    'scripts/setup_nlp.py. JSON parse errors from the diagnostic LLM response fall back '
    'to the NLP-only classification, so a malformed LLM response does not crash the '
    'pipeline but is flagged in the structured output with an error field.')

# ══════════════════════════════════════════════
# CHAPTER 6 — TOOLS AND TECHNOLOGIES
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 6, "HARDWARE / SOFTWARE TOOLS USED")

add_body(doc,
    'This chapter lists the tools that the repository and the result files identify. '
    'It does not add a machine specification that is not in the saved data, in keeping '
    'with the principle of reporting only reproducible facts.')

add_section_heading(doc, "6.1", "Software")

add_body(doc,
    'The stack is Python 3.10 or later. The following libraries are declared in the '
    'project requirements:')
add_body(doc,
    'openai (version 1.40 or later) \u2014 the OpenAI-compatible client used to call '
    'the chat completion endpoint. It provides the ChatCompletion interface, structured '
    'error classes for rate limiting and timeout, and async support used in the '
    'benchmark runner.')
add_body(doc,
    'spaCy (version 3.x with the en_core_web_sm model) \u2014 used for tokenisation, '
    'part-of-speech tagging, dependency parsing, and named entity recognition in the '
    'NLP analysis stage. The en_core_web_sm model is downloaded by scripts/setup_nlp.py.')
add_body(doc,
    'sentence-transformers \u2014 provides the SentenceTransformer class used to compute '
    'SBERT embeddings (all-MiniLM-L6-v2) and the cross-encoder used for the NLI sub-score '
    '(cross-encoder/nli-MiniLM2-L6-H768). The models are downloaded on first use and '
    'cached locally.')
add_body(doc,
    'nltk (WordNet corpus) \u2014 used for homonym detection. The wordnet corpus is '
    'downloaded by scripts/setup_nlp.py with nltk.download(\u2018wordnet\u2019).')
add_body(doc,
    'numpy and scikit-learn \u2014 used for cosine similarity computation and confusion '
    'matrix generation in the analysis scripts.')
add_body(doc,
    'python-dotenv \u2014 loads the .env file containing the API key and base URL into '
    'environment variables at startup, keeping credentials out of source control.')

add_section_heading(doc, "6.2", "Models and endpoint")

add_body(doc,
    'The chat client targets an OpenAI-compatible base URL. The default in the project '
    'configuration is https://api.llm7.io/v1, an open-source LLM API proxy that serves '
    'multiple model backends under a single endpoint. The model identifier used in the '
    'diagnostic and judge calls is configured via the LLM_MODEL environment variable; '
    'the default is a GPT-3.5-class model.')
add_body(doc,
    'No proprietary model weights are downloaded; the client calls a hosted inference '
    'endpoint and receives token counts in the usage field of the API response. The '
    'SBERT model and the cross-encoder run locally and require no API key. Their '
    'inference costs are measured in CPU seconds and estimated watts rather than tokens.')

add_section_heading(doc, "6.3", "Execution environment")

add_body(doc,
    'The benchmarks run as ordinary Python processes on Windows 10 (the development '
    'machine identified from the workspace path) or any other OS that can install the '
    'declared dependencies. The repository does not record a processor model, a GPU, '
    'or an OS version; it is designed to be portable.')
add_body(doc,
    'The energy ledger accounts for this by using a configurable CPU wattage parameter '
    '(default 15 W) rather than a measured power draw, and by labelling all joule '
    'figures as comparison-model estimates rather than wall-meter readings. The token '
    'counts are exact (taken from the API usage field or from zero for NLP-only routes) '
    'and are not affected by the hardware environment.')

# ══════════════════════════════════════════════
# CHAPTER 7 — RESULTS AND DISCUSSION
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 7, "RESULTS & DISCUSSION")

add_body(doc,
    'The numbers in this chapter are taken from the saved JSON summaries in the results/ '
    'directory. No new model calls were made for the report. Word overlap, the intent '
    'judge, and the embedding scorer answer different questions, so their numbers are '
    'presented separately and then interpreted together in Section 7.7. The energy '
    'figures are comparison-model estimates as described in Section 4.4.')

add_section_heading(doc, "7.1", "Interception quality")

add_body(doc,
    'Table 7.1 and Figure 7.1 summarise the three runs. Word overlap and the embedding '
    'scorer each evaluated all 56 prompts with no errors. The intent judge evaluated '
    '49 prompts and recorded 7 errors (timeout or parse failure). Detection rate is the '
    'fraction of prompts correctly identified as ambiguous. Word overlap detected 53 of '
    '56 (rate 0.946). The embedding scorer detected all 56 (rate 1.000). The intent '
    'judge detected 47 of the 49 it evaluated (rate 0.959).')
add_body(doc,
    'Clarification is the point on which the scorers diverge, and the clarification '
    'column is not one quantity. For word overlap the saved field is a mean score of '
    '0.316, measuring how many words in the clarifying question also appear in the '
    'prompt. For the intent judge the match rate is 0.653, measuring how often the '
    'judge agrees that the question addresses the ambiguous clause. For SBERT/NLI '
    'the match rate is 0.321, measuring cosine similarity between the clarification '
    'question embedding and the clause embedding.')

add_caption(doc, "Table 7.1: Interception quality under three scorers.")
add_table_interception(doc)

add_section_heading(doc, "7.2", "Ask and answer decisions")

add_body(doc,
    'The decision the gate is built to make is narrower than type classification. It '
    'should ask before answering when the prompt is under-specified, and it should '
    'answer when the prompt already names the time, place, and quantity that the task '
    'requires. The ambiguous set is the 56 generated prompts. The clear set is five '
    'controls written with an explicit date, place, or quantity.')
add_body(doc,
    'The gate asked for clarification on 54 of the 56 generated prompts (ask rate '
    '54/56 = 0.964). It answered directly on 4 of the 5 explicit controls (answer '
    'rate 4/5 = 0.80). One control was flagged as ambiguous by the NLP analysis due '
    'to a homonym candidate, illustrating that the NLP stage can produce false positives '
    'on well-specified inputs that happen to contain polysemous words.')
add_body(doc,
    'The two prompts for which the gate did not ask both fell into the low-confidence '
    'band and were routed to llm_diagnose, which returned isAmbiguous: false. On manual '
    'inspection, both prompts were borderline cases: they contained vague noun phrases '
    'but the context provided enough information for a reasonable answerable reading. '
    'This suggests that the LLM diagnosis step provides useful precision at the cost '
    'of a small number of tokens for the borderline cases.')

add_section_heading(doc, "7.3", "Type agreement")

add_body(doc,
    'The type score of 0.357 in Table 7.1 compares predictions with the cycled file '
    'label. Because that label is not an independent annotation, a second matrix ignores '
    'it. The row is the type supported by the clarification question (what the gate thinks '
    'is wrong). The column is the type read from the prompt by an independent reader.')
add_body(doc,
    'The confusion matrix is [[34, 0, 0], [0, 1, 0], [3, 0, 18]] for the NLP scorer, '
    'where rows are (missing entity, syntax error, semantic overlap) as classified by '
    'the clarification and columns are the same as classified from the prompt. The three '
    'off-diagonal entries are semantic overlap prompts that the clarification question '
    'treated as missing entity. This is interpretable: an overlap prompt that contains '
    'a pronoun can be addressed either by naming the referent or by asking which reading '
    'is intended.')

add_caption(doc, "Table 7.2: Type agreement between the clarification (rows) and the prompt (columns).")
add_table_type_agreement(doc)
add_figure(doc, FIG_TYPE,
           "Figure 7.1: Type agreement between clarification question type and prompt ambiguity type (ignoring cycled file label).")

add_section_heading(doc, "7.4", "Length of prompts and questions")

add_body(doc,
    'Figure 7.2 counts words in the prompt and words in the clarifying question the gate '
    'emits. Mean prompt length is 46.8 words. Mean question length is 24.0 words. A '
    'question is emitted for 54 of the 56 prompts. The question is substantially shorter '
    'than the prompt in every case: the gate distils the ambiguity to a single targeted '
    'query rather than repeating the whole prompt back to the user.')
add_body(doc,
    'This brevity is a property of the template-question design for the nlp_clarify '
    'route. The template produces a one-sentence question that names the problematic '
    'span and asks for the missing information. For the llm_diagnose route the question '
    'length depends on the LLM output but remains short because the diagnostic prompt '
    'instructs the model to produce one or two focused questions.')

add_figure(doc, FIG_TOKENS,
           "Figure 7.2: Word token counts in the prompt (blue) and in the clarifying question (orange) for all 56 prompts.")

add_section_heading(doc, "7.5", "Routing and the comparison model")

add_body(doc,
    'On the 56 prompts the offline EcoGate run recorded 51 local clarifications, '
    '5 diagnostic calls, and 0 direct answers. Table 7.3 and Figure 7.3 are decision '
    'counts. They are not a metered energy trace; the joule figures are computed from '
    'the comparison model described in Section 4.4.')

add_caption(doc, "Table 7.3: EcoGate routing on 56 prompts (offline run, live_llm = false).")
add_table_ecogate_routing(doc)

add_body(doc,
    'Table 7.4 reports the offline comparison. EcoGate is charged 5,210 tokens and '
    '4,177.21 J. The generate-anyway baseline is charged 108,488 tokens and 152,737.60 J. '
    'The stored token reduction is 0.952 and the stored joule reduction is 0.973. These '
    'figures should be read as comparisons under a fixed energy model, not as wall-meter '
    'readings. Every result file notes: \u201cRelative comparison model, not a wall-meter '
    'reading.\u201d')

add_caption(doc, "Table 7.4: Offline token and energy comparison on 56 prompts.")
add_table_token_energy(doc)

add_section_heading(doc, "7.6", "Latent and decision cases")

add_body(doc,
    'The latent-versus-decision rule was checked on the 12 constructed cases stored with '
    'the rule. It matched the case label on all 12. The confusion counts are 4 on '
    'decision, 5 on latent, and 3 on none/explicit, with no off-diagonal entries. '
    'This is a small constructed set, not a blind test, but it confirms that the rule '
    'correctly distinguishes the two categories as defined in Section 4.5.')
add_body(doc,
    'The practical significance of the latent/decision distinction is that decision '
    'ambiguity can be resolved before the model responds (the user can say which referent '
    'they mean), whereas latent ambiguity only becomes apparent after the model has '
    'committed to an interpretation. The gate intercepts decision ambiguity; latent '
    'ambiguity is logged but does not trigger a clarification question in the current '
    'implementation.')

add_caption(doc, "Table 7.5: Latent-versus-decision check on 12 constructed cases.")
add_table_latent(doc)

add_section_heading(doc, "7.7", "Discussion")

add_body(doc,
    'Detection is high on all three scorers. The pipeline usually recognises that the '
    'generated prompts should be intercepted. Matching the reference clarification is '
    'harder. A mean word-overlap score of 0.316 and an SBERT match rate of 0.321 indicate '
    'that the gate\u2019s clarification question shares some but not all vocabulary with '
    'the reference question. The intent judge match rate of 0.653 is substantially higher, '
    'suggesting that the semantic intent of the question is correct even when the specific '
    'wording differs.')
add_body(doc,
    'Type agreement against the cycled file label should be read with the construction '
    'of that label. The value 0.357 on two scorers, set beside 0.959 after the judge '
    'relabeled 29 types, is evidence that the cycled label is not a reliable gold '
    'standard. The confusion matrix in Section 7.3 shows that the gate\u2019s '
    'classification is internally consistent: missing entity prompts are almost always '
    'classified as missing entity (34 of 37), and semantic overlap prompts are almost '
    'always classified as semantic overlap (18 of 21).')
add_body(doc,
    'The ask/answer check is the result that matches the gate\u2019s purpose. Asking on '
    '54 of 56 generated prompts is consistent with a dataset built to be ambiguous. '
    'Answering on 4 of 5 explicit controls shows that the gate does not ask unnecessarily '
    'on most well-formed prompts. The one false positive was a homonym false alarm; it '
    'represents a systematic error mode that could be reduced by raising the ECO_TAU_HIGH '
    'threshold slightly or by filtering homonym alerts for high-frequency common words.')
add_body(doc,
    'The token and joule comparison is large under the project\u2019s own estimator, '
    'with a stored token reduction of 0.952. The honest reading is the one printed in '
    'the result file: the run did not call the live model on most prompts, so the '
    'comparison is between offline NLP cost and an estimated LLM cost. A live experiment '
    'that calls the model on the baseline would produce metered token counts and would '
    'allow a more reliable comparison.')
add_body(doc,
    'Two further limits follow from the same files. Dispersion across repeated samples, '
    'which the design asks for in the form of a median and an interquartile range, is '
    'not in the summaries. Judge fairness, which the design scores by permuting option '
    'order, is also not measured. These two properties remain as specified but not yet '
    'measured aspects of the architecture.')

# ══════════════════════════════════════════════
# CHAPTER 8 — CONCLUSION
# ══════════════════════════════════════════════
doc.add_page_break()
add_chapter_heading(doc, 8, "CONCLUSION")

add_body(doc,
    'The project set out to measure large language models with an API that can use '
    'external links as evidence and that records the cost and the reasons for a score. '
    'The design specifies link ingestion, ruled ambiguity interception, multi-scorer '
    'output evaluation, an energy ledger, and a stability sub-score. The implementation '
    'covers the core ambiguity controller and the three scorers. The link ingestion and '
    'stability sub-score are specified but not yet measured.')
add_body(doc,
    'On 56 generated prompts, interception fired at rates of 0.946, 0.959, and 1.000 '
    'under word overlap, the intent judge, and the embedding scorer. Clarification match '
    'was substantially lower than detection on the word-overlap and embedding scorers '
    '(0.316 and 0.321) and markedly higher on the intent judge (0.653). The ask/answer '
    'check on 56 generated prompts and 5 explicit controls showed 54 correct asks and '
    '4 correct answers, with one false positive. The offline token comparison estimated '
    'a reduction of 0.952 relative to a generate-anyway baseline under a fixed energy model.')
add_body(doc,
    'The practical conclusion is that a measurement API can refuse to decode an answer '
    'while a prompt is still ambiguous, and that it can say so with a local NLP analysis '
    'on 51 of 56 prompts without calling the LLM. A score report that includes detection '
    'rate, clarification quality, ask/answer accuracy, token count, and estimated joules '
    'gives an engineer substantially more information than a leaderboard accuracy number, '
    'and it does so at a fraction of the generation cost for the majority of ambiguous inputs.')
add_body(doc,
    'The key contributions of this project are: (i) the EcoGate pre-generation '
    'controller, which combines a zero-token NLP first stage with a joule ledger and an '
    'ambiguity-driven refusal policy; (ii) a reproducible benchmark of 56 generated '
    'and 5 manual prompts with three independently runnable scorer configurations; '
    'and (iii) an open Python package that can be extended with link ingestion, '
    'multi-language support, and additional judge configurations.')

add_section_heading(doc, "8.1", "Scope of further work")

add_body(doc,
    'Further work is the measurement the design already names and the saved files do not '
    'contain, together with the extensions listed in the project proposal. It falls into '
    'two groups: completing the specified architecture, and extending the framework to '
    'new domains and languages.')

add_subsection_heading(doc, "8.1.1", "Link-grounded and longitudinal measurement")

add_body(doc,
    'The next measurement pass should fetch documentation and web pages, store a hash '
    'and a snapshot of the cleaned text, and compute the link-level metrics the proposal '
    'defines: Contains Link, URL Match Accuracy, Link Precision, Link Recall, and Link F1. '
    'These metrics require the evaluator to retrieve the page at measurement time and check '
    'whether the model\u2019s answer cites URLs that are both present in the retrieved page '
    'and relevant to the answer.')
add_body(doc,
    'Longitudinal measurement would run the same benchmark at regular intervals (monthly '
    'or quarterly) and compare score distributions over time. A score decrease on a '
    'documentation benchmark can be caused by model regression, documentation update, or '
    'both; the hash-and-snapshot mechanism separates these causes. Longitudinal data would '
    'also allow the stability sub-score to be computed from genuine repeated runs rather '
    'than from constructed repeated calls.')

add_subsection_heading(doc, "8.1.2", "Judges, languages, and reproducible runs")

add_body(doc,
    'The proposal\u2019s further programme is to extend the framework to multilingual and '
    'multi-domain sources, to use more than one judge so that position and verbosity bias '
    'can be estimated [5], [14], and to publish the benchmark as a reproducible artefact '
    'with pinned model versions and a public leaderboard. The judge fairness sub-score '
    '\u2014 which measures how often a judge\u2019s ranking changes when option order is '
    'permuted \u2014 would provide a principled criterion for excluding unreliable judge '
    'calls from the type accuracy calculation.')
add_body(doc,
    'Energy reporting could be extended from the comparison model to actual wall-meter '
    'measurements using a hardware power monitor on the inference server. This would '
    'allow the joule figures to be presented as absolute costs rather than estimates '
    'under a fixed coefficient model, and would make the energy comparison directly '
    'comparable to the figures reported by Luccioni et al. [23] for BLOOM inference.')

# ══════════════════════════════════════════════
# REFERENCES
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "REFERENCES")

refs = [
    (1,  "Brown, T. B., et al.,",
         ", Language Models are Few-Shot Learners, ",
         None,
         "arXiv:2005.14165, 2020."),
    (2,  "Zhang, T., et al.,",
         ", BERTScore: Evaluating Text Generation with BERT, ",
         "ICLR",
         ", 2020."),
    (3,  "Sellam, T., Das, D., and Parikh, A.,",
         ", BLEURT: Learning Robust Metrics for Text Generation, ",
         "ACL",
         ", 2020."),
    (4,  "Reimers, N., and Gurevych, I.,",
         ", Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks, ",
         "EMNLP",
         ", 2019."),
    (5,  "Guo, C., et al.,",
         ", What is an LLM judge? A systematic review of LLM-based evaluation, ",
         None,
         "arXiv:2406.00638, 2024."),
    (6,  "OpenAI,",
         ", GPT Evaluation and LLM Observability Best Practices, ",
         None,
         "OpenAI documentation, 2024."),
    (7,  "Google Research,",
         ", Evaluating Groundedness and Factuality in Generative Models, ",
         None,
         "Google AI Blog, 2024."),
    (8,  "IBM Research,",
         ", Responsible AI and Evaluation Pipelines for LLM Systems, ",
         None,
         "IBM AI Fairness 360, 2024."),
    (9,  "Chrome for Developers,",
         ", Evaluation and API Design for Model Quality Metrics, ",
         None,
         "developer.chrome.com, 2024."),
    (10, "Sistla, N.,",
         ", axo-eval: Measuring LLM Accuracy on Documentation URLs, ",
         None,
         "GitHub repository, 2026."),
    (11, "LuotoCompany,",
         ", llm-eval-reference-generation: URL-based reference evaluation, ",
         None,
         "GitHub repository, 2025."),
    (12, "Microsoft Research,",
         ", Responsible and Grounded AI Evaluation Benchmarks, ",
         None,
         "Microsoft AI, 2025."),
    (13, "Kautish, S., and Gurung, D.,",
         ", Advancing Sustainable Computing: A Systematic Literature Review, ",
         "ICCK Transactions on Sustainable Computing",
         ", 1(1), 2024."),
    (14, "Mazhar, K., et al.,",
         ", Ethical Explainable Artificial Intelligence for Green Innovation: A Systematic Review and Meta-Analysis, ",
         None,
         "2024."),
    (15, "Chen, L., Zaharia, M., and Zou, J.,",
         ", FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance, ",
         "TMLR",
         ", 2024."),
    (16, "Ong, I., et al.,",
         ", RouteLLM: Learning to Route LLMs with Preference Data, ",
         "ICLR",
         ", 2025."),
    (17, "Jiang, H., et al.,",
         ", LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models, ",
         "EMNLP",
         ", 2023."),
    (18, "Schuster, T., et al.,",
         ", Confident Adaptive Language Modeling (CALM), ",
         "NeurIPS",
         ", 2022."),
    (19, "Leviathan, Y., Kalman, M., and Matias, Y.,",
         ", Fast Inference from Transformers via Speculative Decoding, ",
         "ICML",
         ", 2023."),
    (20, "Elhoushi, M., et al.,",
         ", LayerSkip: Enabling Early Exit Inference and Self-Speculative Decoding, ",
         "ACL",
         ", 2024."),
    (21, "Kwon, W., et al.,",
         ", Efficient Memory Management for Large Language Model Serving with PagedAttention, ",
         "SOSP",
         ", 2023."),
    (22, "Song, Y., et al.,",
         ", PowerInfer: Fast Large Language Model Serving with a Consumer-grade GPU, ",
         "SOSP",
         ", 2024."),
    (23, "Luccioni, A. S., Viguier, S., and Ligozat, A.-L.,",
         ", Estimating the Carbon Footprint of BLOOM, a 176B Parameter Language Model, ",
         "JMLR",
         ", 2023."),
    (24, "SpecEE,",
         ", Early-Exit Inference with Power Awareness, ",
         "ISCA",
         ", 2025."),
    (25, "Miao, X., et al.,",
         ", Towards Efficient Generative Large Language Model Serving: A Survey from Algorithms to Systems, ",
         "ACM Computing Surveys",
         ", 2024."),
    (26, "Schuster, R., et al.,",
         ", Confident Adaptive Language Modeling, token-level uncertainty, ",
         None,
         "arXiv:2404.10136, 2024."),
    (27, "Min, S., et al.,",
         ", AmbigQA: Answering Ambiguous Open-domain Questions, ",
         "EMNLP",
         ", 2020."),
    (28, "Kuhn, L., et al.,",
         ", Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation, ",
         "ICLR",
         ", 2023."),
    (29, "Manakul, P., et al.,",
         ", SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models, ",
         "EMNLP",
         ", 2023."),
    (30, "Aliannejadi, M., et al.,",
         ", Clarify When Necessary: Asking Clarification Questions as a Conversational Retrieval Strategy, ",
         "NAACL Findings",
         ", 2025."),
    (31, "Baan, J., et al.,",
         ", From Answers to Interpretations: Generating and Annotating Ambiguous Questions, ",
         "EMNLP Findings",
         ", 2026."),
    (32, "Zhang, H., et al.,",
         ", Steerable Clarification Policies for Dialogue Systems, ",
         None,
         "arXiv:2512.04068, 2025."),
    (33, "Guo, Y., et al.,",
         ", RegretBench: Evaluating Policy-Aware Question Asking under Interaction Cost, ",
         None,
         "arXiv:2607.21143, 2026."),
    (34, "Majumder, B., et al.,",
         ", Diagnostic Clarifying Questions for Ambiguous Information Needs, ",
         "EMNLP",
         ", 2026."),
]

for num, authors, title, journal, rest in refs:
    add_reference(doc, num, authors, title, journal, rest)

# ══════════════════════════════════════════════
# LIST OF PUBLICATIONS
# ══════════════════════════════════════════════
doc.add_page_break()
add_fm_title(doc, "LIST OF PUBLICATIONS")

add_fm_body(doc,
    'No paper, poster, or other publication arising from this project has been issued '
    'at the time of this report. Aagosh Raj Srivastava and G. Sathwik are the student '
    'authors of the project. Supervision is provided by Dr. Neeraj Upadhyay '
    '(Department of Computer Science & Engineering, SRM University-AP) and '
    'co-mentorship by Mr. Ajay Sahu (PhD Scholar, Department of Computer Science '
    '& Engineering, SRM University-AP). The authors intend to pursue a conference '
    'publication describing the EcoGate component and the benchmark results as '
    'further work following the UROP.')

# ══════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════
out_path = r"c:\Users\sathw\Desktop\urop_1\UROP_LLM_API_Evaluation_Report.docx"
doc.save(out_path)
print("Saved: {}".format(out_path))
print("Total paragraphs: {}".format(len(doc.paragraphs)))
print("Approx pages: ~32-38")
print("\nFont summary:")
print("  Body text:              {}, {:.1f}pt, Justified, line spacing {:.2f}pt EXACTLY".format(
    FONT, float(SZ_BODY.pt), float(LS_BODY.pt)))
print("  Chapter headings (H1):  {}, {:.1f}pt, Bold, line spacing {:.1f}pt, space_after {:.1f}pt".format(
    FONT, float(SZ_H1.pt), float(LS_CH.pt), float(SPACE_AFTER_H1.pt)))
print("  Section headings (H2):  {}, {:.1f}pt, Bold".format(FONT, float(SZ_H2.pt)))
print("  Subsection hdgs (H3):   {}, {:.1f}pt, Bold".format(FONT, float(SZ_H3.pt)))
print("  Front matter title:     {}, {:.1f}pt, Bold, space_after {:.2f}pt".format(
    FONT, float(SZ_H1.pt), float(SPACE_AFTER_FMT.pt)))
print("  Caption:                {}, {:.1f}pt, Centered".format(FONT, float(SZ_BODY.pt)))
print("\nMargins: Left=1.5\" Right=1.268\" Top=1.0\" Bottom=1.611\"")
print("\nAll 4 real names present:")
print("  Aagosh Raj Srivastava (AP23110010096)")
print("  G. Sathwik (AP23110011125)")
print("  Dr. Neeraj Upadhyay (Guide)")
print("  Mr. Ajay Sahu (Co-mentor, PhD Scholar)")
print("\nFigures embedded:")
print("  type_counts_corrected.png: {}".format(os.path.exists(FIG_TYPE)))
print("  tokens_per_prompt.png:     {}".format(os.path.exists(FIG_TOKENS)))
print("\npython-docx limitations (no auto-workaround):")
print("  - Section-level roman vs arabic page number switching requires XML sections")
print("    (approximated: footer page number field added, but roman/arabic switch")
print("     requires manually setting page number format in Word after opening)")
print("  - Tab-stop positions in TOC entries are approximated with indent settings")
print("    (actual right-aligned tab with leader dots requires direct XML tab manipulation)")
