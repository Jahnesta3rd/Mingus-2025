"""
Cookie Consent Manager
Cookie consent management system with banner, preferences, and compliance tracking
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
from loguru import logger

from .compliance_manager import ConsentType, get_gdpr_manager

class CookieCategory(Enum):
    """Cookie categories"""
    NECESSARY = "necessary"
    ANALYTICS = "analytics"
    FUNCTIONAL = "functional"
    ADVERTISING = "advertising"
    THIRD_PARTY = "third_party"

@dataclass
class Cookie:
    """Cookie definition"""
    name: str
    domain: str
    category: CookieCategory
    purpose: str
    duration: str
    provider: str = ""
    third_party: bool = False
    essential: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CookieBanner:
    """Cookie banner configuration"""
    banner_id: str
    title: str
    description: str
    accept_all_text: str
    reject_all_text: str
    customize_text: str
    privacy_policy_url: str
    cookie_policy_url: str
    language: str = "en"
    theme: str = "light"
    position: str = "bottom"
    show_again_days: int = 365
    metadata: Dict[str, Any] = field(default_factory=dict)

class CookieConsentManager:
    """Cookie consent management system"""
    
    def __init__(self, db_path: str = "/var/lib/mingus/cookies.db"):
        self.db_path = db_path
        self.gdpr_manager = get_gdpr_manager()
        
        self._init_database()
        self._load_default_cookies()
        self._load_default_banner()
    
    def _init_database(self):
        """Initialize cookie database"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Cookies table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cookies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        domain TEXT NOT NULL,
                        category TEXT NOT NULL,
                        purpose TEXT NOT NULL,
                        duration TEXT NOT NULL,
                        provider TEXT,
                        third_party INTEGER DEFAULT 0,
                        essential INTEGER DEFAULT 0,
                        metadata TEXT,
                        UNIQUE(name, domain)
                    )
                """)
                
                # Cookie banners table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cookie_banners (
                        banner_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        accept_all_text TEXT NOT NULL,
                        reject_all_text TEXT NOT NULL,
                        customize_text TEXT NOT NULL,
                        privacy_policy_url TEXT NOT NULL,
                        cookie_policy_url TEXT NOT NULL,
                        language TEXT DEFAULT 'en',
                        theme TEXT DEFAULT 'light',
                        position TEXT DEFAULT 'bottom',
                        show_again_days INTEGER DEFAULT 365,
                        metadata TEXT
                    )
                """)
                
                # Cookie consent sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cookie_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        ip_address TEXT NOT NULL,
                        user_agent TEXT NOT NULL,
                        consent_given INTEGER DEFAULT 0,
                        consent_timestamp TEXT,
                        preferences TEXT,
                        banner_shown INTEGER DEFAULT 0,
                        banner_shown_timestamp TEXT,
                        metadata TEXT
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cookies_category ON cookies(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cookies_domain ON cookies(domain)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON cookie_sessions(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_consent ON cookie_sessions(consent_given)")
        
        except Exception as e:
            logger.error(f"Error initializing cookie database: {e}")
    
    def _load_default_cookies(self):
        """Load default cookie definitions"""
        try:
            default_cookies = [
                Cookie(
                    name="session_id",
                    domain=".mingus.com",
                    category=CookieCategory.NECESSARY,
                    purpose="Authentication and session management",
                    duration="session",
                    essential=True
                ),
                Cookie(
                    name="consent_preferences",
                    domain=".mingus.com",
                    category=CookieCategory.NECESSARY,
                    purpose="Store user consent preferences",
                    duration="1 year",
                    essential=True
                ),
                Cookie(
                    name="_ga",
                    domain=".google.com",
                    category=CookieCategory.ANALYTICS,
                    purpose="Google Analytics tracking",
                    duration="2 years",
                    provider="Google",
                    third_party=True
                ),
                Cookie(
                    name="_gid",
                    domain=".google.com",
                    category=CookieCategory.ANALYTICS,
                    purpose="Google Analytics session tracking",
                    duration="24 hours",
                    provider="Google",
                    third_party=True
                ),
                Cookie(
                    name="marketing_tracking",
                    domain=".mingus.com",
                    category=CookieCategory.ADVERTISING,
                    purpose="Marketing campaign tracking",
                    duration="90 days"
                ),
                Cookie(
                    name="user_preferences",
                    domain=".mingus.com",
                    category=CookieCategory.FUNCTIONAL,
                    purpose="Store user interface preferences",
                    duration="1 year"
                )
            ]
            
            for cookie in default_cookies:
                self.add_cookie(cookie)
        
        except Exception as e:
            logger.error(f"Error loading default cookies: {e}")
    
    def _load_default_banner(self):
        """Load default cookie banner"""
        try:
            banner = CookieBanner(
                banner_id="default",
                title="Cookie Consent",
                description="We use cookies to enhance your experience, analyze site usage, and assist in our marketing efforts. By clicking 'Accept All', you consent to our use of cookies.",
                accept_all_text="Accept All",
                reject_all_text="Reject All",
                customize_text="Customize",
                privacy_policy_url="/privacy-policy",
                cookie_policy_url="/cookie-policy",
                language="en",
                theme="light",
                position="bottom",
                show_again_days=365
            )
            
            self.add_cookie_banner(banner)
        
        except Exception as e:
            logger.error(f"Error loading default banner: {e}")
    
    def add_cookie(self, cookie: Cookie) -> bool:
        """Add cookie definition"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cookies 
                    (name, domain, category, purpose, duration, provider, third_party, essential, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cookie.name,
                    cookie.domain,
                    cookie.category.value,
                    cookie.purpose,
                    cookie.duration,
                    cookie.provider,
                    1 if cookie.third_party else 0,
                    1 if cookie.essential else 0,
                    json.dumps(cookie.metadata)
                ))
            
            logger.info(f"Cookie added: {cookie.name} ({cookie.domain})")
            return True
        
        except Exception as e:
            logger.error(f"Error adding cookie: {e}")
            return False
    
    def get_cookies(self, category: CookieCategory = None) -> List[Cookie]:
        """Get cookies by category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if category:
                    cursor = conn.execute("""
                        SELECT name, domain, category, purpose, duration, provider, third_party, essential, metadata
                        FROM cookies 
                        WHERE category = ?
                        ORDER BY essential DESC, name
                    """, (category.value,))
                else:
                    cursor = conn.execute("""
                        SELECT name, domain, category, purpose, duration, provider, third_party, essential, metadata
                        FROM cookies 
                        ORDER BY essential DESC, category, name
                    """)
                
                cookies = []
                for row in cursor.fetchall():
                    cookie = Cookie(
                        name=row[0],
                        domain=row[1],
                        category=CookieCategory(row[2]),
                        purpose=row[3],
                        duration=row[4],
                        provider=row[5],
                        third_party=bool(row[6]),
                        essential=bool(row[7]),
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    cookies.append(cookie)
                
                return cookies
        
        except Exception as e:
            logger.error(f"Error getting cookies: {e}")
            return []
    
    def add_cookie_banner(self, banner: CookieBanner) -> bool:
        """Add cookie banner"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cookie_banners 
                    (banner_id, title, description, accept_all_text, reject_all_text, customize_text,
                     privacy_policy_url, cookie_policy_url, language, theme, position, show_again_days, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    banner.banner_id,
                    banner.title,
                    banner.description,
                    banner.accept_all_text,
                    banner.reject_all_text,
                    banner.customize_text,
                    banner.privacy_policy_url,
                    banner.cookie_policy_url,
                    banner.language,
                    banner.theme,
                    banner.position,
                    banner.show_again_days,
                    json.dumps(banner.metadata)
                ))
            
            logger.info(f"Cookie banner added: {banner.banner_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding cookie banner: {e}")
            return False
    
    def get_cookie_banner(self, banner_id: str = "default") -> Optional[CookieBanner]:
        """Get cookie banner"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT banner_id, title, description, accept_all_text, reject_all_text, customize_text,
                           privacy_policy_url, cookie_policy_url, language, theme, position, show_again_days, metadata
                    FROM cookie_banners 
                    WHERE banner_id = ?
                """, (banner_id,))
                
                row = cursor.fetchone()
                if row:
                    return CookieBanner(
                        banner_id=row[0],
                        title=row[1],
                        description=row[2],
                        accept_all_text=row[3],
                        reject_all_text=row[4],
                        customize_text=row[5],
                        privacy_policy_url=row[6],
                        cookie_policy_url=row[7],
                        language=row[8],
                        theme=row[9],
                        position=row[10],
                        show_again_days=row[11],
                        metadata=json.loads(row[12]) if row[12] else {}
                    )
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting cookie banner: {e}")
            return None
    
    def should_show_banner(self, user_id: str = None, ip_address: str = None) -> bool:
        """Check if cookie banner should be shown"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if user has already given consent
                if user_id:
                    cursor = conn.execute("""
                        SELECT consent_given, consent_timestamp
                        FROM cookie_sessions 
                        WHERE user_id = ?
                        ORDER BY consent_timestamp DESC LIMIT 1
                    """, (user_id,))
                    
                    row = cursor.fetchone()
                    if row and row[0]:
                        # Check if consent is still valid (within show_again_days)
                        consent_date = datetime.fromisoformat(row[1])
                        banner = self.get_cookie_banner()
                        if banner:
                            valid_until = consent_date + timedelta(days=banner.show_again_days)
                            if datetime.utcnow() < valid_until:
                                return False
                
                # Check by IP address if no user_id
                if ip_address:
                    cursor = conn.execute("""
                        SELECT consent_given, consent_timestamp
                        FROM cookie_sessions 
                        WHERE ip_address = ? AND user_id IS NULL
                        ORDER BY consent_timestamp DESC LIMIT 1
                    """, (ip_address,))
                    
                    row = cursor.fetchone()
                    if row and row[0]:
                        consent_date = datetime.fromisoformat(row[1])
                        banner = self.get_cookie_banner()
                        if banner:
                            valid_until = consent_date + timedelta(days=banner.show_again_days)
                            if datetime.utcnow() < valid_until:
                                return False
                
                return True
        
        except Exception as e:
            logger.error(f"Error checking banner display: {e}")
            return True
    
    def record_consent(self, user_id: str = None, ip_address: str = None, 
                      user_agent: str = None, preferences: Dict[str, bool] = None) -> str:
        """Record cookie consent"""
        try:
            session_id = hashlib.md5(f"{user_id}_{ip_address}_{datetime.utcnow().isoformat()}".encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO cookie_sessions 
                    (session_id, user_id, ip_address, user_agent, consent_given, consent_timestamp, preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    ip_address,
                    user_agent,
                    1,
                    datetime.utcnow().isoformat(),
                    json.dumps(preferences or {})
                ))
            
            # Record consent in GDPR manager
            if user_id and preferences:
                for category, granted in preferences.items():
                    try:
                        consent_type = ConsentType(category)
                        self.gdpr_manager.record_consent(
                            user_id=user_id,
                            consent_type=consent_type,
                            granted=granted,
                            ip_address=ip_address or "",
                            user_agent=user_agent or "",
                            metadata={'cookie_consent': True, 'session_id': session_id}
                        )
                    except ValueError:
                        # Skip invalid consent types
                        continue
            
            logger.info(f"Cookie consent recorded: {session_id}")
            return session_id
        
        except Exception as e:
            logger.error(f"Error recording cookie consent: {e}")
            return None
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's cookie preferences"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT preferences, consent_timestamp
                    FROM cookie_sessions 
                    WHERE user_id = ?
                    ORDER BY consent_timestamp DESC LIMIT 1
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'preferences': json.loads(row[0]) if row[0] else {},
                        'consent_timestamp': row[1],
                        'cookies': self._get_cookies_by_preferences(json.loads(row[0]) if row[0] else {})
                    }
                
                return {'preferences': {}, 'cookies': []}
        
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {'preferences': {}, 'cookies': []}
    
    def _get_cookies_by_preferences(self, preferences: Dict[str, bool]) -> List[Dict[str, Any]]:
        """Get cookies based on user preferences"""
        try:
            all_cookies = self.get_cookies()
            allowed_cookies = []
            
            for cookie in all_cookies:
                # Necessary cookies are always allowed
                if cookie.essential or cookie.category == CookieCategory.NECESSARY:
                    allowed_cookies.append({
                        'name': cookie.name,
                        'domain': cookie.domain,
                        'category': cookie.category.value,
                        'purpose': cookie.purpose,
                        'duration': cookie.duration,
                        'provider': cookie.provider,
                        'third_party': cookie.third_party,
                        'essential': cookie.essential
                    })
                else:
                    # Check if user has consented to this category
                    category_preference = preferences.get(cookie.category.value, False)
                    if category_preference:
                        allowed_cookies.append({
                            'name': cookie.name,
                            'domain': cookie.domain,
                            'category': cookie.category.value,
                            'purpose': cookie.purpose,
                            'duration': cookie.duration,
                            'provider': cookie.provider,
                            'third_party': cookie.third_party,
                            'essential': cookie.essential
                        })
            
            return allowed_cookies
        
        except Exception as e:
            logger.error(f"Error getting cookies by preferences: {e}")
            return []
    
    def generate_cookie_script(self, user_id: str = None) -> str:
        """Generate JavaScript for setting cookies based on user preferences"""
        try:
            preferences = self.get_user_preferences(user_id)
            allowed_cookies = preferences.get('cookies', [])
            
            script_lines = [
                "// Cookie consent script generated by Mingus GDPR Compliance",
                "document.addEventListener('DOMContentLoaded', function() {",
                "    // Set allowed cookies",
                "    const allowedCookies = " + json.dumps(allowed_cookies, indent=4) + ";",
                "",
                "    // Function to set cookie",
                "    function setCookie(name, value, days) {",
                "        const expires = new Date();",
                "        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));",
                "        document.cookie = name + '=' + value + ';expires=' + expires.toUTCString() + ';path=/';",
                "    }",
                "",
                "    // Set necessary cookies",
                "    allowedCookies.forEach(function(cookie) {",
                "        if (cookie.essential || cookie.category === 'necessary') {",
                "            setCookie(cookie.name, 'consent_given', 365);",
                "        }",
                "    });",
                "",
                "    // Initialize analytics if consented",
                "    const analyticsConsent = " + json.dumps(preferences.get('preferences', {}).get('analytics', False)) + ";",
                "    if (analyticsConsent) {",
                "        // Initialize Google Analytics",
                "        if (typeof gtag !== 'undefined') {",
                "            gtag('consent', 'update', {",
                "                'analytics_storage': 'granted'",
                "            });",
                "        }",
                "    }",
                "",
                "    // Initialize advertising if consented",
                "    const advertisingConsent = " + json.dumps(preferences.get('preferences', {}).get('advertising', False)) + ";",
                "    if (advertisingConsent) {",
                "        // Initialize advertising tracking",
                "        if (typeof gtag !== 'undefined') {",
                "            gtag('consent', 'update', {",
                "                'ad_storage': 'granted'",
                "            });",
                "        }",
                "    }",
                "});"
            ]
            
            return "\n".join(script_lines)
        
        except Exception as e:
            logger.error(f"Error generating cookie script: {e}")
            return "// Error generating cookie script"
    
    def get_cookie_statistics(self) -> Dict[str, Any]:
        """Get cookie consent statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total consents
                cursor = conn.execute("SELECT COUNT(*) FROM cookie_sessions WHERE consent_given = 1")
                total_consents = cursor.fetchone()[0]
                
                # Consents by date (last 30 days)
                thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM cookie_sessions 
                    WHERE consent_given = 1 AND consent_timestamp >= ?
                """, (thirty_days_ago,))
                recent_consents = cursor.fetchone()[0]
                
                # Consent rate
                cursor = conn.execute("SELECT COUNT(*) FROM cookie_sessions")
                total_sessions = cursor.fetchone()[0]
                consent_rate = (total_consents / total_sessions * 100) if total_sessions > 0 else 0
                
                # Preferences breakdown
                cursor = conn.execute("SELECT preferences FROM cookie_sessions WHERE consent_given = 1")
                preference_counts = {}
                
                for row in cursor.fetchall():
                    if row[0]:
                        preferences = json.loads(row[0])
                        for category, granted in preferences.items():
                            if category not in preference_counts:
                                preference_counts[category] = {'granted': 0, 'denied': 0}
                            if granted:
                                preference_counts[category]['granted'] += 1
                            else:
                                preference_counts[category]['denied'] += 1
                
                return {
                    'total_consents': total_consents,
                    'recent_consents': recent_consents,
                    'total_sessions': total_sessions,
                    'consent_rate': round(consent_rate, 2),
                    'preference_breakdown': preference_counts,
                    'generated_at': datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error getting cookie statistics: {e}")
            return {'error': str(e)}

# Global cookie consent manager instance
_cookie_manager = None

def get_cookie_manager() -> CookieConsentManager:
    """Get global cookie consent manager instance"""
    global _cookie_manager
    
    if _cookie_manager is None:
        _cookie_manager = CookieConsentManager()
    
    return _cookie_manager 