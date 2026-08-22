#!/usr/bin/env python3
"""Rebuild publication.html and data/cv_publication.txt from data/publication.csv.

Run from anywhere, e.g. from the repo root:

    python3 scripts/generate.py
"""

import csv
import os

from nltk.corpus import stopwords

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


english_stopwords = stopwords.words('english')
ind = "  "

# venues that are preprint servers rather than peer-reviewed proceedings
PREPRINT_VENUES = ['arXiv', 'Preprints.org', 'TechRxiv', 'MedRxiv', 'PDF', 'SSRN']


with open(os.path.join(DATA, "publication.csv"), "r", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    data = [row for row in reader]

def generate_html_one_publication(row):
    candidates = row["Title"].replace('-', ' ').replace('?', ' ').replace('!', ' ').replace(':', ' ').replace(',', ' ').replace('\'', ' ').split()
    i = 0
    identifier = candidates[i].strip().lower()
    while identifier in english_stopwords:
        i += 1
        identifier = candidates[i].strip().lower()
    identifier = row["Authors"].split(', ')[0].split()[-1].lower() + row["Year"] + identifier

    assert "Jen-tse Huang" in row["Authors"]
    if "Jen-tse Huang" in row["Equal"]:
        role = "co-first"
    elif row["Authors"].split(', ')[0] == "Jen-tse Huang":
        role = "first"
    elif row["Authors"].split(', ')[-1] == "Jen-tse Huang":
        role = "last"
    else:
        role = "other"
    if "Jen-tse Huang" in row["Corresponding"]:
        role += ",corresponding"

    heading = f'<span class="pub-title">{row["Title"]}</span>'
    if row["DOI"] != '':
        heading = f'<a href="{row["DOI"]}" id="{identifier}">{heading}</a>'

    authors = row["Authors"].replace("Jen-tse Huang", "<b>Jen-tse Huang</b>")
    if row["Equal"] != '':
        for i in row["Equal"].split(', '):
            authors = authors.replace(i, f'{i} <i class="fa-solid fa-star-of-life"></i>')
    if row["Corresponding"] != '':
        for i in row["Corresponding"].split(', '):
            authors = authors.replace(i, f'{i} <i class="fa-solid fa-envelope"></i>')

    addons = ''
    if row["Code"] != '':
        addons += f' <a href="{row["Code"]}">code</a> |'
    if row["Homepage"] != '':
        addons += f' <a href="{row["Homepage"]}">homepage</a> |'
    if row["Dataset"] != '':
        addons += f' <a href="{row["Dataset"]}">dataset</a> |'
    if row["Model"] != '':
        addons += f' <a href="{row["Model"]}">model</a> |'
    if row["Demo"] != '':
        addons += f' <a href="{row["Demo"]}">demo</a> |'
    if row["Poster"] != '':
        addons += f' <a href="{row["Poster"]}">poster</a> |'
    if row["Slides"] != '':
        addons += f' <a href="{row["Slides"]}">slides</a> |'
    if row["Video"] != '':
        addons += f' <a href="{row["Video"]}">video</a> |'

    remark = '' if row["Remark"] == '' else f'<b class="red">[{row["Remark"]}]</b> '

    abbr = 'Preprint' if row["Abbreviation"] in PREPRINT_VENUES else row["Abbreviation"]
    if 'arxiv' in row["Arxiv"]:
        paper_link = f' <a href="{row["Arxiv"]}">arXiv</a> |'
    elif row["Arxiv"] != '':
        paper_link = f' <a href="{row["Arxiv"]}">paper</a> |'
    else:
        paper_link = ''
    ret = f'''
<!-- {identifier} -->
<article class="pub" data-roles="{role}" data-topics="{row["Topics"]}">
{ind}<div class="pub-thumb">
{ind}{ind}<img src="images/publications/{identifier}.png" alt="">
{ind}</div>
{ind}<div class="pub-info">
{ind}{ind}<p>
{ind}{ind}{ind}{heading}<br>
{ind}{ind}{ind}{authors}<br>
{ind}{ind}{ind}{remark}{abbr}, {row["Year"]}<br>
{ind}{ind}{ind}|{paper_link}{addons}
{ind}{ind}</p>
{ind}</div>
</article>
'''
    return ret

year = data[-1]["Year"]
html_publication = f'''
<h2 class="section-title">{year}</h2>
'''
for i in range(len(data) - 1, -1, -1):
    if data[i]["Year"] != year:
        year = data[i]["Year"]
        html_publication += f'''
<h2 class="section-title">{year}</h2>
'''
    html_publication += generate_html_one_publication(data[i])

with open(os.path.join(DATA, "prefix.txt"), "r", encoding="utf-8") as f:
    prefix = f.read()
with open(os.path.join(DATA, "suffix.txt"), "r", encoding="utf-8") as f:
    suffix = f.read()

with open(os.path.join(ROOT, "publication.html"), "w", encoding="utf-8") as f:
    f.write(prefix)
    f.write(html_publication)
    f.write(suffix)

def generate_cv_one_publication(row):

    authors = row["Authors"].replace("Jen-tse Huang", "\\textbf{Jen-tse Huang}")
    if row["Equal"] != '':
        for i in row["Equal"].split(', '):
            authors = authors.replace(i, f'{i} *')
    if row["Corresponding"] != '':
        for i in row["Corresponding"].split(', '):
            authors = authors.replace(i, f'{i} \\faEnvelopeO')

    remark = '' if row["Remark"] == '' else '\\\\ {\\color{red} [' + row["Remark"] + ']}'

    if row["Abbreviation"] == "NeurIPS" or "Findings" in row["Abbreviation"]:
        proceedings = f'In {row["Publication"]}'
    elif row["Abbreviation"] == "ICLR":
        proceedings = f'In the {row["Publication"]}'
    elif row["Abbreviation"] == "ICML":
        proceedings = f'In Proceedings of the {row["Publication"]}'
        if row["Vol"] != '':
            proceedings += f', PMLR vol. {row["Vol"]}'
    elif row["Vol"] != '':
        proceedings = f'{row["Publication"]}, vol. {row["Vol"]}'
    elif row["Abbreviation"] in PREPRINT_VENUES:
        arxiv_no = row["Arxiv"].rstrip("/").split("/")[-1]
        if "=" in arxiv_no:  # query-style ids, e.g. SSRN's ?abstract_id=NNNN
            arxiv_no = arxiv_no.split("=")[-1]
        proceedings = f'{row["Abbreviation"]} Preprint: {arxiv_no}'
    else:
        proceedings = f'In Proceedings of the {row["Publication"]}'
    proceedings = '\\textit{' + proceedings + '}'
    if row["No"] != '':
        proceedings += f', issue. {row["No"]}'
    if row["Page"] != '':
        if '-' in row["Page"]:
            proceedings += f', pp. {row["Page"]}'
        else:
            proceedings += f', no. {row["Page"]}'
    if row["Abbreviation"] not in PREPRINT_VENUES:
        proceedings += f'. ({row["Abbreviation"]}\'{row["Year"][-2:]})'
    else:
        proceedings = '\\href{' + row["Arxiv"] + '}{' + proceedings + '}'

    title = row["Title"] + "." if row["Title"][-1].isalnum() else row["Title"]
    ret = f'''
    \\item {authors}, {row["Year"]}. {title} {proceedings}{remark}
'''
    return ret

cv_publication = '''
\\begin{rSection}{Conference Papers}
* equal contribution \\quad \\faEnvelopeO \\ corresponding author
\\begin{etaremune}
'''
for i in range(len(data) - 1, -1, -1):
    if data[i]["Type"] == 'Conference' and data[i]["Abbreviation"] not in PREPRINT_VENUES:
        cv_publication += generate_cv_one_publication(data[i])
cv_publication += '''
\\end{etaremune}
\\end{rSection}

\\begin{rSection}{Journal Papers}
\\begin{etaremune}
'''
for i in range(len(data) - 1, -1, -1):
    if data[i]["Type"] == 'Journal' and data[i]["Abbreviation"] not in PREPRINT_VENUES:
        cv_publication += generate_cv_one_publication(data[i])
cv_publication += '''
\\end{etaremune}
\\end{rSection}

\\begin{rSection}{Preprint Papers}
\\begin{etaremune}
'''
for i in range(len(data) - 1, -1, -1):
    if data[i]["Abbreviation"] in PREPRINT_VENUES:
        cv_publication += generate_cv_one_publication(data[i])
cv_publication += '''
\\end{etaremune}
\\end{rSection}
'''

with open(os.path.join(DATA, "cv_publication.txt"), "w", encoding="utf-8") as f:
    f.write(cv_publication.replace('%', '\\%'))

