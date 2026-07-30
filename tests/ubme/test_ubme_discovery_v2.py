"""Pytest tests for UBDSE — Business Discovery v2 pipeline."""

import pytest
from app.ubme.ontology import (
    BusinessOntology, EntityDef, EntityField, EntityRelationship, InferredMetric,
    ConfidenceLevel, RelationshipCardinality, OntologyEntityType,
)
from app.ubme.ontology_gen import generate_ontology
from app.ubme.ontology_to_module import ontology_to_module
from app.ubme.business_graph import BusinessGraph, register_graph
from app.ubme.interview import InterviewEngine, Question
from app.ubme import engine as ubme_engine
from app.ubme.models import ModuleDef


class TestOntologyModel:
    def test_entity_creation(self):
        e = EntityDef(key="customer", name="Customer")
        assert e.key == "customer"
        assert e.plural_name == "Customers"
        assert e.entity_type == OntologyEntityType.PRIMARY

    def test_entity_serialization(self):
        e = EntityDef(key="invoice", name="Invoice", fields=[
            EntityField(key="amount", label="Amount", field_type="currency"),
        ])
        d = e.to_dict()
        assert d["key"] == "invoice"
        e2 = EntityDef.from_dict(d)
        assert e2.key == "invoice"
        assert len(e2.fields) == 1

    def test_relationship_creation(self):
        r = EntityRelationship(source_entity="customer", target_entity="invoice",
                                cardinality=RelationshipCardinality.ONE_TO_MANY)
        assert r.cardinality == RelationshipCardinality.ONE_TO_MANY

    def test_ontology_confidence(self):
        o = BusinessOntology(key="test", name="Test", entities=[
            EntityDef(key="a", name="A", confidence=ConfidenceLevel.HIGH),
            EntityDef(key="b", name="B", confidence=ConfidenceLevel.MEDIUM),
        ])
        assert 0.7 < o.overall_confidence() < 0.95

    def test_ontology_get_entity(self):
        o = BusinessOntology(key="test", name="Test", entities=[
            EntityDef(key="widget", name="Widget"),
        ])
        assert o.get_entity("widget") is not None
        assert o.get_entity("nonexistent") is None


class TestInterviewEngine:
    def test_engine_initialization(self):
        engine = InterviewEngine("test_session")
        assert engine.state.session_id == "test_session"
        assert engine.state.current_question_index == 0

    def test_engine_asks_questions(self):
        engine = InterviewEngine("test_session")
        q = engine.get_next_question()
        assert q is not None
        assert q.key == "business_description"

    def test_engine_records_answers(self):
        engine = InterviewEngine("test_session")
        engine.answer_question("business_name", "My Business")
        assert engine.state.get_answer("business_name") == "My Business"

    def test_engine_tracks_completion(self):
        engine = InterviewEngine("test_session")
        keys = ["business_description", "business_name", "has_customers", "products", "entities"]
        for k in keys:
            engine.answer_question(k, "test")
        assert not engine.is_complete()
        # Answer more to increase confidence
        for _ in range(10):
            q = engine.get_next_question()
            if q:
                engine.answer_question(q.key, "test answer")

    def test_question_should_ask(self):
        q = Question("test_q", "Test?", "business", depends_on="prereq")
        state = InterviewEngine("test").state
        assert q.should_ask(state) is False  # missing prereq
        state.record_answer("prereq", "done")
        assert q.should_ask(state) is True


class TestOntologyGenerator:
    def test_veterinary_ontology(self):
        answers = {
            'business_name': 'Happy Paws Vet',
            'has_customers': 'Pet owners',
            'products': 'Vaccinations, surgeries',
            'entities': 'Patients, Appointments, Treatments, Prescriptions',
            'entity_relationships': 'an appointment is for a patient, a prescription is for a patient',
            'workflow_stages': 'Check-in, Examination, Treatment, Discharge',
            'metrics': 'Patients per day',
        }
        o = generate_ontology(answers)
        assert len(o.entities) >= 4
        assert o.get_entity("patient") is not None
        assert o.get_entity("appointment") is not None
        assert len(o.relationships) >= 3

    def test_film_studio_ontology(self):
        answers = {
            'business_name': 'Aurora Films',
            'has_customers': 'Streaming platforms',
            'products': 'Feature films, documentaries',
            'entities': 'Projects, Contracts, Budgets, Crew, Cast',
            'entity_relationships': 'a contract is for a project',
            'workflow_stages': 'Development, Pre-Production, Production, Post-Production, Release',
            'metrics': 'Budget utilization, production days',
        }
        o = generate_ontology(answers)
        assert len(o.entities) >= 5
        assert o.get_entity("project") is not None

    def test_energy_epc_ontology(self):
        answers = {
            'business_name': 'GreenGrid EPC',
            'has_customers': 'Utility companies',
            'entities': 'Projects, Contracts, Suppliers, Equipment, Work Orders, Sites',
            'entity_relationships': 'a contract is for a project, equipment belongs to a project',
            'workflow_stages': 'Feasibility, Design, Procurement, Construction, Commissioning',
            'metrics': 'Project progress, budget variance',
        }
        o = generate_ontology(answers)
        assert len(o.entities) >= 5
        assert len(o.relationships) >= 3


