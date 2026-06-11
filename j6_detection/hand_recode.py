"""
Interactive hand re-code of the 10 second-coder institutions (author's verification pass).

Walks the coder through the five dimensions for each institution in
data/policy_corpus_secondcoder_template.csv, one question at a time, and writes
data/policy_corpus_handcoder.csv (coder=author-hand). Progress is saved after every
institution, so the session can be stopped and resumed. The codes of record
(data/policy_corpus.csv) are only read AFTER all ten are coded, at which point the
script reveals per-dimension raw agreement, Cohen's kappa, and the governance-floor
classification under both sets of codes (the quantity the manuscript claims).

Blindness rule: do not open data/policy_corpus.csv or the manuscript's Robustness
section until this script prints the final comparison.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TEMPLATE = os.path.join(DATA, "policy_corpus_secondcoder_template.csv")
OUT = os.path.join(DATA, "policy_corpus_handcoder.csv")
RECORD = os.path.join(DATA, "policy_corpus.csv")

DIMS = ["detector_admissibility", "burden_of_proof", "appeal_pathway",
        "l2_protection", "decision_locus"]

QUESTIONS = [
    ("detector_admissibility",
     "Q1 检测器的输出能不能当作弊证据? (detector_admissibility)",
     [("prohibited",  "白纸黑字禁止: 'may not be used / may not be the basis'"),
      ("advisory",    "说它不可靠/劝阻使用, 但没有禁止: 'should refrain / not reliable proof'"),
      ("silent",      "根本没谈'当证据'这件事 (只提到检测工具存在也算 silent)"),
      ("admissible",  "批准或鼓励使用: 'approved for use / encouraged to explore'")]),
    ("burden_of_proof",
     "Q2 一旦被 flag, 谁必须证明什么? (burden_of_proof)",
     [("institution", "明文规定 flag 不能单独定案: 'not the sole/single basis', 需要旁证"),
      ("student",     "要学生自证清白 (例如交出草稿)"),
      ("unspecified", "没说 (默认值)")]),
    ("appeal_pathway",
     "Q3 有没有申诉渠道? (appeal_pathway)",
     [("formal",   "有名字的申诉/听证程序或机构 (Appeals, Hearing, Grievance...)"),
      ("informal", "提到可以复议/重新考虑, 但没有正式渠道"),
      ("none",     "完全没提 (默认值)")]),
    ("l2_protection",
     "Q4 有没有点名保护多语言/非母语写作者? (l2_protection)",
     [("explicit", "点名 multilingual/ELL/non-native/international, 或警告检测器误伤非母语写作"),
      ("none",     "没有 (泛泛的公平/偏见语言、没落到语言背景上, 也算 none)")]),
    ("decision_locus",
     "Q5 AI/检测器的规矩由谁来定? (decision_locus)",
     [("institutional", "全校统一、有约束力的规则"),
      ("delegated",     "交给任课老师/课程大纲自行决定"),
      ("silent",        "都没有 (注意: 中央办公室只'审理'案件不算 institutional)")]),
]


def floor(row):
    """Mirror of the paper's governance-floor logic."""
    if row["detector_admissibility"] == "prohibited":
        return "cleared (binding ban)"
    if row["l2_protection"] == "explicit":
        return "cleared (explicit L2 protection)"
    if row["burden_of_proof"] == "institution":
        return "cleared (corroboration required)"
    return "VACUUM"


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe == 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


def main():
    with open(TEMPLATE, encoding="utf-8") as f:
        schools = list(csv.DictReader(f))

    done = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            done = {r["institution"]: r for r in csv.DictReader(f)}

    todo = [s for s in schools if s["institution"] not in done]
    print(f"\n=== 人工重码: 已完成 {len(done)}/10, 还剩 {len(todo)} 所 ===")
    print("随时 Ctrl+C 退出, 进度已保存, 下次运行从断点继续。\n")

    for s in todo:
        idx = schools.index(s) + 1
        print("=" * 72)
        print(f"第 {idx}/10 所: {s['institution']} ({s['state']})")
        print(f"先去 data/SECONDCODER_packet.md 里 Cmd+F 搜: ## {idx}. {s['institution']}")
        print("读完它的政策文本后回到这里答题。")
        input("读好了按回车开始答题 > ")

        while True:
            answers = {}
            for dim, qtext, opts in QUESTIONS:
                print(f"\n{qtext}")
                for i, (val, hint) in enumerate(opts, 1):
                    print(f"  {i}. {val:<13} {hint}")
                while True:
                    raw = input(f"选 1-{len(opts)} > ").strip()
                    if raw.isdigit() and 1 <= int(raw) <= len(opts):
                        answers[dim] = opts[int(raw) - 1][0]
                        break
                    print("  请输入选项编号。")
            print(f"\n你的编码: {s['institution']}: " +
                  ", ".join(answers[d] for d in DIMS))
            ok = input("确认按 y, 重答按 r > ").strip().lower()
            if ok == "y":
                break

        row = {"institution": s["institution"], "state": s["state"], "url": s["url"],
               **answers, "coder": "author-hand"}
        write_header = not os.path.exists(OUT)
        with open(OUT, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                w.writeheader()
            w.writerow(row)
        done[s["institution"]] = row
        print(f"已保存 ({len(done)}/10)\n")

    # ---- reveal: only runs when all ten are coded ----
    print("=" * 72)
    print("全部 10 所完成, 现在揭盲, 与记录码 (policy_corpus.csv) 对比:\n")
    with open(RECORD, encoding="utf-8") as f:
        rec = {r["institution"]: r for r in csv.DictReader(f)}

    mismatches = []
    for dim in DIMS:
        a = [done[s["institution"]][dim] for s in schools]
        b = [rec[s["institution"]][dim] for s in schools]
        agree = sum(x == y for x, y in zip(a, b))
        k = kappa(a, b)
        ks = "n/a " if k != k else f"{k:.3f}"
        print(f"  {dim:<24} agreement {agree}/10   kappa {ks}")
        for s in schools:
            h, r = done[s["institution"]][dim], rec[s["institution"]][dim]
            if h != r:
                mismatches.append((s["institution"], dim, h, r))

    print("\n  每所学校的 floor 分类 (论文的主张是这一列两边一致):")
    flips = 0
    for s in schools:
        fh, fr = floor(done[s["institution"]]), floor(rec[s["institution"]])
        mark = "OK " if fh == fr else "FLIP"
        flips += fh != fr
        print(f"  {mark} {s['institution']:<36} 你: {fh:<34} 记录: {fr}")

    if mismatches:
        print("\n  逐格分歧 (拿原文来裁定谁对):")
        for inst, dim, h, r in mismatches:
            print(f"   - {inst} / {dim}: 你={h}  记录={r}")
    print(f"\n  结论: floor 翻转 {flips}/10。把这段输出发给 Claude, 由它更新手稿。")


if __name__ == "__main__":
    main()
