# 🚀 Automation Engine - Insights từ Trading Signals Project

## I. Cái Nhìn Tổng Quát

Trading Signals project cho ta 3 insight lớn:
1. **Pluggable Architecture** - Nhiều components độc lập có thể swap out
2. **Distributed Processing** - Worker-based system với job queue
3. **Configuration-Driven** - YAML configs + dynamic parameters

Những insight này áp dụng tuyệt vời cho automation engine! 🎯

---

## II. Architecture Patterns Từ Trading Signals

### A. **Strategy Registry Pattern** (→ Node Registry)
**Hiện tại trong Trading Signals:**
```python
# strategy_registry.get_strategy(name)
# - Tự động discover strategies
# - Runtime registration
# - Decouple strategy logic từ caller
```

**Áp dụng vào Automation Engine:**
```python
class NodeRegistry:
    """Registry cho tất cả node types"""
    _nodes = {}
    
    @staticmethod
    def register(node_type: str, node_class: Type[BaseNode]):
        """Register một node type"""
        NodeRegistry._nodes[node_type] = node_class
    
    @staticmethod
    def get_node(node_type: str) -> Type[BaseNode]:
        """Get node class by type"""
        return NodeRegistry._nodes.get(node_type)
    
    @staticmethod
    def list_available_nodes() -> Dict[str, NodeMetadata]:
        """List tất cả available nodes với metadata"""
        return {
            name: node_class.get_metadata() 
            for name, node_class in NodeRegistry._nodes.items()
        }
```

**Lợi ích:**
- ✅ Dễ extend với new node types
- ✅ Plugin system hỗ trợ
- ✅ Metadata discovery cho UI

---

### B. **Aggregation Engine Pattern** (→ Data Flow Orchestration)
**Hiện tại trong Trading Signals:**
- Tổng hợp multiple signals với khác nhau aggregation methods
- Configurable thresholds & weights
- Detailed result breakdown

**Áp dụng vào Automation Engine:**
```python
class WorkflowExecutor:
    """Execute workflow nodes with data aggregation"""
    
    def execute_parallel_nodes(self, nodes: List[WorkflowNode], 
                              input_data: Dict) -> Dict:
        """
        Chạy multiple nodes parallel & aggregate results
        Giống như Signal Aggregation:
        - Weighted vote: nodes có khác trọng số
        - Consensus: tất cả nodes phải agree
        - Custom logic: complex aggregation rules
        """
        results = {}
        
        # Execute parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                node.id: executor.submit(node.execute, input_data)
                for node in nodes
            }
        
        # Aggregate results
        for node_id, future in futures.items():
            results[node_id] = future.result()
        
        # Apply aggregation logic
        return self._aggregate_results(results, nodes)
    
    def _aggregate_results(self, results: Dict, nodes: List[WorkflowNode]) -> Dict:
        """Aggregate theo config"""
        # Weighted average
        # Majority vote
        # Custom transform function
        pass
```

**Lợi ích:**
- ✅ Parallel execution (performance)
- ✅ Flexible aggregation strategies
- ✅ Detailed execution breakdown

---

### C. **Multi-Timeframe Strategy** (→ Multi-Scale Workflows)
**Hiện tại trong Trading Signals:**
- Chiến lược phân tích ở 7 timeframes khác nhau (1m - 1D)
- Orchestrated scheduling
- Aggregation across timeframes

**Áp dụng vào Automation Engine:**
```python
class ScheduleStrategy(Enum):
    """Khác execution schedules"""
    IMMEDIATE = "immediate"  # Trigger-based
    INTERVAL = "interval"    # Every X seconds/minutes
    CRON = "cron"           # Scheduled pattern
    EVENT = "event"         # Event-driven

class WorkflowScheduler:
    """Quản lý workflow execution schedules"""
    
    def schedule_workflow(self, workflow_id: str, 
                         strategy: ScheduleStrategy, 
                         config: Dict):
        """
        Schedule workflows ở multiple scales:
        - Minute-level: Real-time data processing
        - Hourly: Report generation
        - Daily: Batch processing
        - Event-based: Webhook triggers
        """
        pass
    
    def execute_tiered_workflows(self, workflows: List[Workflow]) -> Dict:
        """
        Execute hierarchical workflows:
        - Tier 1: Real-time quick tasks
        - Tier 2: Aggregation & analysis
        - Tier 3: Reporting & notifications
        """
        pass
```

**Lợi ích:**
- ✅ Support many execution models
- ✅ Natural hierarchy
- ✅ Scalable scheduling

---

## III. Data Architecture Patterns

### A. **Type-Safe Signal Flow** (→ Type-Safe Data Pipeline)
**Hiện tại:**
```python
@dataclass
class SignalResult:
    """Strongly-typed signal output"""
    strategy_name: str
    direction: SignalDirection  # Enum
    strength: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    details: Dict[str, Any]
    timestamp: str
    timeframe: str
```

