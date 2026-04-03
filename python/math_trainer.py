#!/usr/bin/env python3
import json
import os
import random
import statistics
import sys
import termios
import time
import tty
from datetime import datetime, date

# ─── Config ───────────────────────────────────────────────────────────────────

WIDTH       = 72
DATA_FILE   = os.path.expanduser("~/.math_trainer.json")
TIMED_SECS  = 60

DIFFICULTY = {
    "1": ("Easy",   1),
    "2": ("Medium", 2),
    "3": ("Hard",   3),
    "4": ("Expert", 4),
}

OP_NAMES = {
    1: "ADDITION",
    2: "SUBTRACTION",
    3: "MULTIPLICATION",
    4: "DIVISION",
    5: "MIXED",
}

# ─── Box-drawing helpers ───────────────────────────────────────────────────────

def _ln(style="thin"):
    return ("─" if style == "thin" else "═") * WIDTH

def box_top():    return "╔" + "═" * (WIDTH - 2) + "╗"
def box_bot():    return "╚" + "═" * (WIDTH - 2) + "╝"
def box_mid():    return "╠" + "═" * (WIDTH - 2) + "╣"
def box_sep():    return "║" + "─" * (WIDTH - 2) + "║"

def cx(text, w=None):
    w = w or (WIDTH - 2)
    return text.center(w)

def row(label, value, lw=24):
    content = f"  {label:<{lw}}{value}"
    return "║" + content.ljust(WIDTH - 2) + "║"

def bare(text):
    return "║" + ("  " + text).ljust(WIDTH - 2) + "║"

def print_header(title, subtitle=None):
    print(box_top())
    print("║" + cx(title) + "║")
    if subtitle:
        print("║" + cx(subtitle) + "║")
    print(box_mid())

# ─── Terminal key input ────────────────────────────────────────────────────────

def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return key

def wait_for_key(valid_keys):
    while True:
        k = get_key().lower()
        if k in valid_keys:
            return k

def clear():
    os.system("clear")

# ─── JSON data store ───────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"sessions": [], "personal_bests": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"\n  Warning: could not save data — {e}")

def append_session(session_record):
    data = load_data()
    data["sessions"].append(session_record)
    # update personal bests
    op_key = str(session_record["operation"])
    pb = data.setdefault("personal_bests", {})
    entry = pb.setdefault(op_key, {
        "best_accuracy": 0,
        "best_avg_time": None,
        "best_streak": 0,
        "most_correct": 0,
    })
    acc = session_record["accuracy"]
    avg = session_record["avg_time"]
    streak = session_record["best_streak"]
    correct = session_record["correct"]

    if acc > entry["best_accuracy"]:
        entry["best_accuracy"] = acc
    if entry["best_avg_time"] is None or avg < entry["best_avg_time"]:
        entry["best_avg_time"] = avg
    if streak > entry["best_streak"]:
        entry["best_streak"] = streak
    if correct > entry["most_correct"]:
        entry["most_correct"] = correct

    save_data(data)

# ─── Stats helpers ─────────────────────────────────────────────────────────────

def speed_label(avg):
    if avg < 1.5:  return "⚡ Lightning"
    if avg < 3.0:  return "▲ Fast"
    if avg < 5.0:  return "● Steady"
    return "▼ Slow"

def trend_insight(first_avg, last_avg):
    if last_avg > first_avg + 0.5:  return "You slowed down toward the end."
    if first_avg > last_avg + 0.5:  return "You warmed up — got faster over time!"
    return "Consistent pace throughout."

def sessions_today(data):
    today = date.today().isoformat()
    return [s for s in data["sessions"] if s["date"] == today]

def sessions_on(data, d):
    return [s for s in data["sessions"] if s["date"] == d]

def last_session(data):
    if data["sessions"]:
        return data["sessions"][-1]
    return None

# ─── Since-last-session splash ────────────────────────────────────────────────

