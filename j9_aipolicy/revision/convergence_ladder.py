"""Convergence analysis with a normalization ladder (reviewer points 1 and 2).

Rungs (cumulative):
  L0  replicate the submitted analysis exactly (raw extractor, AI windows of +-300 chars)
  L1  boilerplate-stripped text (extract_clean.extract_text_clean)
  L2  + British-to-American spelling normalization
  L3  + removal of role nouns, governance bodies, regulators, regulatory instruments
  L4  + removal of institution / place / country names, LMS names, domain tokens,
       national administrative vocabulary, and digits
At every rung: the quarterly within/cross/all series (n_inst), the endpoint permutation test,
the 4x4 system-pair matrix, the pre-shock vs endpoint gap with an institution-cluster bootstrap
on their difference, the within and cross rises, and the terms that most separate systems.
Placebo texts at L1 and L4: non-AI page text and pre-shock page text of the same institutions.
"""
from pathlib import Path as _P
REV = _P(__file__).resolve().parent            # j9_aipolicy/revision
PIPE = REV.parent                               # j9_aipolicy
XN = PIPE / "crossnational"
AN = REV / "output"; AN.mkdir(exist_ok=True)    # all outputs of the revision analyses
WS = REV; RP = AN; OUT = AN
import csv, re, sys, time
from collections import Counter
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, str(REV))
import extract_clean as E
B = E.B
AIWIN = 300
SHOCK = pd.Timestamp("2022-11-30")
KS = list(range(-7, 14))
QEND = {k: (pd.Period("2022Q4", freq="Q") + k).to_timestamp(how="end").normalize() for k in KS}
RUNGS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"]
# L8 = strict text (as L7) with US pages restricted to policy-like URLs (no catalog/program/honors/news pages), any count;
# L9 = L8 with one integrity + one AI page per US institution (curated seed if tracked, else shortest policy-like URL)
# L5 = L4 text, junk and inert pages dropped; L6 = L5 on the matched page design (US 1 integrity + 1 AI page);
# L7 = L6 with strict AI terms (no bare "AI"), windows recomputed on the normalized text

# ----------------------------------------------------------------------------- spelling
_ISE_EXCEPT = set("""advertise advise apprise arise chastise comprise compromise concise demise despise
devise disguise enterprise excise exercise expertise franchise improvise incise merchandise otherwise
likewise clockwise anticlockwise counterclockwise wise paradise poise noise praise raise precise premise
promise reprise revise supervise surmise surprise televise treatise turquoise anise cruise bruise guise
rise sunrise moonrise appraise mortise valise""".split())
_OUR_STEMS = ["behavi", "col", "fav", "flav", "hon", "hum", "lab", "neighb", "od", "rig", "rum", "sav",
              "splend", "val", "vap", "vig", "cand", "harb", "arm", "clam", "demean", "endeav", "ferv",
              "succ", "tum", "parl", "ard", "disc"]  # discolour
_RE_WORDS = {"centre": "center", "centres": "centers", "centred": "centered", "centring": "centering",
             "metre": "meter", "metres": "meters", "litre": "liter", "litres": "liters",
             "theatre": "theater", "theatres": "theaters", "fibre": "fiber", "fibres": "fibers",
             "calibre": "caliber", "sombre": "somber", "spectre": "specter", "lustre": "luster",
             "manoeuvre": "maneuver", "manoeuvres": "maneuvers"}
_OGUE = {"catalogue": "catalog", "catalogues": "catalogs", "catalogued": "cataloged",
         "cataloguing": "cataloging", "dialogue": "dialog", "dialogues": "dialogs",
         "analogue": "analog", "analogues": "analogs", "monologue": "monolog", "epilogue": "epilog",
         "prologue": "prolog"}
_ENCE = {"defence": "defense", "defences": "defenses", "offence": "offense", "offences": "offenses",
         "licence": "license", "licences": "licenses", "pretence": "pretense"}
_LL = {"modelling": "modeling", "modelled": "modeled", "labelling": "labeling", "labelled": "labeled",
       "cancelling": "canceling", "cancelled": "canceled", "counselling": "counseling",
       "counselled": "counseled", "counsellor": "counselor", "counsellors": "counselors",
       "travelling": "traveling", "travelled": "traveled", "traveller": "traveler",
       "travellers": "travelers", "fuelled": "fueled", "fuelling": "fueling", "levelled": "leveled",
       "levelling": "leveling", "signalling": "signaling", "signalled": "signaled",
       "totalling": "totaling", "totalled": "totaled", "enrol": "enroll", "enrols": "enrolls",
       "enrolment": "enrollment", "enrolments": "enrollments", "fulfil": "fulfill",
       "fulfils": "fulfills", "fulfilment": "fulfillment", "skilful": "skillful",
       "wilful": "willful", "wilfully": "willfully", "instalment": "installment",
       "instalments": "installments", "instal": "install", "distil": "distill", "enthral": "enthrall",
       "appal": "appall", "jewellery": "jewelry", "marvellous": "marvelous", "dialling": "dialing",
       "dialled": "dialed", "equalled": "equaled", "equalling": "equaling", "quarrelling": "quarreling",
       "tunnelling": "tunneling", "channelled": "channeled", "channelling": "channeling",
       "pencilled": "penciled", "initialled": "initialed", "spiralling": "spiraling",
       "panelled": "paneled", "panelling": "paneling", "towelling": "toweling",
       "remodelling": "remodeling", "remodelled": "remodeled", "unlabelled": "unlabeled",
       "unparalleled": "unparalleled"}
