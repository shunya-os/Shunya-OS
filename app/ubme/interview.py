"""Discovery Interview Engine — dynamic question-asking with confidence scoring and adaptive branching.

No fixed questionnaire. Questions adapt based on previous answers.
The engine continues asking until overall confidence exceeds a threshold.
"""

from __future__ import annotations

import re
from typing import Any

from app.ubme.ontology import ConfidenceLevel


# ── Question Types ────────────────────────────────────────────────────────


class QuestionType:
    """Categories of discovery questions."""
    BUSINESS = "business"           # What do you do?
    PRODUCT = "product"             # What do you sell?
    CUSTOMER = "customer"           # Who are your customers?
    SUPPLIER = "supplier"           # Who are your suppliers/partners?
    ENTITY = "entity"               # What entities exist?
    DOCUMENT = "document"           # What documents do you create?
    APPROVAL = "approval"           # What approvals exist?
    WORKFLOW = "workflow"           # How does work flow?
    METRIC = "metric"               # What do you measure?
    EVENT = "event"                 # What events matter?
    CONFIDENTIAL = "confidential"   # What's private?
    REPETITIVE = "repetitive"       # What tasks repeat?
    PAIN = "pain"                   # What causes delays?
    RELATIONSHIP = "relationship"   # How do things relate?
    ROLE = "role"                   # Who does what?


# ── Interview State ──────────────────────────────────────────────────────


