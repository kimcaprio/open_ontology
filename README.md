# Open Ontology Platform 🚀

An advanced ontology management platform with AI-powered suggestions and interactive graph visualization.

## ✨ Features

- **🎨 Interactive Graph Visualization**: D3.js-powered node-link diagrams with drag-and-drop functionality
- **🔗 Connect Nodes Feature**: Intelligent relationship creation with auto-suggestions
- **🤖 AI-Powered Suggestions**: Smart entity and relationship recommendations
- **📊 Multi-view Support**: Both graph and tree visualization modes
- **🎯 Entity Highlighting**: Auto-highlight connection candidates for new entities
- **💾 Real-time API Integration**: Live database persistence
- **🎭 Advanced UI**: Bootstrap 5 with modern animations and transitions

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI** with async/await support
- **MySQL** database with comprehensive ontology schema
- **AI Integration** with Ollama models (Qwen, Gemma, Llama)
- **RESTful API** design with proper error handling

### Frontend
- **D3.js** for interactive graph visualization
- **Bootstrap 5** for responsive UI
- **Vanilla JavaScript** with ES6+ features
- **CSS animations** for enhanced user experience

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- Node.js (for development tools)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kimcaprio/open_ontology.git
cd open_ontology
```

2. **Set up virtual environment**
```bash
python -m venv venv
source ./venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
- Update database credentials in `src/config/`
- Run initialization scripts in `scripts/`

5. **Start the application**
```bash
python -m src.main
```

6. **Access the platform**
```
http://localhost:8000/ontology
```

## 📁 Project Structure

```
open_ontology/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API endpoints
│   │   └── ontology.py         # Ontology CRUD operations
│   ├── services/               # Business logic services
│   │   └── ontology_service.py # Core ontology management
│   ├── web/                    # Frontend assets
│   │   ├── templates/          # HTML templates
│   │   └── static/             # CSS/JS files
│   └── config/                 # Configuration files
├── scripts/                    # Database scripts
├── .cursor/                    # Cursor IDE rules
└── requirements.txt            # Python dependencies
```

## 🎯 Key Components

### OntologyGraphManager
The core JavaScript class managing graph visualization and interactions.

```javascript
// Global instance
window.ontologyGraph = new OntologyGraphManager();

// Key methods
ontologyGraph.loadVisualizationData(data);
ontologyGraph.toggleConnectionMode();
ontologyGraph.selectNode(nodeId);
```

### ConnectionManager
Handles intelligent node-to-node connections with AI suggestions.

```javascript
// Connection workflow
1. Enable connection mode
2. Click source node (shows suggestion panel)
3. Drag to target OR use quick-connect buttons
4. Automatic API persistence
```

### AI Suggestions System
Provides intelligent recommendations for ontology enhancement.

- **Entity Suggestions**: Add missing domain entities
- **Relationship Suggestions**: Connect isolated entities  
- **Schema Suggestions**: Optimize entity properties

## 🎨 Visual Features

### Entity Highlighting System
- **🔴 New entities**: Red dashed border with pulsing animation
- **🟢 High confidence candidates**: Green highlight (80%+ confidence)
- **🟡 Medium confidence**: Yellow highlight (60-79% confidence)
- **🔵 Low confidence**: Blue highlight (50-59% confidence)

### Connection Suggestions
Real-time floating panel with:
- Confidence-based scoring
- One-click connection creation
- Intelligent relationship naming
- Auto-positioning

## 🛠️ Development

### Backend Development
```bash
# Start with auto-reload
uvicorn src.main:app --reload --port 8000

# API documentation
http://localhost:8000/docs
```

### Frontend Development
- Edit files in `src/web/static/`
- Check browser console for debugging
- Use developer tools for D3.js visualization

### Debugging
See `.cursor/rules/troubleshooting.mdc` for comprehensive debugging guide.

## 📊 API Endpoints

### Entities
- `GET /api/v1/ontology/domains/{domain_id}/entities` - List entities
- `POST /api/v1/ontology/domains/{domain_id}/entities` - Create entity
- `PUT /api/v1/ontology/domains/{domain_id}/entities/{entity_id}` - Update entity
- `DELETE /api/v1/ontology/domains/{domain_id}/entities/{entity_id}` - Delete entity

### Relationships
- `GET /api/v1/ontology/domains/{domain_id}/relationships` - List relationships
- `POST /api/v1/ontology/domains/{domain_id}/relationships` - Create relationship
- `DELETE /api/v1/ontology/domains/{domain_id}/relationships/{relationship_id}` - Delete relationship

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **D3.js** for powerful data visualization
- **FastAPI** for modern Python web framework
- **Bootstrap** for responsive UI components
- **Ollama** for AI model integration

## 📧 Contact

- **GitHub**: [@kimcaprio](https://github.com/kimcaprio)
- **Project Link**: [https://github.com/kimcaprio/open_ontology](https://github.com/kimcaprio/open_ontology)

---

⭐ **Star this repository if you find it useful!** ⭐ 