_MISC = {"programme": "program", "programmes": "programs", "programmed": "programmed",
         "judgement": "judgment", "judgements": "judgments", "acknowledgement": "acknowledgment",
         "acknowledgements": "acknowledgments", "ageing": "aging", "artefact": "artifact",
         "artefacts": "artifacts", "cheque": "check", "cheques": "checks", "grey": "gray",
         "tyre": "tire", "tyres": "tires", "kerb": "curb", "mould": "mold", "moulded": "molded",
         "plough": "plow", "sceptical": "skeptical", "sceptic": "skeptic", "scepticism": "skepticism",
         "storey": "story", "storeys": "stories", "pyjamas": "pajamas", "aluminium": "aluminum",
         "draught": "draft", "whilst": "while", "amongst": "among", "learnt": "learned",
         "spelt": "spelled", "dreamt": "dreamed", "burnt": "burned", "leapt": "leaped",
         "towards": "toward", "afterwards": "afterward", "forwards": "forward",
         "backwards": "backward", "maths": "math", "practise": "practice", "practised": "practiced",
         "practising": "practicing", "practises": "practices", "paediatric": "pediatric",
         "encyclopaedia": "encyclopedia", "anaemia": "anemia", "anaesthesia": "anesthesia",
         "foetus": "fetus", "oestrogen": "estrogen", "orthopaedic": "orthopedic",
         "mediaeval": "medieval", "aeroplane": "airplane", "cosy": "cozy", "doughnut": "donut",
         "speciality": "specialty", "specialities": "specialties", "enquiry": "inquiry",
         "enquiries": "inquiries", "enquire": "inquire", "enquired": "inquired",
         "enquiring": "inquiring", "favourite": "favorite", "favourites": "favorites",
         "favouritism": "favoritism", "honours": "honors", "honour": "honor", "honoured": "honored",
         "honourable": "honorable", "honorary": "honorary", "behaviours": "behaviors",
         "behaviour": "behavior", "behavioural": "behavioral", "colour": "color",
         "colours": "colors", "coloured": "colored", "labour": "labor", "neighbour": "neighbor",
         "neighbours": "neighbors", "neighbourhood": "neighborhood", "endeavour": "endeavor",
         "endeavours": "endeavors", "humour": "humor", "rumour": "rumor", "rumours": "rumors",
         "savour": "savor", "valour": "valor", "vigour": "vigor", "rigour": "rigor",
         "rigorous": "rigorous", "odour": "odor", "flavour": "flavor", "harbour": "harbor",
         "armour": "armor", "candour": "candor", "demeanour": "demeanor", "fervour": "fervor",
         "parlour": "parlor", "splendour": "splendor", "tumour": "tumor", "vapour": "vapor",
         "clamour": "clamor", "disc": "disc", "defence": "defense", "offence": "offense",
         "licence": "license", "analyse": "analyze", "analysed": "analyzed", "analysing": "analyzing",
         "analyses": "analyses", "paralyse": "paralyze", "catalyse": "catalyze", "organise": "organize",
         "organised": "organized", "organising": "organizing", "organisation": "organization",
         "organisations": "organizations", "organisational": "organizational",
         "organiser": "organizer", "organisers": "organizers", "aeon": "eon", "gaol": "jail",
         "gaoled": "jailed", "plagiarise": "plagiarize", "plagiarised": "plagiarized",
         "plagiarising": "plagiarizing", "recognise": "recognize", "recognised": "recognized",
         "recognising": "recognizing", "authorise": "authorize", "authorised": "authorized",
         "authorising": "authorizing", "authorisation": "authorization",
         "unauthorised": "unauthorized", "penalise": "penalize", "penalised": "penalized",
         "penalising": "penalizing", "minimise": "minimize", "minimised": "minimized",
         "maximise": "maximize", "emphasise": "emphasize", "emphasised": "emphasized",
         "summarise": "summarize", "summarised": "summarized", "summarising": "summarizing",
         "criticise": "criticize", "criticised": "criticized", "prioritise": "prioritize",
         "utilise": "utilize", "utilised": "utilized", "utilising": "utilizing",
         "apologise": "apologize", "realise": "realize", "realised": "realized",
         "specialise": "specialize", "specialised": "specialized", "standardise": "standardize",
         "standardised": "standardized", "categorise": "categorize", "categorised": "categorized",
         "finalise": "finalize", "finalised": "finalized", "formalise": "formalize",
         "formalised": "formalized", "legitimise": "legitimize", "memorise": "memorize",
         "mobilise": "mobilize", "characterise": "characterize", "characterised": "characterized",
         "familiarise": "familiarize", "familiarised": "familiarized", "familiarising": "familiarizing",
         "scrutinise": "scrutinize", "scrutinised": "scrutinized", "capitalise": "capitalize",
         "customise": "customize", "customised": "customized", "personalise": "personalize",
         "personalised": "personalized", "optimise": "optimize", "optimised": "optimized",
         "synthesise": "synthesize", "synthesised": "synthesized", "hypothesise": "hypothesize",
         "paraphrase": "paraphrase", "supervise": "supervise", "supervised": "supervised",
         "advise": "advise", "advised": "advised", "revise": "revise", "revised": "revised",
         "exercise": "exercise", "exercises": "exercises", "comprise": "comprise", "promise": "promise",
         "surprise": "surprise", "devise": "devise", "compromise": "compromise",
         "compromised": "compromised", "advertise": "advertise", "merchandise": "merchandise",
         "franchise": "franchise", "improvise": "improvise", "televise": "televise",
         "enterprise": "enterprise", "expertise": "expertise", "premise": "premise",
         "disguise": "disguise", "otherwise": "otherwise", "likewise": "likewise", "precise": "precise",
         "concise": "concise", "demise": "demise", "despise": "despise", "excise": "excise",
         "incise": "incise", "chastise": "chastise", "apprise": "apprise", "reprise": "reprise",
         "treatise": "treatise", "paradise": "paradise", "noise": "noise", "poise": "poise",
         "praise": "praise", "raise": "raise", "rise": "rise", "arise": "arise", "wise": "wise",
         "cruise": "cruise", "bruise": "bruise", "guise": "guise"}
_SPELL = {}
_SPELL.update(_RE_WORDS); _SPELL.update(_OGUE); _SPELL.update(_ENCE); _SPELL.update(_LL); _SPELL.update(_MISC)
_WORD_RE = re.compile(r"[A-Za-z]+")


