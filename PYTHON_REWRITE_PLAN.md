# Bytebot Python Rewrite Plan

## Overview
Complete rewrite of the Bytebot TypeScript/Node.js project to Python, maintaining all core functionality while leveraging Python's strengths in AI/ML and automation.

## Architecture Migration Strategy

### Current Architecture (TypeScript)
```
packages/
├── bytebot-agent/     # NestJS - AI coordination & task processing
├── bytebot-ui/        # Next.js - Web interface & VNC viewer  
├── bytebotd/          # NestJS - Computer control daemon
├── shared/            # TypeScript types & utilities
├── bytebot-agent-cc/  # Claude Code variant
└── bytebot-llm-proxy/ # LiteLLM proxy
```

### Target Architecture (Python)
```
packages-python/
├── ai_agent/          # FastAPI - AI coordination & task processing
├── web_ui/            # Streamlit/FastAPI - Web interface & VNC
├── computer_control/  # FastAPI - Desktop control daemon  
├── shared/            # Pydantic models & utilities
├── agent_cc/          # Claude Code Python variant
└── llm_proxy/         # Python LLM proxy service
```

## Technology Stack Mapping

| Component | TypeScript/Node.js | Python Equivalent |
|-----------|-------------------|-------------------|
| Backend Framework | NestJS | FastAPI + dependency-injector |
| Frontend | Next.js + React | Streamlit + FastAPI |
| Database ORM | Prisma | SQLAlchemy + Alembic |
| Computer Control | @nut-tree-fork/nut-js | PyAutoGUI + pynput |
| Image Processing | sharp | Pillow (PIL) |
| WebSocket | Socket.IO | python-socketio |
| AI SDKs | @anthropic-ai/sdk, openai | anthropic, openai |
| Validation | Zod | Pydantic |
| HTTP Client | axios | httpx |
| Background Jobs | @nestjs/schedule | APScheduler |
| Testing | Jest | pytest |
| Linting | ESLint + Prettier | ruff + black |

## Implementation Steps

### Phase 1: Foundation Setup
1. **Project Structure Setup**
   - Create Python monorepo structure
   - Set up Poetry for dependency management
   - Configure development tooling (ruff, black, mypy)

2. **Shared Package**
   - Migrate TypeScript interfaces to Pydantic models
   - Create common utilities and constants
   - Set up shared database models

### Phase 2: Core Services (Priority Order)

3. **Computer Control Service (`computer_control/`)**
   - **Priority: HIGHEST** - Most specialized functionality
   - Migrate computer interaction logic (mouse, keyboard, screen)
   - Implement VNC server integration
   - Port input tracking and event handling
   - **Files to migrate:**
     - `bytebotd/src/computer-use/` → `computer_control/computer_use/`
     - `bytebotd/src/nut/` → `computer_control/input_control/`

4. **Database Layer**
   - Convert Prisma schema to SQLAlchemy models
   - Set up Alembic for migrations
   - Create database connection and session management
   - **Files to migrate:**
     - `packages/bytebot-agent/prisma/` → `shared/database/`

5. **AI Agent Service (`ai_agent/`)**
   - Port task processing logic
   - Migrate AI provider integrations (Anthropic, OpenAI, Gemini)
   - Implement computer use tool handling
   - **Files to migrate:**
     - `bytebot-agent/src/agent/` → `ai_agent/services/`
     - `bytebot-agent/src/tasks/` → `ai_agent/tasks/`

### Phase 3: User Interface

6. **Web UI Service (`web_ui/`)**
   - Start with Streamlit for rapid prototyping
   - Migrate to FastAPI + templates for production
   - Implement VNC viewer integration
   - **Files to migrate:**
     - `bytebot-ui/src/` → `web_ui/`

### Phase 4: Infrastructure

7. **Docker Configuration**
   - Create Python-based Dockerfiles
   - Update docker-compose configurations
   - Ensure proper service networking

8. **Testing & Documentation**
   - Port existing tests to pytest
   - Update documentation for Python stack
   - Create development setup guides

## Detailed Implementation Plan

### Step 1: Project Structure Setup

#### Directory Structure
```
bytebot-python/
├── pyproject.toml              # Poetry configuration
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.computer-control
│   ├── Dockerfile.ai-agent
│   └── Dockerfile.web-ui
├── packages/
│   ├── shared/
│   │   ├── src/
│   │   │   ├── models/         # Pydantic models
│   │   │   ├── types/          # Type definitions  
│   │   │   └── utils/          # Shared utilities
│   │   └── pyproject.toml
│   ├── computer_control/
│   │   ├── src/
│   │   │   ├── computer_use/   # Screen, mouse, keyboard
│   │   │   ├── vnc/           # VNC server integration
│   │   │   └── api/           # FastAPI routes
│   │   └── pyproject.toml
│   ├── ai_agent/
│   │   ├── src/
│   │   │   ├── services/      # Agent processing
│   │   │   ├── providers/     # AI model providers
│   │   │   ├── tasks/         # Task management
│   │   │   └── api/           # FastAPI routes
│   │   └── pyproject.toml
│   └── web_ui/
│       ├── src/
│       │   ├── pages/         # Streamlit pages
│       │   ├── components/    # Reusable components
│       │   └── api/           # API integration
│       └── pyproject.toml
├── tests/
├── scripts/                   # Development scripts
└── docs/
```