**Áp dụng vào Automation Engine:**
```python
class NodeInput:
    """Type-safe node input"""
    name: str
    type: str  # "string", "number", "object", "array"
    required: bool
    default: Optional[Any]
    description: str

class NodeOutput:
    """Type-safe node output"""
    name: str
    type: str
    description: str

class BaseNode(ABC):
    """Type-safe node"""
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            'inputs': [NodeInput(...), ...],
            'outputs': [NodeOutput(...), ...],
        }
    
    def validate_input(self, data: Dict) -> bool:
        """Validate input against schema"""
        pass
    
    def execute(self, input_data: Dict) -> Dict:
        """Execute node"""
        self.validate_input(input_data)
        return self._execute_internal(input_data)
```

**Lợi ích:**
- ✅ Catch errors early
- ✅ Type validation
- ✅ Better IDE support
- ✅ Self-documenting

---

### B. **Hierarchical Configuration** (→ Workflow Configuration)
**Hiện tại:**
```yaml
# config/symbols/NVDA.yaml
symbol: NVDA
thresholds:
  sma:
    periods: [18, 36, 48, 144]
    zones:
      bullish:
        min_value: 0.5
        max_value: 1.0
      bearish:
        min_value: -1.0
        max_value: -0.5
```

**Áp dụng vào Automation Engine:**
```yaml
workflow:
  id: "data_pipeline_001"
  name: "Data Processing Pipeline"
  trigger: "webhook"
  nodes:
    - id: "fetch_data"
      type: "http_request"
      config:
        url: "{{ env.API_URL }}"
        method: "GET"
        params:
          limit: 100
    
    - id: "transform"
      type: "transform"
      config:
        script: |
          return data.map(item => ({
            id: item.id,
            value: item.price * item.quantity
          }))
    
    - id: "validate"
      type: "validation"
      config:
        rules:
          - field: "value"
            type: "number"
            min: 0
    
    - id: "save"
      type: "database"
      config:
        action: "insert"
        table: "transactions"
  
  edges:
    - from: "fetch_data"
      to: "transform"
    - from: "transform"
      to: "validate"
    - from: "validate"
      to: "save"
```

**Lợi ích:**
- ✅ Declarative workflows
- ✅ Easy versioning & tracking
- ✅ Infrastructure as code
- ✅ Team collaboration

---

## IV. Worker & Execution Patterns

### A. **Background Job Queue** (→ Async Execution)
**Hiện tại trong Trading Signals:**
```python
# Redis Queue
from redis_queue import Queue

# Enqueue jobs
job = queue.enqueue(process_signal, args=(symbol, timeframe))

# Worker picks up job
worker = Worker(queue)
worker.work()
```

**Áp dụng vào Automation Engine:**
```python
class WorkflowExecutor:
    """Execute workflows with job queue"""
    
    def enqueue_workflow(self, workflow_id: str, 
                         input_data: Dict, 
                         priority: int = 0) -> JobId:
        """
        Enqueue workflow cho execution
        Priority-based queue từ trading signals
        """
        job = {
            'workflow_id': workflow_id,
            'input_data': input_data,
            'priority': priority,
            'status': 'queued',
            'created_at': datetime.now()
        }
        return queue.enqueue_job(job)
    
    def execute_job(self, job: WorkflowJob) -> ExecutionResult:
        """Execute từ queue"""
        try:
            # Load workflow definition
            workflow = load_workflow(job.workflow_id)
            
            # Execute nodes
            result = self.execute_workflow(workflow, job.input_data)
            
            # Store result
            store_execution_result(result)
            
            return ExecutionResult(
                status='success',
                output=result,
                execution_time=time.time() - job.created_at
            )
        except Exception as e:
            return ExecutionResult(
                status='failed',
                error=str(e),
                execution_time=time.time() - job.created_at
            )
```

**Lợi ích:**
- ✅ Async processing (không block API)
- ✅ Scalable horizontal
- ✅ Job retry & tracking
- ✅ Priority-based execution

---

### B. **Observability & Logging Pattern**
**Hiện tại:**
```python
# Detailed logging at each stage
logger.info(f"Processing {symbol} - {timeframe}")
logger.debug(f"Signal details: {signal}")
logger.error(f"Failed to fetch data", exc_info=True)
```