def norm_word(w):
    lw = w.lower()
    if lw in _SPELL:
        return _SPELL[lw]
    if len(lw) < 5:
        return lw
    for suf, rep in (("isations", "izations"), ("isation", "ization"), ("ising", "izing"),
                     ("ised", "ized"), ("isers", "izers"), ("iser", "izer"), ("ises", "izes"),
                     ("ise", "ize")):
        if lw.endswith(suf):
            stem = lw[: -len(suf)]
            if stem + "ise" in _ISE_EXCEPT or any(stem.endswith(x[:-3]) for x in _ISE_EXCEPT) or stem in ("", "o", "a", "prem", "exerc", "superv",
                                                        "adv", "rev", "dev", "compr", "prom", "surpr",
                                                        "ar", "ra", "pra", "r", "w", "cru", "bru", "gu",
                                                        "no", "po", "prec", "conc", "dem", "desp",
                                                        "exc", "inc", "chast", "appr", "repr", "treat",
                                                        "parad", "advert", "merchand", "franch",
                                                        "improv", "telev", "enterpr", "expert",
                                                        "disgu", "otherw", "likew", "anticlockw",
                                                        "clockw", "counterclockw", "sunr", "moonr",
                                                        "appra", "mort", "val", "an", "turquo"):
                return lw
            if len(stem) < 3:
                return lw
            return stem + rep
    for suf, rep in (("ysing", "yzing"), ("ysed", "yzed"), ("yses", "yzes"), ("yse", "yze")):
        if lw.endswith(suf) and lw not in ("analyses",):
            stem = lw[: -len(suf)]
            if stem.endswith(("anal", "paral", "catal", "dial", "electrol", "hydrol", "psychoanal")):
                return stem + rep
    for stem in _OUR_STEMS:
        for suf, rep in (("ours", "ors"), ("oured", "ored"), ("ouring", "oring"), ("ourable", "orable"),
                         ("ourful", "orful"), ("ourite", "orite"), ("ourism", "orism"), ("our", "or")):
            if lw == stem + suf:
                return stem + rep
    return lw


def normalize_spelling(text, counter=None):
    def repl(m):
        w = m.group(0)
        n = norm_word(w)
        if counter is not None and n != w.lower():
            counter[(w.lower(), n)] += 1
        return n
    return _WORD_RE.sub(repl, text)

# ----------------------------------------------------------------------------- term lists
ROLE_TERMS = """personal tutor|academic tutor|tutor|unit coordinator|unit co-ordinator|unit convenor|unit convener|unit chair|
subject coordinator|subject co-ordinator|course coordinator|course co-ordinator|course convenor|course convener|course leader|
course director|course instructor|course owner|module leader|module convenor|module convener|module coordinator|module tutor|
programme leader|programme director|program director|program coordinator|academic advisor|academic adviser|advisor|adviser|
instructor|lecturer|professor|faculty member|faculty|teaching assistant|teaching staff|academic staff|staff member|staff|
dean of students|associate dean|deputy dean|dean|head of school|head of department|department head|department chair|
chairperson|chair|vice provost|vice-provost|provost|vice president|vice-president|president|deputy vice-chancellor|
deputy vice chancellor|pro vice-chancellor|pro-vice-chancellor|pro vice chancellor|vice-chancellor|vice chancellor|chancellor|
principal|rector|academic registrar|registrar|registry|proctor|invigilator|ombudsman|ombudsperson|ombuds|
academic integrity officer|academic integrity advisor|academic integrity adviser|integrity officer|academic misconduct officer|
student conduct officer|conduct officer|hearing officer|case manager|investigating officer|investigation officer|secretary|
honor council|honour council|honor committee|honour committee|honor board|honour board|judicial board|judicial committee|
judicial affairs|student conduct board|conduct board|academic integrity board|academic integrity committee|
academic integrity panel|misconduct panel|misconduct committee|disciplinary committee|disciplinary panel|disciplinary board|
academic board|academic senate|faculty senate|university senate|senate|board of regents|regents|board of trustees|trustees|
board of governors|governors|governing board|academic council|university council|faculty council|college council|council|
exam board|examination board|board of examiners|examiners|examiner|progression board|appeals committee|appeals board|
appeal panel|appeals panel|review board|review committee|review panel|committee|panel|
office of student conduct|office of academic integrity|office of the dean|office of the provost|office of the registrar|
student affairs|student services|academic affairs|academic services|centre for teaching|center for teaching|
teaching and learning centre|teaching and learning center|
qaa|quality assurance agency|teqsa|tertiary education quality and standards agency|ofs|office for students|ofqual|hesa|hefce|
ukri|universities uk|uuk|universities australia|universities canada|universities scotland|russell group|group of eight|go8|
u15|atn|australian technology network|iru|innovative research universities|esos act|esos|
higher education standards framework|hesf|threshold standards|teqsa act|higher education support act|education act|
data protection act|gdpr|equality act|human rights act|title ix|ferpa|americans with disabilities act|clery act|
student handbook|academic regulations|general regulations|statute|ordinance|by-law|bylaw|academic calendar|
code of practice|quality code""".replace("\n", "").split("|")

US_STATES = ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida",
             "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
             "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire",
             "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
             "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington",
             "west virginia", "wisconsin", "wyoming"]
