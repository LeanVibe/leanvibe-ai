// Enhanced Bridge for communication between WKWebView and the iOS app

// Global state management
let interactionState = {
    selectedNodes: new Set(),
    hoveredNode: null,
    contextMenu: null,
    touchStartTime: 0,
    touchStartPosition: { x: 0, y: 0 },
    longPressThreshold: 800, // ms
    dragThreshold: 10 // pixels
};

// Enhanced node interaction
function sendNodeTap(nodeId) {
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nodeTapped) {
        window.webkit.messageHandlers.nodeTapped.postMessage({
            type: 'tap',
            nodeId: nodeId,
            timestamp: Date.now(),
            selectedNodes: Array.from(interactionState.selectedNodes)
        });
    }
}

function sendNodeLongPress(nodeId) {
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nodeLongPressed) {
        window.webkit.messageHandlers.nodeLongPressed.postMessage({
            type: 'longPress',
            nodeId: nodeId,
            timestamp: Date.now(),
            position: interactionState.touchStartPosition
        });
    }
}

function sendNodeHover(nodeId, isHovering) {
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nodeHovered) {
        window.webkit.messageHandlers.nodeHovered.postMessage({
            type: 'hover',
            nodeId: nodeId,
            isHovering: isHovering,
            timestamp: Date.now()
        });
    }
}

function sendNodeDoubleClick(nodeId) {
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.nodeDoubleClicked) {
        window.webkit.messageHandlers.nodeDoubleClicked.postMessage({
            type: 'doubleClick',
            nodeId: nodeId,
            timestamp: Date.now()
        });
    }
}

// Selection management
function toggleNodeSelection(nodeId) {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    if (interactionState.selectedNodes.has(nodeId)) {
        interactionState.selectedNodes.delete(nodeId);
        node.classList.remove('node-selected');
    } else {
        interactionState.selectedNodes.add(nodeId);
        node.classList.add('node-selected');
    }
    
    updateSelectionUI();
}

function selectNode(nodeId) {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    interactionState.selectedNodes.add(nodeId);
    node.classList.add('node-selected');
    updateSelectionUI();
}

function deselectNode(nodeId) {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    interactionState.selectedNodes.delete(nodeId);
    node.classList.remove('node-selected');
    updateSelectionUI();
}

function clearSelection() {
    interactionState.selectedNodes.forEach(nodeId => {
        const node = document.querySelector(`[id="${nodeId}"]`);
        if (node) {
            node.classList.remove('node-selected');
        }
    });
    interactionState.selectedNodes.clear();
    updateSelectionUI();
}

function selectAllNodes() {
    const nodes = document.querySelectorAll('.node');
    nodes.forEach(node => {
        const nodeId = getNodeId(node);
        if (nodeId) {
            interactionState.selectedNodes.add(nodeId);
            node.classList.add('node-selected');
        }
    });
    updateSelectionUI();
}

// Node highlighting and visual feedback
function highlightNode(nodeId, highlightType = 'primary') {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    node.classList.add(`node-highlight-${highlightType}`);
    
    // Auto-remove highlight after animation
    setTimeout(() => {
        node.classList.remove(`node-highlight-${highlightType}`);
    }, 2000);
}

function pulseNode(nodeId) {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    node.classList.add('node-pulse');
    
    setTimeout(() => {
        node.classList.remove('node-pulse');
    }, 1000);
}

