"""
LoanGuard - Core Compliance Agent
An autonomous AI agent that intercepts loan advisor responses,
evaluates them against RBI Digital Lending Guidelines,
and rewrites or escalates non-compliant responses.

Built for: Google Cloud Rapid Agent Hackathon 2026 - Arize Track
"""

import os
import json
import vertexai
from vertexai import agent_engines  # This imports the Agent Builder SDK
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "loanguard-prod"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
from agent.evaluator import evaluate_compliance, classify_query, EvaluationResult
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Get tracer for manual spans
tracer = trace.get_tracer("loanguard")



# ── Initialize Gemini client ───────────────────────────────────────────────────

load_dotenv()

# Initialize Vertex AI with Google Cloud project
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "loanguard-prod"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)
GEMINI_MODEL = "gemini-2.5-flash-lite"


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 1 — Classify Query
# ══════════════════════════════════════════════════════════════════════════════
def tool_classify_query(user_question: str) -> dict:
    """
    Tool 1: Classifies the type of financial query.
    Returns category and confidence.
    """
    category = classify_query(user_question)

    return {
        "tool": "classify_query",
        "category": category,
        "description": f"Query classified as: {category.upper()} related"
    }


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 2 — Fetch RBI Rule
# ══════════════════════════════════════════════════════════════════════════════
def tool_fetch_rbi_rule(category: str) -> dict:
    """
    Tool 2: Fetches the most relevant RBI rule for a category.
    Returns rule details.
    """
    rules_path = os.path.join(
        os.path.dirname(__file__), "rules.json"
    )

    with open(rules_path, "r") as f:
        data = json.load(f)

    # Get all rules for this category
    category_rules = [
        r for r in data["rules"]
        if r["category"] == category
    ]

    if not category_rules:
        return {
            "tool": "fetch_rbi_rule",
            "category": category,
            "rules_found": 0,
            "rules": [],
            "message": "No specific rules found for this category"
        }

    return {
        "tool": "fetch_rbi_rule",
        "category": category,
        "rules_found": len(category_rules),
        "rules": [
            {
                "id": r["id"],
                "title": r["title"],
                "rule": r["rule"],
                "severity": r["severity"],
                "action": r["action"]
            }
            for r in category_rules
        ]
    }


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 3 — Evaluate Compliance
# ══════════════════════════════════════════════════════════════════════════════
def tool_evaluate_compliance(
    user_question: str,
    advisor_response: str
) -> dict:
    """
    Tool 3: Runs full compliance evaluation.
    Returns score, violations, and recommended action.
    """
    result: EvaluationResult = evaluate_compliance(
        user_question, advisor_response
    )

    return {
        "tool": "evaluate_compliance",
        "is_compliant": result.is_compliant,
        "confidence_score": result.confidence_score,
        "violated_rules": [
            {
                "id": r["id"],
                "title": r["title"],
                "severity": r["severity"],
                "action": r["action"]
            }
            for r in result.violated_rules
        ],
        "triggered_categories": result.triggered_categories,
        "recommended_action": result.recommended_action,
        "explanation": result.explanation
    }


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 4 — Generate Safe Response
# ══════════════════════════════════════════════════════════════════════════════
def tool_generate_safe_response(
    user_question: str,
    original_response: str,
    violated_rules: list,
    recommended_action: str
) -> dict:
    """
    Tool 4: Rewrites a non-compliant response or escalates to human.
    Returns the safe response and action taken.
    """

    # If ESCALATE — don't rewrite, flag for human review
    if recommended_action == "ESCALATE":
        return {
            "tool": "generate_safe_response",
            "action_taken": "ESCALATED",
            "safe_response": (
                "⚠️ This query has been flagged for human compliance review. "
                "A certified loan officer will contact you within 24 hours "
                "with accurate information. We apologize for any inconvenience."
            ),
            "escalation_reason": (
                f"Response violated {len(violated_rules)} high-severity "
                f"RBI guideline(s): "
                f"{', '.join([r['title'] for r in violated_rules])}"
            )
        }

    # If REWRITE — use LLM to generate compliant response
    rules_context = "\n".join([
        f"- {r['title']}: {r.get('rule', '')}"
        for r in violated_rules
    ])

    system_prompt = """You are LoanGuard, a compliance AI for Indian fintech.
Your job is to rewrite AI loan advisor responses to make them
fully compliant with RBI Digital Lending Guidelines 2022.

Rules to follow when rewriting:
- Always state interest rates as annual percentage (per annum)
- Always mention credit score check for eligibility
- Always mention Key Fact Statement (KFS) before approval
- Always state EMI is calculated on reducing balance method
- Never make definitive eligibility claims without verification
- Add grievance redressal information when relevant
- Be helpful but compliant — don't just refuse to answer

Keep the response friendly, clear, and professional."""

    user_prompt = f"""The following loan advisor response violates these RBI guidelines:

VIOLATED RULES:
{rules_context}

ORIGINAL NON-COMPLIANT RESPONSE:
{original_response}

USER'S ORIGINAL QUESTION:
{user_question}

Please rewrite the response to be fully RBI-compliant while still
being helpful to the customer. Keep it concise and friendly."""

    model = GenerativeModel(
    GEMINI_MODEL,
    system_instruction=system_prompt
)

    rewritten = model.generate_content(
    user_prompt,
    generation_config={
        "temperature": 0.3,
        "max_output_tokens": 500
    }
)

    safe_response = rewritten.text

    return {
        "tool": "generate_safe_response",
        "action_taken": "REWRITTEN",
        "original_response": original_response,
        "safe_response": safe_response,
        "rules_fixed": [r["title"] for r in violated_rules]
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AGENT — LoanGuard
# ══════════════════════════════════════════════════════════════════════════════
def run_loanguard(
    user_question: str,
    advisor_response: str,
    verbose: bool = True
) -> dict:
    """
    LoanGuard main agent pipeline — fully traced in Arize Phoenix.
    Every step appears as a separate span in the trace dashboard.
    """

    if verbose:
        print("\n" + "═" * 60)
        print("🛡️  LOANGUARD COMPLIANCE AGENT — ACTIVATED")
        print("═" * 60)
        print(f"📩 User Question   : {user_question}")
        print(f"🤖 Advisor Response: {advisor_response[:80]}...")
        print("═" * 60)

    audit_trail = {
        "user_question": user_question,
        "original_advisor_response": advisor_response,
        "steps": {}
    }

    # ── Root span — wraps entire agent run ──────────────────────────────────
    with tracer.start_as_current_span("loanguard.compliance_check") as root_span:
        root_span.set_attribute("user.question", user_question)
        root_span.set_attribute("advisor.response", advisor_response[:500])

        # ── Step 1: Classify ─────────────────────────────────────────────────
        with tracer.start_as_current_span("step1.classify_query") as span1:
            if verbose:
                print("\n⚙️  Step 1: Classifying query...")

            step1 = tool_classify_query(user_question)
            audit_trail["steps"]["step1_classify"] = step1
            category = step1["category"]

            span1.set_attribute("query.category", category)
            span1.set_status(Status(StatusCode.OK))

            if verbose:
                print(f"   Category: {category.upper()}")

        # ── Step 2: Fetch Rules ──────────────────────────────────────────────
        with tracer.start_as_current_span("step2.fetch_rbi_rules") as span2:
            if verbose:
                print(f"\n⚙️  Step 2: Fetching RBI rules for '{category}'...")

            step2 = tool_fetch_rbi_rule(category)
            audit_trail["steps"]["step2_fetch_rules"] = step2

            span2.set_attribute("rules.category", category)
            span2.set_attribute("rules.count", step2["rules_found"])
            span2.set_status(Status(StatusCode.OK))

            if verbose:
                print(f"   Found {step2['rules_found']} relevant rule(s)")

        # ── Step 3: Evaluate ─────────────────────────────────────────────────
        with tracer.start_as_current_span("step3.evaluate_compliance") as span3:
            if verbose:
                print("\n⚙️  Step 3: Evaluating compliance...")

            step3 = tool_evaluate_compliance(user_question, advisor_response)
            audit_trail["steps"]["step3_evaluate"] = step3

            span3.set_attribute("compliance.is_compliant", step3["is_compliant"])
            span3.set_attribute("compliance.score", step3["confidence_score"])
            span3.set_attribute("compliance.action", step3["recommended_action"])
            span3.set_attribute("compliance.violations", len(step3["violated_rules"]))

            if not step3["is_compliant"]:
                span3.set_status(Status(StatusCode.ERROR, "Compliance violations detected"))
            else:
                span3.set_status(Status(StatusCode.OK))

            if verbose:
                print(f"   Compliant     : {step3['is_compliant']}")
                print(f"   Score         : {step3['confidence_score']}/100")
                print(f"   Action needed : {step3['recommended_action']}")
                if step3["violated_rules"]:
                    print(f"   Violations    : {len(step3['violated_rules'])}")
                    for v in step3["violated_rules"]:
                        print(f"     ⚠️  [{v['severity']}] {v['title']}")

        # ── Step 4: Generate Safe Response ───────────────────────────────────
        with tracer.start_as_current_span("step4.generate_safe_response") as span4:
            if verbose:
                print("\n⚙️  Step 4: Generating safe response...")

            if step3["is_compliant"]:
                step4 = {
                    "tool": "generate_safe_response",
                    "action_taken": "NONE",
                    "safe_response": advisor_response,
                    "message": "Response is compliant. No changes needed."
                }
            else:
                step4 = tool_generate_safe_response(
                    user_question=user_question,
                    original_response=advisor_response,
                    violated_rules=step3["violated_rules"],
                    recommended_action=step3["recommended_action"]
                )

            audit_trail["steps"]["step4_safe_response"] = step4
            audit_trail["final_response"] = step4["safe_response"]
            audit_trail["action_taken"] = step4["action_taken"]
            audit_trail["is_compliant"] = step3["is_compliant"]
            audit_trail["compliance_score"] = step3["confidence_score"]

            span4.set_attribute("action.taken", step4["action_taken"])
            span4.set_attribute("response.final", step4["safe_response"][:500])
            span4.set_status(Status(StatusCode.OK))

            if verbose:
                print(f"\n   Action taken: {step4['action_taken']}")

        # ── Root span attributes ─────────────────────────────────────────────
        root_span.set_attribute("final.action", step4["action_taken"])
        root_span.set_attribute("final.score", step3["confidence_score"])
        root_span.set_attribute("final.compliant", step3["is_compliant"])

    if verbose:
        print("\n" + "═" * 60)
        print("✅ LOANGUARD FINAL RESPONSE:")
        print("═" * 60)
        print(step4["safe_response"])
        print("═" * 60)
    import time
    time.sleep(2)
    
    return audit_trail


# ── Run test if executed directly ────────────────────────────────────────────
if __name__ == "__main__":

    # Test Case 1 — Non-compliant response
    result1 = run_loanguard(
        user_question="Am I eligible for a home loan at 8.5% interest?",
        advisor_response=(
            "Yes, you are eligible for a home loan! "
            "The interest rate is 8.5% and your EMI will be "
            "₹9,500 per month. You can apply right now and "
            "get instant approval."
        )
    )

    print("\n\n")

    # Test Case 2 — Already compliant response
    result2 = run_loanguard(
        user_question="What is the interest rate for your personal loan?",
        advisor_response=(
            "Our personal loan interest rate is 12% per annum "
            "on a reducing balance basis. The APR including all "
            "processing fees is 13.5% per annum. A Key Fact "
            "Statement will be shared before loan approval. "
            "Please note that eligibility is subject to credit "
            "score verification."
        )
    )