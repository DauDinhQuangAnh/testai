"""Doc results/phase1_results.jsonl va tu dong ghi de bang ket qua trong HANDOFF.md
(giua 2 marker PHASE1_RESULTS_START/END) - day la co che duy nhat de cap nhat file
dong bo chung, KHONG sua tay bang ket qua trong HANDOFF.md.

Chay: python phase1_feasibility/summarize_results.py
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RESULTS_FILE = BASE / "phase1_feasibility" / "results" / "phase1_results.jsonl"
HANDOFF_FILE = BASE / "HANDOFF.md"
START_MARK = "<!-- PHASE1_RESULTS_START -->"
END_MARK = "<!-- PHASE1_RESULTS_END -->"


def build_table() -> str:
    if not RESULTS_FILE.exists():
        return ("(chua co ket qua nao, chay `phase1_feasibility/run_all.py` "
                "truoc roi chay lai script nay)")

    rows = ["| Step | Status | Time (s) | VRAM peak (MB) | Notes |", "|---|---|---|---|---|"]
    with open(RESULTS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            status = "FAILED" if record["error"] else "OK"
            vram = record["vram_peak_mb"] if record["vram_peak_mb"] is not None else "-"
            note = record["error"] or json.dumps(record["extra"], ensure_ascii=False)
            rows.append(
                f"| {record['step']} | {status} | {record['elapsed_sec']} | {vram} | {note} |"
            )
    return "\n".join(rows)


def update_handoff():
    content = HANDOFF_FILE.read_text(encoding="utf-8")
    if START_MARK not in content or END_MARK not in content:
        raise SystemExit("Khong tim thay marker PHASE1_RESULTS trong HANDOFF.md")

    before, rest = content.split(START_MARK, 1)
    _, after = rest.split(END_MARK, 1)
    table = build_table()
    new_content = f"{before}{START_MARK}\n{table}\n{END_MARK}{after}"
    HANDOFF_FILE.write_text(new_content, encoding="utf-8")
    print("HANDOFF.md updated with latest Phase 1 results.")


if __name__ == "__main__":
    update_handoff()