PLACE_TERMS = """united states|usa|u.s.|america|american|americans|canada|canadian|canadians|australia|australian|
australians|united kingdom|uk|britain|british|england|scotland|scottish|wales|welsh|ireland|irish|northern ireland|
new zealand|nz|queensland|victoria|victorian|new south wales|nsw|tasmania|tasmanian|south australia|western australia|
australian capital territory|canberra|sydney|melbourne|brisbane|perth|adelaide|hobart|darwin|wollongong|newcastle|
geelong|gold coast|townsville|cairns|toowoomba|bendigo|ballarat|launceston|ontario|quebec|québec|british columbia|
alberta|manitoba|saskatchewan|nova scotia|new brunswick|newfoundland|labrador|toronto|montreal|montréal|vancouver|
ottawa|calgary|edmonton|winnipeg|halifax|kingston|hamilton|waterloo|guelph|london|manchester|birmingham|leeds|sheffield|
bristol|liverpool|nottingham|southampton|glasgow|edinburgh|cardiff|belfast|oxford|cambridge|exeter|durham|york|
warwick|bath|lancaster|leicester|surrey|sussex|kent|essex|loughborough|aberdeen|dundee|st andrews|strathclyde|
swansea|coventry|brighton|norwich|plymouth|hull|bradford|salford|stirling|boston|chicago|los angeles|san francisco|
san diego|seattle|atlanta|philadelphia|pittsburgh|houston|dallas|austin|denver|phoenix|miami|detroit|minneapolis|
st louis|baltimore|cleveland|cincinnati|columbus|nashville|new orleans|portland|salt lake city|las vegas|honolulu|
berkeley|irvine|davis|santa barbara|santa cruz|riverside|san luis obispo|ann arbor|madison|urbana|champaign|
evanston|ithaca|princeton|providence|new haven|chapel hill|charlottesville|college park|college station|
tempe|tucson|boulder|eugene|corvallis|pullman|lincoln|lawrence|norman|stillwater|fayetteville|baton rouge|gainesville|
tallahassee|athens|knoxville|lexington|louisville|bloomington|lafayette|east lansing|iowa city|ames|columbia|
storrs|amherst|burlington|hanover|syracuse|buffalo|stony brook|binghamton|albany|rochester|newark|piscataway|
state college|university park|morgantown|blacksburg|raleigh|clemson|auburn|tuscaloosa|starkville|fort collins|
moscow|laramie|reno|albuquerque|las cruces|el paso|lubbock|akron|dayton|toledo|north america|europe|european|
asia|asian|africa|african"""
PLACE_TERMS = [t.strip() for t in PLACE_TERMS.replace("\n", "").split("|") if t.strip()] + US_STATES

GENERIC_NAME_TOKENS = set("""university of the and at college institute technology state polytechnic a&m campus
school center centre new north south east west central main city system sciences science technological research
university's national case western reserve community reading eastern northern southern tech agricultural mechanical
medical health arts metropolitan international american british royal memorial trinity general public saint st
mount mary union united states""".split())
ADMIN_TERMS = """module|modules|unit of study|unit|units|course|courses|coursework|programme|programmes|program|programs|
degree|degrees|semester|semesters|trimester|trimesters|marks|marking|grading|undergraduate|undergraduates|postgraduate|
postgraduates|graduate|graduates|phd|doctoral|hdr|higher degree by research|dissertation|dissertations|thesis|theses|
tutorial|tutorials|seminar|seminars|lecture|lectures|viva|invigilated|invigilation|proctored|proctoring|honor code|
honour code|campus|campuses|school|schools|college|colleges|department|departments|canvas|blackboard|moodle|
brightspace|d2l|myuni|blackboard learn|learning management system|lms""".replace("\n", "").split("|")
# kept out on purpose (policy content): grade, graded, credit, term, terms, subject, turnitin, paper
DOMAIN_TOKENS = "http https www ac uk edu au ca com org net gov html htm php aspx asp pdf mailto co nz".split()
ICON_TOKENS = ["external link", "opens in a new window", "opens in new window", "opens in a new tab", "opens new window",
               "skip to main content", "skip to content", "back to top", "print this page", "share this page",
               "last updated", "page last modified", "last modified", "arrow_drop_down", "arrow_forward", "arrow_right",
               "chevron_right", "chevron_down", "expand_more", "expand_less", "open_in_new", "location_on", "smartphone",
               "keyboard_arrow_down", "keyboard_arrow_right", "add_circle", "remove_circle", "toggle navigation",
               "toggle menu", "main navigation", "all rights reserved"]


def institution_name_tokens():
    names = []
    for f in (PIPE / "data" / "sample_frame.csv", XN / "data" / "sample_frame.csv"):
        d = pd.read_csv(f, dtype=str)
        names += list(d["institution"].dropna().unique())
        if "domain" in d.columns:
            names += [x.split(".")[0] for x in d["domain"].dropna().unique()
                      if x.split(".")[0] not in GENERIC_NAME_TOKENS and x.split(".")[0] not in ("case", "reading", "bath", "hull", "kent", "union", "mount", "trinity")]
    toks = set()
    phrases = set()
    for n in names:
        n2 = re.sub(r"[^A-Za-z0-9' ]+", " ", n.lower())
        phrases.add(" ".join(n2.split()))
        for t in n2.split():
            if len(t) >= 3 and t not in GENERIC_NAME_TOKENS:
                toks.add(t)
    return sorted(phrases, key=len, reverse=True) + sorted(toks, key=len, reverse=True)


def build_remover(terms):
    terms = sorted({t.strip().lower() for t in terms if t.strip()}, key=len, reverse=True)
    long_t = [t for t in terms if len(t) >= 4]; short_t = [t for t in terms if len(t) < 4]
    alt_long = "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in long_t)
    alt_short = "|".join(re.escape(t) for t in short_t)
    pat = r"(?<![a-z0-9'])(?:(?:" + alt_long + r")(?:'s|es|s)?"
    if alt_short:
        pat += r"|(?:" + alt_short + r")"
    pat += r")(?![a-z0-9])"
    return re.compile(pat, re.I)


REMOVE_L3 = build_remover(ROLE_TERMS)
REMOVE_L4 = build_remover(PLACE_TERMS + ADMIN_TERMS + DOMAIN_TOKENS + ICON_TOKENS + institution_name_tokens())
STRICT_AI = re.compile(r"artificial intelligence|generative a\.?i\.?|gen(?:erative)?\s?ai|chat\s?gpt|"
                       r"large language model|\bllms?\b|\bgpt\b", re.I)
DIGITS = re.compile(r"\d+")


def remove_terms(text, pat, counter=None):
    def repl(m):
        if counter is not None:
            counter[m.group(0).lower()] += 1
        return " "
    return pat.sub(repl, text)