#### Key Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
pydantic = "^2.5.0"
pyautogui = "^0.9.54"
pynput = "^1.7.6"
pillow = "^10.1.0"
python-socketio = "^5.10.0"
anthropic = "^0.39.0"
openai = "^1.3.0"
streamlit = "^1.28.0"
httpx = "^0.25.0"
python-multipart = "^0.0.6"
dependency-injector = "^4.41.0"
apscheduler = "^3.10.4"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
mypy = "^1.6.0"
ruff = "^0.1.0"
black = "^23.0.0"
```

### Step 2: Shared Models Migration

#### Key Models to Migrate
- Task (with status, priority, type enums)
- Message (with role, content blocks)
- User profiles and authentication
- Computer use actions and responses

#### Example Model Migration
**TypeScript (Prisma):**
```typescript
model Task {
  id          String      @id @default(uuid())
  description String
  status      TaskStatus  @default(PENDING)
  priority    TaskPriority @default(NORMAL)
  type        TaskType    @default(USER_TASK)
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  messages    Message[]
  files       TaskFile[]
}
```

**Python (SQLAlchemy + Pydantic):**
```python
# Database model
class TaskModel(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.NORMAL)
    type = Column(Enum(TaskType), default=TaskType.USER_TASK)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    
    messages = relationship("MessageModel", back_populates="task")
    files = relationship("TaskFileModel", back_populates="task")

# Pydantic schema
class Task(BaseModel):
    id: UUID
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    type: TaskType = TaskType.USER_TASK
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List['Message'] = []
    files: List['TaskFile'] = []
```

### Step 3: Computer Control Service Migration

This is the most critical component as it handles all system-level interactions.

#### Key Components to Migrate:
1. **Screen capture and interaction**
2. **Mouse and keyboard control**
3. **Input event tracking**
4. **VNC server integration**

#### Implementation Priority:
1. Basic screen capture (`screenshot` endpoint)
2. Mouse control (`click_mouse`, `move_mouse`)
3. Keyboard control (`type_text`, `press_key`)
4. Input tracking and event emission
5. VNC server proxy

## Migration Progress Tracking

### Current Status: **PHASE 2 - CORE SERVICES IMPLEMENTATION**

#### Completed:
- ✅ Architecture analysis
- ✅ Technology mapping
- ✅ Implementation plan creation
- ✅ Python project structure with Poetry
- ✅ Shared Pydantic models and database layer
- ✅ Computer control service (FastAPI + PyAutoGUI + pynput)
- ✅ AI agent service with multi-provider support
- ✅ Web UI service with Streamlit interface
- ✅ Docker containerization and service orchestration
- ✅ **CRITICAL FIX**: Anthropic provider image content handling
  - Fixed infinite screenshot loops by enabling proper image interpretation
  - Enhanced message conversion for multi-modal content (text + images)
  - Corrected API-specific message role requirements

#### Core Services Status:
- ✅ **Computer Control Service** (`packages/computer_control/`)
  - Screen capture with scrot integration
  - Mouse control (click, drag, scroll, positioning)
  - Keyboard control (text input, key combinations)
  - Application launching
  - File I/O operations
- ✅ **AI Agent Service** (`packages/ai_agent/`)
  - Task processing and lifecycle management
  - Multi-provider AI integration (Anthropic, OpenAI)
  - Computer use tool handling with proper image processing
  - Background task processing with async execution
- ✅ **Web UI Service** (`packages/web_ui/`)
  - Streamlit-based interface for task management
  - Real-time desktop viewing capabilities
  - Task creation and monitoring
  - Live status updates

#### Infrastructure:
- ✅ Docker containers for all services
- ✅ PostgreSQL database with proper schema
- ✅ Service networking and health checks
- ✅ Development and production configurations

#### Recent Major Achievements:
- **🔧 Fixed Critical Anthropic Provider Bug** (Commit: c043454)
  - Root cause: Anthropic provider wasn't processing image content from screenshots
  - Solution: Enhanced `_convert_messages()` to handle image blocks, tool use, and tool results
  - Impact: Eliminated infinite screenshot loops, enabled proper visual AI capabilities
  - Testing: Verified with successful screenshot analysis tasks

#### In Progress:
- 🔄 Performance optimization and monitoring
- 🔄 Additional UI components and features

#### Next Steps:
1. ✅ ~~Complete core service functionality~~ **DONE**
2. ✅ ~~Fix AI provider image handling~~ **DONE** 
3. 🎯 Performance testing and optimization
4. 🎯 Extended feature parity with TypeScript version
5. 🎯 Production deployment preparation

## Development Workflow

### Commands (Poetry)
```bash
# Development
poetry run uvicorn computer_control.main:app --reload --port 9995
poetry run uvicorn ai_agent.main:app --reload --port 9996  
poetry run streamlit run web_ui/main.py --server.port 9992

# Testing
poetry run pytest packages/computer_control/tests/
poetry run mypy packages/

# Linting
poetry run ruff check .
poetry run black .
```

### Docker Commands
```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up -d

# Individual service logs
docker-compose logs -f computer-control
docker-compose logs -f ai-agent
docker-compose logs -f web-ui
```

## Success Criteria

1. **Functional Parity**: All existing Bytebot features work in Python
2. **Performance**: Response times within 10% of TypeScript version
3. **Maintainability**: Clean, typed Python code with good test coverage
4. **Deployment**: Docker containers build and run successfully
5. **Documentation**: Clear setup and development instructions

## Risk Mitigation

1. **Computer Control Complexity**: Start with PyAutoGUI, fallback to python-xlib if needed
2. **VNC Integration**: Use existing noVNC frontend with Python websocket backend
3. **Performance**: Profile critical paths, optimize with async/await patterns
4. **AI Integration**: All providers have robust Python SDKs
5. **Frontend Complexity**: Start with Streamlit, migrate to FastAPI+templates incrementally

---

*This plan will be updated as implementation progresses. Current focus: Phase 1 - Foundation Setup*