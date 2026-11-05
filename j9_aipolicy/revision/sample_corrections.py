"""Corrections to the recorded page list of the one-page-per-type design, applied by the scripts that
build its sample, panels and convergence documents (seed_design.py, seed_convergence.py and, through
it, pair_structure_checks.py). The robustness design on the automatically discovered United States
pages (pages_audit.py, rebuild_panel_clean.py, convergence_ladder.py) keeps its own page rule.
EXCLUDE: institutions left out of the sample, with the reason. RETYPE: pages recorded as AI guidance
pages that are academic integrity pages ("AI" in their address or title stands for academic
integrity, or the page never carries AI text)."""
EXCLUDE = {
    "139658": "Emory University: the address recorded as its AI guidance page (ai.emory.edu) is the homepage of its "
              "Academic Innovation office, with no integrity text and no AI guidance in any capture (two 2024 captures "
              "carry a news item on AI tools in the workplace; none uses the strict AI vocabulary), and its curated "
              "integrity page was never archived, so no tracked policy page remains",
}
RETYPE = {
    ("9000002", "www_griffith_edu_au_academic_integrity_why_ai_matters"): "integrity",  # titled 'Why Academic Integrity matters'
    ("9000006", "www_queensu_ca_academicintegrity_ai_queens"): "integrity",             # 'AI @ Queen's | Academic Integrity'
    ("9000020", "www_studentsupport_manchester_ac_uk_study_support_academic_support_assessments_a"): "integrity",  # avoiding academic malpractice
}


def page_type(unitid, page_key, recorded):
    return RETYPE.get((str(unitid), page_key), recorded)
