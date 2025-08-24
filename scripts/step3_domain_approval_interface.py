#!/usr/bin/env python3
"""
Mingus Financial Wellness App - Step 3: Domain Approval Interface

This Flask web application provides a fast, visual interface for approving domains
discovered in Steps 1-2 of the Mingus article library implementation.

Features:
- Load domain intelligence data from Step 2 outputs
- Display domains in efficient card-based layout for rapid decisions
- Show sample URLs, cultural relevance, and AI recommendations
- Implement one-click approve/reject/review functionality with bulk operations
- Export approved domains list optimized for Step 4 article scraping
- Cultural awareness features for African American professional content
- Keyboard shortcuts and efficient navigation
- Real-time progress tracking and statistics

Author: Mingus Development Team
Date: 2025
"""

import os
import json
import csv
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
import pandas as pd

# Configuration
DATA_DIR = Path("../data")
CONFIG_DIR = Path("../config")
REPORTS_DIR = Path("../reports")
TEMPLATES_DIR = Path("templates")
STATIC_DIR = Path("static")

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__, 
           template_folder=str(TEMPLATES_DIR),
           static_folder=str(STATIC_DIR))
app.secret_key = os.urandom(24)
CORS(app)

# Data structures
@dataclass
class DomainDecision:
    domain: str
    decision: str  # 'approved', 'rejected', 'review_later'
    timestamp: str
    reasoning: str
    confidence: float
    cultural_relevance: float
    url_count: int
    sample_urls: List[str]