**Áp dụng vào Automation Engine:**
```python
class ExecutionObserver:
    """Track workflow execution"""
    
    def record_node_execution(self, workflow_id: str, node_id: str,
                             input: Dict, output: Dict, 
                             duration: float, status: str):
        """Record mỗi node execution"""
        event = {
            'workflow_id': workflow_id,
            'node_id': node_id,
            'input_hash': hash(str(input)),  # Don't log sensitive data
            'output_hash': hash(str(output)),
            'duration': duration,
            'status': status,
            'timestamp': datetime.now()
        }
        
        # Store to DB for audit trail
        db.execution_logs.insert(event)
        
        # Stream to real-time dashboard
        websocket.broadcast({
            'event': 'node_executed',
            'data': event
        })

class ExecutionTracer:
    """Distributed tracing"""
    
    def trace_workflow(self, workflow_id: str, execution_id: str) -> Dict:
        """Get full execution trace"""
        # Như distributed tracing (Jaeger, Datadog)
        trace = {
            'workflow_id': workflow_id,
            'execution_id': execution_id,
            'nodes': [
                {
                    'node_id': 'fetch_data',
                    'status': 'success',
                    'duration_ms': 245,
                    'start_time': '2024-01-01T10:00:00Z'
                },
                {
                    'node_id': 'transform',
                    'status': 'success',
                    'duration_ms': 123,
                    'start_time': '2024-01-01T10:00:00.245Z'
                }
            ]
        }
        return trace
```

**Lợi ích:**
- ✅ Debug & troubleshooting
- ✅ Performance monitoring
- ✅ Audit trail
- ✅ Real-time visibility

---

## V. Customization & Extension Pattern

### A. **Custom Node Development** (Từ Strategy Implementation)
**Hiện tại:**
```python
class CustomStrategy(BaseStrategy):
    """User-defined strategy"""
    
    def evaluate_signal(self, symbol_id, ticker, exchange, timeframe):
        # Custom logic
        pass
    
    def get_required_indicators(self):
        return ['MACD', 'RSI', 'SMA']
```

**Áp dụng vào Automation Engine:**
```python
class CustomNodeTemplate:
    """Template cho customer development"""
    
    @staticmethod
    def create_custom_node(name: str, inputs: List[NodeInput],
                          outputs: List[NodeOutput],
                          script: str) -> BaseNode:
        """
        Runtime node creation từ script
        Cho phép customers implement custom business logic
        """
        # Validate script
        # Sandbox execution
        # Return node instance
        
        class DynamicNode(BaseNode):
            def execute(self, input_data: Dict) -> Dict:
                # Execute custom script with input_data
                return eval_script(script, input_data)
        
        return DynamicNode()

# Use case
webhook_node = CustomNodeTemplate.create_custom_node(
    name="custom_webhook_processor",
    inputs=[NodeInput(name="payload", type="object")],
    outputs=[NodeOutput(name="result", type="object")],
    script="""
    result = {
        'user_id': payload['userId'],
        'amount': payload['amount'] * 1.1,  # Tính phí 10%
        'processed_at': datetime.now().isoformat()
    }
    """
)
```

**Lợi ích:**
- ✅ Khách hàng có thể tự build workflows
- ✅ Zero-code customization (drag & drop)
- ✅ Code-based customization (scripting)
- ✅ Marketplace của custom nodes

---

## VI. Database Schema Insights

### A. **Workflow Storage**
**Hiện tại trong Trading Signals:**
```python
class Signal(Base):
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"))
    timeframe = Column(Enum(...))
    signal_type = Column(String(30))
    details = Column(JSON)  # Flexible storage
```

**Áp dụng vào Automation Engine:**
```python
class Workflow(Base):
    """Workflow definition"""
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    description = Column(String(1000))
    nodes = Column(JSON)  # Node definitions
    connections = Column(JSON)  # Edge definitions
    properties = Column(JSON)  # Config
    metadata = Column(JSON)  # Tags, categories, etc.
    status = Column(Enum('active', 'inactive', 'draft'))
    version = Column(Integer, default=1)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    created_by = Column(String(100))

class WorkflowExecution(Base):
    """Execution history"""
    __tablename__ = "workflow_executions"
    
    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"))
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(Enum('running', 'success', 'failed'))
    error_message = Column(String)
    execution_trace = Column(JSON)  # Detailed trace
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    duration_ms = Column(Integer)

class NodeExecution(Base):
    """Per-node execution details"""
    __tablename__ = "node_executions"
    
    id = Column(String(36), primary_key=True)
    execution_id = Column(String(36), ForeignKey("workflow_executions.id"))
    node_id = Column(String(100))
    status = Column(Enum('pending', 'running', 'success', 'failed'))
    input = Column(JSON)
    output = Column(JSON)
    error = Column(String)
    duration_ms = Column(Integer)
```

**Lợi ích:**
- ✅ Full audit trail
- ✅ Versioning support
- ✅ Analytics & insights
- ✅ Debugging tools

---

## VII. Real-time Communication

### A. **WebSocket for Live Updates** (Từ Dashboard Updates)
**Hiện tại:**
```python
# Real-time signal updates
@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Stream updates
    await websocket.send_json({
        'signal': 'buy',
        'strength': 0.85,
        'timestamp': now()
    })
```