# ----------------------------------------------------------------------------- text per rung
_cache = {}
spell_counter = {"US": Counter(), "UK": Counter(), "AU": Counter(), "CA": Counter()}
l3_counter = {"US": Counter(), "UK": Counter(), "AU": Counter(), "CA": Counter()}
l4_counter = {"US": Counter(), "UK": Counter(), "AU": Counter(), "CA": Counter()}


def windows(t, pat=None):
    pat = pat or B.AI_TERMS
    sp = [(m.start(), m.end()) for m in pat.finditer(t)]
    return " ".join(t[max(0, s - AIWIN):e + AIWIN] for s, e in sp).lower()


def complement(t, maxwords=3000):
    """Page text with the AI windows cut out (the non-AI placebo text)."""
    sp = [(max(0, m.start() - AIWIN), m.end() + AIWIN) for m in B.AI_TERMS.finditer(t)]
    out, pos = [], 0
    for s, e in sp:
        if s > pos:
            out.append(t[pos:s])
        pos = max(pos, e)
    out.append(t[pos:])
    return " ".join(" ".join(out).lower().split()[:maxwords])


def texts_of(path, system):
    """Return dict rung -> AI-window text, plus full clean normalized text for placebos."""
    if path in _cache:
        return _cache[path]
    raw = B.extract_text(path)
    clean = E.extract_text_clean(path)
    norm = normalize_spelling(clean, spell_counter[system])
    out = {"L0": windows(raw), "L1": windows(clean), "L2": windows(norm)}
    out["L3"] = remove_terms(out["L2"], REMOVE_L3, l3_counter[system])
    out["L4"] = DIGITS.sub(" ", remove_terms(out["L3"], REMOVE_L4, l4_counter[system]))
    out["L4"] = " ".join(out["L4"].split())
    out["L3"] = " ".join(out["L3"].split())
    out["L5"] = out["L4"]; out["L6"] = out["L4"]  # same text; the page SET changes (see build_docs)
    strict = windows(norm, STRICT_AI)
    out["L7"] = " ".join(DIGITS.sub(" ", remove_terms(remove_terms(strict, REMOVE_L3), REMOVE_L4)).split())
    out["L8"] = out["L7"]; out["L9"] = out["L7"]
    # placebo materials
    out["full_L1"] = " ".join(clean.lower().split()[:3000])
    out["nonai_L1"] = complement(clean)
    out["full_L4"] = " ".join(DIGITS.sub(" ", remove_terms(remove_terms(norm.lower(), REMOVE_L3), REMOVE_L4)).split()[:3000])
    out["nonai_L4"] = " ".join(DIGITS.sub(" ", remove_terms(remove_terms(complement(norm), REMOVE_L3), REMOVE_L4)).split())
    _cache[path] = out
    return out

# ----------------------------------------------------------------------------- corpus
def load(index_csv, base, system_of):
    rows = [r for r in csv.DictReader(open(index_csv)) if r.get("bytes") not in ("", "0", None)]
    out = []
    for r in rows:
        p = base / r["local_path"]
        if p.exists():
            out.append({"uid": str(r["unitid"]), "inst": r["institution"], "sys": system_of(r),
                        "url": r["original_url"], "ts": pd.to_datetime(r["timestamp"], format="%Y%m%d%H%M%S"),
                        "path": p})
    return out


PAGESETS = {}


def load_pagesets():
    pages = pd.read_csv(AN / "pages_per_institution.csv", dtype={"unitid": str})
    PAGESETS["dropped"] = set(zip(pages[(pages.junk == 1) | (pages.inert == 1)].unitid, pages[(pages.junk == 1) | (pages.inert == 1)].page_key))
    m = pd.read_csv(AN / "matched_pages_us.csv", dtype={"unitid": str})
    PAGESETS["matched_us"] = set(zip(m.unitid, m.page_key))
    pp = pd.read_csv(AN / "policy_pages.csv", dtype={"unitid": str})
    PAGESETS["policy"] = set(zip(pp.unitid, pp.page_key))
    mp = pd.read_csv(AN / "matched_policy_pages_us.csv", dtype={"unitid": str})
    PAGESETS["matched_policy_us"] = set(zip(mp.unitid, mp.page_key))


def page_allowed(uid, path, rung):
    if rung in ("L0", "L1", "L2", "L3", "L4"):
        return True
    key = (uid, Path(path).stem.rsplit("__", 1)[0])
    if key in PAGESETS["dropped"]:
        return False
    if rung in ("L6", "L7") and int(uid) < 9000000 and key not in PAGESETS["matched_us"]:
        return False
    if rung in ("L8", "L9") and int(uid) < 9000000 and key not in PAGESETS["policy"]:
        return False
    if rung == "L9" and int(uid) < 9000000 and key not in PAGESETS["matched_policy_us"]:
        return False
    return True


def build_docs(snaps, rung):
    docs = []
    snaps = snaps[[page_allowed(u, p, rung) for u, p in zip(snaps["uid"], snaps["path"])]]
    for uid, g in snaps.groupby("uid"):
        sysname = g["sys"].iloc[0]
        for k, qe in QEND.items():
            parts = []
            for url, gp in g.groupby("url"):
                sub = gp[gp["ts"] <= qe]
                if len(sub):
                    parts.append(texts_of(sub.sort_values("ts").iloc[-1]["path"], sysname)[rung])
            doc = " ".join(p for p in parts if p).strip()
            if doc:
                docs.append({"uid": uid, "sys": sysname, "event_q": k, "doc": doc})
    return pd.DataFrame(docs).reset_index(drop=True)


def pair_means(S, sysv, uidv=None, weights=None):
    n = len(sysv)
    iu = np.triu_indices(n, 1)
    same = (sysv[:, None] == sysv[None, :])[iu]
    ok = np.ones(len(iu[0]), bool)
    if uidv is not None:
        ok = (uidv[:, None] != uidv[None, :])[iu]
    w = np.ones(len(iu[0])) if weights is None else weights[iu]
    s = S[iu]
    def wmean(mask):
        m = mask & ok & (w > 0)
        return float(np.sum(s[m] * w[m]) / np.sum(w[m])) if np.any(m) else np.nan
    return wmean(same), wmean(~same), wmean(np.ones_like(same, bool))


