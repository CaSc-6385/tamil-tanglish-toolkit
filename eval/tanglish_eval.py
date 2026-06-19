"""Ad-hoc eval: run a diverse Tanglish corpus through the gemma2 translation step.

Captures output + automated quality flags so we can scan ~100+ sentences for
literal/wrong translations, prompt leakage, or untranslated English.

    uv run python eval/tanglish_eval.py
"""

from __future__ import annotations

import re
import time

from tamil_edu_transliterate import _get  # type: ignore[attr-defined]

SENTENCES = [
    # greetings / social
    "vanakkam nanba",
    "epdi iruka?",
    "naan nalla iruken, nee epdi iruka?",
    "ungaluku enna venum?",
    "romba nandri",
    "naalaiki paarkalam",
    "shapad aacha?",
    "vaanga uloku ulla vaanga",
    # past tense / daily life
    "nettru naan school ku ponen",
    "naan kaalaila saapadu saapten",
    "avan nethu veetuku vanthan",
    "naanga cinema ku ponom",
    "nethu raathiri romba nalla thoonganen",
    "naan kadaiku poi paal vaangiten",
    "avanga ellarum party ku vanthaanga",
    "naan en homework mudichiten",
    "amma samayal panninanga",
    "thambi pandu vilayadinaan",
    # the user's reported sentence + variants
    "nettru, naan nadakumboothu, oru naayai ennai paartthu kuraththathu",
    "naan road la nadanthukittu irunthen",
    "oru periya naai ennai thaaki vanthuchu",
    "poona vaaram naan oorukku ponen",
    # present / continuous
    "naan ippo saapittu kitiruken",
    "avan tv paaktraan",
    "mazhai peஞ்சute",
    "naan tamil padikiren",
    "enaku romba pasikuthu",
    "enaku thookam varuthu",
    "veliya romba veyil adikuthu",
    "kuழந்தை azhuthukittu iruku",
    # future / intent
    "naan naalaiki Chennai ku poren",
    "naanga next week trip ku porom",
    "naan doctor aaganum nu nenakuren",
    " unaku naan help panren",
    "naama veetuku poyiடlaam",
    # questions
    "nee enga poha?",
    "ipo mani enna?",
    "idhu evvalavu?",
    "unaku enna pidikum?",
    "yaaru andha paiyan?",
    "eppo varuvinga?",
    "en azhura?",
    "saapda vanthiya?",
    # emotions / states
    "enaku romba santhosama iruku",
    "avan romba kovama iruந்தான்",
    "naan romba sora paitten",
    "enaku bayama iruku",
    "avalukku udambu sariyilla",
    "naan romba klaippa iruken",
    # family / people
    "en appa office ku poraaru",
    "en thatha kadhai sollுvaaru",
    "engaluku rendu naai iruku",
    "avanga kudumbam periya kudumbam",
    "en sister romba azhaga paaduvaa",
    # food
    "amma dosa suttu kuduthanga",
    "naan kaapி kudichen",
    "idli sambar romba taste a iruந்துchu",
    "enaku sweet romba pidikum",
    "neenga enna saapduveenga?",
    # school / learning
    "naan tamil kaththukittu iruken",
    "teacher class la paadam sollikuduthaanga",
    "exam naalaiki iruku",
    "naan first mark vaangiten",
    "padichaa than nalla velai kidaikum",
    # code-switching (English words inside)
    "send the message reply pannu",
    "naan office la meeting la iruந்தen",
    "weekend ku naanga beach ku ponom",
    "phone la battery low a iruku",
    "naan email check panனanum",
    "traffic la maatti konden",
    "online class romba boring a iruந்துchu",
    "naan bus miss panniten",
    # commands / requests
    "kontham water kudu",
    " inga vaanga",
    "konjam wait pannunga",
    "kathava saathu",
    "sapt vanthudu",
    "siri konjam siri",
    # negation
    "enaku andha padam pidikala",
    "avan innaiki varala",
    "naan saapdala",
    "idhu sariya illa",
    "enaku tamil theriyala",
    # time / numbers
    "ippo ettu mani aachu",
    "naan rendu manineram padichen",
    "naalaiki gnaayitru kizhamai",
    "oru நிமிஷம் wait pannu",
    "naan moonu vருஷama inga velai paakuren",
    # longer / compound
    "naan kaalaila ezhunthu, pal thechi, kuli pannittu, school ku ponen",
    "avan padikira maathiri nadichaan aana padikaला",
    "mழை வந்தadhaala naanga veliya pohala",
    "enaku andha kadai theriyum aana eppadi pohardhu nu theriyala",
    "nethu night நண்பர்களோட சேர்ந்து nalla saapittom",
    # everyday misc
    "naan thoonga poren good night",
    "kaalaila eluந்து udaற்சி pannu",
    "veetuku poi konjam rest edu",
    "enaku indha song romba pidikum",
    "naai veedhiyila ஓடுchu",
    "poonai paal kudichuchu",
    "maram la pazham iruku",
    "vானத்துla nilaa azhaga iruku",
    "kadalkaraila kaathu nalla veesuthu",
    "naan padathula photo eduthen",
    "enga ooru romba azhaga iruku",
    "thanni romba kulira iruku",
    "naalaiki en birthday",
    "naan ipo padichittu velila poren",
    "amma ennoda favorite person",
]


def tamil_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "஀" <= c <= "௿") / len(letters)


def latin_runs(text: str) -> int:
    """Count runs of 2+ consecutive Latin words (possible untranslated English)."""
    return len(re.findall(r"\b[A-Za-z]+(?:\s+[A-Za-z]+)+\b", text))


def main() -> None:
    backend = _get("ollama")
    print(f"# Tanglish translation eval — {len(SENTENCES)} sentences\n")
    flagged: list[tuple[str, str, str]] = []
    times: list[float] = []
    empties = 0

    for i, src in enumerate(SENTENCES, 1):
        t0 = time.time()
        try:
            out = backend.transliterate(src)
        except Exception as exc:
            out = f"<ERROR: {exc}>"
        dt = time.time() - t0
        times.append(dt)

        tr = tamil_ratio(out)
        leak = bool(re.search(r"Tanglish:|Tamil:|Sentence:|^JSON", out))
        runs = latin_runs(out)
        reasons = []
        if not out.strip() or out.startswith("<ERROR"):
            empties += 1
            reasons.append("EMPTY/ERROR")
        if tr < 0.5:
            reasons.append(f"low-tamil({tr:.2f})")
        if leak:
            reasons.append("prompt-leak")
        if runs:
            reasons.append(f"latin-run({runs})")
        flag = "  ⚠ " + ",".join(reasons) if reasons else ""
        if reasons:
            flagged.append((src, out, ",".join(reasons)))
        print(f"{i:>3}. {src}")
        print(f"     -> {out}{flag}")

    avg = sum(times) / len(times) if times else 0
    print("\n" + "=" * 60)
    print(f"total={len(SENTENCES)}  flagged={len(flagged)}  empty/err={empties}")
    print(f"avg_latency={avg:.1f}s  total_time={sum(times):.0f}s")
    print(f"clean_rate={100 * (len(SENTENCES) - len(flagged)) / len(SENTENCES):.0f}%")
    if flagged:
        print("\n--- FLAGGED ---")
        for src, out, why in flagged:
            print(f"[{why}] {src}\n    -> {out}")


if __name__ == "__main__":
    main()
