"""
Safety keyword triage for PlanPal.

Tiers (highest priority first):
  EMERGENCY_911   -> call 911 now
  CRISIS_988      -> call/text 9-8-8 (Canada Suicide Crisis Helpline)
  VIOLENCE_SAFETY -> assault / abuse / threats (911 if in danger, VictimLinkBC 1-800-563-0808)
  POISON_OD       -> poisoning/overdose that may not be 911-level yet (BC Drug & Poison Info 1-800-567-8911)
  URGENT_ER       -> go to ER / call 811 today, don't just book a clinic

VERIFY every phone number and resource before shipping.
Entries are written WITHOUT apostrophes; normalize() strips them from
user input, so "can't" and "cant" both match "cant".
"""
import re
import unicodedata

EMERGENCY_911 = [
    # --- breathing / asthma / airway ---
    "cant breathe", "cannot breathe", "trouble breathing", "difficulty breathing",
    "not breathing", "stopped breathing", "struggling to breathe", "gasping for air",
    "cant catch my breath", "short of breath", "shortness of breath", "hard to breathe",
    "cant speak in full sentences", "lips turning blue", "blue lips", "turning blue",
    "asthma attack", "severe asthma", "inhaler not working", "inhaler isnt working",
    "inhaler isnt helping", "inhaler wont help", "puffer not working", "puffer isnt working",
    "wheezing badly", "cant swallow",
    "drowning", "almost drowned", "near drowning",
    "suffocating", "carbon monoxide", "smoke inhalation",
    # --- heart ---
    "chest pain", "chest pressure", "chest tightness", "crushing chest", "pain in my chest",
    "pain down my left arm", "pain spreading to my arm", "pain in my jaw",
    "heart attack", "cardiac arrest", "heart stopped", "no pulse",
    "heart racing and dizzy", "palpitations and fainting",
    # --- stroke / neuro ---
    "stroke", "face drooping", "slurred speech", "sudden numbness", "cant move one side",
    "one side of my body", "arm went numb", "arm is weak", "cant speak", "sudden confusion",
    "sudden vision loss", "sudden blindness", "worst headache of my life",
    "thunderclap headache", "sudden severe headache", "paralyzed", "cant feel my legs",
    "cant move my legs", "seizure", "convulsing", "having a fit",
    # --- consciousness ---
    "passed out", "unconscious", "unresponsive", "fainted", "blacked out",
    "wont wake up", "cant wake", "not waking up", "limp and not responding",
    # --- bleeding / trauma ---
    "bleeding heavily", "wont stop bleeding", "blood wont stop", "spurting blood",
    "coughing up blood", "vomiting blood", "throwing up blood", "deep cut",
    "stabbed", "stab wound",
    "got shot", "was shot", "been shot", "gunshot", "shot in the",
    "hit my head", "head injury",
    "hit by a car", "car accident", "car crash", "fell from", "fell off a roof",
    "bone sticking out", "broken neck", "broken back", "severed", "amputated",
    "crushed by", "crushed my hand", "crushed my leg", "crushed my foot",
    "severe burn", "burned badly", "chemical burn", "electric shock", "electrocuted",
    "chemical in my eye",
    # --- allergy ---
    "anaphylaxis", "anaphylactic", "throat closing", "throat swelling", "tongue swelling",
    "face swelling", "lips swelling", "severe allergic", "allergic reaction and cant breathe",
    "used my epipen", "need my epipen", "epinephrine",
    # --- overdose / poison (immediate) ---
    "overdose", "overdosed", "took too many pills", "took too much", "too many tablets",
    "poisoned", "poisoning", "swallowed bleach", "drank bleach", "swallowed poison",
    "fentanyl", "narcan", "naloxone", "opioid overdose", "alcohol poisoning",
    "drink was spiked", "spiked drink", "passed out drunk",
    # --- pregnancy / birth ---
    "giving birth", "in labour", "in labor", "water broke", "waters broke",
    "baby not moving", "bleeding while pregnant", "pregnant and bleeding",
    "severe pain while pregnant", "ectopic",
    # --- infants / children ---
    "baby not breathing", "baby is blue", "baby wont wake", "child not breathing",
    "limp baby", "child is limp", "baby choking",
    # --- choking ---
    "choking on food", "is choking", "am choking", "cant stop choking",
    # --- diabetes / metabolic ---
    "diabetic and unconscious", "blood sugar very low", "dka",
    # --- danger to others ---
    "going to hurt someone", "want to hurt someone", "going to kill someone",
    "kill someone", "hurt other people", "homicidal",
]

