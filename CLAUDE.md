# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bytebot is an open-source AI desktop agent that provides AI with a complete virtual desktop environment. It consists of multiple services that work together to enable AI to control computers, process tasks, and interact with applications.

## Architecture

This is a monorepo with multiple packages in the `packages/` directory:

- **bytebot-agent**: NestJS service that coordinates AI model interactions and task processing
- **bytebot-ui**: Next.js web interface for task management and desktop viewing  
- **bytebotd**: Desktop control daemon that handles computer interactions (mouse, keyboard, screenshots)
- **shared**: Common TypeScript types and utilities shared across packages
- **bytebot-agent-cc**: Claude Code specific agent implementation
- **bytebot-llm-proxy**: Proxy service for LLM providers

### Core Services

- **Agent Service** (`packages/bytebot-agent/src/agent/`): Core AI processing logic including task scheduling, computer use handling, and AI model orchestration
- **Desktop Service** (`packages/bytebotd/src/`): Computer interaction layer using libraries like nut-js for mouse/keyboard control
- **Task Management** (`packages/bytebot-agent/src/tasks/`): Task lifecycle management and persistence
- **AI Provider Integrations**: Anthropic, OpenAI, and Google Gemini service modules

## Development Commands

### Individual Package Commands

**Bytebot Agent (NestJS service)**:
```bash
cd packages/bytebot-agent
npm run build        # Build the service
npm run start:dev     # Start in development mode with watch
npm run test          # Run tests
npm run lint          # Lint code
```

**Bytebot UI (Next.js frontend)**:  
```bash
cd packages/bytebot-ui
npm run build         # Build the UI
npm run dev           # Start development server
npm run lint          # Lint code
```

**Bytebotd (Desktop daemon)**:
```bash
cd packages/bytebotd
npm run build         # Build the daemon
npm run start:dev     # Start in development mode
npm run test          # Run tests
npm run lint          # Lint code
```

**Shared Package**:
```bash
cd packages/shared
npm run build         # Build shared types/utilities
```

### Docker Development

The project uses Docker Compose for development and deployment:

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Development with hot reload
docker-compose -f docker/docker-compose.development.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f [service-name]
```

### Environment Setup

Create `docker/.env` with required API keys:
```bash
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...  
# OR
GEMINI_API_KEY=...
```

## Key Files and Entry Points

- `packages/bytebot-agent/src/main.ts`: Agent service main entry point
- `packages/bytebot-agent/src/agent/agent.processor.ts`: Core AI task processing logic
- `packages/bytebot-agent/src/agent/agent.computer-use.ts`: Computer interaction handling
- `packages/bytebotd/src/main.ts`: Desktop daemon entry point
- `packages/bytebot-ui/server.ts`: UI server with proxy configuration
- `packages/shared/src/types/`: Shared TypeScript interfaces

## Database

Uses PostgreSQL with Prisma ORM. Schema and migrations in `packages/bytebot-agent/prisma/`.

## Testing

Each package has its own test suite. Run tests from package directories or use Docker for full integration testing.

## Port Configuration

- **9990**: Desktop daemon (bytebotd) and noVNC access
- **9991**: Agent API service  
- **9992**: Web UI
- **5432**: PostgreSQL database

## AI Model Integration

The system supports multiple AI providers through modular service classes. Each provider (Anthropic, OpenAI, Google) has its own module with standardized interfaces for computer use tool calling.
- by default, use model claude-sonnet-4-20250514 for claude
- I am rewrite the application from typescript to python. Use typescript project as a reference and don't change it. You can refer it when changing code for python. They should do the same thing.
- when use docker-compose build, always using no-cache option