def show_since_last(data):
    sessions = data["sessions"]
    if not sessions:
        return  # first ever run, skip

    last = sessions[-1]
    last_date = last["date"]
    today = date.today().isoformat()

    clear()
    print_header("WELCOME BACK, AZEEM", f"Last session: {last_date}")

    # --- Last session recap ---
    print(bare(f"Operation   : {OP_NAMES.get(last['operation'], '?')}"))
    print(bare(f"Questions   : {last['total']}  ·  Correct: {last['correct']}  ·  Accuracy: {last['accuracy']:.1f}%"))
    print(bare(f"Avg time    : {last['avg_time']:.2f}s  ·  Best streak: {last['best_streak']}"))
    print(box_sep())

    # --- Compare with session before that (if exists) ---
    if len(sessions) >= 2:
        prev = sessions[-2]
        acc_delta  = last["accuracy"]  - prev["accuracy"]
        time_delta = last["avg_time"]  - prev["avg_time"]
        acc_arrow  = "▲" if acc_delta  >= 0 else "▼"
        time_arrow = "▲" if time_delta >= 0 else "▼"  # higher time is worse
        time_arrow = "▼" if time_delta >= 0 else "▲"

        print(bare("  vs. session before:"))
        print(bare(f"  Accuracy  {acc_arrow}  {acc_delta:+.1f}%   |   Avg time {time_arrow}  {time_delta:+.2f}s"))
        print(box_sep())

    # --- Today's total so far ---
    today_sessions = sessions_today(data)
    if today_sessions and last_date == today:
        total_q   = sum(s["total"]   for s in today_sessions)
        total_cor = sum(s["correct"] for s in today_sessions)
        avg_acc   = total_cor / total_q * 100 if total_q else 0
        print(bare(f"Today so far: {len(today_sessions)} session(s)  ·  {total_q} questions  ·  {avg_acc:.1f}% accuracy"))
        print(box_sep())

    # --- Personal bests reminder ---
    pb = data.get("personal_bests", {})
    op_key = str(last["operation"])
    if op_key in pb:
        b = pb[op_key]
        print(bare(f"Your PB ({OP_NAMES.get(last['operation'], '?')}):  {b['best_accuracy']:.1f}% accuracy  ·  {b['best_avg_time']:.2f}s avg  ·  {b['best_streak']} streak"))
        print(box_sep())

    print(bare("Press any key to continue…"))
    print(box_bot())
    get_key()

# ─── Question builder ──────────────────────────────────────────────────────────

def num_range(digits):
    low  = 1 if digits == 1 else 10 ** (digits - 1)
    high = 10 ** digits - 1
    return low, high

def build_question(operation, digits):
    low, high = num_range(digits)
    op = operation
    if op == 5:
        op = random.randint(1, 4)

    if op == 1:
        a, b = random.randint(low, high), random.randint(low, high)
        return f"{a} + {b}", a + b, op
    elif op == 2:
        a, b = random.randint(low, high), random.randint(low, high)
        if b > a: a, b = b, a
        return f"{a} − {b}", a - b, op
    elif op == 3:
        a, b = random.randint(low, high), random.randint(low, high)
        return f"{a} × {b}", a * b, op
    elif op == 4:
        d = random.randint(low, high)
        q = random.randint(low, high)
        return f"{d * q} ÷ {d}", q, op

# ─── Main menu ─────────────────────────────────────────────────────────────────

def ask_main_menu():
    while True:
        clear()
        print(box_top())
        print("║" + cx("AZEEM'S MATH TRAINER") + "║")
        print(box_mid())
        print(bare("  PRACTICE MODE"))
        print(bare("  1 ·  Addition"))
        print(bare("  2 ·  Subtraction"))
        print(bare("  3 ·  Multiplication"))
        print(bare("  4 ·  Division"))
        print(bare("  5 ·  Mixed  (random op each question)"))
        print(box_sep())
        print(bare("  TIMED BLITZ  (60 seconds)"))
        print(bare("  6 ·  Addition blitz"))
        print(bare("  7 ·  Subtraction blitz"))
        print(bare("  8 ·  Multiplication blitz"))
        print(bare("  9 ·  Division blitz"))
        print(bare("  0 ·  Mixed blitz"))
        print(box_sep())
        print(bare("  H ·  History & personal bests"))
        print(bare("  Q ·  Quit"))
        print(box_bot())
        ch = input("\n  › ").strip().lower()
        if ch in {"1","2","3","4","5","6","7","8","9","0","h","q"}:
            return ch
        print("\n  Invalid. Try again.")
        time.sleep(0.8)

