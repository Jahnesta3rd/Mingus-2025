import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BookOpen, TrendingUp, Heart, Target, User, Search, Star, FolderOpen, Tag, BarChart3, Settings, ChevronDown } from 'lucide-react';
import { getArticleLibraryNavigation } from '../../routes/articleLibraryRoutes';
import { isFeatureEnabled } from '../../config/articleLibrary';

const Navigation = () => {
    const location = useLocation();
    const [isArticleMenuOpen, setIsArticleMenuOpen] = useState(false);
    
    // Main navigation items
    const mainNavItems = [
        { path: '/', label: 'Dashboard', icon: TrendingUp },
        { path: '/budget', label: 'Budget', icon: Target },
        { path: '/health', label: 'Health Check', icon: Heart },
        { path: '/profile', label: 'Profile', icon: User },
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

    return (
        <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex space-x-8">
                        {/* Main navigation items */}
                        {mainNavItems.map(({ path, label, icon: Icon }) => (
                            <Link
                                key={path}
                                to={path}
                                className={`
                                    inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
                                    ${location.pathname === path
                                        ? 'border-purple-500 text-purple-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                                `}
                            >
                                <Icon className="w-4 h-4 mr-2" />
                                {label}
                            </Link>
                        ))}
                        
                        {/* Article Library dropdown */}
                        <div className="relative">
                            <button
                                onClick={() => setIsArticleMenuOpen(!isArticleMenuOpen)}
                                className={`
                                    inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
                                    ${isInArticleSection
                                        ? 'border-purple-500 text-purple-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                                `}
                            >
                                <BookOpen className="w-4 h-4 mr-2" />
                                Learning Library
                                <ChevronDown className={`w-4 h-4 ml-1 transition-transform ${isArticleMenuOpen ? 'rotate-180' : ''}`} />
                            </button>
                            
                            {/* Article Library dropdown menu */}
                            {isArticleMenuOpen && (
                                <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-md shadow-lg border border-gray-200 z-50">
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
                                        >
                                            <BookOpen className="w-4 h-4 mr-3" />
                                            All Articles
                                        </Link>
                                        
                                        {/* Divider */}
                                        <div className="border-t border-gray-100 my-1"></div>
                                        
                                        {/* Article library sub-items */}
                                        {articleLibraryNavItems
                                            .filter(item => item.id !== 'home') // Exclude home as it's handled above
                                            .filter(item => {
                                                // Check feature flags
                                                if (item.featureFlag) {
                                                    return isFeatureEnabled(item.featureFlag);
                                                }
                                                return true;
                                            })
                                            .map((item) => {
                                                const isActive = location.pathname.startsWith(item.path);
                                                return (
                                                    <Link
                                                        key={item.id}
                                                        to={item.path}
                                                        className={`
                                                            flex items-center px-4 py-2 text-sm
                                                            ${isActive
                                                                ? 'bg-purple-50 text-purple-700'
                                                                : 'text-gray-700 hover:bg-gray-50'}
                                                        `}
                                                        onClick={() => setIsArticleMenuOpen(false)}
                                                    >
                                                        <span className="mr-3">{item.icon}</span>
                                                        {item.label}
                                                    </Link>
                                                );
                                            })}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                    
                    {/* Current article library section indicator */}
                    {isInArticleSection && currentArticleItem && (
                        <div className="flex items-center">
                            <div className="text-sm text-gray-500">
                                <span className="mr-2">📚</span>
                                {currentArticleItem.label}
                            </div>
                        </div>
                    )}
                </div>
            </div>
            
            {/* Article Library sub-navigation (when in article section) */}
            {isInArticleSection && (
                <div className="bg-gray-50 border-b border-gray-200">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex space-x-8 py-2">
                            {articleLibraryNavItems
                                .filter(item => {
                                    // Check feature flags
                                    if (item.featureFlag) {
                                        return isFeatureEnabled(item.featureFlag);
                                    }
                                    return true;
                                })
                                .map((item) => {
                                    const isActive = location.pathname.startsWith(item.path);
                                    return (
                                        <Link
                                            key={item.id}
                                            to={item.path}
                                            className={`
                                                inline-flex items-center px-3 py-2 text-sm font-medium rounded-md
                                                ${isActive
                                                    ? 'bg-purple-100 text-purple-700'
                                                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'}
                                            `}
                                        >
                                            <span className="mr-2">{item.icon}</span>
                                            {item.label}
                                        </Link>
                                    );
                                })}
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navigation;
