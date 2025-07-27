"""
Citation Generator Module for Mucache Player
Generates academic citations for archived videos in multiple formats
"""

import json
import datetime
import re
from pathlib import Path


class CitationGenerator:
    """Generates academic citations for archived videos in multiple citation styles."""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.citations_dir = self.cache_dir / "citations"
        self.citations_dir.mkdir(exist_ok=True)
    
    def generate_citations(self, video_url, video_filename, custom_info=None):
        """Generate citations in multiple academic formats."""
        try:
            # Load video metadata
            metadata_file = self.cache_dir / f"{video_filename}.metadata.json"
            
            # Load enhanced metadata if available
            enhanced_metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    enhanced_metadata = json.load(f)
            
            # Extract citation data
            citation_data = self._extract_citation_data(video_url, enhanced_metadata, custom_info)
            
            # Generate multiple citation formats
            citations = {
                "APA": self._generate_apa_citation(citation_data),
                "MLA": self._generate_mla_citation(citation_data),
                "Chicago": self._generate_chicago_citation(citation_data),
                "Harvard": self._generate_harvard_citation(citation_data),
                "IEEE": self._generate_ieee_citation(citation_data),
                "Vancouver": self._generate_vancouver_citation(citation_data),
                "BibTeX": self._generate_bibtex_citation(citation_data)
            }
            
            # Save citations to file
            citation_filename = f"citations_{self._clean_filename(citation_data['title'])}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            citation_path = self.citations_dir / citation_filename
            
            self._save_citations_file(citations, citation_data, citation_path)
            
            return {
                "success": True,
                "citations": citations,
                "citation_data": citation_data,
                "file_path": str(citation_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_citation_data(self, video_url, metadata, custom_info):
        """Extract and standardize citation data from metadata."""
        # Parse dates
        original_date = self._parse_date(metadata.get('date'))
        archive_date = self._parse_date(metadata.get('upload_date'))
        access_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Clean and format creator/author
        creator = metadata.get('creator', 'Unknown Creator')
        if isinstance(creator, list):
            creator = ', '.join(creator)
        
        # Determine source type and platform
        source_type = "Archived Video"
        if metadata.get('original_platform'):
            source_type = f"{metadata['original_platform']} Video (Archived)"
        
        citation_data = {
            "title": metadata.get('title', 'Untitled Video'),
            "creator": creator,
            "original_date": original_date,
            "archive_date": archive_date,
            "access_date": access_date,
            "archive_url": video_url,
            "original_url": metadata.get('original_youtube_url', ''),
            "runtime": metadata.get('runtime', ''),
            "description": metadata.get('description', ''),
            "language": metadata.get('language', ''),
            "archive_identifier": metadata.get('identifier', ''),
            "source_type": source_type,
            "platform": "Internet Archive",
            "collection": ', '.join(metadata.get('collection', [])) if metadata.get('collection') else '',
            "subject": ', '.join(metadata.get('subject', [])) if metadata.get('subject') else '',
            "uploader": metadata.get('uploader', 'Internet Archive'),
            "original_platform": metadata.get('original_platform', 'Unknown Platform')
        }
        
        # Apply custom information if provided
        if custom_info:
            citation_data.update(custom_info)
        
        return citation_data
    
    def _parse_date(self, date_string):
        """Parse various date formats into a standardized format."""
        if not date_string or date_string == 'Unknown':
            return ''
        
        # Try to parse ISO format first
        try:
            if 'T' in date_string:
                dt = datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            else:
                # Try various date formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y', '%Y']:
                    try:
                        dt = datetime.datetime.strptime(date_string, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
        except:
            pass
        
        return date_string  # Return as-is if parsing fails
    
    def _clean_filename(self, title):
        """Clean title for use in filename."""
        # Remove or replace problematic characters
        clean = re.sub(r'[<>:"/\\|?*]', '_', title)
        return clean[:50]  # Limit length
    
    def _generate_apa_citation(self, data):
        """Generate APA format citation."""
        citation = f"{data['creator']} ({data['original_date'] or 'n.d.'}). {data['title']}"
        
        if data['runtime']:
            citation += f" [Video file, {data['runtime']}]"
        else:
            citation += " [Video file]"
        
        citation += f". {data['platform']}"
        
        if data['original_url']:
            citation += f". Originally published at {data['original_url']}"
        
        if data['archive_date']:
            citation += f". Archived {data['archive_date']}"
        
        citation += f". Retrieved {data['access_date']}, from {data['archive_url']}"
        
        return citation
    
    def _generate_mla_citation(self, data):
        """Generate MLA format citation."""
        citation = f"{data['creator']}. \"{data['title']}.\""
        
        if data['original_platform'] and data['original_platform'] != 'Unknown Platform':
            citation += f" {data['original_platform']},"
        
        if data['original_date']:
            citation += f" {data['original_date']},"
        
        citation += f" {data['platform']}"
        
        if data['archive_date']:
            citation += f", {data['archive_date']}"
        
        citation += f". Web. {data['access_date']}. <{data['archive_url']}>"
        
        return citation
    
    def _generate_chicago_citation(self, data):
        """Generate Chicago format citation."""
        citation = f"{data['creator']}. \"{data['title']}.\""
        
        if data['original_platform'] and data['original_platform'] != 'Unknown Platform':
            citation += f" {data['original_platform']} video."
        else:
            citation += " Video."
        
        if data['original_date']:
            citation += f" {data['original_date']}."
        
        if data['archive_date']:
            citation += f" Archived {data['archive_date']}."
        
        citation += f" {data['platform']}. Accessed {data['access_date']}. {data['archive_url']}"
        
        return citation
    
    def _generate_harvard_citation(self, data):
        """Generate Harvard format citation."""
        year = data['original_date'][:4] if data['original_date'] else 'n.d.'
        
        citation = f"{data['creator']} ({year}) '{data['title']}'"
        
        if data['original_platform'] and data['original_platform'] != 'Unknown Platform':
            citation += f", {data['original_platform']} video"
        else:
            citation += ", video"
        
        if data['archive_date']:
            citation += f", archived {data['archive_date']}"
        
        citation += f", {data['platform']}, accessed {data['access_date']}, <{data['archive_url']}>"
        
        return citation
    
    def _generate_ieee_citation(self, data):
        """Generate IEEE format citation."""
        citation = f"{data['creator']}, \"{data['title']},\""
        
        if data['original_platform'] and data['original_platform'] != 'Unknown Platform':
            citation += f" {data['original_platform']},"
        
        if data['original_date']:
            citation += f" {data['original_date']}."
        
        citation += f" [Video]. Available: {data['archive_url']}"
        
        if data['archive_date']:
            citation += f" [Archived: {data['archive_date']}]"
        
        citation += f" [Accessed: {data['access_date']}]"
        
        return citation
    
    def _generate_vancouver_citation(self, data):
        """Generate Vancouver format citation."""
        citation = f"{data['creator']}. {data['title']} [video]"
        
        if data['original_platform'] and data['original_platform'] != 'Unknown Platform':
            citation += f". {data['original_platform']}"
        
        if data['original_date']:
            citation += f"; {data['original_date']}"
        
        if data['archive_date']:
            citation += f" [archived {data['archive_date']}]"
        
        citation += f". Available from: {data['archive_url']} [cited {data['access_date']}]"
        
        return citation
    
    def _generate_bibtex_citation(self, data):
        """Generate BibTeX format citation."""
        # Create a clean key for BibTeX
        key = re.sub(r'[^a-zA-Z0-9]', '', data['creator'].replace(' ', ''))[:10]
        year = data['original_date'][:4] if data['original_date'] else 'nd'
        key += year
        
        bibtex = f"@misc{{{key},\n"
        bibtex += f"  author = {{{data['creator']}}},\n"
        bibtex += f"  title = {{{data['title']}}},\n"
        
        if data['original_date']:
            bibtex += f"  year = {{{data['original_date'][:4]}}},\n"
        
        if data['original_platform'] and data['original_platform'] != 'Unknown Platform':
            bibtex += f"  note = {{Video originally published on {data['original_platform']}}},\n"
        
        bibtex += f"  howpublished = {{\\url{{{data['archive_url']}}}}},\n"
        bibtex += f"  organization = {{{data['platform']}}},\n"
        
        if data['archive_date']:
            bibtex += f"  archivedate = {{{data['archive_date']}}},\n"
        
        bibtex += f"  urldate = {{{data['access_date']}}}\n"
        bibtex += "}"
        
        return bibtex
    
    def _save_citations_file(self, citations, citation_data, file_path):
        """Save citations to a formatted text file."""
        content = f"""ACADEMIC CITATIONS
==================

Video: {citation_data['title']}
Creator: {citation_data['creator']}
Original Date: {citation_data['original_date'] or 'Unknown'}
Archive Date: {citation_data['archive_date'] or 'Unknown'}
Access Date: {citation_data['access_date']}
Source: {citation_data['source_type']}

CITATION FORMATS
================

APA (7th Edition):
{citations['APA']}

MLA (9th Edition):
{citations['MLA']}

Chicago (17th Edition):
{citations['Chicago']}

Harvard:
{citations['Harvard']}

IEEE:
{citations['IEEE']}

Vancouver:
{citations['Vancouver']}

BibTeX:
{citations['BibTeX']}

ADDITIONAL METADATA
===================
Archive URL: {citation_data['archive_url']}
Original URL: {citation_data['original_url'] or 'Not Available'}
Archive Identifier: {citation_data['archive_identifier']}
Runtime: {citation_data['runtime'] or 'Unknown'}
Language: {citation_data['language'] or 'Unknown'}
Collection: {citation_data['collection'] or 'None specified'}
Subject Tags: {citation_data['subject'] or 'None specified'}

Generated by Mucache Player Citation Generator
Generation Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def list_citation_files(self):
        """List all generated citation files."""
        citations = []
        for citation_file in self.citations_dir.glob("citations_*.txt"):
            citations.append({
                "filename": citation_file.name,
                "created": datetime.datetime.fromtimestamp(citation_file.stat().st_ctime).isoformat(),
                "file_path": str(citation_file)
            })
        
        return sorted(citations, key=lambda x: x["created"], reverse=True)


def generate_video_citations(cache_dir, video_url, video_filename, custom_info=None):
    """Convenience function to generate citations."""
    generator = CitationGenerator(cache_dir)
    return generator.generate_citations(video_url, video_filename, custom_info)

def _clean_filename(self, title):
    """Clean title for use in filename with comprehensive sanitization."""
    try:
        # Replace non-ASCII characters with spaces
        safe_name = ""
        for c in title:
            if ord(c) < 128:
                safe_name += c
            else:
                safe_name += " "
        
        # Replace Windows invalid characters including forward slashes and problematic chars
        for char in '<>:"|?*\\/()':
            safe_name = safe_name.replace(char, " ")
        
        # Replace other problematic characters
        safe_name = safe_name.replace('.', ' ')  # Periods can cause issues
        safe_name = safe_name.replace(',', ' ')  # Commas
        safe_name = safe_name.replace(';', ' ')  # Semicolons
        
        # Collapse multiple spaces
        while "  " in safe_name:
            safe_name = safe_name.replace("  ", " ")
        
        # Limit length for filename compatibility
        clean = safe_name.strip()[:50]
        
        return clean if clean else "untitled"
    except Exception as e:
        print(f"Error cleaning filename: {e}")
        return "citation_file"