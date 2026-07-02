"""
Tool registry for centralized tool mgmt and executn
"""
from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import asyncio
import time
from datetime import datetime
from app.utils.logger import get_logger
from app.adapters.backend_adapter import get_backend_adapter

logger = get_logger(__name__)

class ToolParameters(BaseModel):
    """Parameter definition for a tool"""
    name: str
    type: str  # "string", "number", "boolean", "object", "array" etc
    description: str
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None  # For fixed choices

class Tool(BaseModel):
    """Complete tool definition with handler"""
    name: str
    description: str
    parameters: List[ToolParameters] = Field(default_factory=list)

    #handler function not serialized
    handler: Optional[Callable] = Field(default=None, exclude=True)

    #Feature flags
    enabled: bool = True
    mvp_ready: bool = True
    
    #metadata
    category: str="general" #"invoice", "payment", "analytics", etc
    requires_confirmation: bool = False
    estimated_time_seconds: int = 2
    
    class Config:
        arbitrary_types_allowed = True

class ToolExecutionResult(BaseModel):
    """Result of tool execution"""
    success: bool
    tool_name : str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None

class ToolRegistry:
    """Central registry for all agent tools
    Manages tool registration, validation, execution
    """
    _alert_thresholds: Dict[str, List[Dict[str, Any]]] = {}

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        logger.info("tool_registry_initialized")

    def register_tool(self, tool: Tool):
        """Register a tool"""
        if tool.name in self._tools :
            logger.warning("tool_already_registered", tool = tool.name)

        self._tools[tool.name ] = tool
        logger.debug("tool_registered", tool=tool.name, category=tool.category)

    def register_tools(self, tools:List[Tool]):
        """Register multiple tools"""
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(tool_name)

    def get_enabled_tools(self) -> List[Tool]:
        """Get all enabled tools"""
        return [t for t in self._tools.values() if t.enabled]
    
    def get_mvp_tools(self) -> List[Tool]:
        """Get MVP-ready enabled tools"""
        return [t for t in self._tools.values() if t.mvp_ready and t.enabled]
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get tools by category"""
        return [t for t in self._tools.values() if t.category == category and t.enabled]
    
    def validate_parameters(
        self,
        tool_name:str,
        parameters: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate parameters for a tool
        
        Returns:
            (isValid, error_message)
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"
        
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in (parameters or {}):
                return False, f"Missing required parameter: '{param.name}'"
            
        # Type validations
        for param in tool.parameters:
            if param.name in (parameters or {}):
                value = parameters[param.name]

                # enum validation
                if param.enum and value not in param.enum:
                    return False, f"Parameter '{param.name}' must be one of {param.enum}"
                
        return True, None
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Execute a tool with given parameters
        
        Args: 
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            context: Additional context like user_id, org_id, etc
        Returns 
            ToolExecutionResult
        """
        start_time = time.time()

        #Get tool
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error=f"Tool {tool_name} not found"
            )
        
        #Check if enabled
        if not tool.enabled:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error=f"Tool '{tool_name} is disabled"
            )
        
        #validate parameters
        is_valid, error_msg = self.validate_parameters(tool_name, parameters)
        if not is_valid:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error=error_msg
            )

        # Execute handler
        if not tool.handler:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error=f"Tool '{tool_name}' has no handler function"
            )
        
        try:
            #call handler(supports both sync and async)
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(parameters, context) 
            else:
                result = tool.handler(parameters, context)

            execution_time = int((time.time() - start_time) * 1000)

            logger.info(
                "tool_executed",
                tool=tool_name,
                success=True,
                execution_time_ms=execution_time
            )

            return ToolExecutionResult(
                success=True,
                tool_name=tool_name,

                result=result,
                execution_time_ms = execution_time
            )
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)

            logger.error(
                "tool_execution_failed",
                tool=tool_name,
                error=str(e),
                execution_time_ms=execution_time
            )
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                error=str(e),
                execution_time_ms=execution_time
            )

    def list_tools(self, enabled_only: bool = True) -> List[str]:
        """List all tool names"""
        if enabled_only:
            return [name for name, tool in self._tools.items() if tool.enabled]
        return list(self._tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get human-readable tool info"""
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in tool.parameters
            ],
            "enabled": tool.enabled,
            "mvp_ready": tool.mvp_ready,
            "requires_confirmation":tool.requires_confirmation,
            "estimate_time_seconds": tool.estimated_time_seconds
        }

    def register_financial_tools(self):
        """Register financial analysis, benchmark, and alert tools"""
        tools = [
            Tool(
                name="analyze_cash_flow",
                description="Analyze cash flow patterns and predict shortfalls",
                category="financial_analysis",
                mvp_ready=True,
                parameters=[
                    ToolParameters(name="period", type="string", description="Analysis period (30d/90d/1y)", required=False, default="90d")
                ],
                handler=self._analyze_cash_flow
            ),
            Tool(
                name="calculate_profit_margin",
                description="Calculate gross and net profit margins by period",
                category="financial_analysis",
                mvp_ready=True,
                parameters=[
                    ToolParameters(name="period", type="string", description="Period to analyze", required=False, default="MONTH")
                ],
                handler=self._calculate_profit_margin
            ),
            Tool(
                name="benchmark_against_industry",
                description="Compare financial metrics against industry benchmarks",
                category="benchmark",
                mvp_ready=False,
                parameters=[
                    ToolParameters(name="industry", type="string", description="Industry vertical", required=False, default="SaaS")
                ],
                handler=self._benchmark_against_industry
            ),
            Tool(
                name="detect_anomalies",
                description="Detect unusual patterns in transactions or invoices",
                category="alert",
                mvp_ready=True,
                parameters=[],
                handler=self._detect_anomalies
            ),
            Tool(
                name="set_alert_threshold",
                description="Configure alert thresholds for cash balance, overdue invoices, etc.",
                category="alert",
                mvp_ready=True,
                parameters=[
                    ToolParameters(name="metric", type="string", description="Metric to alert on", required=True),
                    ToolParameters(name="threshold", type="number", description="Threshold value", required=True),
                    ToolParameters(name="operator", type="string", description="Comparison operator (lt/gt/eq)", required=False, default="lt")
                ],
                handler=self._set_alert_threshold
            ),
            Tool(
                name="forecast_revenue",
                description="Generate revenue forecast based on historical trends",
                category="financial_analysis",
                mvp_ready=True,
                parameters=[
                    ToolParameters(name="months_ahead", type="number", description="Forecast horizon in months", required=False, default=3)
                ],
                handler=self._forecast_revenue
            ),
            Tool(
                name="analyze_customer_lifetime_value",
                description="Calculate customer lifetime value and retention metrics",
                category="financial_analysis",
                mvp_ready=False,
                parameters=[],
                handler=self._analyze_customer_lifetime_value
            ),
        ]
        self.register_tools(tools)

    @staticmethod
    def _items(data: Any) -> List[Dict[str, Any]]:
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return data["data"]
            if isinstance(data.get("data"), dict):
                return ToolRegistry._items(data["data"])
            if isinstance(data.get("content"), list):
                return data["content"]
            for key in ("clients", "invoices", "transactions", "items", "results"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    @staticmethod
    async def _load_moneyops_data(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        context = context or {}
        org_id = context.get("org_id")
        user_id = context.get("user_id")
        if not org_id:
            raise ValueError("org_id is required in tool execution context")

        backend = get_backend_adapter()
        invoices_resp, transactions_resp, summary_resp = await asyncio.gather(
            backend.get_invoices(org_id=org_id, user_id=user_id, limit=500),
            backend._request("GET", "/api/transactions", params={"page": 0, "size": 500}, org_id=org_id, user_id=user_id),
            backend.get_financial_summary(org_id=org_id, user_id=user_id),
            return_exceptions=True,
        )

        invoices = []
        transactions = []
        summary = {}
        if not isinstance(invoices_resp, Exception) and invoices_resp.success:
            invoices = ToolRegistry._items(invoices_resp.data)
        if not isinstance(transactions_resp, Exception) and transactions_resp.success:
            transactions = ToolRegistry._items(transactions_resp.data)
        if not isinstance(summary_resp, Exception) and summary_resp.success and isinstance(summary_resp.data, dict):
            summary = summary_resp.data.get("data", summary_resp.data)

        return {"org_id": org_id, "user_id": user_id, "invoices": invoices, "transactions": transactions, "summary": summary}

    @staticmethod
    def _amount(item: Dict[str, Any]) -> float:
        for key in ("amount", "totalAmount", "balanceDue", "paidAmount"):
            try:
                if item.get(key) is not None:
                    return float(item.get(key) or 0)
            except (TypeError, ValueError):
                continue
        return 0.0

    async def _analyze_cash_flow(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = await self._load_moneyops_data(context)
        transactions = data["transactions"]
        income = sum(self._amount(t) for t in transactions if str(t.get("type", "")).upper() in {"INCOME", "CREDIT"})
        expense = sum(self._amount(t) for t in transactions if str(t.get("type", "")).upper() in {"EXPENSE", "DEBIT"})
        net = income - expense
        burn_rate = expense / 30 if expense else 0
        runway_days = round(max(net, 0) / burn_rate, 1) if burn_rate else None
        return {
            "status": "computed",
            "period": params.get("period", "90d"),
            "cash_in": income,
            "cash_out": expense,
            "net_cash_flow": net,
            "daily_burn_rate": burn_rate,
            "estimated_runway_days": runway_days,
            "insight": "Positive cash flow" if net >= 0 else "Cash outflow exceeds inflow; prioritize collections and expense review.",
        }

    async def _calculate_profit_margin(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = await self._load_moneyops_data(context)
        summary = data["summary"]
        income = float(summary.get("totalIncome") or summary.get("revenue") or 0)
        expense = float(summary.get("totalExpense") or summary.get("expenses") or 0)
        profit = float(summary.get("netProfit") or (income - expense))
        margin = (profit / income * 100) if income else 0
        return {
            "status": "computed",
            "period": params.get("period", "MONTH"),
            "revenue": income,
            "expenses": expense,
            "net_profit": profit,
            "net_margin_percent": round(margin, 2),
        }

    async def _forecast_revenue(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = await self._load_moneyops_data(context)
        monthly: Dict[str, float] = {}
        for inv in data["invoices"]:
            date = str(inv.get("createdAt") or inv.get("invoiceDate") or "")[:7]
            if date:
                monthly[date] = monthly.get(date, 0.0) + float(inv.get("totalAmount") or 0)
        months = sorted(monthly)
        recent = [monthly[m] for m in months[-3:]]
        baseline = sum(recent) / len(recent) if recent else 0
        return {
            "status": "computed",
            "months_ahead": int(params.get("months_ahead", 3) or 3),
            "monthly_revenue": monthly,
            "baseline_monthly_forecast": baseline,
            "confidence": "medium" if len(recent) >= 3 else "low",
        }

    async def _detect_anomalies(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = await self._load_moneyops_data(context)
        transactions = data["transactions"]
        amounts = [self._amount(t) for t in transactions if self._amount(t) > 0]
        if not amounts:
            return {"status": "computed", "anomalies": [], "message": "No transaction data available."}
        avg = sum(amounts) / len(amounts)
        threshold = avg * 3
        anomalies = [t for t in transactions if self._amount(t) > threshold]
        return {
            "status": "computed",
            "average_amount": avg,
            "threshold": threshold,
            "anomalies": anomalies[:10],
            "count": len(anomalies),
        }

    async def _set_alert_threshold(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        metric = params["metric"]
        threshold = params["threshold"]
        operator = params.get("operator", "lt")
        org_key = context.get("org_id", "default")
        if org_key not in self._alert_thresholds:
            self._alert_thresholds[org_key] = []
        self._alert_thresholds[org_key].append({
            "metric": metric,
            "threshold": threshold,
            "operator": operator,
            "created_at": datetime.utcnow().isoformat(),
        })
        return {
            "status": "configured",
            "metric": metric,
            "threshold": threshold,
            "operator": operator,
            "scope": {"org_id": context.get("org_id"), "user_id": context.get("user_id")},
            "active_count": len(self._alert_thresholds[org_key]),
            "message": f"Alert threshold set for {metric} ({operator} {threshold}). Active for this session.",
        }

    async def _benchmark_against_industry(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        margin = await self._calculate_profit_margin(params, context)
        industry = params.get("industry", "SaaS")
        return {
            "status": "computed",
            "industry": industry,
            "metrics": margin,
            "note": "Self-comparison only — your current margin vs prior periods. External industry benchmarks can be configured by connecting a benchmark data source.",
        }

    async def _analyze_customer_lifetime_value(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = await self._load_moneyops_data(context)
        revenue_by_client: Dict[str, float] = {}
        for inv in data["invoices"]:
            client = inv.get("clientName") or inv.get("client", "Unknown")
            revenue_by_client[client] = revenue_by_client.get(client, 0.0) + float(inv.get("totalAmount") or 0)
        values = list(revenue_by_client.values())
        avg_ltv = sum(values) / len(values) if values else 0
        return {
            "status": "computed",
            "average_lifetime_value": avg_ltv,
            "top_clients": sorted(
                [{"client": k, "lifetime_value": v} for k, v in revenue_by_client.items()],
                key=lambda item: item["lifetime_value"],
                reverse=True,
            )[:10],
        }
    
#Global Singleton
tool_registry = ToolRegistry()
tool_registry.register_financial_tools()
