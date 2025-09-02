import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BookOpen, TrendingUp, Heart, Target, User, Search, Star, FolderOpen, Tag, BarChart3, Settings, ChevronDown } from 'lucide-react';
import { getArticleLibraryNavigation } from '../../routes/articleLibraryRoutes';
import { isFeatureEnabled } from '../../config/articleLibrary';

const Navigation = () => {
    const location = useLocation();
    const [isArticleMenuOpen, setIsArticleMenuOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const articleMenuRef = useRef(null);
    const mobileMenuRef = useRef(null);
    
    // Main navigation items
    const mainNavItems = [
        { path: '/', label: 'Dashboard', icon: TrendingUp, description: 'View your financial overview and key metrics' },
        { path: '/budget', label: 'Budget', icon: Target, description: 'Manage your budget and track expenses' },
        { path: '/health', label: 'Health Check', icon: Heart, description: 'Assess your financial health and get recommendations' },
        { path: '/profile', label: 'Profile', icon: User, description: 'Manage your account settings and preferences' },
    ];

    // Article library navigation items
    const articleLibraryNavItems = getArticleLibraryNavigation();
    
    // Check if we're in the article library section
    const isInArticleSection = location.pathname.startsWith('/articles');
    
    // Get the current article library item
    const getCurrentArticleItem = () => {
        const pathSegments = location.pathname.split('/').filter(Boolean);
        if (pathSegments.length > 1) {
            return articleLibraryNavItems.find(item => item.id === pathSegments[1]);
        }
        return articleLibraryNavItems.find(item => item.id === 'home');
    };

    const currentArticleItem = getCurrentArticleItem();

    // Close menus when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (articleMenuRef.current && !articleMenuRef.current.contains(event.target)) {
                setIsArticleMenuOpen(false);
            }
            if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target)) {
                setIsMobileMenuOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Close menus when route changes
    useEffect(() => {
        setIsArticleMenuOpen(false);
        setIsMobileMenuOpen(false);
    }, [location]);

    // Handle keyboard navigation
    const handleKeyDown = (event, action) => {
        switch (event.key) {
            case 'Enter':
            case ' ':
                event.preventDefault();
                action();
                break;
            case 'Escape':
                setIsArticleMenuOpen(false);
                setIsMobileMenuOpen(false);
                break;
            case 'ArrowDown':
                if (event.target.getAttribute('aria-expanded') === 'true') {
                    event.preventDefault();
                    const firstMenuItem = event.target.nextElementSibling?.querySelector('a, button');
                    if (firstMenuItem) firstMenuItem.focus();
                }
                break;
            case 'ArrowUp':
                if (event.target.getAttribute('aria-expanded') === 'true') {
                    event.preventDefault();
                    const lastMenuItem = event.target.nextElementSibling?.querySelector('a:last-child, button:last-child');
                    if (lastMenuItem) lastMenuItem.focus();
                }
                break;
        }
    };

    return (
        <nav 
            className="bg-white shadow-sm border-b" 
            role="navigation" 
            aria-label="Main navigation"
            id="navigation"
        >
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex space-x-8">
                        {/* Main navigation items */}
                        {mainNavItems.map(({ path, label, icon: Icon, description }) => (
                            <Link
                                key={path}
                                to={path}
                                className={`
                                    inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
                                    ${location.pathname === path
                                        ? 'border-purple-500 text-purple-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                                `}
                                aria-current={location.pathname === path ? 'page' : undefined}
                                aria-label={`${label} - ${description}`}
                                title={description}
                            >
                                <Icon className="w-4 h-4 mr-2" aria-hidden="true" />
                                <span className="sr-only">{description}</span>
                                {label}
                            </Link>
                        ))}
                        
                        {/* Article Library dropdown */}
                        <div className="relative" ref={articleMenuRef}>
                            <button
                                onClick={() => setIsArticleMenuOpen(!isArticleMenuOpen)}
                                onKeyDown={(e) => handleKeyDown(e, () => setIsArticleMenuOpen(!isArticleMenuOpen))}
                                className={`
                                    inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
                                    ${isInArticleSection
                                        ? 'border-purple-500 text-purple-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                                `}
                                aria-expanded={isArticleMenuOpen}
                                aria-haspopup="true"
                                aria-controls="article-library-menu"
                                aria-label="Learning Library menu"
                                title="Access financial education articles and resources"
                            >
                                <BookOpen className="w-4 h-4 mr-2" aria-hidden="true" />
                                <span className="sr-only">Learning Library</span>
                                Learning Library
                                <ChevronDown 
                                    className={`w-4 h-4 ml-1 transition-transform ${isArticleMenuOpen ? 'rotate-180' : ''}`} 
                                    aria-hidden="true"
                                />
                            </button>
                            
                            {/* Article Library dropdown menu */}
                            {isArticleMenuOpen && (
                                <div 
                                    id="article-library-menu"
                                    className="absolute top-full left-0 mt-1 w-64 bg-white rounded-md shadow-lg border border-gray-200 z-50"
                                    role="menu"
                                    aria-label="Learning Library options"
                                >
                                    <div className="py-2">
                                        {/* Main article library link */}
                                        <Link
                                            to="/articles"
                                            className={`
                                                flex items-center px-4 py-2 text-sm
                                                ${location.pathname === '/articles'
                                                    ? 'bg-purple-50 text-purple-700'
                                                    : 'text-gray-700 hover:bg-gray-50'}
                                            `}
                                            onClick={() => setIsArticleMenuOpen(false)}
                                            role="menuitem"
                                            aria-label="Browse all financial education articles"
                                            title="Browse all financial education articles"
                                        >
                                            <BookOpen className="w-4 h-4 mr-3" aria-hidden="true" />
                                            <span className="sr-only">Browse all</span>
                                            All Articles
                                        </Link>
                                        
                                        {/* Divider */}
                                        <div className="border-t border-gray-100 my-1" role="separator" aria-hidden="true"></div>
                                        
                                        {/* Article library sub-items */}
                                        {articleLibraryNavItems
                                            .filter(item => item.id !== 'home') // Exclude home as it's handled above
                                            .filter(item => {
                                                // Check feature flags
                                                if (item.featureFlag && !isFeatureEnabled(item.featureFlag)) {
                                                    return false;
                                                }
                                                return true;
                                            })
                                            .map((item) => (
                                                <Link
                                                    key={item.id}
                                                    to={`/articles/${item.id}`}
                                                    className={`
                                                        flex items-center px-4 py-2 text-sm
                                                        ${location.pathname === `/articles/${item.id}`
                                                            ? 'bg-purple-50 text-purple-700'
                                                            : 'text-gray-700 hover:bg-gray-50'}
                                                    `}
                                                    onClick={() => setIsArticleMenuOpen(false)}
                                                    role="menuitem"
                                                    aria-label={`${item.title} - ${item.description}`}
                                                    title={item.description}
                                                >
                                                    {item.icon && <item.icon className="w-4 h-4 mr-3" aria-hidden="true" />}
                                                    <span className="sr-only">{item.description}</span>
                                                    {item.title}
                                                </Link>
                                            ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Mobile menu button */}
                    <div className="flex items-center sm:hidden">
                        <button
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            onKeyDown={(e) => handleKeyDown(e, () => setIsMobileMenuOpen(!isMobileMenuOpen))}
                            className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500"
                            aria-expanded={isMobileMenuOpen}
                            aria-controls="mobile-menu"
                            aria-label="Toggle mobile menu"
                            title="Open or close mobile navigation menu"
                        >
                            <span className="sr-only">Open main menu</span>
                            {isMobileMenuOpen ? (
                                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            ) : (
                                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile menu */}
            {isMobileMenuOpen && (
                <div 
                    id="mobile-menu"
                    className="sm:hidden"
                    role="menu"
                    aria-label="Mobile navigation menu"
                    ref={mobileMenuRef}
                >
                    <div className="pt-2 pb-3 space-y-1">
                        {mainNavItems.map(({ path, label, icon: Icon, description }) => (
                            <Link
                                key={path}
                                to={path}
                                className={`
                                    block pl-3 pr-4 py-2 border-l-4 text-base font-medium
                                    ${location.pathname === path
                                        ? 'bg-purple-50 border-purple-500 text-purple-700'
                                        : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'}
                                `}
                                onClick={() => setIsMobileMenuOpen(false)}
                                role="menuitem"
                                aria-current={location.pathname === path ? 'page' : undefined}
                                aria-label={`${label} - ${description}`}
                                title={description}
                            >
                                <div className="flex items-center">
                                    <Icon className="w-5 h-5 mr-3" aria-hidden="true" />
                                    <span className="sr-only">{description}</span>
                                    {label}
                                </div>
                            </Link>
                        ))}
                        
                        {/* Mobile Article Library section */}
                        <div className="border-t border-gray-200 pt-4">
                            <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                Learning Library
                            </div>
                            <Link
                                to="/articles"
                                className={`
                                    block pl-3 pr-4 py-2 border-l-4 text-base font-medium
                                    ${location.pathname === '/articles'
                                        ? 'bg-purple-50 border-purple-500 text-purple-700'
                                        : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'}
                                `}
                                onClick={() => setIsMobileMenuOpen(false)}
                                role="menuitem"
                                aria-label="Browse all financial education articles"
                                title="Browse all financial education articles"
                            >
                                <div className="flex items-center">
                                    <BookOpen className="w-5 h-5 mr-3" aria-hidden="true" />
                                    <span className="sr-only">Browse all articles</span>
                                    All Articles
                                </div>
                            </Link>
                            
                            {articleLibraryNavItems
                                .filter(item => item.id !== 'home')
                                .filter(item => {
                                    if (item.featureFlag && !isFeatureEnabled(item.featureFlag)) {
                                        return false;
                                    }
                                    return true;
                                })
                                .map((item) => (
                                    <Link
                                        key={item.id}
                                        to={`/articles/${item.id}`}
                                        className={`
                                            block pl-3 pr-4 py-2 border-l-4 text-base font-medium
                                            ${location.pathname === `/articles/${item.id}`
                                                ? 'bg-purple-50 border-purple-500 text-purple-700'
                                                : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'}
                                        `}
                                        onClick={() => setIsMobileMenuOpen(false)}
                                        role="menuitem"
                                        aria-label={`${item.title} - ${item.description}`}
                                        title={item.description}
                                    >
                                        <div className="flex items-center">
                                            {item.icon && <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />}
                                            <span className="sr-only">{item.description}</span>
                                            {item.title}
                                        </div>
                                    </Link>
                                ))}
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navigation;