def ask_difficulty():
    clear()
    print_header("SELECT DIFFICULTY")
    print(bare("  1 ·  Easy    (1 digit   →  1–9)"))
    print(bare("  2 ·  Medium  (2 digits  →  10–99)"))
    print(bare("  3 ·  Hard    (3 digits  →  100–999)"))
    print(bare("  4 ·  Expert  (4 digits  →  1000–9999)"))
    print(box_bot())
    while True:
        ch = input("\n  › ").strip()
        if ch in DIFFICULTY:
            label, digits = DIFFICULTY[ch]
            return label, digits
        print("  Pick 1–4.")

# ─── Session report ────────────────────────────────────────────────────────────

def show_session_report(records, operation, difficulty_label, timed=False):
    clear()
    total   = len(records)
    if total == 0:
        print_header("SESSION REPORT")
        print(bare("No questions answered."))
        print(box_bot())
        print("\n  Press any key…")
        get_key()
        return None

    correct = sum(1 for r in records if r["result"] == "correct")
    wrong   = total - correct
    times   = [r["time"] for r in records]
    total_t = sum(times)
    avg_t   = total_t / total
    med_t   = statistics.median(times)
    fast_t  = min(times)
    slow_t  = max(times)
    std_t   = statistics.pstdev(times) if len(times) > 1 else 0
    acc     = correct / total * 100

    # streak calc
    best_streak = cur_streak = 0
    for r in records:
        if r["result"] == "correct":
            cur_streak += 1
            best_streak = max(best_streak, cur_streak)
        else:
            cur_streak = 0

    mode_tag = "TIMED BLITZ" if timed else "PRACTICE"
    print_header("SESSION REPORT", f"{OP_NAMES[operation]}  ·  {difficulty_label}  ·  {mode_tag}")

    print(row("Questions", str(total)))
    print(row("Correct", f"{correct}  ({acc:.1f}%)"))
    print(row("Wrong", str(wrong)))
    print(row("Best streak", f"{best_streak} in a row"))
    print(box_sep())
    print(row("Total time", f"{total_t:.2f} sec"))
    print(row("Average time", f"{avg_t:.2f} sec"))
    print(row("Median time", f"{med_t:.2f} sec"))
    print(row("Fastest", f"{fast_t:.2f} sec"))
    print(row("Slowest", f"{slow_t:.2f} sec"))
    print(row("Spread (σ)", f"{std_t:.2f} sec"))
    print(row("Speed", speed_label(avg_t)))

    if total >= 6:
        fa = statistics.mean(times[:3])
        la = statistics.mean(times[-3:])
        print(box_sep())
        print(row("First 3 avg", f"{fa:.2f} sec"))
        print(row("Last 3 avg", f"{la:.2f} sec"))
        print(row("Trend", trend_insight(fa, la)))

    ct = [r["time"] for r in records if r["result"] == "correct"]
    wt = [r["time"] for r in records if r["result"] == "wrong"]
    if ct or wt:
        print(box_sep())
        if ct: print(row("Avg correct time", f"{statistics.mean(ct):.2f} sec"))
        if wt: print(row("Avg wrong time",   f"{statistics.mean(wt):.2f} sec"))

    fastest_r = min(records, key=lambda x: x["time"])
    slowest_r = max(records, key=lambda x: x["time"])
    print(box_sep())
    print(row("Fastest Q", f"{fastest_r['question']} = {fastest_r['answer']}  ({fastest_r['time']:.2f}s)"))
    print(row("Slowest Q", f"{slowest_r['question']} = {slowest_r['answer']}  ({slowest_r['time']:.2f}s)"))

    print(box_bot())
    print("\n  Press any key to return to menu…")
    get_key()

    return {
        "date":        date.today().isoformat(),
        "timestamp":   datetime.now().isoformat(),
        "operation":   operation,
        "difficulty":  difficulty_label,
        "timed":       timed,
        "total":       total,
        "correct":     correct,
        "wrong":       wrong,
        "accuracy":    round(acc, 2),
        "avg_time":    round(avg_t, 3),
        "best_streak": best_streak,
        "total_time":  round(total_t, 2),
    }

# ─── Practice session ──────────────────────────────────────────────────────────

