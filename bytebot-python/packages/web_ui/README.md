# Bytebot Web UI - Streamlit Interface

A modern, interactive web interface for the Bytebot AI Desktop Agent built with Streamlit.

## Features

### 🎨 Modern Interface
- Clean, responsive Streamlit design
- Real-time task monitoring
- Interactive desktop viewer
- Professional UI components

### 📝 Task Management
- **Task Creation**: Visual form with AI model selection
- **Task Examples**: Pre-built example tasks for quick testing
- **Task Monitoring**: Real-time status updates and progress tracking
- **Task Control**: Start, stop, and manage task execution

### 🖥️ Desktop Control
- **Live Screenshots**: Take and view desktop screenshots
- **Remote Control**: Click, type, and control the virtual desktop
- **Application Launcher**: Quick access to common applications
- **Coordinate Display**: Visual coordinate system for precise control

### ⚙️ Configuration
- **Service Management**: Configure API endpoints for all services
- **System Status**: Monitor health of all Bytebot components
- **Display Settings**: Customize refresh intervals and auto-refresh behavior

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry (for dependency management)
- Running Bytebot services (Computer Control + AI Agent)

### Installation
```bash
cd packages/web_ui
poetry install
```

### Running
```bash
# Method 1: Using the launch script (recommended)
python run.py

# Method 2: Direct Streamlit command
streamlit run src/web_ui/main.py --server.port 9992
```

### Access
- Open http://localhost:9992 in your browser
- Default port: 9992 (configurable via STREAMLIT_PORT environment variable)

## Service Integration

### AI Agent Service (Port 9996)
- Task creation and management
- Task processing control
- System status monitoring

### Computer Control Service (Port 9995)
- Desktop screenshots
- Mouse and keyboard control
- Application launching

### Database
- Task persistence
- Message history
- Task status tracking

## Interface Overview

### 📍 Navigation
- **Tasks**: Main task management interface
- **Desktop**: Virtual desktop viewer and control
- **Settings**: System configuration and monitoring

### 📝 Task Creation
1. Enter task description (or use examples)
2. Select AI provider and model
3. Set task priority
4. Optional file uploads
5. Submit and monitor progress

### 🖥️ Desktop Viewer
1. Take screenshots of virtual desktop
2. Click at specific coordinates
3. Type text on virtual keyboard
4. Launch applications
5. Real-time desktop interaction

### ⚙️ Settings & Monitoring
1. Configure API endpoints
2. Check service health status
3. Adjust refresh intervals
4. System status dashboard

## Architecture

```
Web UI (Streamlit)
├── main.py              # Main application entry point
├── components/          # Reusable UI components
│   ├── sidebar.py       # Navigation and quick stats
│   ├── task_creator.py  # Task creation interface
│   ├── task_list.py     # Task monitoring and management
│   └── desktop_viewer.py # Virtual desktop control
└── utils/
    └── api_client.py    # HTTP client for service communication
```

## Customization

### Environment Variables
- `STREAMLIT_PORT`: Port for web interface (default: 9992)
- `AI_AGENT_URL`: AI Agent service URL (default: http://localhost:9996)
- `COMPUTER_CONTROL_URL`: Computer Control service URL (default: http://localhost:9995)

### Theming
The interface uses a professional blue theme with:
- Primary color: #3b82f6 (blue)
- Light theme base
- Modern card-based layout
- Responsive design

## Development

### File Structure
```
src/web_ui/
├── main.py              # Main Streamlit app
├── components/          # UI components
│   ├── __init__.py
│   ├── sidebar.py       # Navigation sidebar
│   ├── task_creator.py  # Task creation form
│   ├── task_list.py     # Task list and management
│   └── desktop_viewer.py # Desktop viewer and control
└── utils/
    ├── __init__.py
    └── api_client.py    # API client for services
```

### Adding New Features
1. Create new component in `components/`
2. Add navigation option in `sidebar.py`
3. Integrate in `main.py`
4. Update API client if needed

## Troubleshooting

### Common Issues

**Cannot connect to services**
- Ensure AI Agent is running on port 9996
- Ensure Computer Control is running on port 9995
- Check service health in Settings → System Status

**Screenshots not displaying**
- Verify Computer Control service is accessible
- Check browser console for errors
- Ensure base64 image data is valid

**Tasks not creating**
- Verify AI Agent service is running
- Check database connection
- Ensure valid task description is provided

### Logs
- Streamlit logs appear in terminal where `run.py` was executed
- Service-specific logs appear in their respective terminals
- Browser console may show additional frontend errors

## Production Deployment

For production deployment, consider:
- Using a reverse proxy (nginx, Apache)
- Setting up HTTPS certificates
- Configuring proper authentication
- Using environment-specific configurations
- Setting up monitoring and health checks

## API Integration

The Web UI communicates with backend services via HTTP APIs:

### Task Management
- `POST /tasks` - Create new task
- `GET /tasks` - List tasks with filtering
- `GET /tasks/{id}` - Get specific task details
- `POST /tasks/{id}/process` - Start task processing
- `POST /tasks/{id}/abort` - Stop task processing

### Computer Control
- `POST /computer-use` - Execute computer actions
- Actions: screenshot, click_mouse, type_text, etc.

All API communication is handled through the `APIClient` class in `utils/api_client.py`.