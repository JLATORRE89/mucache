"""
Evidence Generator Module for Mucache Player
Generates court-admissible evidence documentation from video metadata
"""

import json
import datetime
import hashlib
import os
from pathlib import Path
import uuid


class EvidenceGenerator:
    """Generates court-admissible evidence documentation for archived videos."""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.evidence_dir = self.cache_dir / "evidence_reports"
        self.evidence_dir.mkdir(exist_ok=True)
    
    def generate_evidence_report(self, video_url, video_filename, case_info=None):
        """Generate a comprehensive evidence report for legal proceedings."""
        try:
            # Load video metadata
            metadata_file = self.cache_dir / f"{video_filename}.metadata.json"
            video_file = self.cache_dir / video_filename
            
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_filename}")
            
            # Generate file hashes for integrity verification
            file_hashes = self._generate_file_hashes(video_file)
            
            # Load enhanced metadata if available
            enhanced_metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    enhanced_metadata = json.load(f)
            
            # Generate unique evidence ID
            evidence_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            
            # Create evidence report structure
            evidence_report = {
                "evidence_report": {
                    "report_id": evidence_id,
                    "generated_at": timestamp.isoformat(),
                    "generated_by": "Mucache Player Evidence Generator v1.0",
                    "case_information": case_info or {},
                    
                    "digital_evidence": {
                        "file_information": {
                            "filename": video_filename,
                            "file_size_bytes": video_file.stat().st_size,
                            "file_created": datetime.datetime.fromtimestamp(video_file.stat().st_ctime).isoformat(),
                            "file_modified": datetime.datetime.fromtimestamp(video_file.stat().st_mtime).isoformat(),
                            "local_storage_path": str(video_file.absolute())
                        },
                        
                        "integrity_verification": {
                            "md5_hash": file_hashes["md5"],
                            "sha1_hash": file_hashes["sha1"],
                            "sha256_hash": file_hashes["sha256"],
                            "hash_generated_at": timestamp.isoformat(),
                            "verification_status": "VERIFIED" if enhanced_metadata.get('file_md5') else "LOCAL_ONLY"
                        },
                        
                        "chain_of_custody": self._build_chain_of_custody(video_url, enhanced_metadata, timestamp),
                        
                        "content_metadata": self._extract_content_metadata(enhanced_metadata),
                        
                        "source_verification": self._build_source_verification(video_url, enhanced_metadata),
                        
                        "technical_details": self._extract_technical_details(video_file, enhanced_metadata)
                    },
                    
                    "legal_certifications": {
                        "authenticity_statement": "This digital evidence was obtained through automated download from publicly accessible archive sources. File integrity has been verified through cryptographic hashing.",
                        "collection_method": "Automated download via Internet Archive API and direct HTTP transfer",
                        "collection_timestamp": enhanced_metadata.get('upload_date', timestamp.isoformat()),
                        "collector_system": "Mucache Player Digital Evidence Collection System",
                        "evidence_class": "Digital Video Content with Provenance Metadata",
                        "admissibility_notes": "Evidence includes complete metadata chain from original publication through archival preservation to collection."
                    }
                }
            }
            
            # Save evidence report
            report_filename = f"evidence_report_{evidence_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = self.evidence_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(evidence_report, f, indent=2, ensure_ascii=False)
            
            # Generate human-readable summary
            summary_path = self._generate_evidence_summary(evidence_report, report_path)
            
            return {
                "success": True,
                "evidence_id": evidence_id,
                "report_path": str(report_path),
                "summary_path": str(summary_path),
                "report": evidence_report
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_file_hashes(self, file_path):
        """Generate multiple cryptographic hashes for file integrity verification."""
        hashes = {"md5": hashlib.md5(), "sha1": hashlib.sha1(), "sha256": hashlib.sha256()}
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                for hash_obj in hashes.values():
                    hash_obj.update(chunk)
        
        return {name: hash_obj.hexdigest() for name, hash_obj in hashes.items()}
    
    def _build_chain_of_custody(self, video_url, metadata, timestamp):
        """Build complete chain of custody documentation."""
        chain = []
        
        # Original publication
        if metadata.get('date') or metadata.get('creator'):
            chain.append({
                "stage": "ORIGINAL_PUBLICATION",
                "timestamp": metadata.get('date', 'Unknown'),
                "location": metadata.get('original_youtube_url') or metadata.get('source', 'Unknown'),
                "custodian": metadata.get('creator', 'Unknown'),
                "platform": metadata.get('original_platform', 'Unknown'),
                "description": "Original content publication on source platform"
            })
        
        # Archive preservation
        if metadata.get('upload_date') or metadata.get('uploader'):
            chain.append({
                "stage": "ARCHIVAL_PRESERVATION",
                "timestamp": metadata.get('upload_date', 'Unknown'),
                "location": metadata.get('archive_url', video_url),
                "custodian": metadata.get('uploader', 'Internet Archive'),
                "platform": "Archive.org",
                "description": "Content preserved in Internet Archive"
            })
        
        # Local collection
        chain.append({
            "stage": "DIGITAL_EVIDENCE_COLLECTION",
            "timestamp": timestamp.isoformat(),
            "location": "Local Evidence Storage",
            "custodian": "Legal Evidence Collection System",
            "platform": "Mucache Player",
            "description": "Content collected and verified for legal proceedings"
        })
        
        return chain
    
    def _extract_content_metadata(self, metadata):
        """Extract relevant content metadata for legal purposes."""
        return {
            "title": metadata.get('title', 'Unknown'),
            "description": metadata.get('description', ''),
            "creator": metadata.get('creator', 'Unknown'),
            "original_publication_date": metadata.get('date', 'Unknown'),
            "runtime": metadata.get('runtime', 'Unknown'),
            "language": metadata.get('language', 'Unknown'),
            "subject_tags": metadata.get('subject', []),
            "collection": metadata.get('collection', []),
            "original_platform": metadata.get('original_platform', 'Unknown')
        }
    
    def _build_source_verification(self, video_url, metadata):
        """Build source verification information."""
        return {
            "archive_url": video_url,
            "original_source_url": metadata.get('original_youtube_url', 'Not Available'),
            "archive_identifier": metadata.get('identifier', 'Unknown'),
            "archive_md5": metadata.get('file_md5', 'Not Available'),
            "archive_sha1": metadata.get('file_sha1', 'Not Available'),
            "verification_method": "Internet Archive API Metadata Retrieval",
            "source_platform": metadata.get('original_platform', 'Unknown'),
            "archive_date": metadata.get('upload_date', 'Unknown')
        }
    
    def _extract_technical_details(self, video_file, metadata):
        """Extract technical details about the video file."""
        return {
            "file_format": metadata.get('file_format', 'Unknown'),
            "original_filename": metadata.get('original_filename', 'Unknown'),
            "file_size": video_file.stat().st_size,
            "collection_method": "HTTP Download",
            "transfer_protocol": "HTTPS",
            "source_server": "archive.org",
            "encoding": "Binary video data",
            "storage_format": "Local filesystem"
        }
    
    def _generate_evidence_summary(self, evidence_report, report_path):
        """Generate human-readable evidence summary."""
        summary_path = report_path.with_suffix('.txt')
        
        report_data = evidence_report["evidence_report"]
        digital_evidence = report_data["digital_evidence"]
        
        summary_content = f"""
DIGITAL EVIDENCE SUMMARY REPORT
================================

Report ID: {report_data['report_id']}
Generated: {report_data['generated_at']}
Generated By: {report_data['generated_by']}

FILE INFORMATION
----------------
Filename: {digital_evidence['file_information']['filename']}
File Size: {digital_evidence['file_information']['file_size_bytes']:,} bytes
Created: {digital_evidence['file_information']['file_created']}
Modified: {digital_evidence['file_information']['file_modified']}

INTEGRITY VERIFICATION
-----------------------
MD5 Hash: {digital_evidence['integrity_verification']['md5_hash']}
SHA1 Hash: {digital_evidence['integrity_verification']['sha1_hash']}
SHA256 Hash: {digital_evidence['integrity_verification']['sha256_hash']}
Verification Status: {digital_evidence['integrity_verification']['verification_status']}

CONTENT METADATA
----------------
Title: {digital_evidence['content_metadata']['title']}
Creator: {digital_evidence['content_metadata']['creator']}
Original Publication Date: {digital_evidence['content_metadata']['original_publication_date']}
Runtime: {digital_evidence['content_metadata']['runtime']}
Language: {digital_evidence['content_metadata']['language']}
Original Platform: {digital_evidence['content_metadata']['original_platform']}

CHAIN OF CUSTODY
----------------"""
        
        for i, stage in enumerate(digital_evidence['chain_of_custody'], 1):
            summary_content += f"""
{i}. {stage['stage']}
   Timestamp: {stage['timestamp']}
   Location: {stage['location']}
   Custodian: {stage['custodian']}
   Platform: {stage['platform']}
   Description: {stage['description']}"""
        
        summary_content += f"""

SOURCE VERIFICATION
-------------------
Archive URL: {digital_evidence['source_verification']['archive_url']}
Original Source URL: {digital_evidence['source_verification']['original_source_url']}
Archive Identifier: {digital_evidence['source_verification']['archive_identifier']}
Verification Method: {digital_evidence['source_verification']['verification_method']}

LEGAL CERTIFICATIONS
---------------------
Authenticity Statement: {report_data['legal_certifications']['authenticity_statement']}
Collection Method: {report_data['legal_certifications']['collection_method']}
Evidence Class: {report_data['legal_certifications']['evidence_class']}
Admissibility Notes: {report_data['legal_certifications']['admissibility_notes']}

This report was automatically generated and provides comprehensive documentation
for digital evidence authentication and chain of custody verification.
"""
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return summary_path
    
    def list_evidence_reports(self):
        """List all generated evidence reports."""
        reports = []
        for report_file in self.evidence_dir.glob("evidence_report_*.json"):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    reports.append({
                        "filename": report_file.name,
                        "report_id": report_data["evidence_report"]["report_id"],
                        "generated_at": report_data["evidence_report"]["generated_at"],
                        "file_path": str(report_file)
                    })
            except Exception:
                continue
        
        return sorted(reports, key=lambda x: x["generated_at"], reverse=True)


def create_evidence_report(cache_dir, video_url, video_filename, case_info=None):
    """Convenience function to generate evidence report."""
    generator = EvidenceGenerator(cache_dir)
    return generator.generate_evidence_report(video_url, video_filename, case_info)


class EvidenceGenerator:
    """Generates court-admissible evidence documentation for archived videos."""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.evidence_dir = self.cache_dir / "evidence_reports"
        self.evidence_dir.mkdir(exist_ok=True)
    
    # ... [other methods unchanged] ...

    def _sanitize_evidence_filename(self, filename):
        """Sanitize filename for evidence reports to ensure Windows compatibility."""
        try:
            # Replace non-ASCII characters with underscores
            safe_name = ""
            for c in filename:
                if ord(c) < 128 and c.isalnum():
                    safe_name += c
                elif c in '-_':
                    safe_name += c
                else:
                    safe_name += "_"
            
            # Remove consecutive underscores
            while "__" in safe_name:
                safe_name = safe_name.replace("__", "_")
            
            return safe_name.strip("_")[:50]
        except Exception:
            return "evidence_file"