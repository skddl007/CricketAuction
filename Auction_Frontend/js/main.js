/**
 * Main Application Logic
 * Shared functionality across all pages
 */

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeHeader();
    initializeFooter();
    initializeScrollAnimations();
    initializeBackToTop();
});

/**
 * Header Component
 */
function initializeHeader() {
    const headerContainer = document.getElementById('header-container');
    if (!headerContainer) return;

    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    headerContainer.innerHTML = `
        <header class="header">
            <nav class="navbar">
                <div class="container">
                    <div class="nav-brand">
                        <a href="index.html" class="logo">
                            <span class="logo-icon">🏏</span>
                            <span class="logo-text">IPL Auction Strategist</span>
                        </a>
                        <button class="mobile-menu-toggle" aria-label="Toggle menu">
                            <span></span>
                            <span></span>
                            <span></span>
                        </button>
                    </div>
                    <ul class="nav-menu">
                        <li><a href="index.html" class="nav-link ${currentPage === 'index.html' ? 'active' : ''}">Home</a></li>
                        <li><a href="services.html" class="nav-link ${currentPage === 'services.html' ? 'active' : ''}">Services</a></li>
                        <li><a href="team-analysis.html" class="nav-link ${currentPage === 'team-analysis.html' ? 'active' : ''}">Team Analysis</a></li>
                        <li><a href="live-auction.html" class="nav-link ${currentPage === 'live-auction.html' ? 'active' : ''}">Live Auction</a></li>
                        <li><a href="recommender.html" class="nav-link ${currentPage === 'recommender.html' ? 'active' : ''}">Recommender</a></li>
                        <li><a href="chat.html" class="nav-link ${currentPage === 'chat.html' ? 'active' : ''}">Chat</a></li>
                    </ul>
                </div>
            </nav>
        </header>
    `;

    // Add header styles
    if (!document.getElementById('header-styles')) {
        const style = document.createElement('style');
        style.id = 'header-styles';
        style.textContent = `
            .header {
                position: sticky;
                top: 0;
                z-index: 1000;
                background: var(--surface);
                box-shadow: var(--shadow-sm);
                animation: slideInDown 0.5s ease-out;
            }
            .navbar {
                padding: 1rem 0;
            }
            .nav-brand {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .logo {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--primary-color);
            }
            .logo-icon {
                font-size: 1.5rem;
            }
            .nav-menu {
                display: flex;
                list-style: none;
                gap: 2rem;
                margin: 0;
                padding: 0;
            }
            .nav-link {
                position: relative;
                padding: 0.5rem 0;
                color: var(--text-primary);
                font-weight: 500;
                transition: var(--transition);
            }
            .nav-link:hover,
            .nav-link.active {
                color: var(--primary-color);
            }
            .nav-link.active::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: var(--primary-color);
                animation: slideInLeft 0.3s ease-out;
            }
            .mobile-menu-toggle {
                display: none;
                flex-direction: column;
                gap: 4px;
                background: none;
                border: none;
                cursor: pointer;
                padding: 8px;
            }
            .mobile-menu-toggle span {
                width: 24px;
                height: 3px;
                background: var(--text-primary);
                border-radius: 2px;
                transition: var(--transition);
            }
            @media (max-width: 767px) {
                .mobile-menu-toggle {
                    display: flex;
                }
                .nav-menu {
                    position: fixed;
                    top: 70px;
                    right: -100%;
                    width: 80%;
                    max-width: 300px;
                    height: calc(100vh - 70px);
                    background: var(--surface);
                    flex-direction: column;
                    padding: 2rem;
                    box-shadow: var(--shadow-lg);
                    transition: right 0.3s ease-out;
                }
                .nav-menu.active {
                    right: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Mobile menu toggle
    const toggle = headerContainer.querySelector('.mobile-menu-toggle');
    const menu = headerContainer.querySelector('.nav-menu');
    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('active');
        });
    }
}

/**
 * Footer Component
 */
function initializeFooter() {
    const footerContainer = document.getElementById('footer-container');
    if (!footerContainer) return;

    footerContainer.innerHTML = `
        <footer class="footer">
            <div class="container">
                <div class="footer-content">
                    <div class="footer-column">
                        <h3>About</h3>
                        <p>IPL Auction Strategist is an AI-powered system designed to help teams make informed decisions during the IPL auction.</p>
                    </div>
                    <div class="footer-column">
                        <h3>Quick Links</h3>
                        <ul class="footer-links">
                            <li><a href="index.html">Home</a></li>
                            <li><a href="services.html">Services</a></li>
                            <li><a href="team-analysis.html">Team Analysis</a></li>
                            <li><a href="live-auction.html">Live Auction</a></li>
                        </ul>
                    </div>
                    <div class="footer-column">
                        <h3>Contact</h3>
                        <p>For support and inquiries, please use the Chat interface.</p>
                    </div>
                </div>
                <div class="footer-bottom">
                    <p>&copy; ${new Date().getFullYear()} IPL Auction Strategist. All rights reserved.</p>
                    <button class="back-to-top" aria-label="Back to top">
                        <span>↑</span>
                    </button>
                </div>
            </div>
        </footer>
    `;

    // Add footer styles
    if (!document.getElementById('footer-styles')) {
        const style = document.createElement('style');
        style.id = 'footer-styles';
        style.textContent = `
            .footer {
                background: linear-gradient(135deg, var(--primary-dark), var(--primary-color));
                color: white;
                padding: 3rem 0 1rem;
                margin-top: 4rem;
                animation: fadeIn 0.6s ease-out;
            }
            .footer-content {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 2rem;
                margin-bottom: 2rem;
            }
            .footer-column h3 {
                color: white;
                margin-bottom: 1rem;
            }
            .footer-column p {
                color: rgba(255,255,255,0.9);
            }
            .footer-links {
                list-style: none;
            }
            .footer-links li {
                margin-bottom: 0.5rem;
            }
            .footer-links a {
                color: rgba(255,255,255,0.9);
                transition: var(--transition);
            }
            .footer-links a:hover {
                color: var(--secondary-color);
            }
            .footer-bottom {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-top: 2rem;
                border-top: 1px solid rgba(255,255,255,0.2);
            }
            .back-to-top {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                background: var(--secondary-color);
                border: none;
                color: var(--text-primary);
                font-size: 1.5rem;
                cursor: pointer;
                transition: var(--transition);
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .back-to-top:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-md);
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Scroll Animations
 */
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    // Observe all reveal elements
    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });

    // Stagger animation
    const staggerItems = document.querySelectorAll('.stagger-item');
    staggerItems.forEach((item, index) => {
        setTimeout(() => {
            item.classList.add('visible');
        }, index * 100);
    });
}

/**
 * Back to Top Button
 */
function initializeBackToTop() {
    const backToTopBtn = document.querySelector('.back-to-top');
    if (!backToTopBtn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopBtn.style.display = 'flex';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });

    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * Utility: Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Utility: Format number with commas
 */
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}