class DomainApprovalManager:
    def __init__(self):
        self.domains = {}
        self.decisions = {}
        self.bulk_suggestions = {}
        self.cultural_analysis = {}
        self.session_stats = {
            'total_domains': 0,
            'approved': 0,
            'rejected': 0,
            'review_later': 0,
            'start_time': None,
            'decisions_per_minute': 0
        }
        self.load_data()
    
    def load_data(self):
        """Load all domain intelligence data from Step 2 outputs, bookmark domains, and Notes domains"""
        try:
            # Load domain recommendations
            with open(DATA_DIR / "domain_recommendations.json", 'r') as f:
                self.domains = json.load(f)
            
            # Load bookmark domains if available
            bookmark_file = DATA_DIR / "bookmark_domains.json"
            if bookmark_file.exists():
                with open(bookmark_file, 'r') as f:
                    bookmark_domains = json.load(f)
                
                # Merge bookmark domains with existing domains
                # Bookmark domains take precedence for duplicates
                self.domains.update(bookmark_domains)
                print(f"Loaded {len(bookmark_domains)} bookmark domains")
            
            # Load Notes domains if available
            notes_file = DATA_DIR / "notes_recommendations.json"
            if notes_file.exists():
                with open(notes_file, 'r') as f:
                    notes_domains = json.load(f)
                
                # Merge Notes domains with existing domains
                # Notes domains take precedence for duplicates
                self.domains.update(notes_domains)
                print(f"Loaded {len(notes_domains)} Notes domains")
            
            # Load Notes URLs data for context
            self.notes_urls_data = {}
            notes_urls_file = DATA_DIR / "notes_urls_complete.csv"
            if notes_urls_file.exists():
                try:
                    df = pd.read_csv(notes_urls_file)
                    for _, row in df.iterrows():
                        domain = row['domain']
                        if domain not in self.notes_urls_data:
                            self.notes_urls_data[domain] = []
                        self.notes_urls_data[domain].append({
                            'url': row['url'],
                            'note_title': row['note_title'],
                            'surrounding_text': row['surrounding_text'],
                            'note_quality_score': row['note_quality_score']
                        })
                    print(f"Loaded Notes URLs data for {len(self.notes_urls_data)} domains")
                except Exception as e:
                    print(f"Error loading Notes URLs data: {e}")
                    self.notes_urls_data = {}
            
            # Load bulk action suggestions
            with open(DATA_DIR / "bulk_action_suggestions.json", 'r') as f:
                self.bulk_suggestions = json.load(f)
            
            # Load cultural relevance analysis
            with open(DATA_DIR / "cultural_relevance_analysis.json", 'r') as f:
                self.cultural_analysis = json.load(f)
            
            # Load domain categories
            self.high_value_domains = self.load_csv_domains("high_value_domains.csv")
            self.medium_value_domains = self.load_csv_domains("medium_value_domains.csv")
            self.low_value_domains = self.load_csv_domains("low_value_domains.csv")
            
            # Load Notes domain analysis
            self.notes_domain_analysis = {}
            notes_analysis_file = DATA_DIR / "notes_domain_analysis.csv"
            if notes_analysis_file.exists():
                try:
                    df = pd.read_csv(notes_analysis_file)
                    for _, row in df.iterrows():
                        domain = row['domain']
                        self.notes_domain_analysis[domain] = {
                            'note_count': row['note_count'],
                            'avg_note_quality_score': row['avg_note_quality_score'],
                            'note_titles': row['note_titles'].split(';') if pd.notna(row['note_titles']) else []
                        }
                    print(f"Loaded Notes domain analysis for {len(self.notes_domain_analysis)} domains")
                except Exception as e:
                    print(f"Error loading Notes domain analysis: {e}")
                    self.notes_domain_analysis = {}
            
            self.session_stats['total_domains'] = len(self.domains)
            print(f"Loaded {len(self.domains)} total domains for approval")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            self.domains = {}
    
    def load_csv_domains(self, filename: str) -> Dict[str, Any]:
        """Load domain data from CSV files"""
        domains = {}
        try:
            df = pd.read_csv(DATA_DIR / filename)
            for _, row in df.iterrows():
                domain = row['domain']
                domains[domain] = {
                    'url_count': row['url_count'],
                    'quality_score': row['quality_score'],
                    'cultural_relevance_score': row['cultural_relevance_score'],
                    'confidence': row['confidence'],
                    'reasoning': row['reasoning'],
                    'sample_urls': row['sample_urls'].split('; ') if pd.notna(row['sample_urls']) else []
                }
        except Exception as e:
            print(f"Error loading {filename}: {e}")
        return domains
    
    def get_domain_info(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive domain information"""
        info = self.domains.get(domain, {})
        
        # Add sample URLs from CSV data
        for csv_domains in [self.high_value_domains, self.medium_value_domains, self.low_value_domains]:
            if domain in csv_domains:
                info['sample_urls'] = csv_domains[domain].get('sample_urls', [])
                break
        
        # Add Notes-specific information
        if domain in self.notes_urls_data:
            info['source'] = 'notes'
            info['notes_data'] = {
                'urls': self.notes_urls_data[domain],
                'note_count': len(set(url['note_title'] for url in self.notes_urls_data[domain])),
                'avg_quality_score': sum(url['note_quality_score'] for url in self.notes_urls_data[domain]) / len(self.notes_urls_data[domain])
            }
            
            # Add note titles for context
            if domain in self.notes_domain_analysis:
                info['notes_data']['note_titles'] = self.notes_domain_analysis[domain].get('note_titles', [])
        
        # Determine source if not already set
        if 'source' not in info:
            if domain in self.notes_urls_data:
                info['source'] = 'notes'
            elif any(domain in csv_domains for csv_domains in [self.high_value_domains, self.medium_value_domains, self.low_value_domains]):
                info['source'] = 'email'
            else:
                info['source'] = 'unknown'
        
        return info
    
    def make_decision(self, domain: str, decision: str, reasoning: str = ""):
        """Record a decision for a domain"""
        if domain not in self.domains:
            return False
        
        domain_info = self.get_domain_info(domain)
        
        self.decisions[domain] = DomainDecision(
            domain=domain,
            decision=decision,
            timestamp=datetime.now().isoformat(),
            reasoning=reasoning,
            confidence=domain_info.get('confidence', 0.0),
            cultural_relevance=domain_info.get('cultural_relevance_score', 0.0),
            url_count=domain_info.get('url_count', 0),
            sample_urls=domain_info.get('sample_urls', [])
        )
        
        # Update session statistics
        if decision == 'approved':
            self.session_stats['approved'] += 1
        elif decision == 'rejected':
            self.session_stats['rejected'] += 1
        elif decision == 'review_later':
            self.session_stats['review_later'] += 1
        
        # Calculate decisions per minute
        if self.session_stats['start_time']:
            elapsed_minutes = (time.time() - self.session_stats['start_time']) / 60
            if elapsed_minutes > 0:
                total_decisions = (self.session_stats['approved'] + 
                                 self.session_stats['rejected'] + 
                                 self.session_stats['review_later'])
                self.session_stats['decisions_per_minute'] = total_decisions / elapsed_minutes
        
        return True
    
    def bulk_decision(self, domains: List[str], decision: str, reasoning: str = ""):
        """Make bulk decisions for multiple domains"""
        results = []
        for domain in domains:
            success = self.make_decision(domain, decision, reasoning)
            results.append({'domain': domain, 'success': success})
        return results
    
    def get_pending_domains(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get domains that haven't been decided yet"""
        pending = []
        for domain, info in self.domains.items():
            if domain not in self.decisions:
                domain_info = self.get_domain_info(domain)
                pending.append({
                    'domain': domain,
                    **domain_info
                })
                if len(pending) >= limit:
                    break
        return pending
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current approval session statistics"""
        total_decisions = (self.session_stats['approved'] + 
                          self.session_stats['rejected'] + 
                          self.session_stats['review_later'])
        
        progress_percentage = (total_decisions / self.session_stats['total_domains'] * 100) if self.session_stats['total_domains'] > 0 else 0
        
        return {
            **self.session_stats,
            'progress_percentage': round(progress_percentage, 1),
            'remaining_domains': self.session_stats['total_domains'] - total_decisions
        }
    
    def export_approved_domains(self) -> List[str]:
        """Export list of approved domains for Step 4"""
        approved = []
        for domain, decision in self.decisions.items():
            if decision.decision == 'approved':
                approved.append(domain)
        return approved
    
    def save_decisions(self):
        """Save all decisions to JSON file"""
        decisions_data = {domain: asdict(decision) for domain, decision in self.decisions.items()}
        
        with open(DATA_DIR / "domain_decisions_complete.json", 'w') as f:
            json.dump(decisions_data, f, indent=2)
        
        # Save approved domains list
        approved_domains = self.export_approved_domains()
        with open(CONFIG_DIR / "approved_domains.txt", 'w') as f:
            for domain in approved_domains:
                f.write(f"{domain}\n")
        
        # Save detailed approved domains
        approved_detailed = []
        for domain in approved_domains:
            domain_info = self.get_domain_info(domain)
            decision = self.decisions[domain]
            approved_detailed.append({
                'domain': domain,
                'decision_timestamp': decision.timestamp,
                'confidence': decision.confidence,
                'cultural_relevance': decision.cultural_relevance,
                'url_count': decision.url_count,
                'sample_urls': decision.sample_urls,
                'reasoning': domain_info.get('reasoning', ''),
                'quality_score': domain_info.get('quality_score', 0.0)
            })
        
        with open(DATA_DIR / "approved_domains_detailed.json", 'w') as f:
            json.dump(approved_detailed, f, indent=2)

# Initialize the domain manager
domain_manager = DomainApprovalManager()

@app.route('/')
def dashboard():
    """Main dashboard interface"""
    if domain_manager.session_stats['start_time'] is None:
        domain_manager.session_stats['start_time'] = time.time()
    
    stats = domain_manager.get_statistics()
    pending_domains = domain_manager.get_pending_domains(20)  # Show first 20 pending
    
    return render_template('dashboard.html', 
                         stats=stats,
                         pending_domains=pending_domains,
                         bulk_suggestions=domain_manager.bulk_suggestions)

@app.route('/api/approve_domain', methods=['POST'])
def approve_domain():
    """Approve a single domain"""
    data = request.get_json()
    domain = data.get('domain')
    reasoning = data.get('reasoning', '')
    
    success = domain_manager.make_decision(domain, 'approved', reasoning)
    
    return jsonify({
        'success': success,
        'stats': domain_manager.get_statistics()
    })

@app.route('/api/reject_domain', methods=['POST'])
def reject_domain():
    """Reject a single domain"""
    data = request.get_json()
    domain = data.get('domain')
    reasoning = data.get('reasoning', '')
    
    success = domain_manager.make_decision(domain, 'rejected', reasoning)
    
    return jsonify({
        'success': success,
        'stats': domain_manager.get_statistics()
    })

@app.route('/api/review_later', methods=['POST'])
def review_later():
    """Mark domain for later review"""
    data = request.get_json()
    domain = data.get('domain')
    reasoning = data.get('reasoning', '')
    
    success = domain_manager.make_decision(domain, 'review_later', reasoning)
    
    return jsonify({
        'success': success,
        'stats': domain_manager.get_statistics()
    })

@app.route('/api/bulk_approve', methods=['POST'])
def bulk_approve():
    """Bulk approval operations"""
    data = request.get_json()
    domains = data.get('domains', [])
    reasoning = data.get('reasoning', 'Bulk approval')
    
    results = domain_manager.bulk_decision(domains, 'approved', reasoning)
    
    return jsonify({
        'success': True,
        'results': results,
        'stats': domain_manager.get_statistics()
    })

@app.route('/api/bulk_reject', methods=['POST'])
def bulk_reject():
    """Bulk rejection operations"""
    data = request.get_json()
    domains = data.get('domains', [])
    reasoning = data.get('reasoning', 'Bulk rejection')
    
    results = domain_manager.bulk_decision(domains, 'rejected', reasoning)
    
    return jsonify({
        'success': True,
        'results': results,
        'stats': domain_manager.get_statistics()
    })

@app.route('/api/export_decisions', methods=['GET'])
def export_decisions():
    """Export approved domains list"""
    domain_manager.save_decisions()
    
    approved_domains = domain_manager.export_approved_domains()
    
    return jsonify({
        'success': True,
        'approved_count': len(approved_domains),
        'approved_domains': approved_domains,
        'export_path': str(CONFIG_DIR / "approved_domains.txt")
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get real-time statistics"""
    return jsonify(domain_manager.get_statistics())

@app.route('/api/undo', methods=['POST'])
def undo_last_decision():
    """Undo last decision"""
    data = request.get_json()
    domain = data.get('domain')
    
    if domain in domain_manager.decisions:
        decision = domain_manager.decisions[domain]
        
        # Update statistics
        if decision.decision == 'approved':
            domain_manager.session_stats['approved'] -= 1
        elif decision.decision == 'rejected':
            domain_manager.session_stats['rejected'] -= 1
        elif decision.decision == 'review_later':
            domain_manager.session_stats['review_later'] -= 1
        
        # Remove decision
        del domain_manager.decisions[domain]
        
        return jsonify({
            'success': True,
            'stats': domain_manager.get_statistics()
        })
    
    return jsonify({'success': False, 'error': 'Domain not found in decisions'})

@app.route('/api/pending_domains', methods=['GET'])
def get_pending_domains():
    """Get pending domains for display"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    pending = domain_manager.get_pending_domains(limit * page)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    return jsonify({
        'domains': pending[start_idx:end_idx],
        'has_more': len(pending) > end_idx
    })

if __name__ == '__main__':
    print("Starting Mingus Domain Approval Interface...")
    print(f"Loaded {len(domain_manager.domains)} domains for review")
    print("Access the interface at: http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
