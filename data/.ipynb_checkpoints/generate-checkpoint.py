import csv
from nltk.corpus import stopwords


english_stopwords = stopwords.words('english')
ind = "  "


with open("publication.csv", "r") as csvfile:
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

    heading = f'<heading>{row["Title"]}</heading>'
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

    remark = '' if row["Remark"] == '' else f'<font color="red"><b>[{row["Remark"]}]</b></font> '

    ret = f'''
<!-- {identifier} -->
<table class="pub-table" width="100%" align="center" border="0" cellspacing="0" cellpadding="15" data-roles="{role}" data-topics="{row["Topics"]}">
{ind}<tbody>
{ind}{ind}<tr>
{ind}{ind}{ind}<td width="33%" valign="center" align="center">
{ind}{ind}{ind}{ind}<div class="hidden" style="display: inline;">
{ind}{ind}{ind}{ind}{ind}<img src="images/publications/{identifier}.png" width="100%">
{ind}{ind}{ind}{ind}</div>
{ind}{ind}{ind}</td>
{ind}{ind}{ind}<td width="67%" valign="center">
{ind}{ind}{ind}{ind}<p>
{ind}{ind}{ind}{ind}{ind}{heading}<br>
{ind}{ind}{ind}{ind}{ind}{authors}<br>
{ind}{ind}{ind}{ind}{ind}{remark}{row["Abbreviation"]}, {row["Year"]}<br>
{ind}{ind}{ind}{ind}{ind}| <a href="{row["Arxiv"]}">arXiv</a> |{addons}
{ind}{ind}{ind}{ind}</p>
{ind}{ind}{ind}</td>
{ind}{ind}</tr>
{ind}</tbody>
</table>
'''
    return ret

year = data[-1]["Year"]
html_publication = f'''
<table width="100%" align="center" border="0" cellspacing="0" cellpadding="10">
{ind}<tbody>
{ind}{ind}<tr>
{ind}{ind}{ind}<td>
{ind}{ind}{ind}{ind}<sectionheading>&nbsp;&nbsp;{year}</sectionheading>
{ind}{ind}{ind}</td>
{ind}{ind}</tr>
{ind}</tbody>
</table>
'''
for i in range(len(data) - 1, -1, -1):
    if data[i]["Year"] != year:
        year = data[i]["Year"]
        html_publication += f'''
<table width="100%" align="center" border="0" cellspacing="0" cellpadding="10">
{ind}<tbody>
{ind}{ind}<tr>
{ind}{ind}{ind}<td>
{ind}{ind}{ind}{ind}<sectionheading>&nbsp;&nbsp;{year}</sectionheading>
{ind}{ind}{ind}</td>
{ind}{ind}</tr>
{ind}</tbody>
</table>
'''
    html_publication += generate_html_one_publication(data[i])
with open("html_publication.txt", "w") as f:
    f.write(html_publication)