class TestOntologyToModule:
    def test_generates_valid_module(self):
        o = BusinessOntology(key="test", name="Test Co", entities=[
            EntityDef(key="customer", name="Customer", fields=[
                EntityField(key="name", label="Name", field_type="text"),
                EntityField(key="email", label="Email", field_type="email"),
            ]),
            EntityDef(key="invoice", name="Invoice", fields=[
                EntityField(key="total", label="Total", field_type="currency"),
            ], lifecycle=[
                type('LS', (), {'key': 'draft', 'label': 'Draft'}),
                type('LS', (), {'key': 'sent', 'label': 'Sent'}),
                type('LS', (), {'key': 'paid', 'label': 'Paid'}),
            ]),
        ], relationships=[
            EntityRelationship(source_entity="invoice", target_entity="customer",
                               cardinality=RelationshipCardinality.MANY_TO_ONE),
        ])
        # Replace lifecycle list items with proper LifecycleStage objects
        from app.ubme.ontology import LifecycleStage, LifecycleStageType
        o.entities[1].lifecycle = [
            LifecycleStage(key="draft", label="Draft", stage_type=LifecycleStageType.INITIAL),
            LifecycleStage(key="sent", label="Sent", stage_type=LifecycleStageType.INTERMEDIATE),
            LifecycleStage(key="paid", label="Paid", stage_type=LifecycleStageType.FINAL),
        ]
        
        mod = ontology_to_module(o)
        assert isinstance(mod, ModuleDef)
        assert len(mod.object_types) == 2
        assert len(mod.workflows) == 1
        assert len(mod.dashboard_cards or []) >= 1

    def test_workflow_generated_from_lifecycle(self):
        from app.ubme.ontology import LifecycleStage, LifecycleStageType
        o = BusinessOntology(key="t", name="T", entities=[
            EntityDef(key="order", name="Order", lifecycle=[
                LifecycleStage(key="pending", label="Pending", stage_type=LifecycleStageType.INITIAL),
                LifecycleStage(key="shipped", label="Shipped", stage_type=LifecycleStageType.INTERMEDIATE),
                LifecycleStage(key="delivered", label="Delivered", stage_type=LifecycleStageType.FINAL),
            ]),
        ])
        mod = ontology_to_module(o)
        assert len(mod.workflows) == 1
        wf = mod.workflows[0]
        assert wf.default_state == "pending"
        assert len(wf.transitions) == 2


class TestBusinessGraph:
    def test_graph_creation(self):
        o = BusinessOntology(key="t", name="T", entities=[
            EntityDef(key="a", name="A"),
            EntityDef(key="b", name="B"),
        ], relationships=[
            EntityRelationship(source_entity="a", target_entity="b",
                               cardinality=RelationshipCardinality.ONE_TO_MANY),
        ])
        g = BusinessGraph(o)
        g.build()
        assert len(g.get_neighbors("a")) == 1
        assert g.get_neighbors("a")[0]["target"] == "b"

    def test_graph_path_finding(self):
        o = BusinessOntology(key="t", name="T", entities=[
            EntityDef(key="a", name="A"), EntityDef(key="b", name="B"),
            EntityDef(key="c", name="C"),
        ], relationships=[
            EntityRelationship(source_entity="a", target_entity="b"),
            EntityRelationship(source_entity="b", target_entity="c"),
        ])
        g = BusinessGraph(o)
        g.build()
        path = g.get_path("a", "c")
        assert path == ["a", "b", "c"]
        assert g.get_path("c", "a") == ["c", "b", "a"]

    def test_graph_search(self):
        o = BusinessOntology(key="t", name="T", entities=[
            EntityDef(key="customer", name="Customer", synonyms=["client", "buyer"]),
            EntityDef(key="invoice", name="Invoice"),
        ])
        g = BusinessGraph(o)
        g.build()
        results = g.search("client")
        assert len(results) >= 1
        assert results[0]["key"] == "customer"


class TestEndToEnd:
    def test_full_discovery_pipeline(self):
        ubme_engine.reset()
        answers = {
            'business_name': 'Test Business',
            'has_customers': 'Companies',
            'products': 'Widgets',
            'entities': 'Orders, Invoices, Customers',
            'entity_relationships': 'an invoice is for an order',
            'workflow_stages': 'Created, Shipped, Delivered',
            'metrics': 'Revenue, orders per day',
        }
        o = generate_ontology(answers)
        assert len(o.entities) >= 3
        mod = ontology_to_module(o)
        ubme_engine.register_module(mod)
        assert ubme_engine.get_module(mod.key) is not None
        g = register_graph(mod.key, o)
        assert len(g.get_neighbors("invoice")) >= 1