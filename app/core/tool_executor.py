import httpx
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute_tool(self, tool_config: Dict[str, Any], parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool based on its configuration"""
        tool_type = tool_config.get("type")
        configuration = tool_config.get("configuration", {})
        
        try:
            if tool_type == "api":
                return await self._execute_api_tool(configuration, parameters)
            elif tool_type == "function":
                return await self._execute_function_tool(configuration, parameters)
            elif tool_type == "webhook":
                return await self._execute_webhook_tool(configuration, parameters)
            else:
                raise ValueError(f"Unsupported tool type: {tool_type}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_config.get('name')}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_api_tool(self, configuration: Dict[str, Any], parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an API tool"""
        endpoint = configuration.get("endpoint")
        method = configuration.get("method", "GET")
        headers = configuration.get("headers", {})
        auth = configuration.get("auth")
        
        if not endpoint:
            raise ValueError("API tool missing endpoint configuration")
        
        # Merge parameters with configuration
        request_data = {**(configuration.get("default_params", {})), **(parameters or {})}
        
        try:
            if method.upper() == "GET":
                response = await self.http_client.get(
                    endpoint,
                    params=request_data,
                    headers=headers,
                    auth=auth
                )
            elif method.upper() == "POST":
                response = await self.http_client.post(
                    endpoint,
                    json=request_data,
                    headers=headers,
                    auth=auth
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "status_code": e.response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_function_tool(self, configuration: Dict[str, Any], parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a function tool"""
        function_name = configuration.get("function_name")
        
        if not function_name:
            raise ValueError("Function tool missing function name")
        
        # Get the function from the registry
        function_registry = FunctionRegistry()
        func = function_registry.get_function(function_name)
        
        if not func:
            return {
                "success": False,
                "error": f"Function '{function_name}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(**(parameters or {}))
            else:
                result = func(**(parameters or {}))
            
            return {
                "success": True,
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_webhook_tool(self, configuration: Dict[str, Any], parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a webhook tool"""
        webhook_url = configuration.get("webhook_url")
        method = configuration.get("method", "POST")
        headers = configuration.get("headers", {})
        
        if not webhook_url:
            raise ValueError("Webhook tool missing webhook_url configuration")
        
        # Prepare payload
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": parameters or {},
            **(configuration.get("default_payload", {}))
        }
        
        try:
            if method.upper() == "POST":
                response = await self.http_client.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                )
            elif method.upper() == "GET":
                response = await self.http_client.get(
                    webhook_url,
                    params=payload,
                    headers=headers
                )
            else:
                raise ValueError(f"Unsupported HTTP method for webhook: {method}")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "status_code": e.response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()


class FunctionRegistry:
    """Registry for custom functions that can be used as tools"""
    
    def __init__(self):
        self._functions = {}
        self._register_default_functions()
    
    def register_function(self, name: str, func):
        """Register a function with the registry"""
        self._functions[name] = func
    
    def get_function(self, name: str):
        """Get a function from the registry"""
        return self._functions.get(name)
    
    def list_functions(self) -> List[str]:
        """List all registered function names"""
        return list(self._functions.keys())
    
    def _register_default_functions(self):
        """Register default utility functions"""
        
        def get_current_time():
            """Get the current time"""
            return datetime.utcnow().isoformat()
        
        def calculate(expression: str):
            """Safely evaluate a mathematical expression"""
            import ast
            import operator
            
            # Define allowed operators
            allowed_operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.BitXor: operator.xor,
                ast.USub: operator.neg,
            }
            
            def eval_expr(expr):
                if isinstance(expr, ast.Expression):
                    return eval_expr(expr.body)
                elif isinstance(expr, ast.Num):
                    return expr.n
                elif isinstance(expr, ast.BinOp):
                    return allowed_operators[type(expr.op)](eval_expr(expr.left), eval_expr(expr.right))
                elif isinstance(expr, ast.UnaryOp):
                    return allowed_operators[type(expr.op)](eval_expr(expr.operand))
                else:
                    raise TypeError(f"Unsupported operation: {type(expr).__name__}")
            
            try:
                tree = ast.parse(expression, mode='eval')
                return eval_expr(tree.body)
            except Exception as e:
                raise ValueError(f"Invalid expression: {str(e)}")
        
        def format_currency(amount: float, currency: str = "USD"):
            """Format a number as currency"""
            currency_symbols = {
                "USD": "$",
                "EUR": "€",
                "GBP": "£",
                "JPY": "¥"
            }
            symbol = currency_symbols.get(currency, currency)
            return f"{symbol}{amount:,.2f}"
        
        # Register the functions
        self.register_function("get_current_time", get_current_time)
        self.register_function("calculate", calculate)
        self.register_function("format_currency", format_currency) 