#!/usr/bin/env python3
"""
Test script for Apple Notes URL extraction functionality

This script tests the extract_notes_urls.py functionality to ensure it works
correctly with the existing Mingus domain approval system.

Author: Mingus Development Team
Date: 2025
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extract_notes_urls import (
    AppleNotesExtractor, 
    ExtractedNoteURL, 
    NotesDomainAnalysis,
    FINANCIAL_KEYWORDS,
    CAREER_KEYWORDS,
    AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS,
    LIFESTYLE_KEYWORDS
)

class TestAppleNotesExtractor:
    """Test class for Apple Notes extraction functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_data_dir = Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create mock notes database
        self.mock_db_path = self.test_data_dir / "mock_notes.sqlite"
        self.create_mock_notes_database()
        
        # Create mock extracted URLs
        self.mock_urls = [
            ExtractedNoteURL(
                url="https://www.investopedia.com/retirement-planning",
                original_url="https://www.investopedia.com/retirement-planning",
                note_title="Retirement Planning Resources",
                note_date="2025-01-15 10:30:00",
                note_id="1",
                surrounding_text="Check out this great resource for retirement planning strategies",
                domain="investopedia.com",
                extraction_confidence=0.9,
                note_quality_score=0.8,
                context_keywords=["retirement", "planning", "financial"]
            ),
            ExtractedNoteURL(
                url="https://www.linkedin.com/learning/financial-literacy",
                original_url="https://www.linkedin.com/learning/financial-literacy",
                note_title="Financial Literacy Course",
                note_date="2025-01-14 15:45:00",
                note_id="2",
                surrounding_text="LinkedIn Learning course on financial literacy for professionals",
                domain="linkedin.com",
                extraction_confidence=0.85,
                note_quality_score=0.7,
                context_keywords=["financial", "literacy", "course", "professional"]
            ),
            ExtractedNoteURL(
                url="https://www.blackenterprise.com/wealth-building",
                original_url="https://www.blackenterprise.com/wealth-building",
                note_title="Wealth Building for Black Professionals",
                note_date="2025-01-13 09:20:00",
                note_id="3",
                surrounding_text="Excellent article on wealth building strategies for African American professionals",
                domain="blackenterprise.com",
                extraction_confidence=0.95,
                note_quality_score=0.9,
                context_keywords=["wealth", "building", "black", "professionals", "african american"]
            )
        ]
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def create_mock_notes_database(self):
        """Create a mock Apple Notes database for testing"""
        import sqlite3
        
        conn = sqlite3.connect(self.mock_db_path)
        cursor = conn.cursor()
        
        # Create tables similar to Apple Notes database
        cursor.execute("""
            CREATE TABLE ZICCLOUDSYNCINGOBJECT (
                Z_PK INTEGER PRIMARY KEY,
                Z_ENT INTEGER,
                ZTITLE1 TEXT,
                ZCREATIONDATE1 REAL,
                ZMODIFICATIONDATE1 REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE ZNOTEBODY (
                Z_PK INTEGER PRIMARY KEY,
                ZNOTE INTEGER,
                ZDATA BLOB,
                ZLENGTH INTEGER
            )
        """)
        
        # Insert mock note data
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT (Z_PK, Z_ENT, ZTITLE1, ZCREATIONDATE1, ZMODIFICATIONDATE1)
            VALUES (1, 1, 'Retirement Planning Resources', 1705312200, 1705312200)
        """)
        
        cursor.execute("""
            INSERT INTO ZNOTEBODY (Z_PK, ZNOTE, ZDATA, ZLENGTH)
            VALUES (1, 1, ?, 100)
        """, (b'Check out this great resource for retirement planning: https://www.investopedia.com/retirement-planning',))
        
        conn.commit()
        conn.close()
    
    def test_extractor_initialization(self):
        """Test extractor initialization"""
        with patch('extract_notes_urls.NOTES_DB_PATHS', [self.mock_db_path]):
            extractor = AppleNotesExtractor()
            assert extractor.notes_db_path == self.mock_db_path
            assert extractor.domain_analyzer is not None  # Step 2 analyzer is available
    
    def test_url_cleaning(self):
        """Test URL cleaning functionality"""
        extractor = AppleNotesExtractor()
        
        # Test basic URL cleaning
        cleaned = extractor.clean_url("https://example.com?utm_source=test&param=value")
        assert "utm_source" not in cleaned
        assert "param=value" in cleaned
        
        # Test www URL
        cleaned = extractor.clean_url("www.example.com")
        assert cleaned == "https://www.example.com"
        
        # Test URL with fragment
        cleaned = extractor.clean_url("https://example.com/page#section")
        assert cleaned == "https://example.com/page#section"
    
    def test_domain_extraction(self):
        """Test domain extraction from URLs"""
        extractor = AppleNotesExtractor()
        
        assert extractor.extract_domain("https://www.example.com/page") == "www.example.com"
        assert extractor.extract_domain("www.example.com") == "www.example.com"
        assert extractor.extract_domain("https://subdomain.example.com") == "subdomain.example.com"
    
    def test_note_quality_scoring(self):
        """Test note quality scoring"""
        extractor = AppleNotesExtractor()
        
        # High quality note with financial keywords
        score = extractor.calculate_note_quality_score(
            "Retirement Planning Guide",
            "This comprehensive guide covers 401k, IRA, and investment strategies for wealth building"
        )
        assert score > 0.5
        
        # High quality note with lifestyle keywords
        score = extractor.calculate_note_quality_score(
            "Family Wellness and Faith Journey",
            "This comprehensive guide covers relationships, kids, health, and reflection on faith and family values"
        )
        assert score > 0.4
        
        # Low quality note
        score = extractor.calculate_note_quality_score(
            "Random Note",
            "Some random content without relevant keywords"
        )
        assert score < 0.3
    
    def test_context_keyword_extraction(self):
        """Test context keyword extraction"""
        extractor = AppleNotesExtractor()
        
        keywords = extractor.get_context_keywords(
            "Financial Planning for Black Professionals",
            "This article discusses wealth building strategies and career advancement"
        )
        
        assert "financial" in keywords
        assert "wealth" in keywords
        assert "career" in keywords
        assert "black" in keywords
    
    def test_lifestyle_keyword_extraction(self):
        """Test lifestyle keyword extraction"""
        extractor = AppleNotesExtractor()
        
        keywords = extractor.get_context_keywords(
            "Family Wellness and Faith Journey",
            "This note covers relationships, kids, health, and reflection on faith"
        )
        
        assert "family" in keywords
        assert "relationships" in keywords
        assert "kids" in keywords
        assert "health" in keywords
        assert "faith" in keywords
        assert "reflection" in keywords
    
    def test_rich_text_parsing(self):
        """Test rich text content parsing"""
        extractor = AppleNotesExtractor()
        
        # Test UTF-8 content
        content = extractor.parse_rich_text_content(b"Simple text content")
        assert content == "Simple text content"
        
        # Test HTML content
        html_content = b"<p>This is <strong>bold</strong> text</p>"
        content = extractor.parse_rich_text_content(html_content)
        assert "bold" in content
        assert "<p>" not in content
        assert "<strong>" not in content
    
    def test_domain_categorization(self):
        """Test domain categorization"""
        extractor = AppleNotesExtractor()
        
        assert extractor.categorize_domain("bankofamerica.com") == "financial"
        assert extractor.categorize_domain("linkedin.com") == "career"
        assert extractor.categorize_domain("harvard.edu") == "educational"
        assert extractor.categorize_domain("example.com") == "general"
    

    
    def test_domain_recommendation_logic(self):
        """Test domain recommendation logic"""
        extractor = AppleNotesExtractor()
        
        # High quality
        rec, reason = extractor.get_domain_recommendation("example.com", 10, 0.8)
        assert rec == "AUTO_APPROVE"
        
        # Medium quality
        rec, reason = extractor.get_domain_recommendation("example.com", 5, 0.6)
        assert rec == "MANUAL_REVIEW"
        
        # Low quality
        rec, reason = extractor.get_domain_recommendation("example.com", 2, 0.3)
        assert rec == "AUTO_REJECT"
    
    def test_domain_priority_assignment(self):
        """Test domain priority assignment"""
        extractor = AppleNotesExtractor()
        
        assert extractor.get_domain_priority("example.com", 10, 0.9) == "HIGH"
        assert extractor.get_domain_priority("example.com", 5, 0.7) == "MEDIUM"
        assert extractor.get_domain_priority("example.com", 2, 0.4) == "NORMAL"
    
    def test_surrounding_text_extraction(self):
        """Test surrounding text extraction"""
        extractor = AppleNotesExtractor()
        
        text = "This is a long text with a URL https://example.com in the middle and more text after"
        surrounding = extractor.get_surrounding_text(text, "https://example.com", 20)
        
        assert "https://example.com" in surrounding
        assert len(surrounding) > 20
    
    def test_domain_analysis(self):
        """Test domain analysis functionality"""
        extractor = AppleNotesExtractor()
        
        domain_analyses = extractor.analyze_domains(self.mock_urls)
        
        assert len(domain_analyses) == 3
        assert "investopedia.com" in domain_analyses
        assert "linkedin.com" in domain_analyses
        assert "blackenterprise.com" in domain_analyses
        
        # Check blackenterprise.com has high quality
        black_enterprise = domain_analyses["blackenterprise.com"]
        assert black_enterprise.avg_note_quality_score > 0.5
        assert black_enterprise.recommendation == "AUTO_APPROVE"
    
    def test_results_saving(self):
        """Test results saving functionality"""
        extractor = AppleNotesExtractor()
        
        # Create mock domain analyses
        domain_analyses = {
            "example.com": NotesDomainAnalysis(
                domain="example.com",
                url_count=5,
                note_count=3,
                avg_note_quality_score=0.7,
                category_suggestion="financial",
                confidence=0.8,
                recommendation="MANUAL_REVIEW",
                reasoning="Good quality content",
                priority="MEDIUM",
                sample_urls=["https://example.com/1", "https://example.com/2"],
                note_titles=["Note 1", "Note 2"]
            )
        }
        
        # Mock data directory
        with patch('extract_notes_urls.DATA_DIR', self.test_data_dir):
            extractor.save_results(self.mock_urls, domain_analyses)
            
            # Check files were created
            assert (self.test_data_dir / "notes_urls_complete.csv").exists()
            assert (self.test_data_dir / "notes_domain_analysis.csv").exists()
            assert (self.test_data_dir / "notes_recommendations.json").exists()
            assert (self.test_data_dir / "notes_processing_summary.json").exists()
    
    def test_integration_with_step2_analyzer(self):
        """Test integration with Step 2 domain analyzer"""
        # Mock Step 2 analyzer
        mock_analyzer = Mock()
        mock_analyzer.analyze_domain.return_value = {
            'quality_score': 0.8,
            'cultural_relevance': 0.6,
            'category': 'financial'
        }
        
        with patch('extract_notes_urls.DomainIntelligenceAnalyzer', return_value=mock_analyzer):
            extractor = AppleNotesExtractor()
            assert extractor.domain_analyzer is not None
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        extractor = AppleNotesExtractor()
        
        # Test invalid URL handling
        domain = extractor.extract_domain("invalid-url")
        assert domain == ""  # Empty string for invalid URLs
        
        # Test empty content parsing
        content = extractor.parse_rich_text_content(b"")
        assert content == ""
        
        # Test None content
        content = extractor.parse_rich_text_content(None)
        assert content == ""
    
    def test_keyword_constants(self):
        """Test that keyword constants are properly defined"""
        assert len(FINANCIAL_KEYWORDS) > 20
        assert len(CAREER_KEYWORDS) > 20
        assert len(AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS) > 20
        assert len(LIFESTYLE_KEYWORDS) > 20
        
        # Check for specific important keywords
        assert "finance" in FINANCIAL_KEYWORDS
        assert "career" in CAREER_KEYWORDS
        assert "diversity" in AFRICAN_AMERICAN_PROFESSIONAL_KEYWORDS
        
        # Check for new lifestyle keywords
        assert "relationships" in LIFESTYLE_KEYWORDS
        assert "kids" in LIFESTYLE_KEYWORDS
        assert "family" in LIFESTYLE_KEYWORDS
        assert "faith" in LIFESTYLE_KEYWORDS
        assert "health" in LIFESTYLE_KEYWORDS
        assert "reflection" in LIFESTYLE_KEYWORDS
        assert "news" in LIFESTYLE_KEYWORDS

def test_end_to_end_extraction():
    """Test end-to-end extraction process"""
    # This test would require a real Apple Notes database
    # For now, we'll test the process with mocked data
    
    with patch('extract_notes_urls.NOTES_DB_PATHS', [Path("/nonexistent/path")]):
        try:
            extractor = AppleNotesExtractor()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected behavior

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