// Node information and tooltips
function showNodeTooltip(nodeId, content) {
    hideNodeTooltip(); // Hide any existing tooltip
    
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'node-tooltip';
    tooltip.innerHTML = content;
    
    const rect = node.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.top - 10}px`;
    
    document.body.appendChild(tooltip);
    
    // Position tooltip to avoid edges
    const tooltipRect = tooltip.getBoundingClientRect();
    if (tooltipRect.right > window.innerWidth) {
        tooltip.style.left = `${window.innerWidth - tooltipRect.width - 10}px`;
    }
    if (tooltipRect.top < 0) {
        tooltip.style.top = `${rect.bottom + 10}px`;
    }
}

function hideNodeTooltip() {
    const existingTooltip = document.querySelector('.node-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
    }
}

// Path highlighting between nodes
function highlightPath(sourceNodeId, targetNodeId, pathType = 'primary') {
    const sourceNode = document.querySelector(`[id="${sourceNodeId}"]`);
    const targetNode = document.querySelector(`[id="${targetNodeId}"]`);
    
    if (!sourceNode || !targetNode) return;
    
    // Find path elements between nodes
    const edges = document.querySelectorAll('.edgePath');
    edges.forEach(edge => {
        const edgeData = edge.getAttribute('data-source-target');
        if (edgeData && edgeData.includes(sourceNodeId) && edgeData.includes(targetNodeId)) {
            edge.classList.add(`path-highlight-${pathType}`);
            
            setTimeout(() => {
                edge.classList.remove(`path-highlight-${pathType}`);
            }, 3000);
        }
    });
    
    // Highlight the nodes as well
    highlightNode(sourceNodeId, pathType);
    highlightNode(targetNodeId, pathType);
}

// Diagram navigation helpers
function focusOnNode(nodeId, zoomLevel = 1.5) {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    const rect = node.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Smooth scroll to center the node
    window.scrollTo({
        left: centerX - window.innerWidth / 2,
        top: centerY - window.innerHeight / 2,
        behavior: 'smooth'
    });
    
    // Apply zoom if requested
    if (zoomLevel !== 1) {
        setZoomScale(zoomLevel);
    }
    
    // Highlight the focused node
    highlightNode(nodeId, 'focus');
}

function zoomToFit() {
    const diagram = document.querySelector('.mermaid');
    if (!diagram) return;
    
    const diagramRect = diagram.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    const scaleX = viewportWidth / (diagramRect.width + 40); // 40px padding
    const scaleY = viewportHeight / (diagramRect.height + 40);
    const scale = Math.min(scaleX, scaleY, 1); // Don't zoom in beyond 1x
    
    setZoomScale(scale);
}

// Enhanced touch and gesture handling
function setupAdvancedInteractions() {
    const nodes = document.querySelectorAll('.node, .nodeLabel, [id^="node"], g[id*="node"]');
    
    nodes.forEach(node => {
        let clickCount = 0;
        let touchStartPosition = { x: 0, y: 0 };
        let touchStartTime = 0;
        let longPressTimer = null;
        
        // Enhanced click handling
        node.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            const nodeId = getNodeId(this);
            if (!nodeId) return;
            
            clickCount++;
            
            // Handle double-click
            if (clickCount === 1) {
                setTimeout(() => {
                    if (clickCount === 1) {
                        // Single click
                        if (event.metaKey || event.ctrlKey) {
                            toggleNodeSelection(nodeId);
                        } else {
                            clearSelection();
                            selectNode(nodeId);
                        }
                        sendNodeTap(nodeId);
                    } else if (clickCount === 2) {
                        // Double click
                        sendNodeDoubleClick(nodeId);
                        focusOnNode(nodeId);
                    }
                    clickCount = 0;
                }, 300);
            }
        });
        
        // Touch handling for mobile
        node.addEventListener('touchstart', function(event) {
            touchStartTime = Date.now();
            if (event.touches.length > 0) {
                touchStartPosition.x = event.touches[0].clientX;
                touchStartPosition.y = event.touches[0].clientY;
            }
            
            interactionState.touchStartTime = touchStartTime;
            interactionState.touchStartPosition = touchStartPosition;
            
            // Set up long press detection
            longPressTimer = setTimeout(() => {
                const nodeId = getNodeId(this);
                if (nodeId) {
                    sendNodeLongPress(nodeId);
                    // Provide haptic feedback if available
                    if (navigator.vibrate) {
                        navigator.vibrate(50);
                    }
                }
            }, interactionState.longPressThreshold);
        });
        
        node.addEventListener('touchend', function(event) {
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
            
            const touchDuration = Date.now() - touchStartTime;
            if (touchDuration < interactionState.longPressThreshold) {
                // Regular tap - handled by click event
            }
        });
        
        node.addEventListener('touchmove', function(event) {
            if (event.touches.length > 0) {
                const currentX = event.touches[0].clientX;
                const currentY = event.touches[0].clientY;
                const distance = Math.hypot(
                    currentX - touchStartPosition.x,
                    currentY - touchStartPosition.y
                );
                
                // Cancel long press if user drags too far
                if (distance > interactionState.dragThreshold && longPressTimer) {
                    clearTimeout(longPressTimer);
                    longPressTimer = null;
                }
            }
        });
        
        // Hover effects for desktop
        node.addEventListener('mouseenter', function() {
            const nodeId = getNodeId(this);
            if (nodeId) {
                interactionState.hoveredNode = nodeId;
                sendNodeHover(nodeId, true);
                this.classList.add('node-hovered');
            }
        });
        
        node.addEventListener('mouseleave', function() {
            const nodeId = getNodeId(this);
            if (nodeId) {
                interactionState.hoveredNode = null;
                sendNodeHover(nodeId, false);
                this.classList.remove('node-hovered');
                hideNodeTooltip();
            }
        });
        
        // Context menu (right-click)
        node.addEventListener('contextmenu', function(event) {
            event.preventDefault();
            const nodeId = getNodeId(this);
            if (nodeId) {
                showContextMenu(event.clientX, event.clientY, nodeId);
            }
        });
    });
    
    // Global keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        switch(event.key) {
            case 'Escape':
                clearSelection();
                hideContextMenu();
                hideNodeTooltip();
                break;
            case 'a':
            case 'A':
                if (event.metaKey || event.ctrlKey) {
                    event.preventDefault();
                    selectAllNodes();
                }
                break;
            case '0':
                if (event.metaKey || event.ctrlKey) {
                    event.preventDefault();
                    zoomToFit();
                }
                break;
        }
    });
    
    // Clear selection when clicking empty space
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.node, .nodeLabel, [id^="node"], g[id*="node"]')) {
            clearSelection();
            hideContextMenu();
        }
    });
}

// Utility functions
function getNodeId(element) {
    return element.id || 
           element.getAttribute('data-id') || 
           element.getAttribute('data-node-id') ||
           (element.textContent ? element.textContent.trim() : null) ||
           'unknown';
}

function updateSelectionUI() {
    // Update selection count display
    const selectionCount = interactionState.selectedNodes.size;
    
    // Send selection update to iOS
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.selectionChanged) {
        window.webkit.messageHandlers.selectionChanged.postMessage({
            type: 'selectionChanged',
            selectedNodes: Array.from(interactionState.selectedNodes),
            count: selectionCount
        });
    }
}

// Context menu functionality
function showContextMenu(x, y, nodeId) {
    hideContextMenu(); // Hide any existing menu
    
    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.innerHTML = `
        <div class="context-menu-item" onclick="focusOnNode('${nodeId}')">
            <span class="context-menu-icon">🎯</span> Focus on Node
        </div>
        <div class="context-menu-item" onclick="highlightNode('${nodeId}', 'primary')">
            <span class="context-menu-icon">✨</span> Highlight Node
        </div>
        <div class="context-menu-item" onclick="toggleNodeSelection('${nodeId}')">
            <span class="context-menu-icon">☑️</span> Toggle Selection
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" onclick="exportNodeInfo('${nodeId}')">
            <span class="context-menu-icon">📋</span> Copy Node Info
        </div>
    `;
    
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    
    document.body.appendChild(menu);
    interactionState.contextMenu = menu;
    
    // Position menu to stay within viewport
    const rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        menu.style.left = `${x - rect.width}px`;
    }
    if (rect.bottom > window.innerHeight) {
        menu.style.top = `${y - rect.height}px`;
    }
}

function hideContextMenu() {
    if (interactionState.contextMenu) {
        interactionState.contextMenu.remove();
        interactionState.contextMenu = null;
    }
}

function exportNodeInfo(nodeId) {
    const node = document.querySelector(`[id="${nodeId}"]`);
    if (!node) return;
    
    const info = {
        id: nodeId,
        text: node.textContent?.trim() || '',
        className: node.className || '',
        position: node.getBoundingClientRect(),
        attributes: {}
    };
    
    // Collect attributes
    for (let attr of node.attributes) {
        info.attributes[attr.name] = attr.value;
    }
    
    // Copy to clipboard if available
    if (navigator.clipboard) {
        navigator.clipboard.writeText(JSON.stringify(info, null, 2));
    }
    
    hideContextMenu();
}

// Initialize enhanced interactions when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setupAdvancedInteractions();
});

// Fallback initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAdvancedInteractions);
} else {
    setupAdvancedInteractions();
}