def run_practice(operation, difficulty_label, digits):
    records = []
    q_num   = 1
    streak  = 0

    while True:
        clear()
        streak_tag = f"  🔥 {streak}" if streak >= 3 else ""
        print(box_top())
        print("║" + cx(f"{OP_NAMES[operation]}  ·  {difficulty_label}  ·  Q{q_num}{streak_tag}") + "║")
        print(box_bot())

        question, answer, actual_op = build_question(operation, digits)
        print(f"\n  {question} = ?\n")
        print("  [SPACE] reveal    [Q] quit")

        t0  = time.perf_counter()
        key = wait_for_key({" ", "q", "\x03"})
        elapsed = time.perf_counter() - t0

        if key in {"q", "\x03"}:
            rec = show_session_report(records, operation, difficulty_label, timed=False)
            if rec: append_session(rec)
            return

        clear()
        print_header("ANSWER CHECK")
        print(row("Question",    f"{question} = ?"))
        print(row("Answer",      str(answer)))
        print(row("Time taken",  f"{elapsed:.2f} sec"))
        print(box_sep())
        print(bare("  Got it right?"))
        print(bare("  [SPACE] Yes    [N] No    [Q] Quit"))
        print(box_bot())

        mark = wait_for_key({" ", "n", "q", "\x03"})

        if mark in {"q", "\x03"}:
            rec = show_session_report(records, operation, difficulty_label, timed=False)
            if rec: append_session(rec)
            return

        result = "correct" if mark == " " else "wrong"
        streak = streak + 1 if result == "correct" else 0

        records.append({
            "question": question,
            "answer":   answer,
            "time":     elapsed,
            "result":   result,
            "op":       actual_op,
        })
        q_num += 1

# ─── Timed blitz session ───────────────────────────────────────────────────────

def run_timed(operation, difficulty_label, digits):
    records    = []
    q_num      = 1
    streak     = 0
    end_time   = time.perf_counter() + TIMED_SECS

    while True:
        remaining = end_time - time.perf_counter()
        if remaining <= 0:
            break

        clear()
        streak_tag = f"  🔥 {streak}" if streak >= 3 else ""
        print(box_top())
        print("║" + cx(f"{OP_NAMES[operation]}  ·  {difficulty_label}  ·  BLITZ  ·  Q{q_num}{streak_tag}") + "║")
        print(box_bot())

        question, answer, actual_op = build_question(operation, digits)
        print(f"\n  {question} = ?\n")
        print(f"  ⏱  {remaining:.0f}s left")
        print("  [SPACE] reveal    [Q] quit")

        t0  = time.perf_counter()
        key = wait_for_key({" ", "q", "\x03"})
        elapsed = time.perf_counter() - t0

        if key in {"q", "\x03"}:
            break

        remaining2 = end_time - time.perf_counter()
        if remaining2 <= 0:
            # auto-reveal but time up
            records.append({"question": question, "answer": answer,
                            "time": elapsed, "result": "correct", "op": actual_op})
            break

        clear()
        print_header("ANSWER CHECK", f"⏱  {remaining2:.0f}s left")
        print(row("Question",   f"{question} = ?"))
        print(row("Answer",     str(answer)))
        print(row("Time taken", f"{elapsed:.2f} sec"))
        print(box_sep())
        print(bare("  Got it right?"))
        print(bare("  [SPACE] Yes    [N] No"))
        print(box_bot())

        mark = wait_for_key({" ", "n"})
        result = "correct" if mark == " " else "wrong"
        streak = streak + 1 if result == "correct" else 0

        records.append({
            "question": question,
            "answer":   answer,
            "time":     elapsed,
            "result":   result,
            "op":       actual_op,
        })
        q_num += 1

        if end_time - time.perf_counter() <= 0:
            break

    # time's up banner
    clear()
    print(box_top())
    print("║" + cx("⏱  TIME'S UP!") + "║")
    print(box_bot())
    time.sleep(1)

    rec = show_session_report(records, operation, difficulty_label, timed=True)
    if rec:
        append_session(rec)

# ─── History view ──────────────────────────────────────────────────────────────

def ascii_bar(val, max_val, width=20, char="█"):
    if max_val == 0:
        return " " * width
    filled = int(val / max_val * width)
    return char * filled + "░" * (width - filled)