CRISIS_988 = [
    "suicide", "suicidal", "kill myself", "killing myself", "going to kill myself",
    "gonna kill myself", "about to kill myself", "tried to kill myself",
    "end my life", "end it all", "ending it all", "want to die", "wanna die",
    "dont want to live", "dont want to be alive", "wish i was dead", "wish i were dead",
    "wish i wasnt alive", "wish i wouldnt wake up", "better off dead",
    "better off without me", "everyone would be better without me",
    "no reason to live", "not worth living", "life isnt worth", "cant go on",
    "cant do this anymore", "cant take it anymore", "nothing to live for",
    "want to disappear forever", "unalive", "kms",
    "suicide plan", "have a plan to", "planning to kill myself", "planning to end",
    "take all my pills", "pills to end", "hang myself", "hanging myself",
    "shoot myself", "jump off", "jump from a bridge", "jumping off",
    "overdose on purpose", "overdose myself",
    "self harm", "self-harm", "selfharm", "hurt myself", "harm myself",
    "cut myself", "cutting myself", "burning myself", "hitting myself",
    "relapsed self harm", "urge to hurt myself", "urge to cut",
]

VIOLENCE_SAFETY = [
    "raped", "rape", "sexual assault", "sexually assaulted",
    "i was assaulted", "got assaulted", "assaulted me",
    "molested",
    "forced me to", "someone touched me", "date rape", "drugged and",
    "partner hits me", "partner hurts me", "abusive partner", "abusive boyfriend",
    "abusive girlfriend", "abusive relationship", "domestic violence",
    "afraid to go home", "not safe at home", "scared of my partner",
    "someone is hurting me", "being stalked", "being followed", "stalker",
    "threatened to kill me", "threatening me", "being blackmailed", "sextortion",
    "human trafficking", "trafficked",
]

POISON_OD = [
    "ate something toxic", "ate a poisonous", "mushroom poisoning",
    "mixed pills and alcohol", "took extra", "double dose", "took twice",
    "too much tylenol", "too much acetaminophen", "too much ibuprofen",
    "too much medication", "accidentally took", "someone took too many",
    "kid swallowed", "child swallowed", "baby swallowed", "swallowed a battery",
    "swallowed a magnet", "drank antifreeze", "drank cleaner",
]

URGENT_ER = [
    # abdominal
    "worst stomach pain", "severe stomach pain", "severe abdominal pain", "hard belly",
    "rigid abdomen", "pain in lower right", "appendicitis", "black stool", "tarry stool",
    "blood in stool", "blood in my stool", "blood in vomit", "coffee ground",
    "cant keep anything down", "vomiting for days",
    # infection / sepsis / meningitis
    "stiff neck and fever", "neck stiff and fever", "rash that doesnt fade",
    "purple rash", "confused and fever", "fever and confusion", "sepsis",
    "fever over 40", "fever wont go down",
    # urogenital
    "sudden testicle pain", "severe testicle pain", "testicular torsion",
    "cant pee", "unable to urinate", "blood in urine", "blood in my urine",
    # eyes / ears / face
    "lost vision", "sudden vision change", "eye injury", "something in my eye",
    "severe eye pain",
    # neuro / other
    "severe headache with fever", "headache and vomiting and stiff neck",
    "severe dizziness", "cant stop vomiting", "severe dehydration",
    "broken bone", "think i broke", "dislocated", "deep wound", "wont stop shaking",
    "high fever", "fever and rash", "severe allergic rash", "heatstroke", "hypothermia",
    # mental health, same-day (not 988)
    "panic attack wont stop", "hearing voices", "seeing things", "paranoid",
    "havent slept in days", "manic",
    # pediatric
    "baby fever", "infant fever", "baby wont eat", "baby wont stop crying",
    "child wont drink", "dehydrated child",
]

# Order matters: first tier that matches wins.
TIERS = [
    ("EMERGENCY_911", EMERGENCY_911),
    ("CRISIS_988", CRISIS_988),
    ("VIOLENCE_SAFETY", VIOLENCE_SAFETY),
    ("POISON_OD", POISON_OD),
    ("URGENT_ER", URGENT_ER),
]

