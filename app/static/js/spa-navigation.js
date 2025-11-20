/**
 * Single Page Application Navigation
 * Handles smooth transitions between pages without full reloads
 */

class SPANavigation {
    constructor() {
        this.currentPage = null;
        this.isTransitioning = false;
        this.setupNavigation();
    }

    setupNavigation() {
        // Intercept all navigation links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="/pages/"]');
            if (link && !link.hasAttribute('data-external')) {
                e.preventDefault();
                this.navigateTo(link.href);
            }
        });

        // Handle browser back/forward buttons
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.page) {
                this.loadPage(e.state.page, false);
            }
        });

        // Set initial page state
        const currentPath = window.location.pathname;
        if (currentPath.startsWith('/pages/')) {
            history.replaceState({ page: currentPath }, '', currentPath);
        }
    }

    async navigateTo(url) {
        if (this.isTransitioning) return;
        
        const path = new URL(url).pathname;
        
        // Don't navigate if we're already on this page
        if (path === this.currentPage) return;

        this.isTransitioning = true;
        
        try {
            await this.loadPage(path, true);
            history.pushState({ page: path }, '', path);
        } catch (error) {
            console.error('Navigation error:', error);
            // Fallback to normal navigation
            window.location.href = url;
        } finally {
            this.isTransitioning = false;
        }
    }

    async loadPage(path, addToHistory = true) {
        try {
            // Show loading indicator
            this.showLoadingIndicator();

            // Cleanup previous page scripts
            this.cleanupPageScripts();

            // Fetch the new page content
            const response = await fetch(path);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const html = await response.text();
            
            // Parse the HTML to extract the main content
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extract the main content (everything inside body except header and footer)
            const newMain = doc.querySelector('main');
            const newTitle = doc.querySelector('title')?.textContent || 'ProSpeak AI';
            const newScripts = doc.querySelectorAll('script:not([src])'); // Inline scripts
            const newExternalScripts = doc.querySelectorAll('script[src]'); // External scripts
            
            if (newMain) {
                // Fade out current content
                await this.fadeOut();
                
                // Update the main content
                const currentMain = document.querySelector('main');
                if (currentMain) {
                    currentMain.innerHTML = newMain.innerHTML;
                }
                
                // Update page title
                document.title = newTitle;
                
                // Update active navigation
                this.updateActiveNavigation(path);
                
                // Load external scripts first (if not already loaded)
                await this.loadExternalScripts(newExternalScripts);
                
                // Execute inline page-specific scripts
                this.executePageScripts(newScripts);
                
                // Reinitialize common functionality
                this.initializePageScripts();
                
                // Fade in new content
                await this.fadeIn();
                
                this.currentPage = path;
            } else {
                throw new Error('No main content found');
            }
            
        } catch (error) {
            console.error('Failed to load page:', error);
            throw error;
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async fadeOut() {
        const main = document.querySelector('main');
        if (main) {
            main.style.transition = 'opacity 0.2s ease-out';
            main.style.opacity = '0';
            await new Promise(resolve => setTimeout(resolve, 200));
        }
    }

    async fadeIn() {
        const main = document.querySelector('main');
        if (main) {
            main.style.opacity = '0';
            await new Promise(resolve => setTimeout(resolve, 50));
            main.style.transition = 'opacity 0.3s ease-in';
            main.style.opacity = '1';
            await new Promise(resolve => setTimeout(resolve, 300));
        }
    }

    updateActiveNavigation(path) {
        // Remove active class from all nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to current page link
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('href') === path) {
                link.classList.add('active');
            }
        });
    }

    cleanupPageScripts() {
        // Cleanup interview simulator
        if (window.interviewSimulatorInitialized && typeof cleanupInterviewSimulator === 'function') {
            cleanupInterviewSimulator();
        }
        
        // Cleanup audio practice
        if (window.audioPracticeInitialized && typeof cleanupAudioPractice === 'function') {
            cleanupAudioPractice();
        }
        
        // Cleanup fluency coach
        if (window.fluencyCoachInitialized && typeof cleanupFluencyCoach === 'function') {
            cleanupFluencyCoach();
        }
        
        // Cleanup dashboard
        if (window.dashboardInitialized && typeof cleanupDashboard === 'function') {
            cleanupDashboard();
        }
        
        // Cleanup presentation practice
        if (window.presentationPracticeInitialized && typeof cleanupPresentationPractice === 'function') {
            cleanupPresentationPractice();
        }
        
        // Cleanup profile settings
        if (window.profileSettingsInitialized && typeof cleanupProfileSettings === 'function') {
            cleanupProfileSettings();
        }
        
        // Clear any page-specific timers
        if (window.pageTimers) {
            window.pageTimers.forEach(timer => clearInterval(timer));
            window.pageTimers = [];
        }
        
        console.log('Previous page scripts cleaned up');
    }

    async loadExternalScripts(scriptElements) {
        const loadedScripts = new Set();
        
        // Get already loaded scripts
        document.querySelectorAll('script[src]').forEach(script => {
            loadedScripts.add(script.src);
        });
        
        // Load new scripts that aren't already loaded
        const scriptPromises = [];
        scriptElements.forEach(scriptEl => {
            const src = scriptEl.src;
            if (src && !loadedScripts.has(src)) {
                scriptPromises.push(new Promise((resolve, reject) => {
                    const script = document.createElement('script');
                    script.src = src;
                    script.onload = resolve;
                    script.onerror = reject;
                    document.head.appendChild(script);
                }));
            }
        });
        
        await Promise.all(scriptPromises);
    }

    executePageScripts(scriptElements) {
        scriptElements.forEach(scriptEl => {
            try {
                const scriptContent = scriptEl.textContent;
                
                // Skip if it's just a comment or empty
                if (!scriptContent.trim() || scriptContent.trim().startsWith('//')) {
                    return;
                }
                
                // Create a new script element and execute it
                const newScript = document.createElement('script');
                newScript.textContent = scriptContent;
                document.body.appendChild(newScript);
                
                // Remove the script after execution to keep DOM clean
                setTimeout(() => newScript.remove(), 100);
                
            } catch (error) {
                console.error('Error executing page script:', error);
            }
        });
        
        console.log('Page-specific scripts executed');
    }

    initializePageScripts() {
        // Reinitialize common functionality
        if (typeof loadUserData === 'function') {
            loadUserData();
        }
        
        // Reinitialize dropdowns
        if (typeof window.reinitializeDropdowns === 'function') {
            window.reinitializeDropdowns();
        }
        
        // Trigger custom page initialization event
        document.dispatchEvent(new CustomEvent('pageLoaded'));
        
        console.log('Common scripts reinitialized');
    }

    showLoadingIndicator() {
        // Create or show loading indicator
        let loader = document.getElementById('spa-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'spa-loader';
            loader.innerHTML = `
                <div class="fixed top-0 left-0 w-full h-1 bg-gray-200 z-50">
                    <div class="h-full bg-primary transition-all duration-300 ease-out" style="width: 0%"></div>
                </div>
            `;
            document.body.appendChild(loader);
        }
        
        // Animate progress bar
        const progressBar = loader.querySelector('.bg-primary');
        progressBar.style.width = '70%';
    }

    hideLoadingIndicator() {
        const loader = document.getElementById('spa-loader');
        if (loader) {
            const progressBar = loader.querySelector('.bg-primary');
            progressBar.style.width = '100%';
            
            setTimeout(() => {
                loader.remove();
            }, 200);
        }
    }
}

// Initialize SPA navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on user pages
    if (window.location.pathname.startsWith('/pages/user/')) {
        window.spaNav = new SPANavigation();
        console.log('SPA Navigation initialized');
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SPANavigation;
}