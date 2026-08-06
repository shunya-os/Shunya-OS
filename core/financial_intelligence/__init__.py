"""Universal Financial Intelligence — UCP-03.

The canonical capability for understanding how money flows through
human and organizational life.

Financial Intelligence is universal. It does not model accounting software,
ERP, or bookkeeping. These become compositions of Financial Intelligence.

Capabilities:
    - Money, Accounts, Wallets, Budgets
    - Cash Flow, Income, Expenses
    - Assets, Liabilities, Investments
    - Revenue, Profitability, Pricing
    - Quotations, Invoices, Payments, Refunds
    - Taxes, Forecasts
    - Financial Goals, Risks, Commitments
    - AI-powered insights, recommendations, health assessment
    - Reality integration via notify(notification)
    - Adaptive execution integration

Composes exclusively from frozen SHUNYA runtimes.
No Financial Runtime. No Accounting Runtime. No ERP Runtime.
"""

from core.financial_intelligence.engine import FinancialIntelligenceEngine
from core.financial_intelligence.models import (
    Account,
    AccountType,
    Budget,
    BudgetPeriod,
    CashFlowDirection,
    CashFlowSummary,
    FinancialGoal,
    FinancialGoalStatus,
    FinancialGoalType,
    FinancialInsight,
    FinancialProfile,
    FinancialRisk,
    Forecast,
    Invoice,
    InvoiceStatus,
    Money,
    Payment,
    PricingModel,
    Quotation,
    RiskLevel,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from core.financial_intelligence.runtime import FinancialIntelligenceRuntime

__all__ = [
    # Runtime
    "FinancialIntelligenceRuntime",
    "FinancialIntelligenceEngine",
    # Models
    "FinancialProfile",
    "Account",
    "Money",
    "Transaction",
    "Budget",
    "Invoice",
    "Payment",
    "Quotation",
    "CashFlowSummary",
    "FinancialGoal",
    "FinancialRisk",
    "Forecast",
    "FinancialInsight",
    # Enums
    "AccountType",
    "TransactionType",
    "TransactionStatus",
    "BudgetPeriod",
    "InvoiceStatus",
    "FinancialGoalType",
    "FinancialGoalStatus",
    "RiskLevel",
    "CashFlowDirection",
    "PricingModel",
]