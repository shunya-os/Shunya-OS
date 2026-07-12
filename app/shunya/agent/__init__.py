"""Shunya OS — Bird AI Tool Registry.

Every tool Bird AI can execute registers here.
Pattern: register → parse intent → select tool → check permissions → execute → log → return
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, Any, Union
from enum import Enum
import logging, json, datetime

logger = logging.getLogger('shunya.tools')

class ToolCategory(Enum):
    CUSTOMER = "customer"
    QUOTE = "quote"  
    BOOKING = "booking"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    DOCUMENT = "document"
    KNOWLEDGE = "knowledge"
    TRAVEL_INTEL = "travel_intel"
    WORKFLOW = "workflow"
    ADMIN = "admin"
    ANALYTICS = "analytics"

class ToolPermission(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

@dataclass
class ToolDef:
    id: str
    name: str
    description: str
    category: ToolCategory
    permission: ToolPermission
    tier: int  # 1=instant, 2=confirm, 3=multi-step
    handler: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)

@dataclass
class Intent:
    action: str = ""
    entity_type: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""
    
@dataclass
class ToolResult:
    success: bool
    message: str = ""
    data: Any = None
    target_url: Optional[str] = None
    error: Optional[str] = None

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDef] = {}
        
    def register(self, tool: ToolDef):
        self._tools[tool.id] = tool
        logger.info(f"Tool registered: {tool.id} ({tool.category.value})")
        
    def get(self, tool_id: str) -> Optional[ToolDef]:
        return self._tools.get(tool_id)
    
    def all(self) -> List[ToolDef]:
        return list(self._tools.values())
    
    def by_category(self, cat: ToolCategory) -> List[ToolDef]:
        return [t for t in self._tools.values() if t.category == cat]
    
    def by_tier(self, tier: int) -> List[ToolDef]:
        return [t for t in self._tools.values() if t.tier == tier]
    
    def match_intent(self, intent: Intent) -> List[ToolDef]:
        """Find tools that match the intent. Returns sorted by relevance."""
        candidates = []
        query = intent.action.lower()
        entity = (intent.entity_type or '').lower()
        
        for tool in self._tools.values():
            score = 0
            # Match action in tool name/description
            if query in tool.name.lower() or query in tool.description.lower():
                score += 3
            if query in tool.id.lower():
                score += 5
            # Match entity type
            if entity and entity in tool.id.lower():
                score += 2
            if entity and entity in tool.description.lower():
                score += 1
            if score > 0:
                candidates.append((score, tool))
        
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in candidates]
    
    def count(self) -> int:
        return len(self._tools)

# Global singleton
registry = ToolRegistry()

def register_tool(tool: ToolDef):
    registry.register(tool)

# ── Intent Parser ──

COMMON_ACTIONS = {
    'create': ['create', 'make', 'add', 'new', 'build', 'generate', 'register'],
    'search': ['search', 'find', 'lookup', 'look up', 'show', 'list', 'get', 'tell'],
    'send': ['send', 'share', 'message', 'email', 'text', 'whatsapp'],
    'update': ['update', 'change', 'modify', 'edit', 'set'],
    'delete': ['delete', 'remove', 'cancel', 'archive'],
    'analyze': ['analyze', 'analytics', 'report', 'dashboard', 'stats'],
}

ENTITY_TYPES = {
    'lead': ['lead', 'leads', 'customer', 'client', 'inquiry', 'enquiry'],
    'booking': ['booking', 'bookings', 'trip', 'reservation'],
    'invoice': ['invoice', 'invoices', 'bill', 'receipt'],
    'quote': ['quote', 'quotes', 'proposal', 'estimate', 'itinerary'],
    'payment': ['payment', 'payments', 'transaction'],
    'feedback': ['feedback', 'review'],
    'campaign': ['campaign', 'campaigns', 'offer', 'promotion'],
    'ticket': ['ticket', 'tickets', 'support', 'complaint'],
}

def parse_intent(text: str) -> Intent:
    """Parse natural language into structured intent."""
    text_lower = text.lower().strip()
    intent = Intent(raw_text=text)
    
    # Detect action
    best_action = None
    best_score = 0
    for action, keywords in COMMON_ACTIONS.items():
        for kw in keywords:
            if text_lower.startswith(kw) or f" {kw} " in f" {text_lower} ":
                score = len(kw)
                if score > best_score:
                    best_score = score
                    best_action = action
    
    if best_action:
        intent.action = best_action
        intent.confidence = min(1.0, best_score / 10)
    
    # Detect entity type
    best_entity = None
    best_entity_score = 0
    for etype, aliases in ENTITY_TYPES.items():
        for alias in aliases:
            if alias in text_lower:
                score = len(alias)
                if score > best_entity_score:
                    best_entity_score = score
                    best_entity = etype
    
    if best_entity:
        intent.entity_type = best_entity
    
    # Extract parameters from text
    intent.parameters['raw'] = text
    
    # Simple name extraction (after "for" or "called")
    for prefix in [' for ', ' called ', ' named ', " 's "]:
        if prefix in text_lower:
            parts = text.split(prefix, 1)
            if len(parts) > 1:
                name = parts[1].strip().rstrip('.').split(',')[0].strip()
                if name:
                    intent.parameters['name'] = name
    
    # Number extraction
    import re
    numbers = re.findall(r'(\d+)', text)
    if numbers:
        intent.parameters['numbers'] = [int(n) for n in numbers]
    
    return intent

# ── Agent Loop ──

class Agent:
    """The Bird AI agent loop: intent → tool → execute → observe → respond."""
    
    def __init__(self, tenant_id: int, user_id: int, user_role: str = "staff"):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_role = user_role
        self.history: List[Dict] = []
        
    def process(self, text: str) -> ToolResult:
        """Process a natural language request."""
        intent = parse_intent(text)
        self.history.append({"role": "user", "intent": intent})
        
        # Find matching tools
        matches = registry.match_intent(intent)
        
        if not matches:
            # Try web search as fallback
            web_tool = registry.get("search_web")
            if web_tool:
                return web_tool.handler({"query": text})
            return ToolResult(False, "I don't understand. Try: create lead, search web, send invoice, etc.")
        
        # Pick best match
        tool = matches[0]
        
        # Check permission
        if not self._check_permission(tool):
            return ToolResult(False, f"Sorry, you don't have permission to use {tool.name}.")
        
        # Execute
        try:
            result = tool.handler(intent.parameters, self)
            self.history.append({"role": "assistant", "tool": tool.id, "result": result.success})
            return result
        except Exception as e:
            logger.error(f"Tool {tool.id} failed: {e}")
            return ToolResult(False, f"Sorry, something went wrong: {str(e)}")
    
    def _check_permission(self, tool: ToolDef) -> bool:
        if self.user_role == "admin":
            return True
        if tool.permission == ToolPermission.ADMIN:
            return False
        if tool.permission == ToolPermission.WRITE and self.user_role == "readonly":
            return False
        return True