def quarterly_series(X, docs):
    rows, mats = [], {}
    for k in KS:
        sub = docs[docs["event_q"] == k]
        if sub["uid"].nunique() < 4:
            continue
        idx = sub.index.to_numpy()
        S = cosine_similarity(X[idx])
        sysv = sub["sys"].to_numpy()
        w, c, a = pair_means(S, sysv)
        rows.append({"event_q": k, "n_inst": sub["uid"].nunique(), "within_cos": round(w, 4),
                     "cross_cos": round(c, 4), "all_cos": round(a, 4)})
        mats[k] = (S, sysv, sub["uid"].to_numpy())
    return pd.DataFrame(rows), mats


def permutation_gap(Se, sysv, nperm=2000, seed=3):
    rng = np.random.default_rng(seed)
    w0, c0, _ = pair_means(Se, sysv)
    obs = w0 - c0
    perm = np.empty(nperm)
    for i in range(nperm):
        lab = rng.permutation(sysv)
        w, c, _ = pair_means(Se, lab)
        perm[i] = w - c
    p = float((np.sum(np.abs(perm) >= abs(obs)) + 1) / (nperm + 1))
    return {"within": w0, "cross": c0, "gap": obs, "null_lo": float(np.percentile(perm, 2.5)),
            "null_hi": float(np.percentile(perm, 97.5)), "p": p}


def us_vs_rest(Se, sysv, nperm=2000, seed=5):
    """Mean US-US cosine minus mean US-other cosine, label-shuffle null."""
    rng = np.random.default_rng(seed)
    n = len(sysv); iu = np.triu_indices(n, 1)
    def stat(lab):
        us = (lab == "US")
        both = (us[:, None] & us[None, :])[iu]; mixed = (us[:, None] ^ us[None, :])[iu]
        return float(Se[iu][both].mean() - Se[iu][mixed].mean()) if both.any() and mixed.any() else np.nan
    obs = stat(np.asarray(sysv)); perm = np.array([stat(rng.permutation(sysv)) for _ in range(nperm)])
    return {"usrest_gap": obs, "usrest_p": float((np.sum(np.abs(perm) >= abs(obs)) + 1) / (nperm + 1))}


def endpoint_variants(ep, nwords=(300, 600)):
    """Endpoint permutation with every document cut to its first n words; and on the three
    Commonwealth systems only (UK/AU/CA); and the US-vs-rest contrast."""
    out = {}
    sysv = ep["sys"].to_numpy()
    for n in nwords:
        docs = ep["doc"].apply(lambda t: " ".join(t.split()[:n]))
        pm = endpoint_perm(docs, sysv)
        out[f"gap_t{n}"] = pm["gap"]; out[f"p_t{n}"] = pm["p"]; out[f"within_t{n}"] = pm["within"]; out[f"cross_t{n}"] = pm["cross"]
        non = ep[ep["sys"] != "US"]
        if non["sys"].nunique() >= 2 and len(non) >= 8:
            pm2 = endpoint_perm(non["doc"].apply(lambda t: " ".join(t.split()[:n])), non["sys"].to_numpy())
            out[f"nonus_gap_t{n}"] = pm2["gap"]; out[f"nonus_p_t{n}"] = pm2["p"]
    non = ep[ep["sys"] != "US"]
    if non["sys"].nunique() >= 2 and len(non) >= 8:
        pm2 = endpoint_perm(non["doc"], non["sys"].to_numpy()); out["nonus_gap"] = pm2["gap"]; out["nonus_p"] = pm2["p"]; out["nonus_n"] = len(non)
    Xe = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", max_features=4000).fit_transform(ep["doc"])
    out.update(us_vs_rest(cosine_similarity(Xe), sysv))
    out["words_median_US"] = float(np.median([len(t.split()) for t, sy in zip(ep["doc"], sysv) if sy == "US"])) if (sysv == "US").any() else np.nan
    out["words_median_nonUS"] = float(np.median([len(t.split()) for t, sy in zip(ep["doc"], sysv) if sy != "US"])) if (sysv != "US").any() else np.nan
    return out


def endpoint_docs(docs):
    return docs.sort_values("event_q").groupby("uid").tail(1).reset_index(drop=True)


def endpoint_perm(text_series, sysv):
    Xe = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english",
                         max_features=4000).fit_transform(text_series)
    return permutation_gap(cosine_similarity(Xe), np.asarray(sysv))


def bootstrap_gap_diff(mats, nboot=400, seed=7):
    """Institution-cluster bootstrap of (endpoint gap - pre-shock gap) on the quarterly series."""
    rng = np.random.default_rng(seed)
    uids = sorted({u for k in mats for u in mats[k][2]})
    pre_ks = [k for k in mats if k <= -1]
    end_k = max(mats)
    diffs, pres, ends = [], [], []
    for _ in range(nboot):
        samp = rng.choice(uids, len(uids), replace=True)
        mult = Counter(samp)
        def gap_at(k):
            S, sysv, uidv = mats[k]
            m = np.array([mult.get(u, 0) for u in uidv], float)
            if (m > 0).sum() < 4:
                return np.nan
            W = np.outer(m, m)
            w, c, _ = pair_means(S, sysv, uidv, W)
            return w - c
        pre = np.nanmean([gap_at(k) for k in pre_ks]) if pre_ks else np.nan
        end = gap_at(end_k)
        pres.append(pre); ends.append(end); diffs.append(end - pre)
    diffs = np.array(diffs)
    return float(np.nanpercentile(diffs, 2.5)), float(np.nanpercentile(diffs, 97.5)), float(np.nanmean(diffs))


