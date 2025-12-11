from __future__ import annotations
import csv
import random
from pathlib import Path
from typing import List, Dict


# --------------------------
# Config
# --------------------------

N_ROWS = 200  # change this if you want more/less data
OUTPUT_PATH = Path("data/sample_opportunities.csv")

ACCOUNT_NAMES = [
    "Acme Bank",
    "NorthTel",
    "City Health",
    "FinPlus",
    "Macro Finance",
    "Prairie Telecom",
    "Evergreen Health",
    "Summit Insurance",
    "Velocity Capital",
    "Northern Grid",
    "Maple Retail",
    "Skyline Logistics",
]

STAGES = [
    "Prospecting",
    "Qualification",
    "Discovery",
    "Proposal",
    "Negotiation",
    "Closed Won",
    "Closed Lost",
]

# Stage → (probability range)
STAGE_PROB_RANGES: Dict[str, tuple[float, float]] = {
    "Prospecting": (0.05, 0.2),
    "Qualification": (0.1, 0.3),
    "Discovery": (0.2, 0.4),
    "Proposal": (0.3, 0.6),
    "Negotiation": (0.4, 0.8),
    "Closed Won": (0.8, 1.0),
    "Closed Lost": (0.0, 0.15),
}

POSITIVE_NOTES = [
    "Client very engaged and sees strong value in the solution.",
    "Stakeholders aligned and interested in moving forward.",
    "Technical fit confirmed; next step is commercial review.",
    "Positive feedback from the last demo; awaiting internal approval.",
    "Customer sees us as preferred vendor pending contract review.",
]

NEGATIVE_NOTES = [
    "Customer raised concern about integration timeline and complexity.",
    "Budget constraints mentioned; might delay decision.",
    "Competitor mentioned as alternative with lower price.",
    "Project on hold due to internal re-org; risk of delay.",
    "Client thinks current proposal is too expensive.",
    "Decision maker is blocked and wants to pause discussion for now.",
    "Risk of losing to competitor if we cannot improve proposal.",
]

NEUTRAL_NOTES = [
    "Waiting for customer to confirm internal meeting date.",
    "Customer asked for additional documentation.",
    "Internal review ongoing; follow-up planned next week.",
    "Client requested a high-level summary for leadership.",
    "No major concerns raised; next demo is being scheduled.",
]


def random_stage() -> str:
    # Slightly bias toward middle stages
    weights = {
        "Prospecting": 1,
        "Qualification": 2,
        "Discovery": 3,
        "Proposal": 3,
        "Negotiation": 2,
        "Closed Won": 1,
        "Closed Lost": 1,
    }
    population = list(weights.keys())
    w = [weights[s] for s in population]
    return random.choices(population, weights=w, k=1)[0]


def random_probability(stage: str) -> float:
    lo, hi = STAGE_PROB_RANGES.get(stage, (0.1, 0.5))
    return round(random.uniform(lo, hi), 2)


def random_amount(stage: str) -> float:
    """
    Simple heuristic: mid/late-stage deals tend to be a bit bigger on average,
    but this is just to add variety.
    """
    if stage in {"Prospecting", "Qualification"}:
        return float(random.randint(10000, 60000))
    elif stage in {"Discovery", "Proposal"}:
        return float(random.randint(20000, 120000))
    else:
        return float(random.randint(30000, 200000))


def random_days_in_stage(stage: str) -> int:
    if stage in {"Prospecting", "Qualification"}:
        return random.randint(1, 40)
    elif stage in {"Discovery", "Proposal", "Negotiation"}:
        return random.randint(5, 60)
    else:
        # Closed deals might have stayed a while in the last stage
        return random.randint(10, 90)


def random_last_contact_days_ago(stage: str) -> int:
    if stage in {"Prospecting", "Qualification"}:
        return random.randint(3, 30)
    elif stage in {"Discovery", "Proposal", "Negotiation"}:
        return random.randint(0, 30)
    else:
        # Closed deals might not have recent contact
        return random.randint(7, 60)


def random_notes(stage: str) -> str:
    """
    Mix positive, neutral, and negative notes to trigger risk rules.
    Include negative notes more often in early/mid stages.
    """
    r = random.random()

    if r < 0.3:
        base = random.choice(POSITIVE_NOTES)
    elif r < 0.6:
        base = random.choice(NEUTRAL_NOTES)
    else:
        base = random.choice(NEGATIVE_NOTES)

    # Add a tiny stage-specific hint sometimes
    if stage in {"Prospecting", "Qualification"} and random.random() < 0.3:
        base += " Prospect is still defining scope and requirements."
    elif stage in {"Proposal", "Negotiation"} and random.random() < 0.3:
        base += " Legal and procurement may add additional delays."

    return base


def generate_row(idx: int) -> Dict[str, str]:
    stage = random_stage()
    account = random.choice(ACCOUNT_NAMES)
    amount = random_amount(stage)
    probability = random_probability(stage)
    days = random_days_in_stage(stage)
    last_contact = random_last_contact_days_ago(stage)
    notes = random_notes(stage)

    return {
        "id": f"OPP-{idx:03d}",
        "account_name": account,
        "stage": stage,
        "amount": f"{amount:.0f}",
        "probability": f"{probability:.2f}",
        "days_in_stage": str(days),
        "last_contact_days_ago": str(last_contact),
        "notes": notes,
    }


def main() -> None:
    random.seed(42)  # reproducible

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "account_name",
        "stage",
        "amount",
        "probability",
        "days_in_stage",
        "last_contact_days_ago",
        "notes",
    ]

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, N_ROWS + 1):
            row = generate_row(i)
            writer.writerow(row)

    print(f"Generated {N_ROWS} opportunities in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
