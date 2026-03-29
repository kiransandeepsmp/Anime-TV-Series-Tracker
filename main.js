// Main JavaScript for Anime Tracker

// Theme toggle functionality
function toggleTheme() {
    fetch('/toggle_theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        document.documentElement.setAttribute('data-theme', data.theme);
        
        // Show toast notification
        showToast(`Switched to ${data.theme} theme`, 'success');
    })
    .catch(error => {
        console.error('Error toggling theme:', error);
        showToast('Failed to toggle theme', 'error');
    });
}

// Update watchlist item
function updateWatchlistItem(itemId, field, value) {
    const formData = new FormData();
    formData.append('item_id', itemId);
    formData.append(field, value);
    
    fetch('/update_watchlist', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            
            // Update progress bar if episodes were updated
            if (field === 'episodes_watched' && data.progress !== undefined) {
                const progressBar = document.querySelector(`#progress-${itemId}`);
                if (progressBar) {
                    progressBar.style.width = `${data.progress}%`;
                    progressBar.setAttribute('aria-valuenow', data.progress);
                }
            }
            
            // Reload page if status was changed to update layout
            if (field === 'status') {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error updating watchlist:', error);
        showToast('Failed to update watchlist', 'error');
    });
}

// Rating system
function setRating(itemId, rating) {
    // Update visual stars
    const stars = document.querySelectorAll(`#rating-${itemId} .rating-label`);
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
    
    // Update watchlist item
    updateWatchlistItem(itemId, 'rating', rating);
}

// Episode increment/decrement
function updateEpisodes(itemId, change) {
    const input = document.querySelector(`#episodes-${itemId}`);
    if (input) {
        const currentValue = parseInt(input.value) || 0;
        const maxEpisodes = parseInt(input.getAttribute('max')) || 999;
        const newValue = Math.max(0, Math.min(maxEpisodes, currentValue + change));
        
        input.value = newValue;
        updateWatchlistItem(itemId, 'episodes_watched', newValue);
    }
}

// Search functionality
function performSearch() {
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.submit();
    }
}

// Filter functionality
function applyFilters() {
    const filterForm = document.querySelector('#filter-form');
    if (filterForm) {
        filterForm.submit();
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container or create one
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize rating stars
    document.querySelectorAll('.rating-stars').forEach(ratingContainer => {
        const itemId = ratingContainer.dataset.itemId;
        const currentRating = parseInt(ratingContainer.dataset.rating) || 0;
        
        // Set initial star states
        const stars = ratingContainer.querySelectorAll('.rating-label');
        stars.forEach((star, index) => {
            if (index < currentRating) {
                star.classList.add('active');
            }
            
            // Add click event
            star.addEventListener('click', () => {
                setRating(itemId, index + 1);
            });
        });
    });
    
    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
