// ===== ENHANCED SCROLL REVEAL ANIMATIONS =====
document.addEventListener('DOMContentLoaded', function() {
    
    // ===== SCROLL REVEAL OBSERVER =====
    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -50px 0px',
        threshold: 0.1
    };

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                // Add staggered delay for child elements
                const children = entry.target.querySelectorAll('.stagger-child');
                children.forEach((child, index) => {
                    child.style.transitionDelay = `${index * 0.1}s`;
                    child.classList.add('revealed');
                });
            }
        });
    }, observerOptions);

    // Auto-add reveal class to common elements
    const revealSelectors = [
        '.section-title',
        '.feature-card',
        '.hostel-card-wrapper',
        '.why-choose-section .row > div',
        '.search-info',
        '.college-search-box',
        '.card',
        'h1, h2, h3',
        '.hero p',
        '.btn-primary',
        '.filter-dropdown-wrapper'
    ];

    // Apply reveal animation to elements
    revealSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach((el, index) => {
            if (!el.closest('.dropdown-menu')) { // Don't animate dropdown items
                el.classList.add('scroll-reveal');
                el.style.transitionDelay = `${Math.min(index * 0.05, 0.3)}s`;
                revealObserver.observe(el);
            }
        });
    });

    // ===== NAVBAR SCROLL EFFECT =====
    const navbar = document.querySelector('.navbar-custom');
    let lastScroll = 0;
    let ticking = false;

    function updateNavbar() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Hide/show navbar on scroll direction
        if (currentScroll > lastScroll && currentScroll > 200) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }

        lastScroll = currentScroll;
        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateNavbar);
            ticking = true;
        }
    });

    // ===== SMOOTH SCROLL FOR ANCHOR LINKS =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
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

    // ===== BUTTON RIPPLE EFFECT =====
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            button.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // ===== CARD HOVER TILT EFFECT =====
    document.querySelectorAll('.hostel-card, .feature-card').forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 30;
            const rotateY = (centerX - x) / 30;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px) scale(1.02)`;
        });

        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0) scale(1)';
        });
    });

    // ===== PARALLAX EFFECT FOR HERO =====
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            if (scrolled < window.innerHeight) {
                hero.style.backgroundPositionY = `${scrolled * 0.4}px`;
                // Parallax for floating shapes
                document.querySelectorAll('.floating-shape').forEach((shape, index) => {
                    const speed = (index + 1) * 0.1;
                    shape.style.transform = `translateY(${scrolled * speed}px)`;
                });
            }
        });
    }

    // ===== COUNTER ANIMATION =====
    function animateCounter(element, target, duration = 2000) {
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (target - start) * easeOut);

            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    document.querySelectorAll('[data-count]').forEach(counter => {
        const target = parseInt(counter.dataset.count);
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(counter, target);
                    counterObserver.unobserve(counter);
                }
            });
        }, { threshold: 0.5 });

        counterObserver.observe(counter);
    });

    // ===== LAZY LOAD IMAGES WITH FADE =====
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('img-loaded');
                observer.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => imageObserver.observe(img));

    // ===== SEARCH INPUT FOCUS ANIMATION =====
    const searchInput = document.getElementById('searchInput');
    const searchContainer = document.querySelector('.search-container');

    if (searchInput && searchContainer) {
        searchInput.addEventListener('focus', () => {
            searchContainer.classList.add('focused');
        });

        searchInput.addEventListener('blur', () => {
            searchContainer.classList.remove('focused');
        });
    }

    // ===== TEXT TYPING EFFECT =====
    function typeWriter(element, text, speed = 50, callback) {
        let i = 0;
        element.textContent = '';

        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            } else if (callback) {
                callback();
            }
        }

        type();
    }

    // ===== LOADING STATE FOR FORMS =====
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.classList.contains('no-loading')) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
                submitBtn.dataset.originalText = originalText;
            }
        });
    });

    // ===== SCROLL PROGRESS INDICATOR =====
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress';
    document.body.appendChild(progressBar);

    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        progressBar.style.width = scrolled + '%';
    });

    // ===== MOUSE CURSOR GLOW EFFECT (Optional - for hero) =====
    if (hero) {
        hero.addEventListener('mousemove', (e) => {
            const x = e.clientX;
            const y = e.clientY;
            hero.style.setProperty('--mouse-x', `${x}px`);
            hero.style.setProperty('--mouse-y', `${y}px`);
        });
    }

    // ===== PAGE LOAD COMPLETE =====
    document.body.classList.add('page-loaded');
    
    // Trigger initial animations after short delay
    setTimeout(() => {
        document.querySelectorAll('.animate-on-load').forEach((el, index) => {
            setTimeout(() => {
                el.classList.add('animated');
            }, index * 100);
        });
    }, 100);

    console.log('✨ Enhanced animations initialized');
});

// ===== DYNAMIC STYLES =====
const dynamicStyles = document.createElement('style');
dynamicStyles.textContent = `
    /* Scroll Reveal Animation - Elements visible by default */
    .scroll-reveal {
        opacity: 1;
        transform: translateY(0);
        transition: opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), 
                    transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Use this class if you want elements hidden initially */
    .scroll-reveal-hidden {
        opacity: 0;
        transform: translateY(40px);
    }
    
    .scroll-reveal.revealed,
    .scroll-reveal-hidden.revealed {
        opacity: 1;
        transform: translateY(0);
    }
    
    /* Stagger children */
    .stagger-child {
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.4s ease, transform 0.4s ease;
    }
    
    .stagger-child.revealed {
        opacity: 1;
        transform: translateY(0);
    }
    
    /* Ripple Effect */
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.4);
        transform: scale(0);
        animation: ripple-anim 0.6s linear;
        pointer-events: none;
        width: 100px;
        height: 100px;
        margin-left: -50px;
        margin-top: -50px;
    }
    
    @keyframes ripple-anim {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    /* Page Load Animation */
    .page-loaded {
        animation: pageLoad 0.5s ease-out;
    }
    
    @keyframes pageLoad {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Image Load Animation */
    .img-loaded {
        animation: imgFadeIn 0.5s ease-out;
    }
    
    @keyframes imgFadeIn {
        from { 
            opacity: 0; 
            transform: scale(1.05);
        }
        to { 
            opacity: 1; 
            transform: scale(1);
        }
    }
    
    /* Search Focus Effect */
    .search-container {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .search-container.focused {
        transform: scale(1.02);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Scroll Progress Bar */
    .scroll-progress {
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, #2196F3, #667eea, #764ba2);
        z-index: 9999;
        transition: width 0.1s ease;
        width: 0%;
    }
    
    /* Navbar Transition */
    .navbar-custom {
        transition: transform 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    .navbar-custom.scrolled {
        background-color: rgba(255, 255, 255, 0.98) !important;
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Animate on load */
    .animate-on-load {
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 0.6s ease, transform 0.6s ease;
    }
    
    .animate-on-load.animated {
        opacity: 1;
        transform: translateY(0);
    }
    
    /* Hero Mouse Glow */
    .hero::before {
        content: '';
        position: absolute;
        top: var(--mouse-y, 50%);
        left: var(--mouse-x, 50%);
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        transform: translate(-50%, -50%);
        pointer-events: none;
        opacity: 0.5;
        transition: opacity 0.3s ease;
    }
    
    /* Card Smooth Transition */
    .hostel-card, .feature-card, .college-search-box {
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), 
                    box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Floating Animation for Elements */
    @keyframes gentleFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .float-animation {
        animation: gentleFloat 3s ease-in-out infinite;
    }
    
    /* Pulse Animation for CTA */
    @keyframes gentlePulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.4); }
        50% { box-shadow: 0 0 0 15px rgba(33, 150, 243, 0); }
    }
    
    .pulse-animation {
        animation: gentlePulse 2s ease-in-out infinite;
    }
    
    /* Gradient Border Animation */
    @keyframes gradientBorder {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .gradient-border {
        background: linear-gradient(90deg, #2196F3, #667eea, #764ba2, #2196F3);
        background-size: 300% 300%;
        animation: gradientBorder 3s ease infinite;
    }
`;
document.head.appendChild(dynamicStyles);