**Áp dụng vào Automation Engine:**
```python
class WorkflowMonitoringService:
    """Real-time workflow monitoring"""
    
    @app.websocket("/ws/workflow/{workflow_id}")
    async def monitor_workflow(self, websocket: WebSocket, 
                              workflow_id: str):
        """
        Live monitoring của workflow execution
        Stream updates:
        - Node started/completed
        - Progress percentage
        - Errors
        - Performance metrics
        """
        await websocket.accept()
        
        # Subscribe to execution events
        async for event in self.execution_events.subscribe(workflow_id):
            await websocket.send_json({
                'type': event.type,
                'node_id': event.node_id,
                'status': event.status,
                'timestamp': event.timestamp,
                'duration_ms': event.duration_ms
            })
```

**Lợi ích:**
- ✅ Real-time debugging
- ✅ Live dashboard
- ✅ Performance monitoring
- ✅ Error alerts

---

## VIII. System Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────┐
│                   AUTOMATION ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ REST API     │  │ WebSocket    │  │ Webhook      │     │
│  │ Endpoints    │  │ Real-time    │  │ Handlers     │     │
│  └────────┬─────┘  └────────┬─────┘  └────────┬─────┘     │
│           │                 │                  │            │
│  ┌────────▼─────────────────▼──────────────────▼────────┐  │
│  │          WORKFLOW ENGINE                             │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  Node Registry & Executor                    │    │  │
│  │  │  - Strategy pattern                          │    │  │
│  │  │  - Type validation                           │    │  │
│  │  │  - Parallel execution                        │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  Scheduler & Queue Manager                   │    │  │
│  │  │  - Multi-scale execution                     │    │  │
│  │  │  - Priority-based queue                      │    │  │
│  │  │  - Retry & backoff logic                     │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │  Execution Tracer & Observer                 │    │  │
│  │  │  - Audit trail                               │    │  │
│  │  │  - Performance metrics                       │    │  │
│  │  │  - Error tracking                            │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────┘  │
│           │                 │                  │            │
│  ┌────────▼─────┐  ┌───────▼────────┐  ┌─────▼────────┐   │
│  │   MySQL      │  │    Redis       │  │  S3/Storage  │   │
│  │   Database   │  │    Queue       │  │  Artifacts   │   │
│  └──────────────┘  └────────────────┘  └──────────────┘   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Worker Pool  │  │ Worker Pool   │  │ Worker Pool  │     │
│  │ (Tier 1)     │  │ (Tier 2)      │  │ (Tier 3)     │     │
│  │ Real-time    │  │ Processing    │  │ Heavy tasks  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## IX. Implementation Roadmap

### Phase 1: Core Engine (Week 1-2)
- ✅ Node Registry & Base Node
- ✅ Workflow Definition (JSON/YAML)
- ✅ Simple Executor
- ✅ Database schema

### Phase 2: Execution & Scheduling (Week 3-4)
- ✅ Job Queue (Redis)
- ✅ Worker Pool
- ✅ Scheduler (Interval, Cron, Event)
- ✅ Execution Tracing

### Phase 3: Built-in Nodes (Week 5-6)
- ✅ HTTP Request node
- ✅ Database node
- ✅ Transform/Script node
- ✅ Conditional node
- ✅ Notification node

### Phase 4: UI & Monitoring (Week 7-8)
- ✅ Workflow Builder (Drag & Drop)
- ✅ Execution Dashboard
- ✅ Real-time Monitoring (WebSocket)
- ✅ Error Tracking

### Phase 5: Customization & API (Week 9-10)
- ✅ Custom Node SDK
- ✅ Plugin System
- ✅ Public API
- ✅ Marketplace

### Phase 6: Enterprise Features (Week 11+)
- ✅ Multi-tenancy
- ✅ Role-based Access
- ✅ Audit Logging
- ✅ Performance Analytics
- ✅ Disaster Recovery

---

## X. Key Differences vs n8n

| Feature | n8n | Our Engine |
|---------|-----|-----------|
| **Primary Use** | General workflow automation | Custom for business needs |
| **Deployment** | Cloud-first | On-premise focus |
| **Customization** | Plugins via npm | YAML + Python scripts |
| **Pricing** | Per-execution | Per-deployment |
| **Learning Curve** | Low (visual builder) | Medium (visual + config) |
| **Our Advantage** | Full control + custom nodes + B2B focus |

---

## XI. Next Steps

1. **Prototype Node System** - Build base node registry & executor
2. **Workflow Persistence** - Design & implement DB schema
3. **Job Queue** - Integrate Redis for background jobs
4. **Build 5-10 core nodes** - HTTP, DB, Transform, etc.
5. **Create Builder UI** - React-based drag & drop
6. **Performance Testing** - Load testing with multiple concurrent workflows

---

**Document này sẽ được update khi có developments mới! 🚀**
