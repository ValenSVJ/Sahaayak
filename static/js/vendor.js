// Vendor Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeVoiceSearch();
    initializeDonationForm();
});

// Voice Search Functionality
function initializeVoiceSearch() {
    const voiceBtn = document.getElementById('voiceBtn');
    const searchInput = document.getElementById('searchInput');
    
    // Check if browser supports Speech Recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        voiceBtn.addEventListener('click', function() {
            if (voiceBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
        
        recognition.onstart = function() {
            voiceBtn.classList.add('listening');
            searchInput.placeholder = 'Listening...';
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            searchInput.value = transcript;
            searchInput.placeholder = 'Search Ingredients by Voice...';
            
            // Trigger search
            performSearch(transcript);
        };
        
        recognition.onend = function() {
            voiceBtn.classList.remove('listening');
            searchInput.placeholder = 'Search Ingredients by Voice...';
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            voiceBtn.classList.remove('listening');
            searchInput.placeholder = 'Voice search failed. Try typing...';
            
            setTimeout(() => {
                searchInput.placeholder = 'Search Ingredients by Voice...';
            }, 3000);
        };
    } else {
        voiceBtn.style.display = 'none';
        searchInput.placeholder = 'Search Ingredients...';
    }
    
    // Text search functionality
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });
}

// Search function
function performSearch(query) {
    if (query.trim()) {
        // In a real application, you would implement actual search functionality
        // For now, we'll just show an alert
        showToast(`Searching for: ${query}`, 'info');
        
        // You can redirect to a search results page
        // window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }
}

// Quantity Controls
function increaseQty(btn) {
    const input = btn.parentElement.querySelector('.qty-input');
    input.value = parseInt(input.value) + 1;
}

function decreaseQty(btn) {
    const input = btn.parentElement.querySelector('.qty-input');
    const currentValue = parseInt(input.value);
    if (currentValue > 1) {
        input.value = currentValue - 1;
    }
}

// Reorder functionality
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('reorder-btn')) {
        const card = e.target.closest('.order-card');
        const productName = card.querySelector('.product-name').textContent;
        const quantity = card.querySelector('.qty-input').value;
        
        showToast(`Added ${quantity}x ${productName} to cart!`, 'success');
        
        // In a real application, you would add the item to cart
        // addToCart(productName, quantity);
    }
});

// Donation Form Handling
function initializeDonationForm() {
    const donationForm = document.querySelector('.donation-form');
    
    if (donationForm) {
        donationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(donationForm);
            const foodType = donationForm.querySelector('input[placeholder*="Rice"]').value;
            const quantity = donationForm.querySelector('input[placeholder*="3 kg"]').value;
            const address = donationForm.querySelector('textarea').value;
            const pickupTime = donationForm.querySelector('input[type="datetime-local"]').value;
            
            // Validate form
            if (!foodType || !quantity || !address || !pickupTime) {
                showToast('Please fill in all fields', 'error');
                return;
            }
            
            // Submit donation request
            submitDonationRequest({
                foodType,
                quantity,
                address,
                pickupTime
            });
        });
    }
}

function submitDonationRequest(data) {
    // In a real application, you would send this to your backend
    showToast('Donation request submitted! We\'ll contact you soon.', 'success');
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('donationModal'));
    modal.hide();
    
    // Reset form
    document.querySelector('.donation-form').reset();
    
    // You can send this to your backend API
    // fetch('/api/donation', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify(data)
    // });
}

// Toast notification system
function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getToastColor(type)};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        z-index: 9999;
        font-weight: 500;
        max-width: 300px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

function getToastColor(type) {
    switch (type) {
        case 'success': return '#2ecc71';
        case 'error': return '#e74c3c';
        case 'warning': return '#f39c12';
        default: return '#3498db';
    }
}

// Category click handling
document.addEventListener('click', function(e) {
    if (e.target.closest('.category-item')) {
        const categoryItem = e.target.closest('.category-item');
        const categoryName = categoryItem.querySelector('span').textContent;
        
        // Add loading state
        categoryItem.style.opacity = '0.7';
        categoryItem.style.pointerEvents = 'none';
        
        setTimeout(() => {
            categoryItem.style.opacity = '1';
            categoryItem.style.pointerEvents = 'auto';
        }, 1000);
    }
});

// Smooth scrolling for better UX
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add loading animation for category clicks
function addLoadingState(element) {
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    
    const loader = document.createElement('div');
    loader.className = 'category-loader';
    loader.style.cssText = `
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: loading 1s ease-in-out;
    `;
    
    element.appendChild(loader);
    
    setTimeout(() => {
        if (loader.parentNode) {
            loader.parentNode.removeChild(loader);
        }
    }, 1000);
}

// Add CSS animation for loading
const style = document.createElement('style');
style.textContent = `
    @keyframes loading {
        0% { left: -100%; }
        100% { left: 100%; }
    }
`;
document.head.appendChild(style);

// Initialize tooltips if Bootstrap is available
if (typeof bootstrap !== 'undefined') {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Performance optimization: Lazy load images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
if ('IntersectionObserver' in window) {
    lazyLoadImages();
}