def system_matrix(S, sysv):
    out = []
    systems = ["US", "UK", "AU", "CA"]
    n = len(sysv)
    for a in systems:
        for b in systems:
            vals = []
            for i in range(n):
                for j in range(i + 1, n):
                    if {sysv[i], sysv[j]} == {a, b} and (a != b or sysv[i] == sysv[j] == a):
                        vals.append(S[i, j])
            if a == b:
                vals = [S[i, j] for i in range(n) for j in range(i + 1, n) if sysv[i] == a and sysv[j] == a]
            out.append({"sys_a": a, "sys_b": b, "mean_cos": round(float(np.mean(vals)), 4) if vals else np.nan,
                        "n_pairs": len(vals)})
    return pd.DataFrame(out).drop_duplicates(subset=["mean_cos", "n_pairs", "sys_a", "sys_b"])


def top_terms(vec, X, docs, k_end, rung, ntop=30):
    sub = docs[docs["event_q"] == k_end]
    Xs = X[sub.index.to_numpy()]
    names = np.array(vec.get_feature_names_out())
    sysv = sub["sys"].to_numpy()
    rows = []
    for s in ["US", "UK", "AU", "CA"]:
        m_in = np.asarray(Xs[sysv == s].mean(axis=0)).ravel()
        m_out = np.asarray(Xs[sysv != s].mean(axis=0)).ravel()
        score = m_in - m_out
        for r, i in enumerate(np.argsort(-score)[:ntop], 1):
            rows.append({"rung": rung, "system": s, "rank": r, "term": names[i], "score": round(float(score[i]), 5),
                         "mean_in": round(float(m_in[i]), 5), "mean_out": round(float(m_out[i]), 5)})
    return pd.DataFrame(rows)


def paired_excess(ai_docs, non_docs, sysv, nperm=2000, seed=11):
    """Within-minus-cross gap of (AI-text cosine minus non-AI-text cosine) for the same institution
    pairs, with a country-label permutation: does the AI text carry MORE national clustering than
    the surrounding page text of the same institutions?"""
    Xa = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", max_features=4000).fit_transform(ai_docs)
    Xn = TfidfVectorizer(ngram_range=(1, 2), min_df=2, stop_words="english", max_features=4000).fit_transform(non_docs)
    D = cosine_similarity(Xa) - cosine_similarity(Xn)
    return permutation_gap(D, np.asarray(sysv), nperm=nperm, seed=seed)


