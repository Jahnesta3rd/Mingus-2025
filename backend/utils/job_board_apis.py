#!/usr/bin/env python3
"""
Job Board API Integration Module
Integrates with major job boards and company data sources for the IncomeBoostJobMatcher
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

@dataclass
class JobBoardConfig:
    """Configuration for job board APIs"""
    base_url: str
    api_key: str
    rate_limit: int  # requests per minute
    headers: Dict[str, str]

class JobBoardAPIManager:
    """Manages API integrations with major job boards"""
    
    def __init__(self):
        self.configs = {
            'indeed': JobBoardConfig(
                base_url="https://indeed-indeed.p.rapidapi.com",
                api_key=os.getenv('INDEED_API_KEY', ''),
                rate_limit=60,
                headers={
                    'X-RapidAPI-Key': os.getenv('INDEED_API_KEY', ''),
                    'X-RapidAPI-Host': 'indeed-indeed.p.rapidapi.com'
                }
            ),
            'linkedin': JobBoardConfig(
                base_url="https://linkedin-jobs-search.p.rapidapi.com",
                api_key=os.getenv('LINKEDIN_API_KEY', ''),
                rate_limit=30,
                headers={
                    'X-RapidAPI-Key': os.getenv('LINKEDIN_API_KEY', ''),
                    'X-RapidAPI-Host': 'linkedin-jobs-search.p.rapidapi.com'
                }
            ),
            'glassdoor': JobBoardConfig(
                base_url="https://glassdoor.p.rapidapi.com",
                api_key=os.getenv('GLASSDOOR_API_KEY', ''),
                rate_limit=20,
                headers={
                    'X-RapidAPI-Key': os.getenv('GLASSDOOR_API_KEY', ''),
                    'X-RapidAPI-Host': 'glassdoor.p.rapidapi.com'
                }
            )
        }
        
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_indeed_jobs(self, query: str, location: str, salary_min: int, 
                                salary_max: int, limit: int = 50) -> List[Dict]:
        """Search Indeed for jobs with salary filters"""
        config = self.configs['indeed']
        
        params = {
            'query': query,
            'location': location,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'limit': limit,
            'sort': 'date'
        }
        
        try:
            async with self.session.get(
                f"{config.base_url}/search",
                headers=config.headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_indeed_jobs(data)
                else:
                    logger.error(f"Indeed API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching Indeed: {e}")
            return []
    
    async def search_linkedin_jobs(self, keywords: str, location: str, 
                                  salary_min: int, salary_max: int, limit: int = 50) -> List[Dict]:
        """Search LinkedIn for jobs"""
        config = self.configs['linkedin']
        
        params = {
            'keywords': keywords,
            'location': location,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'limit': limit
        }
        
        try:
            async with self.session.get(
                f"{config.base_url}/search",
                headers=config.headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_linkedin_jobs(data)
                else:
                    logger.error(f"LinkedIn API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            return []
    
    async def search_glassdoor_jobs(self, query: str, location: str, 
                                   salary_min: int, salary_max: int, limit: int = 50) -> List[Dict]:
        """Search Glassdoor for jobs"""
        config = self.configs['glassdoor']
        
        params = {
            'query': query,
            'location': location,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'limit': limit
        }
        
        try:
            async with self.session.get(
                f"{config.base_url}/jobs/search",
                headers=config.headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_glassdoor_jobs(data)
                else:
                    logger.error(f"Glassdoor API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching Glassdoor: {e}")
            return []
    
    def _parse_indeed_jobs(self, data: Dict) -> List[Dict]:
        """Parse Indeed API response"""
        jobs = []
        for job in data.get('jobs', []):
            jobs.append({
                'job_id': f"indeed_{job.get('id', '')}",
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'salary_min': self._extract_salary(job.get('salary', ''), 'min'),
                'salary_max': self._extract_salary(job.get('salary', ''), 'max'),
                'description': job.get('description', ''),
                'url': job.get('url', ''),
                'posted_date': job.get('date', ''),
                'job_board': 'indeed'
            })
        return jobs
    
    def _parse_linkedin_jobs(self, data: Dict) -> List[Dict]:
        """Parse LinkedIn API response"""
        jobs = []
        for job in data.get('jobs', []):
            jobs.append({
                'job_id': f"linkedin_{job.get('id', '')}",
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'salary_min': self._extract_salary(job.get('salary', ''), 'min'),
                'salary_max': self._extract_salary(job.get('salary', ''), 'max'),
                'description': job.get('description', ''),
                'url': job.get('url', ''),
                'posted_date': job.get('date', ''),
                'job_board': 'linkedin'
            })
        return jobs
    
    def _parse_glassdoor_jobs(self, data: Dict) -> List[Dict]:
        """Parse Glassdoor API response"""
        jobs = []
        for job in data.get('jobs', []):
            jobs.append({
                'job_id': f"glassdoor_{job.get('id', '')}",
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'salary_min': self._extract_salary(job.get('salary', ''), 'min'),
                'salary_max': self._extract_salary(job.get('salary', ''), 'max'),
                'description': job.get('description', ''),
                'url': job.get('url', ''),
                'posted_date': job.get('date', ''),
                'job_board': 'glassdoor'
            })
        return jobs
    
    def _extract_salary(self, salary_text: str, salary_type: str) -> Optional[int]:
        """Extract salary from text"""
        if not salary_text:
            return None
        
        # Remove common text and extract numbers
        import re
        numbers = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', salary_text.replace(',', ''))
        
        if not numbers:
            return None
        
        try:
            if salary_type == 'min':
                return int(float(numbers[0]))
            else:
                return int(float(numbers[-1]))
        except (ValueError, IndexError):
            return None

class CompanyDataAPIManager:
    """Manages API integrations for company data sources"""
    
    def __init__(self):
        self.configs = {
            'glassdoor_company': JobBoardConfig(
                base_url="https://glassdoor.p.rapidapi.com",
                api_key=os.getenv('GLASSDOOR_API_KEY', ''),
                rate_limit=20,
                headers={
                    'X-RapidAPI-Key': os.getenv('GLASSDOOR_API_KEY', ''),
                    'X-RapidAPI-Host': 'glassdoor.p.rapidapi.com'
                }
            ),
            'crunchbase': JobBoardConfig(
                base_url="https://crunchbase-crunchbase-v1.p.rapidapi.com",
                api_key=os.getenv('CRUNCHBASE_API_KEY', ''),
                rate_limit=30,
                headers={
                    'X-RapidAPI-Key': os.getenv('CRUNCHBASE_API_KEY', ''),
                    'X-RapidAPI-Host': 'crunchbase-crunchbase-v1.p.rapidapi.com'
                }
            )
        }
        
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_company_profile(self, company_name: str) -> Dict:
        """Get comprehensive company profile"""
        profile = {
            'name': company_name,
            'industry': 'Unknown',
            'size': 'Unknown',
            'diversity_score': 0.0,
            'growth_score': 0.0,
            'culture_score': 0.0,
            'benefits_score': 0.0,
            'glassdoor_rating': None,
            'remote_friendly': False,
            'headquarters': 'Unknown'
        }
        
        # Get Glassdoor data
        glassdoor_data = await self._get_glassdoor_company_data(company_name)
        if glassdoor_data:
            profile.update(glassdoor_data)
        
        # Get Crunchbase data
        crunchbase_data = await self._get_crunchbase_data(company_name)
        if crunchbase_data:
            profile.update(crunchbase_data)
        
        return profile
    
    async def _get_glassdoor_company_data(self, company_name: str) -> Dict:
        """Get company data from Glassdoor"""
        config = self.configs['glassdoor_company']
        
        try:
            async with self.session.get(
                f"{config.base_url}/company/{quote(company_name)}",
                headers=config.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'glassdoor_rating': data.get('rating'),
                        'culture_score': data.get('culture_score', 0.0),
                        'benefits_score': data.get('benefits_score', 0.0),
                        'industry': data.get('industry', 'Unknown'),
                        'size': data.get('size', 'Unknown'),
                        'headquarters': data.get('headquarters', 'Unknown')
                    }
        except Exception as e:
            logger.error(f"Error getting Glassdoor data for {company_name}: {e}")
        
        return {}
    
    async def _get_crunchbase_data(self, company_name: str) -> Dict:
        """Get company data from Crunchbase"""
        config = self.configs['crunchbase']
        
        try:
            async with self.session.get(
                f"{config.base_url}/companies/{quote(company_name)}",
                headers=config.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'industry': data.get('industry', 'Unknown'),
                        'founded_year': data.get('founded_year'),
                        'funding_stage': data.get('funding_stage'),
                        'revenue': data.get('revenue'),
                        'growth_score': self._calculate_growth_score(data)
                    }
        except Exception as e:
            logger.error(f"Error getting Crunchbase data for {company_name}: {e}")
        
        return {}
    
    def _calculate_growth_score(self, data: Dict) -> float:
        """Calculate company growth score based on funding and revenue data"""
        score = 50.0  # Base score
        
        # Funding stage scoring
        funding_stage = data.get('funding_stage', '').lower()
        if 'series' in funding_stage:
            score += 20
        elif 'ipo' in funding_stage:
            score += 30
        elif 'acquisition' in funding_stage:
            score += 15
        
        # Revenue scoring
        revenue = data.get('revenue', '')
        if 'million' in revenue.lower():
            score += 10
        elif 'billion' in revenue.lower():
            score += 20
        
        return min(100.0, score)

# Example usage
async def main():
    """Example usage of the API managers"""
    async with JobBoardAPIManager() as job_manager:
        jobs = await job_manager.search_indeed_jobs(
            query="software engineer",
            location="Atlanta, GA",
            salary_min=80000,
            salary_max=120000,
            limit=10
        )
        print(f"Found {len(jobs)} Indeed jobs")
    
    async with CompanyDataAPIManager() as company_manager:
        profile = await company_manager.get_company_profile("Google")
        print(f"Company profile: {profile}")

if __name__ == "__main__":
    asyncio.run(main())
