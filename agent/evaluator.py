"""
LoanGuard - Compliance Evaluator
Checks AI loan advisor responses against RBI Digital Lending Guidelines.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional


# ── Load RBI rules once at startup ──────────────────────────────────────────
RULES_PATH = os.path.join(os.path.dirname(__file__), "rules.json")

with open(RULES_PATH, "r") as f:
    _rules_data = json.load(f)

RBI_RULES = _rules_data["rules"]
RULES_SOURCE = _rules_data["source"]


# ── Data classes ─────────────────────────────────────────────────────────────
@dataclass
class EvaluationResult:
    """Result of a compliance evaluation."""
    is_compliant: bool
    confidence_score: float        # 0.0 to 100.0
    violated_rules: list[dict]
    triggered_categories: list[str]
    recommended_action: str        # SAFE / REWRITE / ESCALATE / APPEND
    explanation: str


# ── Core evaluation logic ────────────────────────────────────────────────────
def classify_query(user_question: str) -> str:
    """
    Step 1: Classify what type of financial query this is.
    Returns one of: interest_rate, eligibility, disclosure, repayment, kyc, general
    """
    question_lower = user_question.lower()

    category_keywords = {
        "interest_rate": [
            "interest", "rate", "apr", "annual", "percent",
            "processing fee", "charges", "penalty"
        ],
        "eligibility": [
            "eligible", "qualify", "eligibility", "income",
            "salary", "credit score", "cibil", "age", "approved"
        ],
        "repayment": [
            "emi", "repay", "tenure", "instalment", "prepay",
            "foreclose", "monthly payment", "amortization"
        ],
        "kyc": [
            "kyc", "aadhaar", "pan", "verify", "verification",
            "identity", "document", "biometric"
        ],
        "disclosure": [
            "disclose", "agreement", "document", "insurance",
            "cancel", "cooling", "grievance", "complaint",
            "approved", "approve", "sanction", "disburse", "sign"
        ],
        
    }

    scores = {cat: 0 for cat in category_keywords}
    for cat, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in question_lower:
                scores[cat] += 1

    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] > 0 else "general"


def fetch_relevant_rules(category: str, response_text: str) -> list[dict]:
    """
    Step 2: Fetch RBI rules relevant to the category and response.
    Returns list of matching rules.
    """
    response_lower = response_text.lower()
    matched_rules = []

    for rule in RBI_RULES:
        # Match by category
        if rule["category"] != category and category != "general":
            continue

        # Match by violation keywords found in response
        for keyword in rule["violation_keywords"]:
            if keyword.lower() in response_lower:
                matched_rules.append(rule)
                break

    return matched_rules


def evaluate_compliance(
    user_question: str,
    advisor_response: str
) -> EvaluationResult:
    """
    Step 3: Full compliance evaluation pipeline.

    Runs the complete 3-step check:
    1. Classify the query
    2. Fetch relevant rules
    3. Evaluate and score

    Returns an EvaluationResult with verdict and recommended action.
    """

    # Step 1 — Classify
    category = classify_query(user_question)

    # Step 2 — Fetch relevant rules
    relevant_rules = fetch_relevant_rules(category, advisor_response)

    # Step 3 — Evaluate
    violated_rules = []
    triggered_categories = set()
    highest_severity_action = "SAFE"

    severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    action_order = {"SAFE": 0, "APPEND": 1, "REWRITE": 2, "ESCALATE": 3}

    for rule in relevant_rules:
        # Check if the response is missing required disclosures
        is_violation = _check_violation(advisor_response, rule)

        if is_violation:
            violated_rules.append(rule)
            triggered_categories.add(rule["category"])

            # Escalate action if this rule requires stronger action
            rule_action = rule["action"]
            if action_order.get(rule_action, 0) > action_order.get(
                highest_severity_action, 0
            ):
                highest_severity_action = rule_action

    # Calculate compliance score
    if not relevant_rules:
        confidence_score = 85.0  # No rules triggered — likely safe
        is_compliant = True
    else:
        violation_ratio = len(violated_rules) / len(relevant_rules)
        confidence_score = round((1 - violation_ratio) * 100, 2)
        is_compliant = len(violated_rules) == 0

    # Build explanation
    if is_compliant:
        explanation = (
            f"Response appears compliant. "
            f"Checked against {len(relevant_rules)} RBI rules "
            f"in category '{category}'. No violations detected."
        )
        recommended_action = "SAFE"
    else:
        rule_titles = [r["title"] for r in violated_rules]
        explanation = (
            f"⚠️ {len(violated_rules)} potential violation(s) detected "
            f"in category '{category}'. "
            f"Rules triggered: {', '.join(rule_titles)}. "
            f"Recommended action: {highest_severity_action}."
        )
        recommended_action = highest_severity_action

    return EvaluationResult(
        is_compliant=is_compliant,
        confidence_score=confidence_score,
        violated_rules=violated_rules,
        triggered_categories=list(triggered_categories),
        recommended_action=recommended_action,
        explanation=explanation,
    )


def _check_violation(response: str, rule: dict) -> bool:
    """
    Internal helper: determines if a response violates a specific rule.
    Uses heuristic checks based on rule category and safe_threshold.
    """
    response_lower = response.lower()
    threshold = rule["safe_threshold"].lower()
    category = rule["category"]

    # Interest rate rules — check if annual rate is mentioned
    if category == "interest_rate":
        if "per month" in response_lower or "monthly rate" in response_lower:
            return True  # Quoting monthly not annual — violation
        if "per annum" not in response_lower and "annual" not in response_lower and "%" in response_lower:
            return True  # Rate mentioned without annual clarification

    # Eligibility rules — check if credit score mentioned
    if category == "eligibility":
        if "eligible" in response_lower and "credit score" not in response_lower:
            return True  # Eligibility stated without credit score check

    # Disclosure rules — check for missing KFS mention
    if category == "disclosure":
     if ("approve" in response_lower or "approved" in response_lower or 
            "disburse" in response_lower or "sign" in response_lower) and \
       "key fact" not in response_lower and "kfs" not in response_lower:
        return True

    # Repayment rules — check for EMI without reducing balance
    if category == "repayment":
        if "emi" in response_lower and "reducing balance" not in response_lower:
            return True  # EMI stated without reducing balance method

    return False


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🛡️  LoanGuard Compliance Evaluator — Test Run\n")

    # Test Case 1: BAD response — should be flagged
    question1 = "Am I eligible for a home loan at 8.5% interest?"
    response1 = (
        "Yes, you are eligible for a home loan. "
        "The interest rate is 8.5% and your EMI will be ₹9,500 per month."
    )

    result1 = evaluate_compliance(question1, response1)
    print("Test 1 — Bad Response:")
    print(f"  Question : {question1}")
    print(f"  Compliant: {result1.is_compliant}")
    print(f"  Score    : {result1.confidence_score}/100")
    print(f"  Action   : {result1.recommended_action}")
    print(f"  Verdict  : {result1.explanation}")
    print()

    # Test Case 2: GOOD response — should pass
    question2 = "What is the interest rate for your personal loan?"
    response2 = (
        "Our personal loan interest rate is 12% per annum on a reducing balance basis. "
        "The APR including all processing fees is 13.5% per annum. "
        "A Key Fact Statement will be shared before loan approval."
    )

    result2 = evaluate_compliance(question2, response2)
    print("Test 2 — Good Response:")
    print(f"  Question : {question2}")
    print(f"  Compliant: {result2.is_compliant}")
    print(f"  Score    : {result2.confidence_score}/100")
    print(f"  Action   : {result2.recommended_action}")
    print(f"  Verdict  : {result2.explanation}")