# IGNORE_PHRASES: if the normalized text contains one of these phrases, suppress
# the specific single-keyword matches it would falsely trigger.
# key = phrase to look for; value = set of keywords to skip.
IGNORE_PHRASES = [
    ("drowning in homework", {"drowning"}),
    ("drowning in work",     {"drowning"}),
    ("dying of laughter",    set()),
    ("killing it",           set()),
    ("crushed my exam",      set()),
    ("crushed it",           set()),
    ("i could die of",       set()),
    ("shot my shot",         set()),
    ("flu shot",             set()),
    ("covid shot",           set()),
    ("vaccine shot",         set()),
    ("allergy shot",         set()),
    ("booster shot",         set()),
]


def normalize(text: str) -> str:
    """Lowercase, strip accents/apostrophes/punctuation, collapse whitespace.
    Drops all non-ASCII — use normalize_ml() for non-Latin scripts.
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"['’`]", "", text)       # cant / can't -> cant
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_ml(text: str) -> str:
    """NFKC-normalize, lowercase; keeps non-Latin scripts for multilingual matching."""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"['’`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


_COMPILED = [
    (name, [(kw, re.compile(r"\b" + re.escape(normalize(kw)) + r"\b")) for kw in kws])
    for name, kws in TIERS
]

_IGNORE_MAP = [
    (normalize(phrase), {normalize(k) for k in skip_kws})
    for phrase, skip_kws in IGNORE_PHRASES
]

# ---------------------------------------------------------------------------
# Multilingual keyword list — highest-risk emergencies only.
# Matched with simple substring matching on NFKC-normalized text.
# REVIEW BY NATIVE SPEAKERS BEFORE PRODUCTION.
# ---------------------------------------------------------------------------
MULTILINGUAL = [
    # Mandarin Simplified — can't breathe / chest pain
    ("EMERGENCY_911", "喘不过气"),
    ("EMERGENCY_911", "我喘不过气"),
    ("EMERGENCY_911", "胸痛"),
    ("EMERGENCY_911", "胸口痛"),
    # Mandarin Simplified — suicide / want to die
    ("CRISIS_988", "自杀"),
    ("CRISIS_988", "想死"),
    ("CRISIS_988", "我想死"),
    # Mandarin Simplified — overdose
    ("EMERGENCY_911", "服药过量"),
    ("EMERGENCY_911", "吃药过多"),
    # Mandarin Simplified — sexual assault / someone hurting me
    ("VIOLENCE_SAFETY", "性侵"),
    ("VIOLENCE_SAFETY", "有人在伤害我"),

    # Mandarin Traditional — can't breathe / chest pain
    ("EMERGENCY_911", "喘不過氣"),
    ("EMERGENCY_911", "我喘不過氣"),
    # Mandarin Traditional — suicide
    ("CRISIS_988", "自殺"),
    # Mandarin Traditional — overdose
    ("EMERGENCY_911", "服藥過量"),
    # Mandarin Traditional — sexual assault
    ("VIOLENCE_SAFETY", "有人在傷害我"),

    # Cantonese written — can't breathe
    ("EMERGENCY_911", "喘唔到氣"),

    # Punjabi (Gurmukhi) — can't breathe / chest pain
    ("EMERGENCY_911", "ਸਾਹ ਨਹੀਂ ਆ ਰਿਹਾ"),
    ("EMERGENCY_911", "ਛਾਤੀ ਦਰਦ"),
    # Punjabi — suicide / want to die
    ("CRISIS_988", "ਖੁਦਕੁਸ਼ੀ"),
    ("CRISIS_988", "ਮਰਨਾ ਚਾਹੁੰਦਾ"),
    # Punjabi — overdose
    ("EMERGENCY_911", "ਓਵਰਡੋਜ਼"),
    # Punjabi — sexual assault
    ("VIOLENCE_SAFETY", "ਜਿਨਸੀ ਹਮਲਾ"),

    # Hindi — can't breathe / chest pain
    ("EMERGENCY_911", "सांस नहीं ले सकता"),
    ("EMERGENCY_911", "सांस नहीं ले सकती"),
    ("EMERGENCY_911", "छाती में दर्द"),
    # Hindi — suicide / want to die
    ("CRISIS_988", "आत्महत्या"),
    ("CRISIS_988", "मरना चाहता हूं"),
    ("CRISIS_988", "मरना चाहती हूं"),
    # Hindi — overdose
    ("EMERGENCY_911", "ओवरडोज़"),
    # Hindi — sexual assault
    ("VIOLENCE_SAFETY", "यौन उत्पीड़न"),

    # Korean — can't breathe / chest pain
    ("EMERGENCY_911", "숨을 못 쉬겠어"),
    ("EMERGENCY_911", "가슴이 아파요"),
    # Korean — suicide / want to die
    ("CRISIS_988", "자살"),
    ("CRISIS_988", "죽고 싶어"),
    ("CRISIS_988", "죽고 싶다"),
    # Korean — took too many pills
    ("EMERGENCY_911", "약을 너무 많이"),
    # Korean — sexual assault
    ("VIOLENCE_SAFETY", "성폭행"),

    # Spanish — can't breathe / chest pain
    ("EMERGENCY_911", "no puedo respirar"),
    ("EMERGENCY_911", "dolor en el pecho"),
    # Spanish — suicide / want to die / want to kill myself
    ("CRISIS_988", "suicidio"),
    ("CRISIS_988", "quiero morir"),
    ("CRISIS_988", "me quiero matar"),
    # Spanish — overdose
    ("EMERGENCY_911", "sobredosis"),
    # Spanish — sexual assault / someone hurting me
    ("VIOLENCE_SAFETY", "agresión sexual"),
    ("VIOLENCE_SAFETY", "me están lastimando"),

    # Farsi/Persian — can't breathe / chest pain
    ("EMERGENCY_911", "نمی توانم نفس بکشم"),
    ("EMERGENCY_911", "درد قفسه سینه"),
    # Farsi — suicide / want to die
    ("CRISIS_988", "خودکشی"),
    ("CRISIS_988", "می خواهم بمیرم"),
    # Farsi — overdose
    ("EMERGENCY_911", "مصرف بیش از حد"),
    # Farsi — sexual assault
    ("VIOLENCE_SAFETY", "تجاوز جنسی"),

    # French — can't breathe / chest pain
    ("EMERGENCY_911", "je ne peux pas respirer"),
    ("EMERGENCY_911", "douleur à la poitrine"),
    # French — suicide / want to die / want to kill myself
    ("CRISIS_988", "je veux mourir"),
    ("CRISIS_988", "je veux me tuer"),
    # French — overdose
    ("EMERGENCY_911", "overdose"),
    # French — sexual assault
    ("VIOLENCE_SAFETY", "agression sexuelle"),
]

_ML_COMPILED = [
    (tier, phrase, normalize_ml(phrase))
    for tier, phrase in MULTILINGUAL
]


def check_safety(user_text: str):
    """Return (tier, matched_keyword) or (None, None).

    Deliberately does NOT suppress on negation ("I'm not suicidal"):
    showing resources by mistake is cheap, missing a real case is not.
    """
    t = normalize(user_text)

    # Build skip set from ignore phrases present in the text.
    skip = set()
    for phrase_norm, to_skip in _IGNORE_MAP:
        if phrase_norm in t:
            skip.update(to_skip)

    # English keyword pass.
    for name, patterns in _COMPILED:
        for kw, pat in patterns:
            if normalize(kw) in skip:
                continue
            if pat.search(t):
                return name, kw

    # Multilingual substring pass (NFKC-normalized, no word boundaries for CJK).
    t_ml = normalize_ml(user_text)
    for tier, phrase, phrase_norm in _ML_COMPILED:
        if phrase_norm in t_ml:
            return tier, phrase

    return None, None


if __name__ == "__main__":
    tests = [
        "I need a flu shot",
        "I crushed my exam",
        "I'm drowning in homework",
        "I got shot",
        "I cant breathe",
        "I have an asthma attack",
        "my inhaler isnt helping",
        "I have asthma and need my inhaler",
        "I want to kill myself",
        "I was sexually assaulted",
        "chest pain",
        "I have a stomachach so bad",
        "sprained ankle",
        "我喘不过气",
        "no puedo respirar",
    ]
    for s in tests:
        print(f"{s!r:50} -> {check_safety(s)}")
