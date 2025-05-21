# Lucie - Personal AI Assistant

Lucie is a comprehensive personal AI assistant with a Node.js backend, Python AI services, and a React frontend.

## Project Structure

```
├── backend/             # Node.js backend server
├── python-ai/           # Python AI services
├── lucie-ui/            # React frontend
├── shared/              # Shared resources
├── scripts/             # Utility scripts
└── deployment/          # Deployment configurations
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- Protocol Buffers compiler (for gRPC)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Lucie.git
   cd Lucie
   ```

2. Run the initialization script:
   ```bash
   ./scripts/setup/init_project.sh
   ```
   
   This script will:
   - Create all necessary `.env` files from the examples
   - Set up required directories
   - Generate Protocol Buffer files for gRPC
   - Make all scripts executable

3. Configure your environment variables in the `.env` files

### Generate Protocol Buffers

If you need to regenerate the Protocol Buffer files manually:

```bash
./scripts/generate_protos.sh
```

### Development Mode

Start the development environment:

```bash
docker-compose -f docker-compose.dev.yml up
```

Or use the dev script:

```bash
./dev.sh start
```

### Production Setup

For production deployment:

```bash
docker-compose up -d
```

## API Documentation

- Backend API: http://localhost:5000
- Python AI API: http://localhost:8000

## Database Administration

- Neo4j Browser: http://localhost:7474
- Redis Commander: http://localhost:8081

## Main Features

- Natural language understanding and processing
- Knowledge management and retrieval
- Multi-AI provider integration (OpenAI, Anthropic, Mistral)
- Voice input and avatar visualization
- Proactive assistance based on user patterns

## Development Guidelines

- Follow the code style of each language
- Write tests for new features
- Update documentation when API changes

## License

[MIT License](LICENSE)
