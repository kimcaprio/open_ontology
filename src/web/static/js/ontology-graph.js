/**
 * Advanced Ontology Graph Visualization
 * Using React Flow for modern node-based UI interactions
 */

class OntologyGraphManager {
    constructor() {
        this.currentOntology = null;
        this.selectedNode = null;
        this.selectedEdge = null;
        this.isFullscreen = false;
        this.currentView = 'graph'; // 'graph' or 'tree'
        this.graphInstance = null;
        this.treeInstance = null;
        
        // New properties for suggestion management
        this.appliedSuggestions = new Set();
        this.changeHistory = [];
        this.currentChangeId = 0;
        
        // Connection management
        this.connectionManager = new ConnectionManager(this);
        this.isConnectionMode = false;
        
        // Sample ontology data for demonstration
        this.sampleData = {
            'customer-domain': {
                nodes: [
                    { 
                        id: 'customer', 
                        type: 'class',
                        position: { x: 100, y: 100 },
                        data: { 
                            label: 'Customer',
                            properties: ['id', 'name', 'email', 'registration_date'],
                            description: 'Represents a customer entity'
                        }
                    },
                    { 
                        id: 'order', 
                        type: 'class',
                        position: { x: 300, y: 100 },
                        data: { 
                            label: 'Order',
                            properties: ['order_id', 'total_amount', 'order_date', 'status'],
                            description: 'Represents an order placed by a customer'
                        }
                    },
                    { 
                        id: 'product', 
                        type: 'class',
                        position: { x: 500, y: 100 },
                        data: { 
                            label: 'Product',
                            properties: ['product_id', 'name', 'price', 'category'],
                            description: 'Represents a product in the catalog'
                        }
                    },
                    { 
                        id: 'address', 
                        type: 'property',
                        position: { x: 100, y: 250 },
                        data: { 
                            label: 'Address',
                            properties: ['street', 'city', 'country', 'postal_code'],
                            description: 'Customer address information'
                        }
                    }
                ],
                edges: [
                    {
                        id: 'customer-order',
                        source: 'customer',
                        target: 'order',
                        type: 'relationship',
                        data: { 
                            label: 'places',
                            relationshipType: 'one-to-many',
                            description: 'Customer places orders'
                        }
                    },
                    {
                        id: 'order-product',
                        source: 'order',
                        target: 'product',
                        type: 'relationship',
                        data: { 
                            label: 'contains',
                            relationshipType: 'many-to-many',
                            description: 'Order contains products'
                        }
                    },
                    {
                        id: 'customer-address',
                        source: 'customer',
                        target: 'address',
                        type: 'property',
                        data: { 
                            label: 'has_address',
                            relationshipType: 'one-to-one',
                            description: 'Customer has address'
                        }
                    }
                ]
            },
            'product-catalog': {
                nodes: [
                    { 
                        id: 'category', 
                        type: 'class',
                        position: { x: 200, y: 50 },
                        data: { 
                            label: 'Category',
                            properties: ['category_id', 'name', 'description'],
                            description: 'Product category'
                        }
                    },
                    { 
                        id: 'product', 
                        type: 'class',
                        position: { x: 200, y: 200 },
                        data: { 
                            label: 'Product',
                            properties: ['product_id', 'name', 'price', 'description'],
                            description: 'Product in catalog'
                        }
                    },
                    { 
                        id: 'variant', 
                        type: 'class',
                        position: { x: 400, y: 200 },
                        data: { 
                            label: 'Product Variant',
                            properties: ['variant_id', 'size', 'color', 'sku'],
                            description: 'Product variant with specific attributes'
                        }
                    }
                ],
                edges: [
                    {
                        id: 'category-product',
                        source: 'category',
                        target: 'product',
                        type: 'relationship',
                        data: { 
                            label: 'contains',
                            relationshipType: 'one-to-many',
                            description: 'Category contains products'
                        }
                    },
                    {
                        id: 'product-variant',
                        source: 'product',
                        target: 'variant',
                        type: 'relationship',
                        data: { 
                            label: 'has_variant',
                            relationshipType: 'one-to-many',
                            description: 'Product has variants'
                        }
                    }
                ]
            }
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeVisualization();
    }
    
    setupEventListeners() {
        // Fullscreen toggle
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            }
            if (e.key === 'Escape' && this.isFullscreen) {
                this.exitFullscreen();
            }
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.resizeVisualization();
        });
    }
    
    initializeVisualization() {
        const container = document.getElementById('ontology-visualization');
        if (!container) return;
        
        // Initialize with welcome message
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100 ontology-welcome">
                <div class="text-center">
                    <i class="fas fa-project-diagram fa-4x text-primary mb-4"></i>
                    <h4 class="text-primary mb-3">Advanced Ontology Visualization</h4>
                    <p class="text-muted mb-4">Select an ontology from the left panel to view its graph structure</p>
                    <div class="features-preview">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="feature-item">
                                    <i class="fas fa-mouse-pointer text-info me-2"></i>
                                    <span>Interactive Drag & Drop</span>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="feature-item">
                                    <i class="fas fa-search-plus text-success me-2"></i>
                                    <span>Zoom & Pan Controls</span>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="feature-item">
                                    <i class="fas fa-expand text-warning me-2"></i>
                                    <span>Fullscreen Mode</span>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="feature-item">
                                    <i class="fas fa-sitemap text-danger me-2"></i>
                                    <span>Tree & Graph Views</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    createCustomNode(nodeData) {
        const nodeTypes = {
            'class': {
                color: '#4285f4',
                icon: 'fas fa-cube',
                shape: 'rounded-rectangle'
            },
            'property': {
                color: '#34a853',
                icon: 'fas fa-tag',
                shape: 'ellipse'
            },
            'instance': {
                color: '#ea4335',
                icon: 'fas fa-circle',
                shape: 'circle'
            },
            'relationship': {
                color: '#fbbc04',
                icon: 'fas fa-link',
                shape: 'diamond'
            }
        };
        
        const nodeStyle = nodeTypes[nodeData.type] || nodeTypes['class'];
        
        return {
            ...nodeData,
            style: {
                background: nodeStyle.color,
                color: 'white',
                border: '2px solid #fff',
                borderRadius: nodeStyle.shape === 'circle' ? '50%' : '8px',
                padding: '10px',
                fontSize: '12px',
                fontWeight: 'bold',
                width: 120,
                height: nodeStyle.shape === 'circle' ? 60 : 80,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
                transition: 'all 0.3s ease'
            }
        };
    }
    
    createCustomEdge(edgeData) {
        const edgeTypes = {
            'relationship': {
                color: '#666',
                style: 'solid',
                width: 2
            },
            'property': {
                color: '#34a853',
                style: 'dashed',
                width: 1.5
            },
            'inheritance': {
                color: '#4285f4',
                style: 'solid',
                width: 3
            }
        };
        
        const edgeStyle = edgeTypes[edgeData.type] || edgeTypes['relationship'];
        
        return {
            ...edgeData,
            style: {
                stroke: edgeStyle.color,
                strokeWidth: edgeStyle.width,
                strokeDasharray: edgeStyle.style === 'dashed' ? '5,5' : '0'
            },
            markerEnd: {
                type: 'arrowclosed',
                width: 20,
                height: 20,
                color: edgeStyle.color,
            },
            labelStyle: {
                fill: edgeStyle.color,
                fontWeight: 600,
                fontSize: 11
            }
        };
    }
    
    loadOntologyGraph(ontologyId) {
        console.log('=== loadOntologyGraph START ===');
        console.log('ontologyId:', ontologyId);
        
        this.currentOntology = ontologyId;
        const data = this.sampleData[ontologyId];
        
        console.log('Sample data found:', !!data);
        
        if (!data) {
            console.warn('No sample data found for ontologyId:', ontologyId);
            console.log('Available sample data keys:', Object.keys(this.sampleData));
            this.showError('Ontology data not found');
            return;
        }
        
        console.log('loadOntologyGraph called for:', ontologyId);
        
        // Use safe methods for rendering
        if (this.currentView === 'graph') {
            this.safeRenderGraphView(data).catch(error => {
                console.error('Failed to render graph view:', error);
                this.showError(`Failed to load graph: ${error.message}`);
            });
        } else {
            this.safeRenderTreeView(data).catch(error => {
                console.error('Failed to render tree view:', error);
                this.showError(`Failed to load tree: ${error.message}`);
            });
        }
        
        this.updateControls();
    }
    
    // NEW FUNCTION: Load visualization data from API
    loadVisualizationData(vizData) {
        console.log('=== loadVisualizationData START ===');
        console.log('Received visualization data:', vizData);
        
        try {
            // Validate the incoming data
            if (!vizData) {
                throw new Error('No visualization data provided');
            }
            
            // Convert API data format to internal format if needed
            let processedData;
            
            if (vizData.nodes && vizData.edges) {
                console.log('Data has nodes/edges format, checking structure...');
                
                // Check if nodes have the internal format (with data.label) or API format (with direct label)
                const firstNode = vizData.nodes[0];
                if (firstNode && firstNode.label && !firstNode.data) {
                    // API format - convert to internal format
                    console.log('Converting API format to internal format');
                    processedData = this.convertAPIToInternalFormat(vizData);
                } else {
                    // Already in internal format
                    console.log('Data is already in internal format');
                    processedData = vizData;
                }
            } else if (vizData.entities && vizData.relationships) {
                // Convert from ontology format to graph format
                console.log('Converting ontology format to graph format');
                processedData = this.convertOntologyToGraphData(vizData);
            } else {
                throw new Error('Invalid data format: expected nodes/edges or entities/relationships');
            }
            
            console.log('Processed data:', processedData);
            console.log('Nodes count:', processedData.nodes?.length || 0);
            console.log('Edges count:', processedData.edges?.length || 0);
            
            // Validate the processed data structure
            if (processedData.nodes && processedData.nodes.length > 0) {
                const firstNode = processedData.nodes[0];
                console.log('First processed node structure:', firstNode);
                console.log('First node has data.label:', !!firstNode.data?.label);
            }
            
            // Store the current ontology ID
            this.currentOntology = 'api-data';
            
            // Store processed data in sampleData for future reference
            this.sampleData['api-data'] = processedData;
            console.log('Stored API data in sampleData for future access');
            
            // Render the visualization
            if (this.currentView === 'graph') {
                this.safeRenderGraphView(processedData).catch(error => {
                    console.error('Failed to render graph view:', error);
                    this.showError(`Failed to load graph: ${error.message}`);
                });
            } else {
                this.safeRenderTreeView(processedData).catch(error => {
                    console.error('Failed to render tree view:', error);
                    this.showError(`Failed to load tree: ${error.message}`);
                });
            }
            
            this.updateControls();
            console.log('=== loadVisualizationData SUCCESS ===');
            
        } catch (error) {
            console.error('=== loadVisualizationData ERROR ===');
            console.error('Error in loadVisualizationData:', error);
            this.showError(`Failed to load visualization data: ${error.message}`);
        }
    }
    
    // Convert API format to internal format
    convertAPIToInternalFormat(apiData) {
        console.log('=== convertAPIToInternalFormat START ===');
        
        const nodes = apiData.nodes.map((node, index) => {
            // Convert API node format to internal format
            const internalNode = {
                id: node.id || `node-${index}`,
                type: node.type === 'table' ? 'class' : (node.type || 'class'),
                position: node.position || { 
                    x: 100 + (index % 5) * 200, 
                    y: 100 + Math.floor(index / 5) * 150 
                },
                data: {
                    label: node.label || node.id || `Node ${index}`,
                    properties: Array.isArray(node.properties) ? node.properties : 
                               (node.properties && typeof node.properties === 'object' ? 
                                Object.keys(node.properties) : []),
                    description: node.description || '',
                    source_table: node.source_table,
                    row_count: node.row_count
                }
            };
            
            console.log(`Converted node ${index}:`, {
                original: node,
                converted: internalNode
            });
            
            return internalNode;
        });
        
        const edges = apiData.edges.map((edge, index) => {
            // Convert API edge format to internal format
            const internalEdge = {
                id: edge.id || `edge-${index}`,
                source: edge.source,
                target: edge.target,
                type: 'relationship',
                data: {
                    label: edge.label || edge.id || `Edge ${index}`,
                    relationshipType: edge.type || 'relationship',
                    description: edge.description || ''
                }
            };
            
            console.log(`Converted edge ${index}:`, {
                original: edge,
                converted: internalEdge
            });
            
            return internalEdge;
        });
        
        const result = { nodes, edges };
        console.log('=== convertAPIToInternalFormat COMPLETE ===');
        console.log('Final result:', result);
        
        return result;
    }
    
    // Convert ontology data format to graph visualization format
    convertOntologyToGraphData(ontologyData) {
        console.log('Converting ontology data to graph format');
        
        const nodes = [];
        const edges = [];
        
        // Convert entities to nodes
        if (ontologyData.entities && Array.isArray(ontologyData.entities)) {
            ontologyData.entities.forEach((entity, index) => {
                nodes.push({
                    id: entity.id || `entity-${index}`,
                    type: 'class',
                    position: { 
                        x: 100 + (index % 5) * 200, 
                        y: 100 + Math.floor(index / 5) * 150 
                    },
                    data: {
                        label: entity.name || entity.id || `Entity ${index}`,
                        properties: entity.properties || [],
                        description: entity.description || '',
                        source_table: entity.source_table,
                        row_count: entity.row_count
                    }
                });
            });
        }
        
        // Convert relationships to edges
        if (ontologyData.relationships && Array.isArray(ontologyData.relationships)) {
            ontologyData.relationships.forEach((relationship, index) => {
                edges.push({
                    id: relationship.id || `relationship-${index}`,
                    source: relationship.source_entity_id || relationship.from_entity,
                    target: relationship.target_entity_id || relationship.to_entity,
                    type: 'relationship',
                    data: {
                        label: relationship.name || relationship.id || `Relationship ${index}`,
                        relationshipType: relationship.cardinality || 'one-to-many',
                        description: relationship.description || ''
                    }
                });
            });
        }
        
        console.log(`Converted ${nodes.length} entities to nodes and ${edges.length} relationships to edges`);
        
        return { nodes, edges };
    }
    
    renderGraphView(data) {
        const container = document.getElementById('ontology-visualization');
        
        if (!container) {
            console.error('Visualization container not found');
            this.showError('Visualization container not found');
            return;
        }
        
        try {
            // Create React Flow container with more robust error handling
            container.innerHTML = `
                <div id="react-flow-container" style="width: 100%; height: 100%;">
                    <div class="graph-controls">
                        <div class="btn-group-vertical position-absolute" style="top: 10px; right: 10px; z-index: 1000;">
                            <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.zoomIn()" title="Zoom In">
                                <i class="fas fa-plus"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.zoomOut()" title="Zoom Out">
                                <i class="fas fa-minus"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.fitView()" title="Fit View">
                                <i class="fas fa-expand-arrows-alt"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="ontologyGraph.resetView()" title="Reset View">
                                <i class="fas fa-home"></i>
                            </button>
                        </div>
                    </div>
                    <div id="graph-canvas" style="width: 100%; height: 100%; position: relative;">
                        <!-- Graph visualization will be rendered here -->
                    </div>
                </div>
            `;
            
            // Wait for DOM to be fully rendered before initializing D3 graph with enhanced checks
            requestAnimationFrame(() => {
                setTimeout(() => {
                    // Double-check that elements still exist after DOM manipulation
                    const canvas = document.getElementById('graph-canvas');
                    if (canvas && canvas.parentElement) {
                        this.initializeD3Graph(data);
                    } else {
                        console.error('Graph canvas disappeared after container setup');
                        // Try one more time after a longer delay
                        setTimeout(() => {
                            const retryCanvas = document.getElementById('graph-canvas');
                            if (retryCanvas && retryCanvas.parentElement) {
                                this.initializeD3Graph(data);
                            } else {
                                this.showError('Failed to initialize graph canvas after multiple attempts');
                            }
                        }, 200);
                    }
                }, 100); // Increased delay for better DOM stability
            });
            
        } catch (error) {
            console.error('Error in renderGraphView:', error);
            this.showError(`Failed to render graph view: ${error.message}`);
        }
    }
    
    initializeD3Graph(data) {
        const container = document.getElementById('graph-canvas');
        
        if (!container) {
            console.error('Graph canvas container not found');
            this.showError('Graph canvas container not found');
            return;
        }
        
        // Check if container is properly attached to DOM
        if (!container.parentElement || !document.contains(container)) {
            console.error('Graph canvas container is not properly attached to DOM');
            this.showError('Graph canvas container is not attached to DOM');
            return;
        }
        
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 500;
        
        if (width === 0 || height === 0) {
            console.warn('Container has zero dimensions, using defaults');
            // Don't return here, continue with default dimensions
        }
        
        try {
            // Clear previous graph with safer selection
            const d3Container = d3.select(container);
            if (d3Container.empty()) {
                throw new Error('D3 could not select the container');
            }
            
            d3Container.selectAll("*").remove();
            
            // Create SVG with error checking
            const svg = d3Container
                .append('svg')
                .attr('width', width)
                .attr('height', height)
                .style('background', '#f8f9fa');
            
            if (svg.empty()) {
                throw new Error('Failed to create SVG element');
            }
            
            // Add zoom behavior
            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on('zoom', (event) => {
                    if (g && !g.empty()) {
                        g.attr('transform', event.transform);
                    }
                });
            
            svg.call(zoom);
            
            const g = svg.append('g');
            
            if (g.empty()) {
                throw new Error('Failed to create main group element');
            }
            
            // Validate data
            if (!data || !data.nodes || !data.edges) {
                throw new Error('Invalid data structure provided');
            }
            
            // Validate data arrays
            if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
                throw new Error('Data nodes and edges must be arrays');
            }
            
            // Create force simulation
            const simulation = d3.forceSimulation(data.nodes)
                .force('link', d3.forceLink(data.edges).id(d => d.id).distance(150))
                .force('charge', d3.forceManyBody().strength(-800))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(50));
            
            // Create edges with error checking
            const linkGroup = g.append('g');
            if (linkGroup.empty()) {
                throw new Error('Failed to create link group');
            }
            
            const link = linkGroup
                .selectAll('line')
                .data(data.edges)
                .enter().append('line')
                .attr('class', 'edge')
                .attr('stroke', '#666')
                .attr('stroke-width', 2)
                .attr('marker-end', 'url(#arrowhead)');
            
            // Add arrowhead marker with error checking
            const defs = svg.append('defs');
            if (defs.empty()) {
                throw new Error('Failed to create defs element');
            }
            
            const marker = defs.append('marker')
                .attr('id', 'arrowhead')
                .attr('viewBox', '-0 -5 10 10')
                .attr('refX', 25)
                .attr('refY', 0)
                .attr('orient', 'auto')
                .attr('markerWidth', 8)
                .attr('markerHeight', 8);
            
            marker.append('path')
                .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
                .attr('fill', '#666');
            
            // Create nodes with error checking
            const nodeGroup = g.append('g');
            if (nodeGroup.empty()) {
                throw new Error('Failed to create node group');
            }
            
            const node = nodeGroup
                .selectAll('g')
                .data(data.nodes)
                .enter().append('g')
                .attr('class', 'node')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
            
            // Add node rectangles
            node.append('rect')
                .attr('width', 100)
                .attr('height', 60)
                .attr('x', -50)
                .attr('y', -30)
                .attr('rx', 8)
                .attr('fill', d => this.getNodeColor(d.type))
                .attr('stroke', '#fff')
                .attr('stroke-width', 2)
                .style('cursor', 'pointer')
                .on('click', (event, d) => this.selectNode(d.id))
                .on('mouseover', function() {
                    d3.select(this).attr('stroke-width', 3);
                })
                .on('mouseout', function() {
                    d3.select(this).attr('stroke-width', 2);
                });
            
            // Add node labels
            node.append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '0.35em')
                .attr('fill', 'white')
                .attr('font-weight', 'bold')
                .attr('font-size', '12px')
                .text(d => d.data.label);
            
            // Add node icons
            node.append('text')
                .attr('text-anchor', 'middle')
                .attr('dy', '-10px')
                .attr('fill', 'white')
                .attr('font-family', 'Font Awesome 5 Free')
                .attr('font-weight', '900')
                .attr('font-size', '14px')
                .text(d => this.getNodeIcon(d.type));
            
            // Add edge labels
            const edgeLabelsGroup = g.append('g');
            const edgeLabels = edgeLabelsGroup
                .selectAll('text')
                .data(data.edges)
                .enter().append('text')
                .attr('text-anchor', 'middle')
                .attr('font-size', '10px')
                .attr('fill', '#666')
                .text(d => d.data.label);
            
            // Update positions on simulation tick
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                
                node
                    .attr('transform', d => `translate(${d.x},${d.y})`);
                
                edgeLabels
                    .attr('x', d => (d.source.x + d.target.x) / 2)
                    .attr('y', d => (d.source.y + d.target.y) / 2);
            });
            
            // Store references for external access
            this.graphInstance = {
                svg: svg,
                g: g,
                simulation: simulation,
                zoom: zoom
            };
            
            // Drag functions
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
            
            console.log('D3 graph initialized successfully');
            
        } catch (error) {
            console.error('Error initializing D3 graph:', error);
            this.showError(`Failed to initialize graph: ${error.message}`);
        }
    }
    
    getNodeColor(type) {
        const colors = {
            'class': '#4285f4',
            'property': '#34a853',
            'instance': '#ea4335',
            'relationship': '#fbbc04'
        };
        return colors[type] || colors['class'];
    }
    
    getNodeIcon(type) {
        const icons = {
            'class': '\uf1b2',      // cube
            'property': '\uf02b',   // tag
            'instance': '\uf111',   // circle
            'relationship': '\uf0c1' // link
        };
        return icons[type] || icons['class'];
    }
    
    renderTreeView(data) {
        const container = document.getElementById('ontology-visualization');
        
        container.innerHTML = `
            <div id="tree-container" style="width: 100%; height: 100%; overflow: auto;">
                <div class="tree-controls position-absolute" style="top: 10px; right: 10px; z-index: 1000;">
                    <div class="btn-group-vertical">
                        <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.expandAllTree()" title="Expand All">
                            <i class="fas fa-plus-square"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-primary" onclick="ontologyGraph.collapseAllTree()" title="Collapse All">
                            <i class="fas fa-minus-square"></i>
                        </button>
                    </div>
                </div>
                <div id="tree-content" class="p-3">
                    <!-- Tree structure will be rendered here -->
                </div>
            </div>
        `;
        
        this.initializeTreeView(data);
    }
    
    initializeTreeView(data) {
        const treeContent = document.getElementById('tree-content');
        
        // Build hierarchical structure from flat node/edge data
        const hierarchy = this.buildHierarchy(data);
        
        // Render tree structure
        treeContent.innerHTML = this.renderTreeNode(hierarchy, 0);
    }
    
    buildHierarchy(data) {
        // Create a simple hierarchy based on relationships
        const nodeMap = new Map(data.nodes.map(node => [node.id, { ...node, children: [] }]));
        const roots = [];
        
        // Process edges to build parent-child relationships
        data.edges.forEach(edge => {
            const parent = nodeMap.get(edge.source);
            const child = nodeMap.get(edge.target);
            
            if (parent && child) {
                if (!parent.children) parent.children = [];
                parent.children.push(child);
                child.parent = parent;
            }
        });
        
        // Find root nodes (nodes without parents)
        data.nodes.forEach(node => {
            const hierarchyNode = nodeMap.get(node.id);
            if (!hierarchyNode.parent) {
                roots.push(hierarchyNode);
            }
        });
        
        return roots.length > 0 ? roots : Array.from(nodeMap.values()).slice(0, 1);
    }
    
    renderTreeNode(nodes, level) {
        if (!Array.isArray(nodes)) {
            nodes = [nodes];
        }
        
        return nodes.map(node => {
            const hasChildren = node.children && node.children.length > 0;
            const indent = level * 20;
            
            return `
                <div class="tree-node" data-node-id="${node.id}" style="margin-left: ${indent}px;">
                    <div class="tree-node-content d-flex align-items-center py-2 px-3 mb-1 rounded cursor-pointer" 
                         onclick="ontologyGraph.selectNode('${node.id}')"
                         onmouseover="this.style.backgroundColor='#f8f9fa'"
                         onmouseout="this.style.backgroundColor='transparent'">
                        ${hasChildren ? 
                            `<button class="btn btn-sm btn-link p-0 me-2" onclick="event.stopPropagation(); ontologyGraph.toggleTreeNode('${node.id}')">
                                <i class="fas fa-chevron-down tree-toggle"></i>
                            </button>` : 
                            '<span style="width: 24px; display: inline-block;"></span>'
                        }
                        <i class="fas ${this.getTreeNodeIcon(node.type)} me-2" style="color: ${this.getNodeColor(node.type)};"></i>
                        <span class="fw-bold">${node.data.label}</span>
                        <span class="badge bg-secondary ms-2">${node.type}</span>
                    </div>
                    ${hasChildren ? 
                        `<div class="tree-children" data-parent="${node.id}">
                            ${this.renderTreeNode(node.children, level + 1)}
                        </div>` : 
                        ''
                    }
                </div>
            `;
        }).join('');
    }
    
    getTreeNodeIcon(type) {
        const icons = {
            'class': 'fa-cube',
            'property': 'fa-tag',
            'instance': 'fa-circle',
            'relationship': 'fa-link'
        };
        return icons[type] || icons['class'];
    }
    
    selectNode(nodeId) {
        const node = this.findNodeById(nodeId);
        if (!node) {
            this.showToast('Node not found', 'error');
            return;
        }
        
        this.selectedNode = node;
        
        // Close any open modals
        const connectionsModal = document.getElementById('connectionsModal');
        if (connectionsModal) {
            const modalInstance = bootstrap.Modal.getInstance(connectionsModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
        
        // Update node details panel
        this.updateNodeDetails(node);
        
        // Highlight the selected node in the visualization
        try {
            if (this.graphInstance && this.graphInstance.svg) {
                const svg = this.graphInstance.svg;
                
                // Reset all node styles first
                svg.selectAll('.node rect')
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 2)
                    .style('filter', 'none');
                
                // Highlight the selected node
                svg.selectAll('.node')
                    .filter(d => d.id === nodeId)
                    .select('rect')
                    .attr('stroke', '#ffc107')
                    .attr('stroke-width', 4)
                    .style('filter', 'drop-shadow(0 0 10px rgba(255, 193, 7, 0.8))');
            }
        } catch (error) {
            console.error('Error highlighting selected node:', error);
        }
        
        this.showToast(`Selected node: ${node.data.label}`, 'info');
    }
    
    findNodeById(nodeId) {
        if (!this.currentOntology || !this.sampleData[this.currentOntology]) return null;
        return this.sampleData[this.currentOntology].nodes.find(n => n.id === nodeId);
    }
    
    updateNodeDetails(node) {
        const detailsContainer = document.getElementById('entity-details');
        if (!detailsContainer) return;
        
        detailsContainer.innerHTML = `
            <div class="node-details">
                <div class="d-flex align-items-center mb-3">
                    <i class="fas ${this.getTreeNodeIcon(node.type)} me-2" style="color: ${this.getNodeColor(node.type)}; font-size: 1.2em;"></i>
                    <h6 class="mb-0">${node.data.label}</h6>
                    <span class="badge bg-primary ms-2">${node.type}</span>
                </div>
                
                <div class="mb-3">
                    <strong>Description:</strong>
                    <p class="text-muted mt-1">${node.data.description || 'No description available'}</p>
                </div>
                
                <div class="mb-3">
                    <strong>Properties:</strong>
                    <div class="mt-2">
                        ${node.data.properties ? 
                            node.data.properties.map(prop => `
                                <span class="badge bg-light text-dark me-1 mb-1">${prop}</span>
                            `).join('') :
                            '<span class="text-muted">No properties defined</span>'
                        }
                    </div>
                </div>
                
                <div class="mb-3">
                    <strong>Node ID:</strong>
                    <code class="text-muted">${node.id}</code>
                </div>
                
                <div class="action-buttons mt-3">
                    <button class="btn btn-sm btn-outline-primary me-2" onclick="ontologyGraph.editNode('${node.id}')">
                        <i class="fas fa-edit me-1"></i>Edit
                    </button>
                    <button class="btn btn-sm btn-outline-info me-2" onclick="ontologyGraph.viewNodeConnections('${node.id}')">
                        <i class="fas fa-link me-1"></i>Connections
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="ontologyGraph.deleteNode('${node.id}')">
                        <i class="fas fa-trash me-1"></i>Delete
                    </button>
                </div>
            </div>
        `;
    }
    
    highlightSelectedNode(nodeId) {
        // Remove previous highlights
        if (this.currentView === 'graph' && this.graphInstance) {
            const svg = this.graphInstance.svg;
            svg.selectAll('.node rect').attr('stroke-width', 2);
            svg.selectAll('.node').filter(d => d.id === nodeId)
                .select('rect').attr('stroke-width', 4).attr('stroke', '#ff6b35');
        } else if (this.currentView === 'tree') {
            document.querySelectorAll('.tree-node-content').forEach(el => {
                el.style.backgroundColor = 'transparent';
            });
            const selectedElement = document.querySelector(`[data-node-id="${nodeId}"] .tree-node-content`);
            if (selectedElement) {
                selectedElement.style.backgroundColor = '#e3f2fd';
            }
        }
    }
    
    // Control functions
    refresh() {
        if (this.currentOntology) {
            this.loadOntologyGraph(this.currentOntology);
            this.showToast('Ontology visualization refreshed', 'success');
        } else {
            this.showToast('No ontology selected', 'warning');
        }
    }
    
    toggleFullscreen() {
        const container = document.getElementById('ontology-visualization').closest('.card');
        
        if (!this.isFullscreen) {
            // Enter fullscreen
            if (container.requestFullscreen) {
                container.requestFullscreen();
            } else if (container.webkitRequestFullscreen) {
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) {
                container.msRequestFullscreen();
            }
            this.isFullscreen = true;
            container.classList.add('fullscreen-card');
        } else {
            this.exitFullscreen();
        }
    }
    
    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        this.isFullscreen = false;
        const container = document.getElementById('ontology-visualization').closest('.card');
        container.classList.remove('fullscreen-card');
    }
    
    switchView(viewType) {
        this.currentView = viewType;
        
        // Update button states
        document.querySelectorAll('.btn-group button').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
        
        if (this.currentOntology) {
            this.loadOntologyGraph(this.currentOntology);
        }
        
        this.showToast(`Switched to ${viewType} view`, 'info');
    }
    
    // Graph control functions
    zoomIn() {
        if (this.graphInstance && this.graphInstance.zoom) {
            const svg = this.graphInstance.svg;
            svg.transition().call(this.graphInstance.zoom.scaleBy, 1.5);
        }
    }
    
    zoomOut() {
        if (this.graphInstance && this.graphInstance.zoom) {
            const svg = this.graphInstance.svg;
            svg.transition().call(this.graphInstance.zoom.scaleBy, 0.67);
        }
    }
    
    fitView() {
        if (this.graphInstance && this.graphInstance.zoom) {
            const svg = this.graphInstance.svg;
            const container = document.getElementById('graph-canvas');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            svg.transition().call(
                this.graphInstance.zoom.transform,
                d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
            );
        }
    }
    
    resetView() {
        if (this.graphInstance && this.graphInstance.zoom) {
            const svg = this.graphInstance.svg;
            svg.transition().call(
                this.graphInstance.zoom.transform,
                d3.zoomIdentity
            );
        }
    }
    
    // Tree control functions
    toggleTreeNode(nodeId) {
        const childrenContainer = document.querySelector(`[data-parent="${nodeId}"]`);
        const toggleIcon = document.querySelector(`[onclick*="${nodeId}"] .tree-toggle`);
        
        if (childrenContainer && toggleIcon) {
            if (childrenContainer.style.display === 'none') {
                childrenContainer.style.display = 'block';
                toggleIcon.classList.remove('fa-chevron-right');
                toggleIcon.classList.add('fa-chevron-down');
            } else {
                childrenContainer.style.display = 'none';
                toggleIcon.classList.remove('fa-chevron-down');
                toggleIcon.classList.add('fa-chevron-right');
            }
        }
    }
    
    expandAllTree() {
        document.querySelectorAll('.tree-children').forEach(el => {
            el.style.display = 'block';
        });
        document.querySelectorAll('.tree-toggle').forEach(icon => {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
        });
        this.showToast('All tree nodes expanded', 'info');
    }
    
    collapseAllTree() {
        document.querySelectorAll('.tree-children').forEach(el => {
            el.style.display = 'none';
        });
        document.querySelectorAll('.tree-toggle').forEach(icon => {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
        });
        this.showToast('All tree nodes collapsed', 'info');
    }
    
    // Node action functions
    editNode(nodeId) {
        const node = this.findNodeById(nodeId);
        if (!node) {
            this.showToast('Node not found', 'error');
            return;
        }
        
        this.openEditNodeModal(node);
    }
    
    openEditNodeModal(node) {
        // Create modal HTML
        const modalHtml = `
            <div class="modal fade" id="editNodeModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-edit me-2"></i>Edit Node
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editNodeForm">
                                <div class="mb-3">
                                    <label for="nodeName" class="form-label">Node Name *</label>
                                    <input type="text" class="form-control" id="nodeName" value="${node.data.label}" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="nodeType" class="form-label">Node Type</label>
                                    <select class="form-select" id="nodeType">
                                        <option value="class" ${node.type === 'class' ? 'selected' : ''}>Class</option>
                                        <option value="property" ${node.type === 'property' ? 'selected' : ''}>Property</option>
                                        <option value="instance" ${node.type === 'instance' ? 'selected' : ''}>Instance</option>
                                        <option value="relationship" ${node.type === 'relationship' ? 'selected' : ''}>Relationship</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="nodeDescription" class="form-label">Description</label>
                                    <textarea class="form-control" id="nodeDescription" rows="3">${node.data.description || ''}</textarea>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="nodeProperties" class="form-label">Properties</label>
                                    <div id="propertiesList">
                                        ${(node.data.properties || []).map((prop, index) => `
                                            <div class="input-group mb-2 property-item">
                                                <input type="text" class="form-control" value="${prop}" name="property">
                                                <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        `).join('')}
                                    </div>
                                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="addProperty()">
                                        <i class="fas fa-plus"></i> Add Property
                                    </button>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="saveNodeEdits('${node.id}')">
                                <i class="fas fa-save"></i> Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('editNodeModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editNodeModal'));
        modal.show();
    }
    
    saveNodeEdits(nodeId) {
        const node = this.findNodeById(nodeId);
        if (!node) return;
        
        const form = document.getElementById('editNodeForm');
        const formData = new FormData(form);
        
        // Validate form
        const nodeName = document.getElementById('nodeName').value.trim();
        if (!nodeName) {
            this.showToast('Node name is required', 'warning');
            return;
        }
        
        // Check for duplicate names (excluding current node)
        const currentData = this.sampleData[this.currentOntology];
        const duplicateNode = currentData.nodes.find(n => 
            n.id !== nodeId && n.data.label.toLowerCase() === nodeName.toLowerCase()
        );
        
        if (duplicateNode) {
            this.showToast('A node with this name already exists', 'warning');
            return;
        }
        
        // Create change record for undo
        const changeId = ++this.currentChangeId;
        const change = {
            id: changeId,
            type: 'EDIT_NODE',
            timestamp: new Date().toISOString(),
            beforeState: structuredClone(currentData),
            nodeId: nodeId
        };
        
        // Update node data
        node.data.label = nodeName;
        node.type = document.getElementById('nodeType').value;
        node.data.description = document.getElementById('nodeDescription').value;
        
        // Update properties
        const propertyInputs = document.querySelectorAll('#propertiesList input[name="property"]');
        node.data.properties = Array.from(propertyInputs).map(input => input.value.trim()).filter(prop => prop);
        
        // Record change
        change.afterState = structuredClone(currentData);
        this.changeHistory.push(change);
        
        // Update visualization
        this.loadOntologyGraph(this.currentOntology);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editNodeModal'));
        modal.hide();
        
        this.showToast('Node updated successfully', 'success');
    }
    
    viewNodeConnections(nodeId) {
        const node = this.findNodeById(nodeId);
        if (!node) {
            this.showToast('Node not found', 'error');
            return;
        }
        
        this.openConnectionsModal(node);
    }
    
    openConnectionsModal(node) {
        const currentData = this.sampleData[this.currentOntology];
        const connections = currentData.edges.filter(edge => 
            edge.source === node.id || edge.target === node.id
        );
        
        const modalHtml = `
            <div class="modal fade" id="connectionsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-link me-2"></i>Connections for "${node.data.label}"
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${connections.length > 0 ? `
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Relationship</th>
                                                <th>Direction</th>
                                                <th>Connected Node</th>
                                                <th>Type</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${connections.map(edge => {
                                                const isOutgoing = edge.source === node.id;
                                                const connectedNodeId = isOutgoing ? edge.target : edge.source;
                                                const connectedNode = currentData.nodes.find(n => n.id === connectedNodeId);
                                                return `
                                                    <tr>
                                                        <td>
                                                            <strong>${edge.data.label}</strong>
                                                            ${edge.data.description ? `<br><small class="text-muted">${edge.data.description}</small>` : ''}
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-${isOutgoing ? 'primary' : 'secondary'}">
                                                                ${isOutgoing ? 'Outgoing' : 'Incoming'}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <i class="fas ${this.getTreeNodeIcon(connectedNode?.type || 'class')} me-2"></i>
                                                            ${connectedNode?.data.label || 'Unknown'}
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-info">${edge.data.relationshipType || 'relationship'}</span>
                                                        </td>
                                                        <td>
                                                            <button class="btn btn-sm btn-outline-primary me-1" onclick="ontologyGraph.selectNode('${connectedNodeId}')">
                                                                <i class="fas fa-eye"></i>
                                                            </button>
                                                            <button class="btn btn-sm btn-outline-warning me-1" onclick="ontologyGraph.editConnection('${edge.id}')">
                                                                <i class="fas fa-edit"></i>
                                                            </button>
                                                            <button class="btn btn-sm btn-outline-danger" onclick="ontologyGraph.deleteConnection('${edge.id}')">
                                                                <i class="fas fa-trash"></i>
                                                            </button>
                                                        </td>
                                                    </tr>
                                                `;
                                            }).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            ` : `
                                <div class="text-center py-4">
                                    <i class="fas fa-link fa-3x text-muted mb-3"></i>
                                    <h5 class="text-muted">No connections found</h5>
                                    <p class="text-muted">This node is not connected to any other nodes.</p>
                                    <button class="btn btn-primary" onclick="ontologyGraph.toggleConnectionMode()">
                                        <i class="fas fa-plus"></i> Create Connection
                                    </button>
                                </div>
                            `}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" onclick="ontologyGraph.toggleConnectionMode()">
                                <i class="fas fa-plus"></i> Add New Connection
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('connectionsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('connectionsModal'));
        modal.show();
    }
    
    deleteNode(nodeId) {
        const node = this.findNodeById(nodeId);
        if (!node) {
            this.showToast('Node not found', 'error');
            return;
        }
        
        this.openDeleteConfirmModal(node, 'node');
    }
    
    openDeleteConfirmModal(item, type) {
        const isNode = type === 'node';
        const title = isNode ? item.data.label : item.data.label;
        const currentData = this.sampleData[this.currentOntology];
        
        let dependencyWarning = '';
        if (isNode) {
            const connectedEdges = currentData.edges.filter(edge => 
                edge.source === item.id || edge.target === item.id
            );
            if (connectedEdges.length > 0) {
                dependencyWarning = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        This node has ${connectedEdges.length} connection(s) that will also be deleted.
                    </div>
                `;
            }
        }
        
        const modalHtml = `
            <div class="modal fade" id="deleteConfirmModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle me-2"></i>Confirm Deletion
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${dependencyWarning}
                            <p>Are you sure you want to delete the ${type} <strong>"${title}"</strong>?</p>
                            <p class="text-muted small">This action cannot be undone (unless you use the Undo feature).</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger" onclick="ontologyGraph.confirmDelete('${item.id}', '${type}')">
                                <i class="fas fa-trash"></i> Delete ${type === 'node' ? 'Node' : 'Connection'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('deleteConfirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();
    }
    
    confirmDelete(itemId, type) {
        const currentData = this.sampleData[this.currentOntology];
        
        // Create change record for undo
        const changeId = ++this.currentChangeId;
        const change = {
            id: changeId,
            type: type === 'node' ? 'DELETE_NODE' : 'DELETE_CONNECTION',
            timestamp: new Date().toISOString(),
            beforeState: structuredClone(currentData),
            itemId: itemId
        };
        
        if (type === 'node') {
            // Delete node and all connected edges
            const nodeIndex = currentData.nodes.findIndex(n => n.id === itemId);
            if (nodeIndex >= 0) {
                currentData.nodes.splice(nodeIndex, 1);
                
                // Remove all edges connected to this node
                currentData.edges = currentData.edges.filter(edge => 
                    edge.source !== itemId && edge.target !== itemId
                );
            }
        } else {
            // Delete connection only
            const edgeIndex = currentData.edges.findIndex(e => e.id === itemId);
            if (edgeIndex >= 0) {
                currentData.edges.splice(edgeIndex, 1);
            }
        }
        
        // Record change
        change.afterState = structuredClone(currentData);
        this.changeHistory.push(change);
        
        // Update visualization
        this.loadOntologyGraph(this.currentOntology);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
        modal.hide();
        
        // Close connections modal if open
        const connectionsModal = document.getElementById('connectionsModal');
        if (connectionsModal) {
            const connectionModalInstance = bootstrap.Modal.getInstance(connectionsModal);
            if (connectionModalInstance) {
                connectionModalInstance.hide();
            }
        }
        
        this.showToast(`${type === 'node' ? 'Node' : 'Connection'} deleted successfully`, 'success');
    }
    
    editConnection(edgeId) {
        const currentData = this.sampleData[this.currentOntology];
        const edge = currentData.edges.find(e => e.id === edgeId);
        
        if (!edge) {
            this.showToast('Connection not found', 'error');
            return;
        }
        
        // For now, just show a simple alert - can be expanded later
        this.showToast('Connection editing will be implemented in the next version', 'info');
    }
    
    resizeVisualization() {
        if (this.currentOntology) {
            setTimeout(() => {
                this.loadOntologyGraph(this.currentOntology);
            }, 100);
        }
    }
    
    updateControls() {
        // Update control button states based on current view and selection
        const refreshBtn = document.querySelector('[onclick*="refreshVisualization"]');
        const fullscreenBtn = document.querySelector('[onclick*="fullScreenView"]');
        
        if (refreshBtn && this.currentOntology) {
            refreshBtn.disabled = false;
            refreshBtn.title = 'Refresh visualization';
        }
        
        if (fullscreenBtn) {
            const icon = fullscreenBtn.querySelector('i');
            if (this.isFullscreen) {
                icon.classList.remove('fa-expand');
                icon.classList.add('fa-compress');
                fullscreenBtn.title = 'Exit fullscreen';
            } else {
                icon.classList.remove('fa-compress');
                icon.classList.add('fa-expand');
                fullscreenBtn.title = 'Enter fullscreen';
            }
        }
    }
    
    showError(message) {
        // Enhanced error logging
        console.error('=== ONTOLOGY GRAPH ERROR ===');
        console.error('Error message:', message);
        console.error('Current ontology:', this.currentOntology);
        console.error('Available sample data keys:', Object.keys(this.sampleData));
        console.error('Current view:', this.currentView);
        console.error('Timestamp:', new Date().toISOString());
        console.error('==============================');
        
        const container = document.getElementById('ontology-visualization');
        
        if (!container) {
            console.error('Visualization container not found when trying to show error');
            return;
        }
        
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <h5 class="text-danger">Error</h5>
                    <p class="text-muted">${message}</p>
                    <div class="mt-3">
                        <button class="btn btn-primary me-2" onclick="ontologyGraph.refresh()">
                            <i class="fas fa-sync me-2"></i>Try Again
                        </button>
                        <button class="btn btn-secondary" onclick="console.log('Debug info:', { currentOntology: ontologyGraph.currentOntology, sampleDataKeys: Object.keys(ontologyGraph.sampleData), currentView: ontologyGraph.currentView })">
                            <i class="fas fa-bug me-2"></i>Debug Info
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    showToast(message, type = 'info') {
        // Use existing toast function if available
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    /**
     * Immutable data update helper using structured cloning
     */
    immutableUpdate(obj, updateFn) {
        try {
            // Use structuredClone for deep copying (modern browsers)
            const cloned = structuredClone(obj);
            updateFn(cloned);
            return cloned;
        } catch (error) {
            // Fallback to JSON deep copy for older browsers
            const cloned = JSON.parse(JSON.stringify(obj));
            updateFn(cloned);
            return cloned;
        }
    }
    
    /**
     * Generate unique ID for new nodes/edges
     */
    generateUniqueId(prefix = 'node') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Calculate optimal position for new node
     */
    calculateNewNodePosition(existingNodes, nodeType) {
        const positions = existingNodes.map(node => node.position);
        
        // Find a position that doesn't overlap
        let x = 100;
        let y = 100;
        const spacing = 150;
        
        // Simple grid-based positioning
        const maxX = Math.max(...positions.map(p => p.x), 0);
        const maxY = Math.max(...positions.map(p => p.y), 0);
        
        if (nodeType === 'class') {
            x = maxX + spacing;
            y = 100;
        } else if (nodeType === 'property') {
            x = 100;
            y = maxY + spacing;
        } else {
            x = maxX + spacing;
            y = maxY + spacing;
        }
        
        return { x, y };
    }
    
    /**
     * Validate suggestion before applying
     */
    validateSuggestion(suggestion, currentData) {
        const validation = {
            valid: true,
            errors: [],
            warnings: []
        };
        
        if (suggestion.type === 'ontology_class') {
            // Check for duplicate class names
            const existingNode = currentData.nodes.find(
                node => node.data.label.toLowerCase() === suggestion.title.toLowerCase()
            );
            if (existingNode) {
                validation.errors.push(`Class "${suggestion.title}" already exists`);
                validation.valid = false;
            }
        } else if (suggestion.type === 'relationship') {
            // Validate relationship endpoints
            if (!suggestion.sourceNode || !suggestion.targetNode) {
                validation.errors.push('Relationship must specify source and target nodes');
                validation.valid = false;
            }
        }
        
        return validation;
    }
    
    /**
     * Apply AI suggestion to ontology data
     */
    applySuggestion(suggestionId, suggestion) {
        console.log('=== applySuggestion START ===');
        console.log('suggestionId:', suggestionId);
        console.log('suggestion:', suggestion);
        
        if (!this.currentOntology) {
            console.log('No ontology selected');
            this.showToast('No ontology selected', 'warning');
            return false;
        }
        
        if (this.appliedSuggestions.has(suggestionId)) {
            console.log('Suggestion already applied');
            this.showToast('Suggestion already applied', 'info');
            return false;
        }
        
        const currentData = this.sampleData[this.currentOntology];
        if (!currentData) {
            console.log('Current ontology data not found');
            this.showToast('Current ontology data not found', 'danger');
            return false;
        }
        
        const validation = this.validateSuggestion(suggestion, currentData);
        
        if (!validation.valid) {
            console.log('Validation failed:', validation.errors);
            this.showToast(`Cannot apply suggestion: ${validation.errors.join(', ')}`, 'danger');
            return false;
        }
        
        try {
            console.log('=== DOM VERIFICATION START ===');
            
            // Enhanced DOM verification with multiple checks
            const container = document.getElementById('ontology-visualization');
            console.log('Container found:', !!container);
            console.log('Container parent:', !!container?.parentElement);
            console.log('Container in document:', container ? document.contains(container) : false);
            
            if (!container) {
                throw new Error('Ontology visualization container not found in DOM');
            }
            
            if (!container.parentElement) {
                throw new Error('Ontology visualization container has no parent');
            }
            
            if (!document.contains(container)) {
                throw new Error('Ontology visualization container is not attached to document');
            }
            
            // Check for any existing modals or overlays that might interfere
            const existingModals = document.querySelectorAll('.modal.show');
            console.log('Existing modals:', existingModals.length);
            
            // Verify document readiness
            console.log('Document ready state:', document.readyState);
            console.log('Document body:', !!document.body);
            
            console.log('=== DOM VERIFICATION PASSED ===');
            
            // Create change record
            const changeId = ++this.currentChangeId;
            const change = {
                id: changeId,
                suggestionId,
                suggestion,
                timestamp: new Date().toISOString(),
                type: 'APPLY_SUGGESTION',
                beforeState: this.deepClone(currentData)
            };
            
            console.log('Change record created:', change.id);
            
            // Apply the suggestion based on type
            let updatedData;
            console.log('Applying suggestion type:', suggestion.type);
            
            switch (suggestion.type) {
                case 'ontology_class':
                    console.log('Applying class suggestion...');
                    updatedData = this.applyClassSuggestion(currentData, suggestion);
                    change.type = 'ADD_NODE';
                    break;
                case 'property':
                    console.log('Applying property suggestion...');
                    updatedData = this.applyPropertySuggestion(currentData, suggestion);
                    change.type = 'EDIT_NODE';
                    break;
                case 'relationship':
                    console.log('Applying relationship suggestion...');
                    updatedData = this.applyRelationshipSuggestion(currentData, suggestion);
                    change.type = 'CREATE_CONNECTION';
                    break;
                case 'enhancement':
                    console.log('Applying enhancement suggestion...');
                    updatedData = this.applyEnhancementSuggestion(currentData, suggestion);
                    change.type = 'EDIT_NODE';
                    break;
                default:
                    throw new Error(`Unknown suggestion type: ${suggestion.type}`);
            }
            
            console.log('Suggestion applied, validating updated data...');
            
            // Validate updated data
            if (!updatedData || !updatedData.nodes || !updatedData.edges) {
                throw new Error('Invalid updated data structure');
            }
            
            console.log('Updated data valid, updating state...');
            
            // Update the data
            this.sampleData[this.currentOntology] = updatedData;
            change.afterState = this.deepClone(updatedData);
            
            // Record the change
            this.changeHistory.push(change);
            this.appliedSuggestions.add(suggestionId);
            
            console.log('State updated, starting visualization update...');
            
            // Use enhanced visualization update with better error isolation
            this.safeUpdateVisualizationEnhanced(change)
                .then(() => {
                    console.log('Visualization update completed successfully');
                    // Update suggestion UI
                    this.updateSuggestionStatus(suggestionId, 'applied');
                    this.showToast(`Applied suggestion: ${suggestion.title}`, 'success');
                })
                .catch((error) => {
                    console.error('Visualization update failed:', error);
                    this.showToast('Suggestion applied but visualization update failed', 'warning');
                });
            
            console.log('=== applySuggestion SUCCESS ===');
            return true;
            
        } catch (error) {
            console.error('=== applySuggestion ERROR ===');
            console.error('Error details:', error);
            console.error('Error stack:', error.stack);
            this.showToast(`Failed to apply suggestion: ${error.message}`, 'danger');
            return false;
        }
    }
    
    /**
     * Enhanced deep cloning that handles all cases safely
     */
    deepClone(obj) {
        try {
            // First try structuredClone (most reliable)
            if (typeof structuredClone !== 'undefined') {
                return structuredClone(obj);
            }
        } catch (error) {
            console.warn('structuredClone failed, trying JSON method:', error);
        }
        
        try {
            // Fallback to JSON deep copy
            return JSON.parse(JSON.stringify(obj));
        } catch (error) {
            console.error('All cloning methods failed:', error);
            throw new Error('Failed to clone data structure');
        }
    }
    
    /**
     * Enhanced safe visualization update with better error isolation
     */
    safeUpdateVisualizationEnhanced(change) {
        return new Promise((resolve, reject) => {
            console.log('=== safeUpdateVisualizationEnhanced START ===');
            
            try {
                // Pre-flight checks
                const container = document.getElementById('ontology-visualization');
                if (!container) {
                    throw new Error('Visualization container disappeared');
                }
                
                if (!document.contains(container)) {
                    throw new Error('Visualization container detached from DOM');
                }
                
                console.log('Pre-flight checks passed');
                
                // Use a more robust retry mechanism
                const updateWithEnhancedRetry = (retries = 5, delay = 200) => {
                    console.log(`Update attempt, retries left: ${retries}`);
                    
                    if (retries <= 0) {
                        reject(new Error('Failed to update visualization after all retries'));
                        return;
                    }
                    
                    // Create a safe execution environment
                    const safeExecute = () => {
                        try {
                            console.log('Starting safe execution...');
                            
                            // Verify DOM state before each attempt
                            const currentContainer = document.getElementById('ontology-visualization');
                            if (!currentContainer || !document.contains(currentContainer)) {
                                throw new Error('Container state changed during update');
                            }
                            
                            console.log('Container verification passed, loading graph...');
                            
                            // The actual update - wrap in try-catch to isolate appendChild errors
                            this.safeLoadOntologyGraph(this.currentOntology)
                                .then(() => {
                                    console.log('Graph loaded successfully, applying highlights...');
                                    
                                    // Apply highlights after another delay
                                    setTimeout(() => {
                                        try {
                                            this.highlightChanges(change);
                                            
                                            // Update node details if needed
                                            if (this.selectedNode) {
                                                const updatedNode = this.findNodeById(this.selectedNode.id);
                                                if (updatedNode) {
                                                    this.updateNodeDetails(updatedNode);
                                                }
                                            }
                                            
                                            console.log('=== safeUpdateVisualizationEnhanced SUCCESS ===');
                                            resolve();
                                        } catch (highlightError) {
                                            console.warn('Highlight error (non-critical):', highlightError);
                                            resolve(); // Still resolve as main update succeeded
                                        }
                                    }, 400);
                                })
                                .catch((loadError) => {
                                    console.warn(`Graph load failed, retrying... (${retries - 1} left)`, loadError);
                                    setTimeout(() => updateWithEnhancedRetry(retries - 1, delay * 1.5), delay);
                                });
                                
                        } catch (executeError) {
                            console.warn(`Execution failed, retrying... (${retries - 1} left)`, executeError);
                            setTimeout(() => updateWithEnhancedRetry(retries - 1, delay * 1.5), delay);
                        }
                    };
                    
                    // Use multiple async layers for maximum DOM stability
                    requestAnimationFrame(() => {
                        setTimeout(() => {
                            requestAnimationFrame(() => {
                                setTimeout(safeExecute, 50);
                            });
                        }, delay);
                    });
                };
                
                updateWithEnhancedRetry();
                
            } catch (error) {
                console.error('Critical error in safeUpdateVisualizationEnhanced:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Safe wrapper for loadOntologyGraph
     */
    safeLoadOntologyGraph(ontologyId) {
        return new Promise((resolve, reject) => {
            console.log('=== safeLoadOntologyGraph START ===');
            
            try {
                if (!ontologyId || !this.sampleData[ontologyId]) {
                    throw new Error('Invalid ontology data');
                }
                
                const data = this.sampleData[ontologyId];
                console.log('Data validation passed, nodes:', data.nodes.length, 'edges:', data.edges.length);
                
                // Verify container one more time
                const container = document.getElementById('ontology-visualization');
                if (!container) {
                    throw new Error('Container not found during safe load');
                }
                
                console.log('Container verified, rendering view...');
                
                if (this.currentView === 'graph') {
                    this.safeRenderGraphView(data).then(resolve).catch(reject);
                } else {
                    this.safeRenderTreeView(data).then(resolve).catch(reject);
                }
                
            } catch (error) {
                console.error('Error in safeLoadOntologyGraph:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Safe wrapper for renderGraphView
     */
    safeRenderGraphView(data) {
        return new Promise((resolve, reject) => {
            console.log('=== safeRenderGraphView START ===');
            
            try {
                const container = document.getElementById('ontology-visualization');
                
                if (!container) {
                    throw new Error('Visualization container not found');
                }
                
                console.log('Creating new container HTML...');
                
                // Use a safer approach to replace innerHTML
                const newContent = `
                    <div id="react-flow-container" style="width: 100%; height: 100%;">
                        <div class="graph-controls">
                            <div class="btn-group-vertical position-absolute" style="top: 10px; right: 10px; z-index: 1000;">
                                <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.zoomIn()" title="Zoom In">
                                    <i class="fas fa-plus"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.zoomOut()" title="Zoom Out">
                                    <i class="fas fa-minus"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.fitView()" title="Fit View">
                                    <i class="fas fa-expand-arrows-alt"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-primary" onclick="ontologyGraph.resetView()" title="Reset View">
                                    <i class="fas fa-home"></i>
                                </button>
                            </div>
                        </div>
                        <div id="graph-canvas" style="width: 100%; height: 100%; position: relative;">
                            <!-- Graph visualization will be rendered here -->
                        </div>
                    </div>
                `;
                
                // Clear and set new content safely
                while (container.firstChild) {
                    container.removeChild(container.firstChild);
                }
                
                container.innerHTML = newContent;
                
                console.log('Container HTML updated, waiting for DOM...');
                
                // Enhanced DOM readiness checking
                const waitForCanvas = (attempts = 10) => {
                    if (attempts <= 0) {
                        reject(new Error('Canvas element never became available'));
                        return;
                    }
                    
                    const canvas = document.getElementById('graph-canvas');
                    console.log(`Canvas check attempt ${11 - attempts}:`, !!canvas, !!canvas?.parentElement);
                    
                    if (canvas && canvas.parentElement && document.contains(canvas)) {
                        console.log('Canvas is ready, initializing D3...');
                        
                        this.safeInitializeD3Graph(data)
                            .then(() => {
                                console.log('=== safeRenderGraphView SUCCESS ===');
                                resolve();
                            })
                            .catch(reject);
                    } else {
                        setTimeout(() => waitForCanvas(attempts - 1), 100);
                    }
                };
                
                // Start waiting for canvas
                requestAnimationFrame(() => {
                    setTimeout(() => waitForCanvas(), 150);
                });
                
            } catch (error) {
                console.error('Error in safeRenderGraphView:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Safe wrapper for initializeD3Graph
     */
    safeInitializeD3Graph(data) {
        return new Promise((resolve, reject) => {
            console.log('=== safeInitializeD3Graph START ===');
            
            try {
                const container = document.getElementById('graph-canvas');
                
                if (!container) {
                    throw new Error('Graph canvas container not found');
                }
                
                if (!container.parentElement || !document.contains(container)) {
                    throw new Error('Graph canvas container is not properly attached to DOM');
                }
                
                const width = container.clientWidth || 800;
                const height = container.clientHeight || 500;
                
                console.log('Container dimensions:', width, 'x', height);
                
                // Validate data before proceeding
                if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
                    throw new Error('Invalid data structure for D3 graph');
                }
                
                console.log('Data validated, creating D3 elements...');
                
                // Clear previous graph with enhanced safety
                const d3Container = d3.select(container);
                if (d3Container.empty()) {
                    throw new Error('D3 could not select the container');
                }
                
                // Remove all children safely
                d3Container.selectAll("*").remove();
                
                console.log('Previous content cleared, creating SVG...');
                
                // Create SVG with comprehensive error checking
                const svg = d3Container
                    .append('svg')
                    .attr('width', width)
                    .attr('height', height)
                    .style('background', '#f8f9fa');
                
                if (svg.empty() || !svg.node()) {
                    throw new Error('Failed to create SVG element');
                }
                
                console.log('SVG created successfully');
                
                // Continue with the rest of the D3 setup...
                const zoom = d3.zoom()
                    .scaleExtent([0.1, 4])
                    .on('zoom', (event) => {
                        if (g && !g.empty()) {
                            g.attr('transform', event.transform);
                        }
                    });
                
                svg.call(zoom);
                
                const g = svg.append('g');
                
                if (g.empty()) {
                    throw new Error('Failed to create main group element');
                }
                
                console.log('Basic D3 structure created, adding simulation...');
                
                // Create force simulation
                const simulation = d3.forceSimulation(data.nodes)
                    .force('link', d3.forceLink(data.edges).id(d => d.id).distance(150))
                    .force('charge', d3.forceManyBody().strength(-800))
                    .force('center', d3.forceCenter(width / 2, height / 2))
                    .force('collision', d3.forceCollide().radius(50));
                
                console.log('Force simulation created, adding visual elements...');
                
                // Create edges with enhanced error checking
                const linkGroup = g.append('g');
                if (linkGroup.empty()) {
                    throw new Error('Failed to create link group');
                }
                
                const link = linkGroup
                    .selectAll('line')
                    .data(data.edges)
                    .enter().append('line')
                    .attr('class', 'edge')
                    .attr('stroke', '#666')
                    .attr('stroke-width', 2)
                    .attr('marker-end', 'url(#arrowhead)');
                
                // Add arrowhead marker
                const defs = svg.append('defs');
                if (defs.empty()) {
                    throw new Error('Failed to create defs element');
                }
                
                const marker = defs.append('marker')
                    .attr('id', 'arrowhead')
                    .attr('viewBox', '-0 -5 10 10')
                    .attr('refX', 25)
                    .attr('refY', 0)
                    .attr('orient', 'auto')
                    .attr('markerWidth', 8)
                    .attr('markerHeight', 8);
                
                marker.append('path')
                    .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
                    .attr('fill', '#666');
                
                // Create nodes
                const nodeGroup = g.append('g');
                if (nodeGroup.empty()) {
                    throw new Error('Failed to create node group');
                }
                
                const node = nodeGroup
                    .selectAll('g')
                    .data(data.nodes)
                    .enter().append('g')
                    .attr('class', 'node')
                    .call(d3.drag()
                        .on('start', dragstarted)
                        .on('drag', dragged)
                        .on('end', dragended));
                
                // Add node rectangles
                node.append('rect')
                    .attr('width', 100)
                    .attr('height', 60)
                    .attr('x', -50)
                    .attr('y', -30)
                    .attr('rx', 8)
                    .attr('fill', d => this.getNodeColor(d.type))
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 2)
                    .style('cursor', 'pointer')
                    .on('click', (event, d) => this.selectNode(d.id))
                    .on('mouseover', function() {
                        d3.select(this).attr('stroke-width', 3);
                    })
                    .on('mouseout', function() {
                        d3.select(this).attr('stroke-width', 2);
                    });
                
                // Add node labels
                node.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', '0.35em')
                    .attr('fill', 'white')
                    .attr('font-weight', 'bold')
                    .attr('font-size', '12px')
                    .text(d => d.data.label);
                
                // Add node icons
                node.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', '-10px')
                    .attr('fill', 'white')
                    .attr('font-family', 'Font Awesome 5 Free')
                    .attr('font-weight', '900')
                    .attr('font-size', '14px')
                    .text(d => this.getNodeIcon(d.type));
                
                // Add edge labels
                const edgeLabelsGroup = g.append('g');
                const edgeLabels = edgeLabelsGroup
                    .selectAll('text')
                    .data(data.edges)
                    .enter().append('text')
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '10px')
                    .attr('fill', '#666')
                    .text(d => d.data.label);
                
                // Update positions on simulation tick
                simulation.on('tick', () => {
                    link
                        .attr('x1', d => d.source.x)
                        .attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x)
                        .attr('y2', d => d.target.y);
                    
                    node
                        .attr('transform', d => `translate(${d.x},${d.y})`);
                    
                    edgeLabels
                        .attr('x', d => (d.source.x + d.target.x) / 2)
                        .attr('y', d => (d.source.y + d.target.y) / 2);
                });
                
                // Store references for external access
                this.graphInstance = {
                    svg: svg,
                    g: g,
                    simulation: simulation,
                    zoom: zoom
                };
                
                // Drag functions
                function dragstarted(event, d) {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }
                
                function dragged(event, d) {
                    d.fx = event.x;
                    d.fy = event.y;
                }
                
                function dragended(event, d) {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }
                
                console.log('=== safeInitializeD3Graph SUCCESS ===');
                resolve();
                
            } catch (error) {
                console.error('Error in safeInitializeD3Graph:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Safe wrapper for renderTreeView
     */
    safeRenderTreeView(data) {
        return new Promise((resolve, reject) => {
            try {
                const container = document.getElementById('ontology-visualization');
                
                container.innerHTML = `
                    <div id="tree-container" style="width: 100%; height: 100%; overflow: auto;">
                        <div class="tree-controls position-absolute" style="top: 10px; right: 10px; z-index: 1000;">
                            <div class="btn-group-vertical">
                                <button class="btn btn-sm btn-outline-primary mb-1" onclick="ontologyGraph.expandAllTree()" title="Expand All">
                                    <i class="fas fa-plus-square"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-primary" onclick="ontologyGraph.collapseAllTree()" title="Collapse All">
                                    <i class="fas fa-minus-square"></i>
                                </button>
                            </div>
                        </div>
                        <div id="tree-content" class="p-3">
                            <!-- Tree structure will be rendered here -->
                        </div>
                    </div>
                `;
                
                this.initializeTreeView(data);
                resolve();
            } catch (error) {
                reject(error);
            }
        });
    }
    
    /**
     * Apply class suggestion
     */
    applyClassSuggestion(currentData, suggestion) {
        return this.immutableUpdate(currentData, (data) => {
            const newNodeId = this.generateUniqueId('class');
            const position = this.calculateNewNodePosition(data.nodes, 'class');
            
            const newNode = {
                id: newNodeId,
                type: 'class',
                position,
                data: {
                    label: suggestion.title.replace('Add ', '').replace(' Entity', ''),
                    properties: suggestion.implementation ? 
                        suggestion.implementation.match(/properties:\s*\[(.*?)\]/)?.[1]?.split(',').map(p => p.trim().replace(/['"`]/g, '')) || [] :
                        ['id', 'created_date'],
                    description: suggestion.description,
                    isNew: true // Mark as new for highlighting
                }
            };
            
            data.nodes.push(newNode);
        });
    }
    
    /**
     * Apply property suggestion
     */
    applyPropertySuggestion(currentData, suggestion) {
        return this.immutableUpdate(currentData, (data) => {
            // Find target node or create new property node
            const targetNodeId = suggestion.targetNode || data.nodes[0]?.id;
            const targetNode = data.nodes.find(node => node.id === targetNodeId);
            
            if (targetNode) {
                // Add property to existing node
                const propertyName = suggestion.implementation.match(/Add\s+(\w+)/)?.[1] || 'new_property';
                if (!targetNode.data.properties.includes(propertyName)) {
                    targetNode.data.properties.push(propertyName);
                    targetNode.data.isModified = true;
                }
            }
        });
    }
    
    /**
     * Apply relationship suggestion
     */
    applyRelationshipSuggestion(currentData, suggestion) {
        return this.immutableUpdate(currentData, (data) => {
            // Extract relationship info from suggestion
            const relationshipMatch = suggestion.implementation.match(/(\w+)\s+(\w+)\s+(\w+)/);
            const sourceId = suggestion.sourceNode || data.nodes[0]?.id;
            const targetId = suggestion.targetNode || data.nodes[1]?.id;
            
            if (sourceId && targetId) {
                const newEdgeId = this.generateUniqueId('edge');
                const relationshipLabel = suggestion.title.toLowerCase().includes('enhance') ? 
                    'enhanced_relationship' : 
                    suggestion.implementation.match(/Add\s+(\w+)/)?.[1] || 'relates_to';
                
                const newEdge = {
                    id: newEdgeId,
                    source: sourceId,
                    target: targetId,
                    type: 'relationship',
                    data: {
                        label: relationshipLabel,
                        relationshipType: suggestion.implementation.includes('quantity') ? 'attributed' : 'one-to-many',
                        description: suggestion.description,
                        isNew: true // Mark as new for highlighting
                    }
                };
                
                data.edges.push(newEdge);
            }
        });
    }
    
    /**
     * Apply enhancement suggestion
     */
    applyEnhancementSuggestion(currentData, suggestion) {
        return this.immutableUpdate(currentData, (data) => {
            // Find the edge mentioned in the suggestion
            const edgeToEnhance = data.edges.find(edge => 
                suggestion.description.toLowerCase().includes(edge.data.label.toLowerCase())
            );
            
            if (edgeToEnhance) {
                // Add properties mentioned in implementation
                if (suggestion.implementation.includes('quantity')) {
                    edgeToEnhance.data.properties = ['quantity', 'unit_price', 'discount'];
                    edgeToEnhance.data.isModified = true;
                }
            }
        });
    }
    
    /**
     * Highlight changes in visualization
     */
    highlightChanges(change) {
        if (!this.graphInstance || !this.graphInstance.svg) return;
        
        const svg = this.graphInstance.svg;
        
        if (change.type === 'CREATE_CONNECTION') {
            // Find and highlight the new edge
            const newEdges = change.afterState.edges.filter(edge => 
                !change.beforeState.edges.find(beforeEdge => beforeEdge.id === edge.id)
            );
            
            newEdges.forEach(edge => {
                // Find the edge element and add highlighting
                svg.selectAll('.edge')
                    .filter(d => d.id === edge.id)
                    .classed('edge-highlighted', true)
                    .transition()
                    .duration(3000)
                    .on('end', function() {
                        d3.select(this).classed('edge-highlighted', false);
                    });
            });
        } else if (change.type === 'ADD_NODE') {
            // Highlight new nodes
            const newNodes = change.afterState.nodes.filter(node => 
                !change.beforeState.nodes.find(beforeNode => beforeNode.id === node.id)
            );
            
            newNodes.forEach(node => {
                svg.selectAll('.node')
                    .filter(d => d.id === node.id)
                    .select('rect')
                    .style('stroke', '#28a745')
                    .style('stroke-width', '4px')
                    .style('filter', 'drop-shadow(0 0 10px rgba(40, 167, 69, 0.8))')
                    .transition()
                    .duration(3000)
                    .style('stroke', '#fff')
                    .style('stroke-width', '2px')
                    .style('filter', 'none');
            });
        }
    }
    
    /**
     * Update suggestion status in UI
     */
    updateSuggestionStatus(suggestionId, status) {
        const suggestionElement = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
        if (suggestionElement) {
            const applyButton = suggestionElement.querySelector('.btn-outline-success');
            if (applyButton && status === 'applied') {
                applyButton.classList.remove('btn-outline-success');
                applyButton.classList.add('btn-success');
                applyButton.innerHTML = '<i class="fas fa-check"></i> Applied';
                applyButton.disabled = true;
                
                // Add applied badge
                const badge = document.createElement('span');
                badge.className = 'badge bg-success ms-2';
                badge.textContent = 'Applied';
                suggestionElement.querySelector('.tree-node-content').appendChild(badge);
            }
        }
    }
    
    /**
     * Get change history for display
     */
    getChangeHistory() {
        return this.changeHistory.map(change => ({
            id: change.id,
            title: change.suggestion.title,
            type: change.suggestion.type,
            timestamp: change.timestamp,
            description: change.suggestion.description
        }));
    }
    
    /**
     * Undo last change
     */
    undoLastChange() {
        if (this.changeHistory.length === 0) {
            this.showToast('No changes to undo', 'info');
            return;
        }
        
        const lastChange = this.changeHistory.pop();
        this.sampleData[this.currentOntology] = lastChange.beforeState;
        this.appliedSuggestions.delete(lastChange.suggestionId);
        
        // Update visualization
        this.loadOntologyGraph(this.currentOntology);
        
        // Update suggestion UI
        this.updateSuggestionStatus(lastChange.suggestionId, 'undone');
        
        this.showToast(`Undone: ${lastChange.suggestion.title}`, 'info');
    }
    
    /**
     * Toggle connection mode for creating edges between nodes
     */
    toggleConnectionMode() {
        this.isConnectionMode = !this.isConnectionMode;
        this.connectionManager.setConnectionMode(this.isConnectionMode);
        
        const button = document.querySelector('[onclick*="toggleConnectionMode"]');
        if (button) {
            if (this.isConnectionMode) {
                button.classList.add('active');
                button.innerHTML = '<i class="fas fa-link"></i> Exit Connect Mode';
                this.showToast('Connection mode enabled - click and drag between nodes to create connections', 'info');
            } else {
                button.classList.remove('active');
                button.innerHTML = '<i class="fas fa-link"></i> Connect Nodes';
                this.showToast('Connection mode disabled', 'info');
            }
        }
    }
}

/**
 * ConnectionManager class for handling node-to-node connections
 */
class ConnectionManager {
    constructor(graphManager) {
        this.graphManager = graphManager;
        this.isConnectionMode = false;
        this.sourceNode = null;
        this.ghostLine = null;
        this.isDragging = false;
    }
    
    setConnectionMode(enabled) {
        this.isConnectionMode = enabled;
        
        if (enabled) {
            this.attachConnectionListeners();
        } else {
            this.detachConnectionListeners();
            this.cancelConnection();
        }
    }
    
    attachConnectionListeners() {
        // Add connection-specific event listeners to nodes
        if (this.graphManager.graphInstance && this.graphManager.graphInstance.svg) {
            const svg = this.graphManager.graphInstance.svg;
            const nodes = svg.selectAll('.node');
            
            nodes
                .style('cursor', 'crosshair')
                .on('mousedown.connection', (event, d) => this.startConnection(event, d))
                .on('mouseup.connection', (event, d) => this.endConnection(event, d));
            
            // Add mousemove to SVG for ghost line
            svg.on('mousemove.connection', (event) => this.updateGhostLine(event));
        }
    }
    
    detachConnectionListeners() {
        if (this.graphManager.graphInstance && this.graphManager.graphInstance.svg) {
            const svg = this.graphManager.graphInstance.svg;
            const nodes = svg.selectAll('.node');
            
            nodes
                .style('cursor', 'pointer')
                .on('mousedown.connection', null)
                .on('mouseup.connection', null);
            
            svg.on('mousemove.connection', null);
        }
    }
    
    startConnection(event, sourceNode) {
        if (!this.isConnectionMode) return;
        
        event.stopPropagation();
        this.sourceNode = sourceNode;
        this.isDragging = true;
        
        console.log('Starting connection from:', sourceNode.data.label);
        
        // Create ghost line
        this.createGhostLine(sourceNode.x, sourceNode.y);
        
        // Highlight potential target nodes with intelligent suggestions
        this.highlightTargetNodesWithSuggestions(sourceNode);
        
        // Show connection guidance message
        this.graphManager.showToast(
            `Connection started from "${sourceNode.data.label}". Drag to another node to create a connection.`, 
            'info'
        );
    }
    
    // Enhanced version with intelligent suggestions
    highlightTargetNodesWithSuggestions(sourceNode) {
        if (!this.graphManager.graphInstance || !this.graphManager.graphInstance.svg) return;
        
        const svg = this.graphManager.graphInstance.svg;
        const currentData = this.graphManager.currentOntology ? 
            this.graphManager.sampleData[this.graphManager.currentOntology] : null;
            
        if (!currentData) return;
        
        console.log('Highlighting targets with suggestions for:', sourceNode.data.label);
        
        // Find connection candidates
        const candidates = this.findConnectionCandidates(sourceNode, currentData.nodes);
        
        svg.selectAll('.node')
            .each(function(d) {
                const node = d3.select(this);
                const rect = node.select('rect');
                
                if (d.id === sourceNode.id) {
                    // Highlight source node
                    rect.attr('stroke', '#007bff')
                        .attr('stroke-width', 4)
                        .attr('stroke-dasharray', '3,3');
                } else {
                    // Check if this node is a candidate
                    const candidate = candidates.find(c => c.targetEntityId === d.id);
                    
                    if (candidate) {
                        // Color code by confidence level
                        let strokeColor = '#28a745'; // Green for high confidence
                        let strokeWidth = 3;
                        
                        if (candidate.confidence < 70) {
                            strokeColor = '#ffc107'; // Yellow for medium
                        }
                        if (candidate.confidence < 50) {
                            strokeColor = '#17a2b8'; // Blue for low
                            strokeWidth = 2;
                        }
                        
                        rect.attr('stroke', strokeColor)
                            .attr('stroke-width', strokeWidth)
                            .attr('opacity', 0.9);
                        
                        // Add tooltip with suggestion
                        node.append('title')
                            .text(`Suggested: ${candidate.relationshipName} (${candidate.confidence}% confidence)\n${candidate.reasoning}`);
                        
                        // Add visual indicator for high confidence candidates
                        if (candidate.confidence >= 80) {
                            rect.style('filter', 'drop-shadow(0 0 10px rgba(40, 167, 69, 0.8))');
                        }
                    } else {
                        // Default highlighting for all other nodes
                        rect.attr('stroke', '#6c757d')
                            .attr('stroke-width', 2)
                            .attr('opacity', 0.6);
                    }
                }
            });
        
        // Show suggestions in a temporary info panel
        this.showConnectionSuggestionsPanel(sourceNode, candidates);
    }
    
    // Show a temporary panel with connection suggestions
    showConnectionSuggestionsPanel(sourceNode, candidates) {
        // Remove existing panel
        d3.select('#connection-suggestions-panel').remove();
        
        if (candidates.length === 0) return;
        
        const panelHtml = `
            <div id="connection-suggestions-panel" class="connection-suggestions-panel">
                <div class="panel-header">
                    <h6><i class="fas fa-lightbulb me-2"></i>Connection Suggestions for "${sourceNode.data.label}"</h6>
                    <button class="btn-close btn-sm" onclick="d3.select('#connection-suggestions-panel').remove()"></button>
                </div>
                <div class="panel-body">
                    ${candidates.slice(0, 5).map(candidate => `
                        <div class="suggestion-item" data-target="${candidate.targetEntityId}">
                            <div class="d-flex align-items-center">
                                <div class="confidence-indicator confidence-${this.getConfidenceLevel(candidate.confidence)}"></div>
                                <div class="flex-grow-1">
                                    <strong>${candidate.targetEntityName}</strong>
                                    <br>
                                    <small class="text-muted">${candidate.relationshipName} (${candidate.confidence}%)</small>
                                    <br>
                                    <small class="text-info">${candidate.reasoning}</small>
                                </div>
                                <button class="btn btn-sm btn-outline-primary" onclick="window.ontologyGraph.connectionManager.createQuickConnection('${sourceNode.id}', '${candidate.targetEntityId}', '${candidate.relationshipName}')">
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        // Add panel to body
        document.body.insertAdjacentHTML('beforeend', panelHtml);
        
        // Position the panel
        const panel = document.getElementById('connection-suggestions-panel');
        panel.style.position = 'fixed';
        panel.style.top = '20px';
        panel.style.right = '20px';
        panel.style.zIndex = '2000';
        panel.style.maxWidth = '350px';
        
        // Auto-remove after 15 seconds
        setTimeout(() => {
            const existingPanel = document.getElementById('connection-suggestions-panel');
            if (existingPanel) existingPanel.remove();
        }, 15000);
    }
    
    // Get confidence level for styling
    getConfidenceLevel(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 60) return 'medium';
        return 'low';
    }
    
    // Quick connection creation without modal
    createQuickConnection(sourceNodeId, targetNodeId, suggestedRelationship) {
        console.log('Creating quick connection:', sourceNodeId, '->', targetNodeId, 'as', suggestedRelationship);
        
        // Create connection with suggested relationship
        const relationshipRequest = {
            name: suggestedRelationship,
            description: `Auto-suggested connection based on entity pattern analysis`,
            source_entity_id: sourceNodeId,
            target_entity_id: targetNodeId,
            cardinality: 'one-to-many', // Default cardinality
            is_ai_suggested: true
        };
        
        // Save to API
        this.saveConnectionToAPI(sourceNodeId, targetNodeId, suggestedRelationship, 'one-to-many', relationshipRequest.description)
            .then(result => {
                if (result.success) {
                    // Update local data
                    const currentData = this.graphManager.currentOntology ? 
                        this.graphManager.sampleData[this.graphManager.currentOntology] : null;
                    
                    if (currentData) {
                        // Create new edge
                        const newEdgeId = this.graphManager.generateUniqueId('edge');
                        const newEdge = {
                            id: newEdgeId,
                            source: sourceNodeId,
                            target: targetNodeId,
                            type: 'relationship',
                            data: {
                                label: suggestedRelationship,
                                relationshipType: 'one-to-many',
                                description: relationshipRequest.description,
                                isNew: true
                            }
                        };
                        
                        currentData.edges.push(newEdge);
                        
                        // Update visualization
                        this.graphManager.loadOntologyGraph(this.graphManager.currentOntology);
                        
                        // Remove suggestions panel
                        const panel = document.getElementById('connection-suggestions-panel');
                        if (panel) panel.remove();
                        
                        this.graphManager.showToast(`Quick connection "${suggestedRelationship}" created successfully!`, 'success');
                    }
                } else {
                    this.graphManager.showToast('Failed to create quick connection: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error creating quick connection:', error);
                this.graphManager.showToast('Error creating quick connection', 'danger');
            });
    }
    
    endConnection(event, targetNode) {
        if (!this.isConnectionMode || !this.isDragging || !this.sourceNode) return;
        
        event.stopPropagation();
        
        if (this.sourceNode.id !== targetNode.id) {
            // Valid connection
            this.createConnection(this.sourceNode, targetNode);
        }
        
        this.cancelConnection();
    }
    
    createGhostLine(startX, startY) {
        if (this.graphManager.graphInstance && this.graphManager.graphInstance.svg) {
            const svg = this.graphManager.graphInstance.svg;
            
            this.ghostLine = svg.append('line')
                .attr('class', 'ghost-connection')
                .attr('x1', startX)
                .attr('y1', startY)
                .attr('x2', startX)
                .attr('y2', startY)
                .attr('stroke', '#007bff')
                .attr('stroke-width', 3)
                .attr('stroke-dasharray', '5,5')
                .attr('opacity', 0.7);
        }
    }
    
    updateGhostLine(event) {
        if (!this.isDragging || !this.ghostLine) return;
        
        const [mouseX, mouseY] = d3.pointer(event);
        this.ghostLine
            .attr('x2', mouseX)
            .attr('y2', mouseY);
    }
    
    highlightTargetNodes(sourceNodeId) {
        if (this.graphManager.graphInstance && this.graphManager.graphInstance.svg) {
            const svg = this.graphManager.graphInstance.svg;
            
            svg.selectAll('.node')
                .filter(d => d.id !== sourceNodeId)
                .select('rect')
                .attr('stroke', '#28a745')
                .attr('stroke-width', 3);
        }
    }
    
    cancelConnection() {
        this.isDragging = false;
        this.sourceNode = null;
        
        // Remove ghost line
        if (this.ghostLine) {
            this.ghostLine.remove();
            this.ghostLine = null;
        }
        
        // Remove highlights
        if (this.graphManager.graphInstance && this.graphManager.graphInstance.svg) {
            const svg = this.graphManager.graphInstance.svg;
            svg.selectAll('.node rect')
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);
        }
    }
    
    createConnection(sourceNode, targetNode) {
        // Show connection type selection modal
        this.showConnectionTypeModal(sourceNode, targetNode);
    }
    
    showConnectionTypeModal(sourceNode, targetNode) {
        const modalHtml = `
            <div class="modal fade" id="connectionTypeModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-link me-2"></i>Create Connection
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>From:</strong> ${sourceNode.data.label} 
                                <i class="fas fa-arrow-right mx-2"></i>
                                <strong>To:</strong> ${targetNode.data.label}
                            </div>
                            
                            <form id="connectionForm">
                                <div class="mb-3">
                                    <label for="connectionType" class="form-label">Connection Type</label>
                                    <select class="form-select" id="connectionType" required>
                                        <option value="relationship">Relationship</option>
                                        <option value="property">Property</option>
                                        <option value="inheritance">Inheritance</option>
                                        <option value="composition">Composition</option>
                                        <option value="aggregation">Aggregation</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="connectionLabel" class="form-label">Connection Label *</label>
                                    <input type="text" class="form-control" id="connectionLabel" placeholder="e.g., contains, has, is-a" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="relationshipType" class="form-label">Relationship Type</label>
                                    <select class="form-select" id="relationshipType">
                                        <option value="one-to-one">One to One</option>
                                        <option value="one-to-many">One to Many</option>
                                        <option value="many-to-one">Many to One</option>
                                        <option value="many-to-many">Many to Many</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="connectionDescription" class="form-label">Description</label>
                                    <textarea class="form-control" id="connectionDescription" rows="2" placeholder="Describe this connection..."></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="ontologyGraph.connectionManager.saveConnection('${sourceNode.id}', '${targetNode.id}')">
                                <i class="fas fa-save"></i> Create Connection
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('connectionTypeModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('connectionTypeModal'));
        modal.show();
    }
    
    saveConnection(sourceNodeId, targetNodeId) {
        const form = document.getElementById('connectionForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const connectionLabel = document.getElementById('connectionLabel').value.trim();
        const connectionType = document.getElementById('connectionType').value;
        const relationshipType = document.getElementById('relationshipType').value;
        const description = document.getElementById('connectionDescription').value.trim();
        
        // Create new edge for local data
        const newEdgeId = this.graphManager.generateUniqueId('edge');
        const newEdge = {
            id: newEdgeId,
            source: sourceNodeId,
            target: targetNodeId,
            type: connectionType,
            data: {
                label: connectionLabel,
                relationshipType: relationshipType,
                description: description,
                isNew: true
            }
        };
        
        // Save to backend API if we have a selected domain
        this.saveConnectionToAPI(sourceNodeId, targetNodeId, connectionLabel, relationshipType, description)
            .then(result => {
                if (result.success) {
                    // Update local data
                    const currentData = this.graphManager.currentOntology ? 
                        this.graphManager.sampleData[this.graphManager.currentOntology] : null;
                    
                    if (currentData) {
                        // Check for duplicate connections
                        const duplicateEdge = currentData.edges.find(edge => 
                            edge.source === sourceNodeId && edge.target === targetNodeId && edge.data.label === connectionLabel
                        );
                        
                        if (!duplicateEdge) {
                            // Create change record for undo
                            const changeId = ++this.graphManager.currentChangeId;
                            const change = {
                                id: changeId,
                                type: 'CREATE_CONNECTION',
                                timestamp: new Date().toISOString(),
                                beforeState: structuredClone(currentData)
                            };
                            
                            currentData.edges.push(newEdge);
                            
                            // Record change
                            change.afterState = structuredClone(currentData);
                            this.graphManager.changeHistory.push(change);
                            
                            // Update visualization
                            this.graphManager.loadOntologyGraph(this.graphManager.currentOntology);
                            
                            // Highlight new connection
                            setTimeout(() => {
                                this.graphManager.highlightChanges(change);
                            }, 100);
                        }
                    }
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('connectionTypeModal'));
                    if (modal) modal.hide();
                    
                    this.graphManager.showToast('Connection created successfully', 'success');
                } else {
                    this.graphManager.showToast('Failed to create connection: ' + result.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error creating connection:', error);
                this.graphManager.showToast('Error creating connection: ' + error.message, 'danger');
            });
    }
    
    // Save connection to backend API
    async saveConnectionToAPI(sourceNodeId, targetNodeId, relationshipName, cardinality, description) {
        try {
            // Get selected domain from global variable
            const selectedDomain = window.selectedDomain;
            
            if (!selectedDomain) {
                console.warn('No domain selected, saving connection locally only');
                return { success: true, message: 'Saved locally' };
            }
            
            console.log('Saving connection to API:', {
                domain: selectedDomain,
                source: sourceNodeId,
                target: targetNodeId,
                name: relationshipName
            });
            
            const relationshipRequest = {
                name: relationshipName,
                description: description,
                source_entity_id: sourceNodeId,
                target_entity_id: targetNodeId,
                cardinality: cardinality,
                is_ai_suggested: false
            };
            
            const response = await fetch(`/api/v1/ontology/domains/${selectedDomain}/relationships`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(relationshipRequest)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('Connection saved to API successfully:', result);
                return result;
            } else {
                const errorText = await response.text();
                console.error('API error:', response.status, errorText);
                return { success: false, message: `HTTP ${response.status}: ${errorText}` };
            }
            
        } catch (error) {
            console.error('Error saving connection to API:', error);
            return { success: false, message: error.message };
        }
    }
    
    // Enhanced function to highlight connection candidates for new entities
    highlightConnectionCandidatesForNewEntity(newEntityId) {
        if (!this.graphManager.graphInstance || !this.graphManager.graphInstance.svg) return;
        
        console.log('Highlighting connection candidates for new entity:', newEntityId);
        
        const svg = this.graphManager.graphInstance.svg;
        const currentData = this.graphManager.currentOntology ? 
            this.graphManager.sampleData[this.graphManager.currentOntology] : null;
            
        if (!currentData) return;
        
        const newEntity = currentData.nodes.find(node => node.id === newEntityId);
        if (!newEntity) return;
        
        // Find potential connection candidates using the intelligent analysis
        const connectionCandidates = this.findConnectionCandidates(newEntity, currentData.nodes);
        
        console.log('Found connection candidates:', connectionCandidates);
        
        // Highlight candidate nodes
        svg.selectAll('.node')
            .each(function(d) {
                const node = d3.select(this);
                const rect = node.select('rect');
                
                if (d.id === newEntityId) {
                    // Highlight the new entity itself with a special color
                    rect.attr('stroke', '#ff6b6b')
                        .attr('stroke-width', 4)
                        .attr('stroke-dasharray', '5,5');
                    
                    // Add pulsing effect
                    rect.transition()
                        .duration(1000)
                        .attr('opacity', 0.7)
                        .transition()
                        .duration(1000)
                        .attr('opacity', 1)
                        .on('end', function repeat() {
                            d3.select(this)
                                .transition()
                                .duration(1000)
                                .attr('opacity', 0.7)
                                .transition()
                                .duration(1000)
                                .attr('opacity', 1)
                                .on('end', repeat);
                        });
                } else {
                    const candidate = connectionCandidates.find(c => c.targetEntityId === d.id);
                    if (candidate) {
                        // Highlight connection candidates with confidence-based colors
                        const confidence = candidate.confidence;
                        let highlightColor = '#28a745'; // Green for high confidence
                        
                        if (confidence < 70) {
                            highlightColor = '#ffc107'; // Yellow for medium confidence
                        }
                        if (confidence < 50) {
                            highlightColor = '#17a2b8'; // Blue for low confidence
                        }
                        
                        rect.attr('stroke', highlightColor)
                            .attr('stroke-width', 3)
                            .attr('opacity', 0.8);
                        
                        // Add tooltip with connection suggestion
                        node.append('title')
                            .text(`Suggested connection: ${candidate.relationshipName} (${confidence}% confidence)`);
                    }
                }
            });
        
        // Show toast with information
        if (connectionCandidates.length > 0) {
            this.graphManager.showToast(
                `Found ${connectionCandidates.length} potential connections for the new entity. Click "Connect Nodes" to create connections.`, 
                'info'
            );
        }
        
        // Auto-clear highlights after 10 seconds
        setTimeout(() => {
            this.clearAllHighlights();
        }, 10000);
    }
    
    // Find connection candidates using intelligent analysis
    findConnectionCandidates(newEntity, allNodes) {
        const candidates = [];
        const existingEntities = allNodes.filter(node => node.id !== newEntity.id);
        
        existingEntities.forEach(targetEntity => {
            const analysis = this.analyzeEntityRelationship(newEntity, targetEntity);
            
            if (analysis.shouldConnect) {
                candidates.push({
                    targetEntityId: targetEntity.id,
                    targetEntityName: targetEntity.data.label,
                    relationshipName: analysis.relationshipName,
                    confidence: analysis.confidence,
                    reasoning: analysis.reasoning
                });
            }
        });
        
        // Sort by confidence
        return candidates.sort((a, b) => b.confidence - a.confidence);
    }
    
    // Entity relationship analysis (imported from ontology.html)
    analyzeEntityRelationship(entity1, entity2) {
        const name1 = entity1.data.label.toLowerCase();
        const name2 = entity2.data.label.toLowerCase();
        
        // Comprehensive relationship patterns with confidence scores
        const relationshipPatterns = [
            // High confidence patterns (90-95%)
            { pattern: ['user', 'profile'], relationship: 'has_profile', cardinality: 'one-to-one', confidence: 95 },
            { pattern: ['customer', 'order'], relationship: 'places_order', cardinality: 'one-to-many', confidence: 95 },
            { pattern: ['artist', 'album'], relationship: 'creates_album', cardinality: 'one-to-many', confidence: 95 },
            { pattern: ['album', 'track'], relationship: 'contains_track', cardinality: 'one-to-many', confidence: 95 },
            { pattern: ['category', 'product'], relationship: 'categorizes_product', cardinality: 'one-to-many', confidence: 90 },
            { pattern: ['genre', 'track'], relationship: 'categorizes_track', cardinality: 'one-to-many', confidence: 90 },
            
            // Medium confidence patterns (70-85%)
            { pattern: ['user', 'order'], relationship: 'places_order', cardinality: 'one-to-many', confidence: 85 },
            { pattern: ['customer', 'invoice'], relationship: 'receives_invoice', cardinality: 'one-to-many', confidence: 85 },
            { pattern: ['product', 'order'], relationship: 'ordered_in', cardinality: 'many-to-many', confidence: 80 },
            { pattern: ['employee', 'customer'], relationship: 'supports_customer', cardinality: 'one-to-many', confidence: 80 },
            { pattern: ['playlist', 'track'], relationship: 'includes_track', cardinality: 'many-to-many', confidence: 85 },
            { pattern: ['invoice', 'invoiceline'], relationship: 'contains_line', cardinality: 'one-to-many', confidence: 90 },
            
            // Lower confidence but still valid patterns (60-75%)
            { pattern: ['company', 'employee'], relationship: 'employs', cardinality: 'one-to-many', confidence: 75 },
            { pattern: ['department', 'employee'], relationship: 'belongs_to', cardinality: 'many-to-one', confidence: 75 },
            { pattern: ['media', 'track'], relationship: 'defines_format', cardinality: 'one-to-many', confidence: 70 },
            { pattern: ['address', 'customer'], relationship: 'belongs_to', cardinality: 'many-to-one', confidence: 70 }
        ];
        
        // Find matching patterns
        for (const patternObj of relationshipPatterns) {
            const [word1, word2] = patternObj.pattern;
            
            // Direct pattern matching
            if ((name1.includes(word1) && name2.includes(word2))) {
                return {
                    shouldConnect: true,
                    relationshipName: patternObj.relationship,
                    confidence: patternObj.confidence,
                    reasoning: `Direct pattern match: ${word1} → ${word2}`
                };
            }
            
            // Reverse pattern matching
            if ((name1.includes(word2) && name2.includes(word1))) {
                const reverseRelationship = this.getReverseRelationship(patternObj.relationship);
                return {
                    shouldConnect: true,
                    relationshipName: reverseRelationship,
                    confidence: Math.max(50, patternObj.confidence - 10), // Slightly lower confidence for reverse
                    reasoning: `Reverse pattern match: ${word2} → ${word1}`
                };
            }
        }
        
        // Fuzzy matching for similar entity names
        const similarity = this.calculateAdvancedSimilarity(name1, name2);
        if (similarity > 0.3) { // 30% similarity threshold
            return {
                shouldConnect: true,
                relationshipName: 'relates_to',
                confidence: Math.round(similarity * 60), // Max 60% confidence for fuzzy matches
                reasoning: `Semantic similarity: ${Math.round(similarity * 100)}%`
            };
        }
        
        return { shouldConnect: false };
    }
    
    // Helper function for reverse relationships
    getReverseRelationship(relationshipName) {
        const reverseMap = {
            'has_profile': 'belongs_to_user',
            'places_order': 'placed_by',
            'creates_album': 'created_by',
            'contains_track': 'belongs_to_album',
            'categorizes_product': 'belongs_to_category',
            'employs': 'works_for'
        };
        
        return reverseMap[relationshipName] || 'relates_to';
    }
    
    // Advanced similarity calculation
    calculateAdvancedSimilarity(name1, name2) {
        const tokens1 = name1.toLowerCase().split(/[_\s]+/).filter(t => t.length > 2);
        const tokens2 = name2.toLowerCase().split(/[_\s]+/).filter(t => t.length > 2);
        
        if (tokens1.length === 0 || tokens2.length === 0) return 0;
        
        let maxSimilarity = 0;
        
        for (const token1 of tokens1) {
            for (const token2 of tokens2) {
                if (token1 === token2) {
                    maxSimilarity = Math.max(maxSimilarity, 1.0);
                } else if (token1.includes(token2) || token2.includes(token1)) {
                    const longer = Math.max(token1.length, token2.length);
                    const shorter = Math.min(token1.length, token2.length);
                    maxSimilarity = Math.max(maxSimilarity, shorter / longer);
                }
            }
        }
        
        return maxSimilarity;
    }
    
    // Clear all highlights
    clearAllHighlights() {
        if (!this.graphManager.graphInstance || !this.graphManager.graphInstance.svg) return;
        
        const svg = this.graphManager.graphInstance.svg;
        
        // Remove all highlights and animations
        svg.selectAll('.node rect')
            .transition()
            .duration(500)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', 'none')
            .attr('opacity', 1);
        
        // Remove all tooltips
        svg.selectAll('.node title').remove();
        
        console.log('All highlights cleared');
    }
}

// ===== CLASS DEFINITION COMPLETE =====
console.log('=== OntologyGraphManager CLASS DEFINITION COMPLETE ===');
console.log('OntologyGraphManager prototype methods:', Object.getOwnPropertyNames(OntologyGraphManager.prototype));
console.log('loadVisualizationData method defined:', typeof OntologyGraphManager.prototype.loadVisualizationData);

// Make the class available globally FIRST
window.OntologyGraphManager = OntologyGraphManager;

// Verify class is properly available
console.log('=== CLASS AVAILABILITY CHECK ===');
console.log('window.OntologyGraphManager:', typeof window.OntologyGraphManager);
console.log('Constructor available:', typeof window.OntologyGraphManager);

// Now create the global instance
console.log('=== CREATING GLOBAL INSTANCE ===');
try {
    window.ontologyGraph = new OntologyGraphManager();
    console.log('Instance created successfully');
    console.log('Instance methods available:', Object.getOwnPropertyNames(window.ontologyGraph.__proto__));
    console.log('loadVisualizationData available on instance:', typeof window.ontologyGraph.loadVisualizationData);
} catch (error) {
    console.error('Failed to create OntologyGraphManager instance:', error);
}

// Global helper functions for modals
function addProperty() {
    const propertiesList = document.getElementById('propertiesList');
    const newPropertyDiv = document.createElement('div');
    newPropertyDiv.className = 'input-group mb-2 property-item';
    newPropertyDiv.innerHTML = `
        <input type="text" class="form-control" value="" name="property" placeholder="Enter property name">
        <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">
            <i class="fas fa-trash"></i>
        </button>
    `;
    propertiesList.appendChild(newPropertyDiv);
}

function saveNodeEdits(nodeId) {
    window.ontologyGraph.saveNodeEdits(nodeId);
}