def main():
    t0 = time.time()
    import warnings
    warnings.filterwarnings("ignore")
    load_pagesets()
    snaps = load(PIPE / "data" / "snapshot_index.csv", PIPE, lambda r: "US")
    snaps += load(XN / "data" / "snapshot_index.csv", XN, lambda r: r["state"])
    snaps = pd.DataFrame(snaps)
    print("institutions:", snaps["uid"].nunique(), "snapshots:", len(snaps), flush=True)
    # warm the cache once (all rungs computed per file)
    for i, (p, s) in enumerate(zip(snaps["path"], snaps["sys"]), 1):
        texts_of(p, s)
        if i % 400 == 0:
            print(f"  text {i}/{len(snaps)} {time.time()-t0:.0f}s", flush=True)
    series_rows, end_rows, mat_rows, term_rows, comp_rows = [], [], [], [], []
    endpoint_sets = {}
    for rung in RUNGS:
        docs = build_docs(snaps, rung)
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english", max_features=5000)
        X = vec.fit_transform(docs["doc"])
        ser, mats = quarterly_series(X, docs)
        ser.insert(0, "rung", rung)
        series_rows.append(ser)
        k_end = int(ser["event_q"].max())
        pre = ser[ser["event_q"] <= -1]
        pre_w, pre_c = pre["within_cos"].mean(), pre["cross_cos"].mean()
        end = ser[ser["event_q"] == k_end].iloc[0]
        lo, hi, mean_diff = bootstrap_gap_diff(mats)
        ep = endpoint_docs(docs)
        endpoint_sets[rung] = ep
        pm = endpoint_perm(ep["doc"], ep["sys"])
        ev = endpoint_variants(ep)
        end_rows.append({"rung": rung, "n_endpoint_inst": len(ep), **{k: round(v, 4) for k, v in pm.items()},
                         **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in ev.items()},
                         "pre_within": round(pre_w, 4), "pre_cross": round(pre_c, 4),
                         "pre_gap": round(pre_w - pre_c, 4), "end_within": end["within_cos"],
                         "end_cross": end["cross_cos"], "end_gap": round(end["within_cos"] - end["cross_cos"], 4),
                         "gap_diff": round(end["within_cos"] - end["cross_cos"] - (pre_w - pre_c), 4),
                         "gap_diff_boot_mean": round(mean_diff, 4), "gap_diff_ci_lo": round(lo, 4),
                         "gap_diff_ci_hi": round(hi, 4), "within_rise": round(end["within_cos"] - pre_w, 4),
                         "cross_rise": round(end["cross_cos"] - pre_c, 4), "end_quarter": k_end,
                         "n_features": X.shape[1]})
        S, sysv, _ = mats[k_end]
        m = system_matrix(S, sysv); m.insert(0, "rung", rung); mat_rows.append(m)
        term_rows.append(top_terms(vec, X, docs, k_end, rung))
        print(f"[{rung}] trunc300 gap {ev.get('gap_t300', float('nan')):+.4f} p={ev.get('p_t300', float('nan')):.3f} | trunc600 gap {ev.get('gap_t600', float('nan')):+.4f} p={ev.get('p_t600', float('nan')):.3f} | "
              f"non-US gap {ev.get('nonus_gap', float('nan')):+.4f} p={ev.get('nonus_p', float('nan')):.3f} | US-vs-rest {ev['usrest_gap']:+.4f} p={ev['usrest_p']:.3f} | words median US {ev['words_median_US']:.0f} non-US {ev['words_median_nonUS']:.0f}", flush=True)
        print(f"[{rung}] q{k_end}: within {end['within_cos']:.4f} cross {end['cross_cos']:.4f} | "
              f"endpoint-perm within {pm['within']:.3f} cross {pm['cross']:.3f} gap {pm['gap']:+.4f} p={pm['p']:.3f} | "
              f"pre gap {pre_w-pre_c:+.4f} end gap {end['within_cos']-end['cross_cos']:+.4f} diff CI [{lo:+.4f},{hi:+.4f}] "
              f"({time.time()-t0:.0f}s)", flush=True)
        comp = ep.groupby("sys").size().reindex(["US", "UK", "AU", "CA"]).fillna(0).astype(int)
        q13 = docs[docs["event_q"] == k_end].groupby("sys")["uid"].nunique().reindex(["US", "UK", "AU", "CA"]).fillna(0).astype(int)
        for sname in ["US", "UK", "AU", "CA"]:
            comp_rows.append({"rung": rung, "system": sname, "n_inst_q13": int(q13[sname]), "n_inst_endpoint_perm": int(comp[sname])})
    pd.DataFrame(comp_rows).to_csv(AN / "endpoint_composition.csv", index=False)
    pd.concat(series_rows).to_csv(AN / "convergence_ladder_series.csv", index=False)
    pd.DataFrame(end_rows).to_csv(AN / "convergence_ladder_endpoint.csv", index=False)
    pd.concat(mat_rows).to_csv(AN / "system_pair_matrix.csv", index=False)
    pd.concat(term_rows).to_csv(AN / "top_terms.csv", index=False)

    # ---- placebo texts: non-AI page text and pre-shock page text, at L1 and L4 settings
    plac = []
    for rung in ("L1", "L4"):
        for kind in ("nonai", "full_pre"):
            rows = []
            for uid, g in snaps.groupby("uid"):
                sysname = g["sys"].iloc[0]
                parts = []
                for url, gp in g.groupby("url"):
                    if kind == "nonai":
                        sub = gp
                    else:
                        sub = gp[gp["ts"] < SHOCK]
                    if len(sub):
                        t = texts_of(sub.sort_values("ts").iloc[-1]["path"], sysname)
                        parts.append(t["nonai_" + rung] if kind == "nonai" else t["full_" + rung])
                doc = " ".join(p for p in parts if p).strip()
                if doc:
                    rows.append({"uid": uid, "sys": sysname, "doc": " ".join(doc.split()[:3000])})
            d = pd.DataFrame(rows)
            pm = endpoint_perm(d["doc"], d["sys"])
            plac.append({"rung": rung, "text": kind, "n_inst": len(d), **{k: round(v, 4) for k, v in pm.items()}})
            print(f"[placebo {rung} {kind}] n={len(d)} within {pm['within']:.3f} cross {pm['cross']:.3f} gap {pm['gap']:+.4f} p={pm['p']:.3f}", flush=True)
        # the AI text itself under the same endpoint settings is already in convergence_ladder_endpoint.csv
    # paired excess: same institutions, AI text vs non-AI text
    for rung in ("L1", "L4"):
        ai_rows, non_rows, sysv = [], [], []
        for uid, g in snaps.groupby("uid"):
            sysname = g["sys"].iloc[0]
            if rung == "L4":
                g = g[[page_allowed(u, p, "L5") for u, p in zip(g["uid"], g["path"])]]
                if len(g) == 0:
                    continue
            a_parts, n_parts = [], []
            for url, gp in g.groupby("url"):
                t = texts_of(gp.sort_values("ts").iloc[-1]["path"], sysname)
                a_parts.append(t[rung]); n_parts.append(t["nonai_" + rung])
            a = " ".join(x for x in a_parts if x).strip(); n = " ".join(x for x in n_parts if x).strip()
            if a and n:
                ai_rows.append(" ".join(a.split()[:600])); non_rows.append(" ".join(n.split()[:600])); sysv.append(sysname)
        pm = paired_excess(ai_rows, non_rows, sysv)
        plac.append({"rung": rung, "text": "paired_excess_ai_minus_nonai_cap600" + ("_junkdropped" if rung == "L4" else ""), "n_inst": len(sysv), **{k: round(v, 4) for k, v in pm.items()}})
        print(f"[paired excess {rung}] n={len(sysv)} gap of (ai - nonai) within-minus-cross {pm['gap']:+.4f} null [{pm['null_lo']:+.4f},{pm['null_hi']:+.4f}] p={pm['p']:.3f}", flush=True)
    pd.DataFrame(plac).to_csv(AN / "placebo_text.csv", index=False)

    # ---- pre-shock pool: who had AI text before the shock and what it is
    pre_rows = []
    for uid, g in snaps.groupby("uid"):
        sysname = g["sys"].iloc[0]
        for url, gp in g.groupby("url"):
            sub = gp[gp["ts"] < SHOCK].sort_values("ts")
            for r in sub.itertuples(index=False):
                t = texts_of(r.path, sysname)
                if t["L0"]:
                    pre_rows.append({"uid": uid, "sys": sysname, "institution": r.inst, "url": url,
                                     "timestamp": r.ts.strftime("%Y-%m-%d"), "n_ai_terms_raw": len(B.AI_TERMS.findall(B.extract_text(r.path))),
                                     "n_ai_terms_clean": len(B.AI_TERMS.findall(E.extract_text_clean(r.path))),
                                     "ai_text_raw_200": t["L0"][:200], "ai_text_clean_200": t["L1"][:200]})
                    break
    pd.DataFrame(pre_rows).to_csv(AN / "preshock_pool.csv", index=False)

    # ---- audit tables for the normalization
    sp = []
    for s, c in spell_counter.items():
        for (a, b), n in c.most_common(60):
            sp.append({"system": s, "from": a, "to": b, "n": n})
    pd.DataFrame(sp).to_csv(AN / "spelling_changes.csv", index=False)
    tr = []
    for lab, cnt in (("L3", l3_counter), ("L4", l4_counter)):
        for s, c in cnt.items():
            for term, n in c.most_common(80):
                tr.append({"rung": lab, "system": s, "term": term, "n": n})
    pd.DataFrame(tr).to_csv(AN / "term_removal_counts.csv", index=False)
    print("done", f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
