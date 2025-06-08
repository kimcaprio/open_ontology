// Main application JavaScript

// Utility functions
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function showLoading(element) {
    element.innerHTML = '<span class="loading-spinner me-2"></span>Loading...';
    element.disabled = true;
}

function hideLoading(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

// API helper functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// System status checker
class SystemStatus {
    constructor() {
        this.statusElements = {
            minio: document.querySelector('#minio-status'),
            unityCatalog: document.querySelector('#unity-catalog-status'),
            ollama: document.querySelector('#ollama-status')
        };
    }
    
    async checkAll() {
        try {
            const status = await apiRequest('/api/v1/system/status');
            this.updateUI(status);
        } catch (error) {
            console.error('Failed to check system status:', error);
            this.updateUI({ error: 'Failed to connect to API' });
        }
    }
    
    updateUI(status) {
        Object.keys(this.statusElements).forEach(service => {
            const element = this.statusElements[service];
            if (element) {
                const badge = element.querySelector('.badge');
                if (status[service]) {
                    badge.className = 'badge bg-success';
                    badge.textContent = 'Online';
                } else {
                    badge.className = 'badge bg-danger';
                    badge.textContent = 'Offline';
                }
            }
        });
    }
}

// Data source management
class DataSourceManager {
    constructor() {
        this.form = document.querySelector('#data-source-form');
        this.list = document.querySelector('#data-source-list');
        
        if (this.form) {
            this.form.addEventListener('submit', this.handleSubmit.bind(this));
        }
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData.entries());
        
        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        try {
            showLoading(submitBtn);
            
            // Demo mode - simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            showToast('Data source configuration saved! (Demo mode - API coming soon)', 'success');
            this.form.reset();
            this.loadDataSources();
            
            // Close modal if it exists
            const modal = document.querySelector('#addDataSourceModal');
            if (modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
            
        } catch (error) {
            showToast('Failed to register data source: ' + error.message, 'danger');
        } finally {
            hideLoading(submitBtn, originalText);
        }
    }
    
    async loadDataSources() {
        if (!this.list) return;
        
        try {
            // Demo mode - show placeholder instead of making actual API call
            this.list.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Demo Mode:</strong> Data source management API is coming soon. 
                    You can use the form above to test the UI functionality.
                </div>
                <div class="text-muted text-center py-4">
                    <i class="fas fa-database fa-3x mb-3"></i>
                    <p>No data sources registered yet.</p>
                    <p>Click "Add Data Source" to get started.</p>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load data sources:', error);
            this.list.innerHTML = '<div class="alert alert-danger">Failed to load data sources</div>';
        }
    }
    
    renderDataSources(dataSources) {
        if (dataSources.length === 0) {
            this.list.innerHTML = '<div class="alert alert-info">No data sources registered yet</div>';
            return;
        }
        
        const html = dataSources.map(ds => `
            <div class="card data-source-card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="card-title">${ds.name}</h5>
                            <p class="card-text text-muted">${ds.description || 'No description'}</p>
                            <small class="text-muted">Type: ${ds.type} | Created: ${new Date(ds.created_at).toLocaleDateString()}</small>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="testConnection('${ds.id}')">
                                <i class="fas fa-plug"></i> Test
                            </button>
                            <button class="btn btn-sm btn-outline-info" onclick="scanMetadata('${ds.id}')">
                                <i class="fas fa-search"></i> Scan
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDataSource('${ds.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        this.list.innerHTML = html;
    }
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize system status checker (for all pages)
    const systemStatus = new SystemStatus();
    
    // Initialize data source manager only on datasources page
    const currentPath = window.location.pathname;
    if (currentPath === '/datasources') {
        const dataSourceManager = new DataSourceManager();
        // Note: loadDataSources will be called by the page-specific JavaScript
    }
    
    // Set up periodic status checks (for dashboard)
    if (currentPath === '/') {
        systemStatus.checkAll();
        setInterval(() => systemStatus.checkAll(), 30000);
    }
    
    // Set up navigation active states
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// Global functions for button actions (Demo mode)
async function testConnection(dataSourceId) {
    showToast('Connection test initiated... (Demo mode)', 'info');
    
    // Simulate connection test
    setTimeout(() => {
        showToast('Connection test successful! (Demo mode)', 'success');
    }, 2000);
}

async function scanMetadata(dataSourceId) {
    showToast('Starting metadata scan... (Demo mode)', 'info');
    
    // Simulate metadata scan
    setTimeout(() => {
        showToast('Metadata scan completed! (Demo mode)', 'success');
    }, 3000);
}

async function deleteDataSource(dataSourceId) {
    if (!confirm('Are you sure you want to delete this data source? (Demo mode)')) {
        return;
    }
    
    showToast('Data source deleted successfully! (Demo mode)', 'success');
} 