def show_history(data):
    sessions = data["sessions"]
    while True:
        clear()
        print_header("HISTORY & PERSONAL BESTS")
        print(bare("  1 ·  Personal bests per operation"))
        print(bare("  2 ·  Daily summaries (last 7 days)"))
        print(bare("  3 ·  Last 10 sessions"))
        print(bare("  4 ·  7-day accuracy graph"))
        print(box_sep())
        print(bare("  B ·  Back to menu"))
        print(box_bot())

        ch = input("\n  › ").strip().lower()

        if ch == "b":
            return

        elif ch == "1":
            clear()
            print_header("PERSONAL BESTS")
            pb = data.get("personal_bests", {})
            if not pb:
                print(bare("  No data yet — play some sessions first!"))
            else:
                for op_key, b in pb.items():
                    op_int = int(op_key)
                    print(bare(f"  {OP_NAMES.get(op_int, op_key)}"))
                    print(bare(f"    Best accuracy  : {b['best_accuracy']:.1f}%"))
                    bt = b.get("best_avg_time")
                    if bt: print(bare(f"    Best avg time  : {bt:.2f}s"))
                    print(bare(f"    Best streak    : {b['best_streak']}"))
                    print(bare(f"    Most correct   : {b['most_correct']}"))
                    print(box_sep())

        elif ch == "2":
            clear()
            print_header("DAILY SUMMARIES  (last 7 days)")
            from datetime import timedelta
            today = date.today()
            for i in range(6, -1, -1):
                d = (today - timedelta(days=i)).isoformat()
                day_sessions = sessions_on(data, d)
                if not day_sessions:
                    print(bare(f"  {d}  ·  no sessions"))
                else:
                    total_q   = sum(s["total"]   for s in day_sessions)
                    total_cor = sum(s["correct"] for s in day_sessions)
                    avg_acc   = total_cor / total_q * 100 if total_q else 0
                    avg_t     = statistics.mean(s["avg_time"] for s in day_sessions)
                    print(bare(f"  {d}  ·  {len(day_sessions)} session(s)  ·  {total_q} Qs  ·  {avg_acc:.1f}%  ·  {avg_t:.2f}s avg"))

        elif ch == "3":
            clear()
            print_header("LAST 10 SESSIONS")
            last10 = sessions[-10:][::-1]
            if not last10:
                print(bare("  No sessions yet."))
            else:
                for s in last10:
                    timed_tag = " [BLITZ]" if s.get("timed") else ""
                    print(bare(f"  {s['date']}  {OP_NAMES.get(s['operation'],'?')}{timed_tag}"))
                    print(bare(f"    {s['total']} Qs  ·  {s['correct']} correct  ·  {s['accuracy']:.1f}%  ·  {s['avg_time']:.2f}s avg  ·  streak {s['best_streak']}"))
                    print(box_sep())

        elif ch == "4":
            from datetime import timedelta
            clear()
            print_header("7-DAY ACCURACY GRAPH")
            today = date.today()
            accs  = []
            days  = []
            for i in range(6, -1, -1):
                d = (today - timedelta(days=i)).isoformat()
                day_s = sessions_on(data, d)
                if day_s:
                    total_q   = sum(s["total"]   for s in day_s)
                    total_cor = sum(s["correct"] for s in day_s)
                    acc = total_cor / total_q * 100 if total_q else 0
                else:
                    acc = None
                accs.append(acc)
                days.append(d[5:])  # MM-DD

            max_acc = max((a for a in accs if a is not None), default=100)
            for d_label, acc in zip(days, accs):
                if acc is None:
                    bar = "░" * 20
                    val = " no data"
                else:
                    bar = ascii_bar(acc, 100, 20)
                    val = f" {acc:.1f}%"
                print(bare(f"  {d_label}  {bar}{val}"))

        else:
            print("\n  Invalid.")
            time.sleep(0.6)
            continue

        print(box_bot())
        print("\n  Press any key…")
        get_key()

# ─── Entry point ───────────────────────────────────────────────────────────────

MENU_TO_OP = {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 1, "7": 2, "8": 3, "9": 4, "0": 5,
}
TIMED_CHOICES = {"6","7","8","9","0"}

def main():
    data = load_data()
    show_since_last(data)

    while True:
        ch = ask_main_menu()

        if ch == "q":
            clear()
            print(box_top())
            print("║" + cx("GOODBYE  ·  KEEP GRINDING") + "║")
            print(box_bot())
            print()
            return

        if ch == "h":
            data = load_data()  # refresh
            show_history(data)
            continue

        operation = MENU_TO_OP[ch]
        is_timed  = ch in TIMED_CHOICES

        diff_label, digits = ask_difficulty()

        if is_timed:
            run_timed(operation, diff_label, digits)
        else:
            run_practice(operation, diff_label, digits)

        data = load_data()  # reload after session saved


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\n  Exited.\n")