class InterviewState:
    """Tracks the state of a discovery interview conversation."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.answers: dict[str, Any] = {}
        self.asked_questions: list[str] = []
        self.current_question_index: int = 0
        self.completed_categories: set[str] = set()
        self.confidence_scores: dict[str, float] = {}
        self.active_entity: str | None = None
        self.entity_context: dict[str, Any] = {}

    def record_answer(self, question_key: str, answer: Any) -> None:
        """Record an answer and mark the question as asked."""
        self.answers[question_key] = answer
        self.asked_questions.append(question_key)

    def get_answer(self, key: str, default: Any = None) -> Any:
        return self.answers.get(key, default)


# ── Question Definitions ─────────────────────────────────────────────────


class Question:
    """A single interview question with adaptive branching."""
    def __init__(
        self, key: str, text: str, category: str,
        follow_ups: list[str] | None = None,
        required: bool = False,
        options: list[str] | None = None,
        confidence_if_answered: float = 0.7,
        depends_on: str | None = None,
        entity_specific: bool = False,
    ):
        self.key = key
        self.text = text
        self.category = category
        self.follow_ups = follow_ups or []
        self.required = required
        self.options = options
        self.confidence_if_answered = confidence_if_answered
        self.depends_on = depends_on
        self.entity_specific = entity_specific

    def should_ask(self, state: InterviewState) -> bool:
        """Determine if this question should be asked based on state."""
        if self.key in state.asked_questions:
            return False
        if self.category in state.completed_categories:
            return False
        if self.depends_on and self.depends_on not in state.answers:
            return False
        return True


# ── Question Bank ─────────────────────────────────────────────────────────


BASE_QUESTIONS: list[Question] = [
    # ── Business Overview ──
    Question("business_description", "What does your business do? Describe it in a sentence or two.", QuestionType.BUSINESS, required=True, confidence_if_answered=0.85),
    Question("business_name", "What is the name of your business?", QuestionType.BUSINESS, required=True, confidence_if_answered=0.9),
    Question("industry", "What industry are you in?", QuestionType.BUSINESS, options=["Technology", "Healthcare", "Manufacturing", "Retail", "Services", "Construction", "Education", "Hospitality", "Entertainment", "Energy", "Other"], confidence_if_answered=0.7),

    # ── Customers ──
    Question("has_customers", "Who are your customers or clients?", QuestionType.CUSTOMER, required=True, confidence_if_answered=0.8),
    Question("customer_types", "Do you have different types of customers (e.g., individuals vs businesses)?", QuestionType.CUSTOMER, follow_ups=["customer_type_list"], depends_on="has_customers", confidence_if_answered=0.6),
    Question("customer_type_list", "What are the different types of customers you serve?", QuestionType.CUSTOMER, confidence_if_answered=0.7),

    # ── Products/Services ──
    Question("products", "What products or services do you provide?", QuestionType.PRODUCT, required=True, confidence_if_answered=0.85),
    Question("product_categories", "Do you categorize your products/services into different types?", QuestionType.PRODUCT, depends_on="products", confidence_if_answered=0.6),

    # ── Suppliers/Partners ──
    Question("has_suppliers", "Do you work with suppliers, vendors, or partners?", QuestionType.SUPPLIER, options=["Yes", "No"], confidence_if_answered=0.6),
    Question("supplier_types", "What kind of suppliers/vendors do you work with?", QuestionType.SUPPLIER, depends_on="has_suppliers", follow_ups=["supplier_agreements"], confidence_if_answered=0.7),

    # ── Core Entities ──
    Question("entities", "What are the main things you track in your business? For example: customers, projects, orders, invoices.", QuestionType.ENTITY, required=True, confidence_if_answered=0.8),
    Question("entity_details", "For each of those, what key information do you need to record? (e.g., for a customer: name, phone, email)", QuestionType.ENTITY, depends_on="entities", confidence_if_answered=0.65),
    Question("entity_statuses", "Do these entities go through status changes? (e.g., lead → active → inactive)", QuestionType.ENTITY, depends_on="entities", confidence_if_answered=0.55),

    # ── Documents ──
    Question("documents", "What documents or records do you create and manage? (e.g., invoices, contracts, reports)", QuestionType.DOCUMENT, confidence_if_answered=0.7),
    Question("document_approvals", "Do any documents require approval before they're final?", QuestionType.DOCUMENT, options=["Yes", "No"], depends_on="documents", confidence_if_answered=0.6),

    # ── Workflow ──
    Question("workflow_stages", "Walk me through a typical process from start to finish. What are the stages?", QuestionType.WORKFLOW, confidence_if_answered=0.75),
    Question("workflow_handoffs", "Who is involved at each stage? Are there handoffs or approvals?", QuestionType.WORKFLOW, depends_on="workflow_stages", confidence_if_answered=0.65),
    Question("workflow_delays", "Where do delays or bottlenecks happen in your process?", QuestionType.PAIN, confidence_if_answered=0.55),

    # ── Metrics ──
    Question("metrics", "What numbers or metrics do you look at every day to know how your business is doing?", QuestionType.METRIC, confidence_if_answered=0.7),
    Question("metric_detail", "What reports matter most to you? (daily, weekly, monthly)", QuestionType.METRIC, depends_on="metrics", confidence_if_answered=0.6),

    # ── Relationships ──
    Question("entity_relationships", "How do your main entities relate to each other? (e.g., a booking belongs to a customer, an invoice comes from a booking)", QuestionType.RELATIONSHIP, depends_on="entities", confidence_if_answered=0.7),

    # ── Automation ──
    Question("repetitive_tasks", "What tasks do you find yourself repeating regularly?", QuestionType.REPETITIVE, confidence_if_answered=0.65),
    Question("automation_candidates", "What would you most like to automate?", QuestionType.REPETITIVE, depends_on="repetitive_tasks", confidence_if_answered=0.6),

    # ── Roles & Permissions ──
    Question("roles", "Who works in your business? What are their roles?", QuestionType.ROLE, confidence_if_answered=0.6),
    Question("confidential_info", "Is any of your information confidential or restricted?", QuestionType.CONFIDENTIAL, options=["Yes", "No"], depends_on="entities", confidence_if_answered=0.5),
]


# ── Dynamic Entity Questions ─────────────────────────────────────────────


def generate_entity_questions(entity_name: str, entity_type_hint: str = "") -> list[Question]:
    """Generate dynamic questions about a specific discovered entity."""
    questions = []
    key = entity_name.lower().replace(" ", "_")
    questions.append(Question(
        f"{key}_fields",
        f"What information do you need to track for {entity_name}? (e.g., name, date, amount, status)",
        QuestionType.ENTITY,
        entity_specific=True,
        confidence_if_answered=0.7,
    ))
    questions.append(Question(
        f"{key}_statuses",
        f"What statuses or stages does {entity_name} go through?",
        QuestionType.WORKFLOW,
        entity_specific=True,
        confidence_if_answered=0.65,
    ))
    questions.append(Question(
        f"{key}_relationships",
        f"What is {entity_name} connected to? (e.g., a booking is for a customer, an invoice is for a booking)",
        QuestionType.RELATIONSHIP,
        entity_specific=True,
        confidence_if_answered=0.65,
    ))
    return questions


# ── Interview Engine ──────────────────────────────────────────────────────


class InterviewEngine:
    """Drives a dynamic discovery conversation with the founder."""

    def __init__(self, session_id: str):
        self.state = InterviewState(session_id)
        self._question_pool = list(BASE_QUESTIONS)
        self._current_entity_questions: list[Question] = []

    def get_next_question(self) -> Question | None:
        """Get the next question to ask based on state and confidence."""
        # Check entity-specific questions first
        if self._current_entity_questions:
            q = self._current_entity_questions.pop(0)
            return q

        # Check dynamic entity questions if entities were discovered
        entities_answer = self.state.get_answer("entities")
        if entities_answer and not self.state.get_answer("_entity_questions_generated"):
            parsed = self._parse_entity_list(entities_answer)
            if parsed:
                for entity in parsed:
                    self._current_entity_questions.extend(generate_entity_questions(entity))
                self.state.answers["_entity_questions_generated"] = True
            if self._current_entity_questions:
                q = self._current_entity_questions.pop(0)
                return q

        # Find next unanswered question
        for question in self._question_pool:
            if question.should_ask(self.state):
                return question

        # If confidence is low, generate follow-up
        if self._get_average_confidence() < 0.6:
            return self._generate_follow_up()

        return None

    def answer_question(self, question_key: str, answer: Any) -> None:
        """Record an answer and update confidence scores."""
        self.state.record_answer(question_key, answer)
        # Update confidence for this category
        for q in self._question_pool:
            if q.key == question_key:
                self.state.confidence_scores[question_key] = q.confidence_if_answered
                break
        self.state.confidence_scores[question_key] = 0.7  # default

    def get_answers(self) -> dict[str, Any]:
        """Get all recorded answers."""
        return dict(self.state.answers)

    def is_complete(self) -> bool:
        """Check if confidence is sufficient to generate a module."""
        return self._get_average_confidence() >= 0.75

    def _get_average_confidence(self) -> float:
        scores = list(self.state.confidence_scores.values())
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _parse_entity_list(self, text: str) -> list[str]:
        """Parse a free-text answer into a list of entities."""
        # Split on commas, 'and', bullet points, newlines
        parts = re.split(r'[,;、\n•\-]|\s+and\s+', text)
        entities = []
        for p in parts:
            p = p.strip().lower()
            if p and len(p) > 2:
                # Normalize: remove trailing "s" plural, articles, whitespace
                p = p.rstrip('s')
                p = p.strip('. ')
                if p:
                    entities.append(p.capitalize())
        return entities

    def _generate_follow_up(self) -> Question:
        """Generate an adaptive follow-up question when confidence is low."""
        unanswered = []
        for q in self._question_pool:
            if q.required and q.key not in self.state.asked_questions:
                unanswered.append(q)
        if unanswered:
            return unanswered[0]
        # Generic follow-up
        return Question(
            "follow_up", "Is there anything else about your business you think I should understand?",
            QuestionType.BUSINESS, confidence_if_answered=0.5,
        )