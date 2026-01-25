import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, User, LogOut, Shield, Home } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

interface NavigationBarProps {
  className?: string;
}

const NavigationBar: React.FC<NavigationBarProps> = ({ className = '' }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [showUserMenu, setShowUserMenu] = useState(false);
  // const menuRef = useRef<HTMLDivElement>(null);
  const menuItemsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  // Handle scroll effect for navbar background
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu and user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isMenuOpen && !target.closest('.mobile-menu-container')) {
        setIsMenuOpen(false);
      }
      if (showUserMenu && !target.closest('.user-menu-container')) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMenuOpen, showUserMenu]);

  // Keyboard navigation for mobile menu
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isMenuOpen) return;

      const menuItems = menuItemsRef.current.filter(Boolean);
      const currentIndex = focusedIndex;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setFocusedIndex(prev => 
            prev < menuItems.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusedIndex(prev => 
            prev > 0 ? prev - 1 : menuItems.length - 1
          );
          break;
        case 'Escape':
          event.preventDefault();
          setIsMenuOpen(false);
          setFocusedIndex(-1);
          break;
        case 'Tab':
          if (event.shiftKey && currentIndex === 0) {
            event.preventDefault();
            setFocusedIndex(menuItems.length - 1);
          } else if (!event.shiftKey && currentIndex === menuItems.length - 1) {
            event.preventDefault();
            setFocusedIndex(0);
          }
          break;
      }
    };

    if (isMenuOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isMenuOpen, focusedIndex]);

  // Focus management for mobile menu
  useEffect(() => {
    if (isMenuOpen && focusedIndex >= 0) {
      const menuItem = menuItemsRef.current[focusedIndex];
      if (menuItem) {
        menuItem.focus();
      }
    }
  }, [focusedIndex, isMenuOpen]);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      // Enhanced smooth scrolling with offset for fixed navbar
      const offsetTop = element.offsetTop - 80; // Account for fixed navbar height
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
    }
    setIsMenuOpen(false);
    setFocusedIndex(-1);
  };

  // Enhanced keyboard navigation for section buttons
  const handleSectionKeyDown = (e: React.KeyboardEvent, sectionId: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      scrollToSection(sectionId);
    }
  };

  const handleMenuToggle = () => {
    setIsMenuOpen(!isMenuOpen);
    if (!isMenuOpen) {
      setFocusedIndex(0);
    } else {
      setFocusedIndex(-1);
    }
  };

  const handleUserMenuToggle = () => {
    setShowUserMenu(!showUserMenu);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    setShowUserMenu(false);
  };

  const handleNavigateToDashboard = () => {
    navigate('/career-dashboard');
    setShowUserMenu(false);
  };

  return (
    <nav 
      role="navigation"
      aria-label="Main navigation"
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        isScrolled 
          ? 'bg-slate-900/95 backdrop-blur-md border-b border-slate-800/50' 
          : 'bg-slate-900/90 backdrop-blur-sm'
      } ${className}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <img 
                src="/mingus-logo.png" 
                alt="Mingus" 
                className="h-8 w-auto object-contain brightness-0 invert"
              />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-white">
                Mingus
              </h1>
            </div>
          </div>

          {/* Desktop Menu */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <button
                onClick={() => scrollToSection('features')}
                onKeyDown={(e) => handleSectionKeyDown(e, 'features')}
                className="text-gray-300 hover:text-violet-400 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-900"
                aria-label="Navigate to Features section"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                onKeyDown={(e) => handleSectionKeyDown(e, 'pricing')}
                className="text-gray-300 hover:text-violet-400 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-900"
                aria-label="Navigate to Pricing section"
              >
                Pricing
              </button>
              <button
                onClick={() => scrollToSection('faq')}
                onKeyDown={(e) => handleSectionKeyDown(e, 'faq')}
                className="text-gray-300 hover:text-violet-400 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-900"
                aria-label="Navigate to FAQ section"
              >
                FAQ
              </button>
            </div>
          </div>

          {/* CTA Button or User Menu */}
          <div className="hidden md:flex items-center">
            {isAuthenticated ? (
              <div className="relative user-menu-container">
                <button
                  onClick={handleUserMenuToggle}
                  className="flex items-center gap-2 text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-900"
                  aria-label="User menu"
                  aria-expanded={showUserMenu}
                >
                  <User className="h-5 w-5" />
                  <span>{user?.name || 'User'}</span>
                </button>
                
                {showUserMenu && (
                  <div 
                    ref={userMenuRef}
                    className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-lg border border-slate-700 py-1 z-50"
                    role="menu"
                    aria-label="User menu"
                  >
                    <button
                      onClick={handleNavigateToDashboard}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-300 hover:bg-slate-700 hover:text-white transition-colors"
                      role="menuitem"
                    >
                      <Shield className="h-4 w-4" />
                      Career Dashboard
                    </button>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-300 hover:bg-slate-700 hover:text-white transition-colors"
                      role="menuitem"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button 
                onClick={() => navigate('/signup?source=cta')}
                className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-violet-500/25 hover:-translate-y-0.5 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-900"
                aria-label="Get started with Mingus"
              >
                Get Started
              </button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden mobile-menu-container">
            <button
              onClick={handleMenuToggle}
              className="text-gray-300 hover:text-white p-2 rounded-md transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-900"
              aria-label={isMenuOpen ? "Close mobile menu" : "Open mobile menu"}
              aria-expanded={isMenuOpen}
              aria-controls="mobile-menu"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu - Slide Down */}
        <div 
          id="mobile-menu"
          className={`md:hidden transition-all duration-300 ease-in-out ${
            isMenuOpen 
              ? 'max-h-64 opacity-100' 
              : 'max-h-0 opacity-0 overflow-hidden'
          }`}
          role="menu"
          aria-label="Mobile navigation menu"
        >
          <div className="px-2 pt-2 pb-3 space-y-1 bg-slate-800/50 backdrop-blur-md rounded-lg mt-2 border border-slate-700/50">
            <button
              ref={el => menuItemsRef.current[0] = el}
              onClick={() => scrollToSection('features')}
              onKeyDown={(e) => handleSectionKeyDown(e, 'features')}
              className="block w-full text-left text-gray-300 hover:text-violet-400 hover:bg-slate-700/50 px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
              role="menuitem"
              aria-label="Navigate to Features section"
            >
              Features
            </button>
            <button
              ref={el => menuItemsRef.current[1] = el}
              onClick={() => scrollToSection('pricing')}
              onKeyDown={(e) => handleSectionKeyDown(e, 'pricing')}
              className="block w-full text-left text-gray-300 hover:text-violet-400 hover:bg-slate-700/50 px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
              role="menuitem"
              aria-label="Navigate to Pricing section"
            >
              Pricing
            </button>
            <button
              ref={el => menuItemsRef.current[2] = el}
              onClick={() => scrollToSection('faq')}
              onKeyDown={(e) => handleSectionKeyDown(e, 'faq')}
              className="block w-full text-left text-gray-300 hover:text-violet-400 hover:bg-slate-700/50 px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
              role="menuitem"
              aria-label="Navigate to FAQ section"
            >
              FAQ
            </button>
            <div className="pt-2 border-t border-slate-700/50">
              {isAuthenticated ? (
                <>
                  <button 
                    ref={el => menuItemsRef.current[3] = el}
                    onClick={handleNavigateToDashboard}
                    className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
                    role="menuitem"
                    aria-label="Career Dashboard"
                  >
                    <Shield className="h-4 w-4" />
                    Career Dashboard
                  </button>
                  <button 
                    ref={el => menuItemsRef.current[4] = el}
                    onClick={() => navigate('/career-dashboard?tab=housing')}
                    className="w-full flex items-center justify-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800 mt-2"
                    role="menuitem"
                    aria-label="Housing Location"
                  >
                    <Home className="h-4 w-4" />
                    Housing Location
                  </button>
                  <button 
                    ref={el => menuItemsRef.current[5] = el}
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800 mt-2"
                    role="menuitem"
                    aria-label="Sign Out"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </>
              ) : (
                <button 
                  ref={el => menuItemsRef.current[3] = el}
                  onClick={() => navigate('/signup?source=cta')}
                  className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 transform hover:scale-105 focus-ring focus-visible:ring-4 focus-visible:ring-violet-400 focus-visible:ring-offset-4 focus-visible:ring-offset-slate-800"
                  role="menuitem"
                  aria-label="Get started with Mingus"
                >
                  Get Started
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationBar;
