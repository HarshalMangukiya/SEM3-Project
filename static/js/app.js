// Main Application Module - Coordinates all modules
class StayfinderApp {
    constructor() {
        this.currentPage = '';
        this.currentFilter = 'all'; // Default filter for enhanced search
        this.init();
    }

    async init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupApp());
        } else {
            this.setupApp();
        }
    }

    async setupApp() {
        try {
            // Initialize authentication
            await authService.init();
            
            // Setup page-specific functionality
            this.setupPageHandlers();
            
            // Setup global event listeners
            this.setupGlobalEventListeners();
            
            // Setup routing
            this.setupRouting();
            
            // Load initial data if needed
            await this.loadInitialData();
            
            console.log('Stayfinder app initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
        }
    }

    setupPageHandlers() {
        const path = window.location.pathname;
        this.currentPage = path;

        // Page-specific initialization
        switch (path) {
            case '/':
            case '/index.html':
                this.setupHomePage();
                break;
            case '/login':
                this.setupLoginPage();
                break;
            case '/register':
                this.setupRegisterPage();
                break;
            case '/add':
                this.setupAddHostelPage();
                break;
            case '/account-settings':
                this.setupAccountSettingsPage();
                break;
            default:
                if (path.startsWith('/hostel/')) {
                    this.setupHostelDetailPage();
                }
                break;
        }
    }

    setupGlobalEventListeners() {
        // Enhanced search functionality
        this.setupEnhancedSearch();

        // Filter changes
        const filters = ['cityFilter', 'typeFilter', 'priceRange'];
        filters.forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element) {
                element.addEventListener('change', () => this.applyFilters());
            }
        });

        // Amenity checkboxes
        document.querySelectorAll('.amenity-filters input').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.applyFilters());
        });

        // Price range slider
        const priceRange = document.getElementById('priceRange');
        const priceValue = document.getElementById('priceValue');
        if (priceRange && priceValue) {
            priceRange.addEventListener('input', (e) => {
                priceValue.textContent = e.target.value;
            });
        }

        // Custom events
        window.addEventListener('filtersCleared', () => this.applyFilters());
        window.addEventListener('userLoggedIn', () => this.handleUserLogin());
        window.addEventListener('userLoggedOut', () => this.handleUserLogout());
    }

    setupEnhancedSearch() {
        // Filter buttons
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFilterClick(e));
        });

        // Search button
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.handleEnhancedSearch());
        }

        // Search input with debouncing
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.handleSearchSuggestions(e.target.value);
                }, 300);
            });

            // Handle Enter key
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleEnhancedSearch();
                }
            });

            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.search-container')) {
                    document.getElementById('searchSuggestions').style.display = 'none';
                }
            });
        }
    }

    handleFilterClick(e) {
        const filterBtn = e.target;
        const filterType = filterBtn.dataset.filter;
        
        // Update active state
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        filterBtn.classList.add('active');
        
        // Store current filter
        this.currentFilter = filterType;
        
        // Trigger search with current query if exists
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value.trim()) {
            this.handleEnhancedSearch();
        }
    }

    async handleEnhancedSearch() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput ? searchInput.value.trim() : '';
        const propertyType = this.currentFilter || 'all';
        
        try {
            stateManager.setLoading(true);
            stateManager.setSearchQuery(query);
            
            const results = await apiService.searchHostels(query, propertyType);
            
            if (results.success) {
                // Update state with search results
                stateManager.setHostels(results.data);
                this.renderHostelGrid();
                
                // Show results count
                this.showSearchResults(results.count, query, propertyType);
            } else {
                throw new Error(results.message || 'Search failed');
            }
        } catch (error) {
            console.error('Enhanced search failed:', error);
            uiComponents.showNotification('Search failed. Please try again.', 'error');
            
            // Show empty state on error
            const container = document.querySelector('.hostels-scroll-container');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-5 w-100">
                        <i class="bi bi-exclamation-triangle display-1 text-warning"></i>
                        <h3 class="mt-3">Search Error</h3>
                        <p class="text-muted">Unable to perform search. Please try again.</p>
                        <button class="btn btn-primary mt-3" onclick="app.clearSearch()">Clear Search</button>
                    </div>
                `;
            }
        } finally {
            stateManager.setLoading(false);
        }
    }

    async handleSearchSuggestions(query) {
        const suggestionsContainer = document.getElementById('searchSuggestions');
        
        if (query.length < 2) {
            suggestionsContainer.style.display = 'none';
            suggestionsContainer.innerHTML = '';
            return;
        }

        try {
            const propertyType = this.currentFilter || 'all';
            const results = await apiService.searchHostels(query, propertyType);
            
            if (results.success && results.data.length > 0) {
                const suggestions = results.data.slice(0, 5).map(hostel => `
                    <div class="suggestion-item" onclick="app.selectSuggestion('${hostel.name}', '${hostel.city}')">
                        <i class="bi bi-geo-alt"></i> 
                        <strong>${hostel.name}</strong> - ${hostel.city}
                        ${hostel.location ? `, ${hostel.location}` : ''}
                    </div>
                `).join('');
                
                suggestionsContainer.innerHTML = suggestions;
                suggestionsContainer.style.display = 'block';
            } else {
                suggestionsContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to get suggestions:', error);
            suggestionsContainer.style.display = 'none';
        }
    }

    selectSuggestion(hostelName, city) {
        const searchInput = document.getElementById('searchInput');
        const suggestionsContainer = document.getElementById('searchSuggestions');
        
        searchInput.value = `${hostelName}, ${city}`;
        suggestionsContainer.style.display = 'none';
        this.handleEnhancedSearch();
    }

    showSearchResults(count, query, propertyType) {
        const container = document.querySelector('.container.mt-5');
        const resultsHeader = container.querySelector('h3');
        
        if (query) {
            const propertyTypeText = propertyType !== 'all' ? propertyType.charAt(0).toUpperCase() + propertyType.slice(1) : '';
            resultsHeader.textContent = `Search Results (${count})${propertyTypeText ? ` - ${propertyTypeText}` : ''}`;
            
            if (count === 0) {
                resultsHeader.innerHTML += `<br><small class="text-muted">No results found for "${query}"${propertyTypeText ? ` in ${propertyTypeText}` : ''}</small>`;
            }
        } else {
            resultsHeader.textContent = 'Popular Hostels & PGs';
        }
    }

    setupRouting() {
        // Client-side routing for single-page feel
        const links = document.querySelectorAll('[data-route]');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const route = link.getAttribute('data-route');
                this.navigateTo(route);
            });
        });
    }

    async loadInitialData() {
        // Load hostels if on home page
        if (this.currentPage === '/' || this.currentPage === '/index.html') {
            await this.loadHostels();
        }
    }

    // Page-specific setup methods
    setupHomePage() {
        console.log('Setting up home page');
        this.renderHostelGrid();
    }

    setupLoginPage() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // OAuth buttons
        const googleBtn = document.getElementById('googleLoginBtn');
        const facebookBtn = document.getElementById('facebookLoginBtn');
        
        if (googleBtn) googleBtn.addEventListener('click', () => authService.loginWithGoogle());
        if (facebookBtn) facebookBtn.addEventListener('click', () => authService.loginWithFacebook());
    }

    setupRegisterPage() {
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Password confirmation validation
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirmPassword');
        
        if (password && confirmPassword) {
            confirmPassword.addEventListener('input', () => {
                if (confirmPassword.value !== password.value) {
                    confirmPassword.setCustomValidity('Passwords do not match');
                } else {
                    confirmPassword.setCustomValidity('');
                }
            });
        }
    }

    setupAddHostelPage() {
        const addHostelForm = document.getElementById('addHostelForm');
        if (addHostelForm) {
            addHostelForm.addEventListener('submit', (e) => this.handleAddHostel(e));
        }

        // Dynamic form fields
        this.setupDynamicFormFields();
    }

    setupAccountSettingsPage() {
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => this.handleProfileUpdate(e));
        }

        // Load user data
        this.loadUserProfile();
    }

    setupHostelDetailPage() {
        // Load hostel details
        this.loadHostelDetails();
        
        // Setup booking form
        const bookingForm = document.getElementById('bookingForm');
        if (bookingForm) {
            bookingForm.addEventListener('submit', (e) => this.handleBooking(e));
        }
    }

    // Event handlers (legacy - kept for compatibility)
    async handleSearch(e) {
        e.preventDefault();
        // Redirect to enhanced search
        this.handleEnhancedSearch();
    }

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        const errors = authService.validateLoginForm(email, password);
        if (errors) {
            this.displayFormErrors(errors);
            return;
        }

        const result = await authService.login(email, password);
        if (result.success) {
            window.location.href = result.redirect;
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const userData = Object.fromEntries(formData.entries());

        const errors = authService.validateRegisterForm(userData);
        if (errors) {
            this.displayFormErrors(errors);
            return;
        }

        const result = await authService.register(userData);
        if (result.success) {
            window.location.href = result.redirect;
        }
    }

    async handleAddHostel(e) {
        e.preventDefault();
        const formData = new FormData(e.target);

        try {
            stateManager.setLoading(true);
            const result = await apiService.addHostel(formData);
            
            if (result.success !== false) {
                uiComponents.showNotification('Hostel added successfully!', 'success');
                window.location.href = '/';
            } else {
                throw new Error(result.message || 'Failed to add hostel');
            }
        } catch (error) {
            console.error('Add hostel failed:', error);
            uiComponents.showNotification(error.message, 'error');
        } finally {
            stateManager.setLoading(false);
        }
    }

    async handleProfileUpdate(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const profileData = Object.fromEntries(formData.entries());

        const result = await authService.updateProfile(profileData);
        if (result.success) {
            uiComponents.showNotification('Profile updated successfully!', 'success');
        }
    }

    async handleBooking(e) {
        e.preventDefault();
        if (!authService.isAuthenticated()) {
            uiComponents.showNotification('Please login to make a booking', 'warning');
            window.location.href = '/login';
            return;
        }

        // Handle booking logic
        uiComponents.showNotification('Booking feature coming soon!', 'info');
    }

    // Data loading methods
    async loadHostels() {
        try {
            stateManager.setLoading(true);
            const hostels = await apiService.getHostels();
            stateManager.setHostels(hostels);
            this.renderHostelGrid();
        } catch (error) {
            console.error('Failed to load hostels:', error);
        } finally {
            stateManager.setLoading(false);
        }
    }

    async loadHostelDetails() {
        const hostelId = window.location.pathname.split('/').pop();
        try {
            stateManager.setLoading(true);
            const hostel = await apiService.getHostel(hostelId);
            stateManager.setCurrentHostel(hostel);
            this.renderHostelDetails(hostel);
        } catch (error) {
            console.error('Failed to load hostel details:', error);
        } finally {
            stateManager.setLoading(false);
        }
    }

    async loadUserProfile() {
        if (!authService.isAuthenticated()) return;

        try {
            const user = authService.getCurrentUser();
            if (user) {
                this.populateProfileForm(user);
            }
        } catch (error) {
            console.error('Failed to load user profile:', error);
        }
    }

    // Rendering methods
    renderHostelGrid() {
        const hostels = stateManager.filterHostels();
        const container = document.querySelector('.hostels-scroll-container');
        
        if (!container) return;

        if (hostels.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 w-100">
                    <i class="bi bi-house-x display-1 text-muted"></i>
                    <h3 class="mt-3">No hostels found</h3>
                    <p class="text-muted">Try adjusting your search or filters</p>
                    <button class="btn btn-primary mt-3" onclick="app.clearSearch()">Clear Search</button>
                </div>
            `;
            return;
        }

        container.innerHTML = hostels.map(hostel => this.createHostelCard(hostel)).join('');
    }

    createHostelCard(hostel) {
        const amenities = hostel.amenities ? hostel.amenities.slice(0, 5) : ['WiFi', 'Fully Furnished', 'AC', 'TV', 'Laundry'];
        const amenityBadges = amenities.map(amenity => {
            let icon = '';
            let text = amenity.toUpperCase();
            
            if (amenity === 'WiFi' || amenity === 'WIFI') {
                icon = '<i class="bi bi-wifi"></i>';
                text = 'WIFI';
            } else if (amenity === 'Fully Furnished' || amenity === 'FULLY FURNISHED') {
                icon = '<i class="bi bi-house-check"></i>';
                text = 'FULLY FURNISHED';
            } else if (amenity === 'AC') {
                icon = '<i class="bi bi-snow"></i>';
            } else if (amenity === 'TV') {
                icon = '<i class="bi bi-tv"></i>';
            } else if (amenity === 'Laundry' || amenity === 'LAUNDARY') {
                icon = '<i class="bi bi-droplet"></i>';
                text = 'LAUNDARY';
            } else {
                icon = '<i class="bi bi-check-circle"></i>';
            }
            
            return `<span class="amenity-badge">${icon} ${text}</span>`;
        }).join('');

        const imageUrl = (hostel.image && hostel.image.trim() && hostel.image !== 'undefined') ? 
            hostel.image : 
            'https://via.placeholder.com/400x300?text=No+Image';

        return `
            <div class="hostel-card-wrapper">
                <div class="card shadow-sm h-100 border-0 hostel-card">
                    <div class="position-relative">
                        <img src="${imageUrl}" class="card-img-top" alt="${hostel.name}" 
                             style="height: 240px; object-fit: cover; width: 100%;" 
                             onerror="this.onerror=null; this.src='https://via.placeholder.com/400x300?text=Image+Not+Available';">
                        <div class="position-absolute top-0 end-0 m-2">
                            ${hostel.type ? `
                                <span class="badge bg-dark text-white px-3 py-2 rounded-pill" style="font-size: 0.8rem; background-color: rgba(0, 0, 0, 0.75) !important;">
                                    <i class="bi bi-${hostel.type === 'Boys' ? 'gender-male' : hostel.type === 'Girls' ? 'gender-female' : 'people'}"></i> ${hostel.type}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title mb-2 fw-bold">${hostel.name}</h5>
                        <p class="text-muted mb-3">
                            <i class="bi bi-geo-alt-fill"></i> 
                            ${hostel.location ? `${hostel.location}, ` : ''}${hostel.city}
                        </p>
                        
                        <!-- Amenities -->
                        <div class="mb-3 d-flex flex-wrap gap-2">
                            ${amenityBadges}
                        </div>
                        
                        <!-- Pricing -->
                        <div class="mt-auto">
                            <div class="mb-2 price-display">
                                ${hostel.original_price && hostel.original_price != hostel.price ? 
                                    `<span class="text-decoration-line-through text-muted" style="font-size: 0.9rem;">₹${hostel.original_price}/-</span>` : ''
                                }
                                <span class="fw-bold text-primary" style="font-size: 1.3rem;">₹${hostel.price}/-</span>
                            </div>
                            <p class="text-muted mb-3" style="font-size: 0.85rem;">Monthly Rent From</p>
                            <a href="/hostel/${hostel._id}" class="btn btn-primary w-100">View Details</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Reset filter to 'all'
        this.currentFilter = 'all';
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.filter === 'all') {
                btn.classList.add('active');
            }
        });
        
        // Reset search query and reload hostels
        stateManager.setSearchQuery('');
        this.loadHostels();
        this.showSearchResults(0, '', 'all');
    }

    renderHostelDetails(hostel) {
        // Implement hostel detail rendering
        console.log('Rendering hostel details:', hostel);
    }

    populateProfileForm(user) {
        const form = document.getElementById('profileForm');
        if (!form) return;

        Object.keys(user).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = user[key] || '';
            }
        });
    }

    // Utility methods
    applyFilters() {
        const city = document.getElementById('cityFilter')?.value || '';
        const type = document.getElementById('typeFilter')?.value || '';
        const maxPrice = parseInt(document.getElementById('priceRange')?.value || '10000');
        const amenities = Array.from(document.querySelectorAll('.amenity-filters input:checked'))
            .map(cb => cb.value);

        stateManager.setFilters({ city, type, priceRange: [0, maxPrice], amenities });
        this.renderHostelGrid();
    }

    setupDynamicFormFields() {
        // Add dynamic neighborhood highlights
        const addNeighborhoodBtn = document.getElementById('addNeighborhoodBtn');
        if (addNeighborhoodBtn) {
            addNeighborhoodBtn.addEventListener('click', () => this.addNeighborhoodField());
        }

        // Add dynamic room types
        const addRoomTypeBtn = document.getElementById('addRoomTypeBtn');
        if (addRoomTypeBtn) {
            addRoomTypeBtn.addEventListener('click', () => this.addRoomTypeField());
        }
    }

    addNeighborhoodField() {
        const container = document.getElementById('neighborhoodHighlights');
        const index = container.children.length;
        const field = document.createElement('div');
        field.className = 'row mb-2';
        field.innerHTML = `
            <div class="col-md-4">
                <input type="text" class="form-control" name="nearby_place_${index}" placeholder="Place name">
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control" name="nearby_distance_${index}" placeholder="Distance">
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control" name="nearby_time_${index}" placeholder="Travel time">
            </div>
        `;
        container.appendChild(field);
    }

    addRoomTypeField() {
        // Implement dynamic room type addition
        console.log('Adding room type field');
    }

    displayFormErrors(errors) {
        Object.keys(errors).forEach(field => {
            const input = document.getElementById(field);
            if (input) {
                input.setCustomValidity(errors[field]);
                input.classList.add('is-invalid');
            }
        });
    }

    navigateTo(route) {
        window.history.pushState({}, '', route);
        this.setupPageHandlers();
    }

    handleUserLogin() {
        console.log('User logged in');
        // Update UI for logged-in user
        this.updateAuthUI();
    }

    handleUserLogout() {
        console.log('User logged out');
        // Update UI for logged-out user
        this.updateAuthUI();
    }

    updateAuthUI() {
        const authButtons = document.getElementById('authButtons');
        const userMenu = document.getElementById('userMenu');
        
        if (authService.isAuthenticated()) {
            if (authButtons) authButtons.style.display = 'none';
            if (userMenu) userMenu.style.display = 'block';
        } else {
            if (authButtons) authButtons.style.display = 'block';
            if (userMenu) userMenu.style.display = 'none';
        }
    }
}

// Initialize the app
const app = new StayfinderApp();
export default app;
