# PDF Download with Paywall Bypass - Feature Roadmap

## Overview
Add comprehensive PDF download functionality to Mucache with configurable paywall bypass methods, automatic metadata extraction, citation generation, and legal evidence documentation.

## Configuration Decisions
- **Paywall Methods**: All methods with configurable priority
- **Authentication**: Session-based (user logs in each session, no persistent storage)
- **PDF Sources**: Academic publishers, ArXiv, open-access repositories, news sites, legal databases
- **Integration**: Full integration with existing CitationGenerator and EvidenceGenerator
- **Legal/Ethical**: Include disclaimer/terms of use for users
- **UI Triggers**: Automatic PDF detection from URLs + batch download from citation lists

---

## Phase 1: Core PDF Infrastructure (Foundation)

### 1.1 Create PDF Manager Module (`pdf_manager.py`)
**Purpose**: Track and manage downloaded PDFs similar to VideoManager and WebpageManager

**Features**:
- Store PDFs in `cache_dir/pdfs/` directory
- Maintain metadata in `cache_dir/pdfs/pdfs.json`
- Metadata fields:
  - `url`: Original source URL
  - `filename`: Local PDF filename
  - `title`: Paper/document title
  - `authors`: List of authors
  - `doi`: Digital Object Identifier
  - `publisher`: Publisher name
  - `publication_date`: Publication date
  - `download_date`: When downloaded
  - `access_method`: Method used (archive_org, institutional, open_access, etc.)
  - `file_size`: File size in bytes
  - `file_hash_md5`: MD5 hash for integrity
  - `tags`: User-defined tags
  - `abstract`: Paper abstract (if available)
  - `citation_count`: Citation count (if available)

**Methods**:
```python
class PDFManager:
    def __init__(self, cache_dir)
    def add_pdf(self, metadata_dict)
    def remove_pdf(self, url)
    def get_pdf_by_url(self, url)
    def get_all_pdfs(self)
    def get_sorted_pdfs(self, sort_by='download_date')
    def update_metadata(self, url, metadata_updates)
    def repair_pdf_list(self)  # Fix filename mismatches
```

### 1.2 PDF Detection & Metadata Extraction
**Purpose**: Automatically detect PDF URLs and extract metadata

**URL Pattern Detection**:
- Academic publishers: IEEE, Springer, Elsevier, Wiley, Nature, Science, JSTOR, ACM
- Preprint servers: ArXiv, bioRxiv, medRxiv, SSRN
- Open access: PubMed Central, PLOS, DOAJ
- Legal databases: CourtListener, PACER, Google Scholar
- News sites: NYTimes, WSJ, WashPost (PDF articles)
- Direct PDF URLs: `.pdf` extension detection

**DOI Extraction**:
- Parse DOI from URL patterns
- Extract from HTML meta tags
- Use CrossRef API for DOI resolution

**Metadata Extraction Sources**:
1. **From PDF file** (using PyPDF2/pdfplumber):
   - Title from document properties
   - Author from document properties
   - Creation date, modification date
   - Page count

2. **From Publisher APIs**:
   - CrossRef API (comprehensive metadata)
   - Unpaywall API (OA availability)
   - Semantic Scholar API (citations, influence)
   - arXiv API (for arXiv papers)
   - PubMed API (for medical papers)

3. **From HTML page**:
   - Meta tags (DC.title, citation_title, etc.)
   - JSON-LD structured data
   - OpenGraph tags

**Implementation**:
```python
def detect_pdf_url(url):
    """Detect if URL is or leads to a PDF"""

def extract_doi_from_url(url):
    """Extract DOI from URL if present"""

def fetch_metadata_from_doi(doi):
    """Get metadata from CrossRef/other APIs"""

def extract_metadata_from_pdf(pdf_path):
    """Extract metadata from PDF file itself"""

def extract_metadata_from_html(url):
    """Extract metadata from publisher's HTML page"""
```

### 1.3 Update UI (`player.html`)
**Purpose**: Add PDF management interface to existing React UI

**New Components**:

1. **PDFs Tab**:
   - Add alongside "Videos" and "Webpages" tabs
   - Display PDF grid/list view
   - Show thumbnail (first page preview using PDF.js)
   - Display metadata: title, authors, year, publisher, DOI
   - Show access method badge (Archive.org, Open Access, Institutional, etc.)

2. **PDF Download Input**:
   - Input field for URL/DOI
   - Auto-detect PDF URLs
   - Batch import button (for citation lists)
   - Download progress indicator

3. **PDF Detail View**:
   - Full metadata display
   - Generated citation (all formats)
   - Evidence report link
   - Download source information
   - Tags editor
   - Notes field
   - Related PDFs (by author, topic)

4. **PDF Actions**:
   - Open PDF (in browser or external viewer)
   - Re-download (try different method)
   - Generate citation
   - Generate evidence report
   - Export metadata
   - Remove from library
   - Add/edit tags

5. **Search & Filter**:
   - Search by title, author, DOI, tags, abstract
   - Filter by year, publisher, access method
   - Sort by date added, publication date, title, author

**UI Mockup**:
```
┌─────────────────────────────────────────────────┐
│ [Videos] [Webpages] [PDFs]                      │
├─────────────────────────────────────────────────┤
│ Download PDF: [URL or DOI input] [Download]     │
│              [Import Citation List]             │
├─────────────────────────────────────────────────┤
│ Search: [________] Filter: [Year▾] [Publisher▾] │
├─────────────────────────────────────────────────┤
│ ┌──────────────┐  ┌──────────────┐             │
│ │ [PDF thumb]  │  │ [PDF thumb]  │             │
│ │ Title Here   │  │ Another PDF  │             │
│ │ Author et al.│  │ Smith et al. │             │
│ │ 2024 • IEEE  │  │ 2023 • ArXiv │             │
│ │ [OA] [Cite]  │  │ [Archive.org]│             │
│ └──────────────┘  └──────────────┘             │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Phase 2: Download Methods (Priority System)

### 2.1 Configurable Priority System
**Purpose**: Allow users to configure which methods to try and in what order

**Settings Structure** (`settings.json`):
```json
{
  "pdf_download_priority": [
    "open_access",
    "archive_org",
    "institutional",
    "alternative"
  ],
  "pdf_access_methods": {
    "archive_org": {
      "enabled": true,
      "prefer_original": true
    },
    "institutional": {
      "enabled": false,
      "proxy_url": "",
      "institution_name": ""
    },
    "open_access": {
      "enabled": true,
      "sources": ["arxiv", "pubmed", "unpaywall"]
    },
    "alternative": {
      "enabled": false,
      "service_url": "",
      "disclaimer_accepted": false
    }
  },
  "pdf_session": {
    "timeout_minutes": 60,
    "auto_logout": true
  }
}
```

**Settings UI**:
- Drag-and-drop priority ordering
- Enable/disable individual methods
- Configure method-specific settings
- Test connection for each method

**Implementation**:
```python
def download_pdf_with_priority(url, settings, session=None):
    """Try download methods in priority order until success"""
    priority = settings.get('pdf_download_priority', [])

    for method in priority:
        if not settings['pdf_access_methods'][method]['enabled']:
            continue

        try:
            if method == 'archive_org':
                return download_from_archive_org(url)
            elif method == 'institutional':
                return download_via_institutional(url, session)
            elif method == 'open_access':
                return download_from_open_access(url)
            elif method == 'alternative':
                return download_from_alternative(url, settings)
        except Exception as e:
            logger.warning(f"Method {method} failed: {e}")
            continue

    raise Exception("All download methods failed")
```

### 2.2 Method 1: Archive.org Wayback Machine
**Purpose**: Download PDFs from Internet Archive's Wayback Machine

**Features**:
- Search for archived snapshots of the PDF URL
- Find closest snapshot to publication date
- Download original PDF if available
- Track archive date in metadata

**API Endpoints**:
- Availability: `http://archive.org/wayback/available?url={url}`
- CDX Search: `http://web.archive.org/cdx/search/cdx?url={url}&output=json`
- Download: `http://web.archive.org/web/{timestamp}/{url}`

**Implementation**:
```python
def download_from_archive_org(url):
    """Download PDF from Wayback Machine"""
    # 1. Check availability
    availability = requests.get(
        f"http://archive.org/wayback/available?url={url}"
    ).json()

    # 2. If available, get snapshot URL
    if availability['archived_snapshots']:
        snapshot_url = availability['archived_snapshots']['closest']['url']

        # 3. Download PDF
        pdf_content = requests.get(snapshot_url).content

        # 4. Return with metadata
        return {
            'content': pdf_content,
            'access_method': 'archive_org',
            'archive_date': availability['archived_snapshots']['closest']['timestamp']
        }

    raise Exception("Not available in Wayback Machine")
```

**Edge Cases**:
- Multiple snapshots: prefer closest to publication date
- Redirects: follow redirect chain
- Memento protocol support

### 2.3 Method 2: Institutional/Proxy Access
**Purpose**: Download through institutional subscriptions via proxy

**Supported Proxy Types**:
1. **EZproxy**: `https://proxy.institution.edu/login?url={target_url}`
2. **Shibboleth**: SAML-based authentication
3. **WAYFless URLs**: Direct institutional access links
4. **OpenAthens**: Alternative to Shibboleth

**Features**:
- Session-based authentication (no stored passwords)
- Cookie management for authenticated sessions
- Support multiple institutions
- Automatic session renewal
- Login form detection and submission

**Implementation**:
```python
class InstitutionalAccess:
    def __init__(self):
        self.sessions = {}  # session_id -> requests.Session

    def login(self, institution_config, credentials):
        """Login to institutional proxy"""
        session = requests.Session()

        if institution_config['type'] == 'ezproxy':
            # EZproxy login
            login_url = f"{institution_config['proxy_url']}/login"
            session.post(login_url, data={
                'user': credentials['username'],
                'pass': credentials['password']
            })

        elif institution_config['type'] == 'shibboleth':
            # Shibboleth SAML flow
            # Complex multi-step authentication
            pass

        # Store session
        session_id = generate_session_id()
        self.sessions[session_id] = session

        return session_id

    def download_pdf(self, url, session_id):
        """Download PDF using authenticated session"""
        session = self.sessions[session_id]

        # Construct proxied URL
        proxied_url = self.construct_proxy_url(url)

        # Download through proxy
        response = session.get(proxied_url)

        if response.headers.get('content-type') == 'application/pdf':
            return {
                'content': response.content,
                'access_method': 'institutional'
            }

        raise Exception("PDF not accessible via institutional access")

    def logout(self, session_id):
        """Clear session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
```

**UI Flow**:
1. User clicks "Login to Institution"
2. Modal appears with institution selector
3. User enters credentials (username/password)
4. Session established and stored in memory
5. Downloads use this session automatically
6. Session expires after timeout or manual logout
7. Clear all credentials on server shutdown

### 2.4 Method 3: Open Access Repositories
**Purpose**: Download from legitimate open access sources

**Supported Sources**:

1. **ArXiv** (`arxiv.org`):
   - Direct PDF downloads: `https://arxiv.org/pdf/{arxiv_id}.pdf`
   - API for metadata: `http://export.arxiv.org/api/query?id_list={arxiv_id}`

2. **PubMed Central** (`ncbi.nlm.nih.gov/pmc`):
   - Free full-text articles
   - API: `https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmc_id}`

3. **bioRxiv/medRxiv** (`biorxiv.org`, `medrxiv.org`):
   - Preprint servers for biology and medicine
   - Direct PDF links

4. **SSRN** (`papers.ssrn.com`):
   - Social science research network
   - Some papers freely available

5. **Unpaywall API** (`unpaywall.org`):
   - Aggregates OA locations for DOI-identified papers
   - API: `https://api.unpaywall.org/v2/{doi}?email={email}`

6. **CORE** (`core.ac.uk`):
   - Aggregates open access research papers
   - API: `https://api.core.ac.uk/v3/`

7. **Directory of Open Access Journals (DOAJ)**:
   - Curated list of OA journals

**Implementation**:
```python
def download_from_open_access(url):
    """Try multiple OA sources"""

    # 1. Extract DOI if present
    doi = extract_doi_from_url(url)

    if doi:
        # 2. Try Unpaywall first
        unpaywall_result = query_unpaywall(doi)
        if unpaywall_result['is_oa'] and unpaywall_result['best_oa_location']:
            oa_url = unpaywall_result['best_oa_location']['url_for_pdf']
            pdf_content = requests.get(oa_url).content
            return {
                'content': pdf_content,
                'access_method': 'open_access_unpaywall',
                'oa_status': unpaywall_result['oa_status']
            }

    # 3. Try ArXiv
    if 'arxiv.org' in url:
        arxiv_id = extract_arxiv_id(url)
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_content = requests.get(pdf_url).content
        return {
            'content': pdf_content,
            'access_method': 'open_access_arxiv'
        }

    # 4. Try PubMed Central
    if 'ncbi.nlm.nih.gov/pmc' in url or 'pubmed' in url:
        # ... PMC download logic
        pass

    # 5. Try CORE API
    # ...

    raise Exception("No open access version found")

def query_unpaywall(doi):
    """Query Unpaywall API for OA availability"""
    email = "your-email@example.com"  # Required by Unpaywall
    response = requests.get(
        f"https://api.unpaywall.org/v2/{doi}?email={email}"
    )
    return response.json()
```

### 2.5 Method 4: Alternative Access Services
**Purpose**: Support for user-configured alternative services (with legal disclaimers)

**Features**:
- Configurable service URL
- Legal disclaimer required before enabling
- Disabled by default
- User assumes all legal responsibility
- Logs all usage

**Disclaimer Text**:
```
WARNING: Alternative Access Services

By enabling this feature, you acknowledge that:

1. You are solely responsible for ensuring your use complies with
   applicable laws, institutional policies, and terms of service.

2. Mucache developers do not endorse or encourage copyright infringement
   or unauthorized access to paywalled content.

3. This feature is provided for legitimate research purposes only, such as:
   - Accessing works you have legal rights to
   - Academic research under fair use provisions
   - Verifying citations and references
   - Accessing works in jurisdictions with different copyright laws

4. You understand the potential legal risks and consequences.

5. All usage will be logged for accountability.

By clicking "I Accept", you agree to use this feature responsibly and
legally.

[I Accept] [Cancel]
```

**Implementation**:
```python
def download_from_alternative(url, settings):
    """Download from user-configured alternative service"""

    # 1. Check disclaimer accepted
    if not settings['pdf_access_methods']['alternative']['disclaimer_accepted']:
        raise Exception("Must accept disclaimer before using alternative services")

    # 2. Get service URL
    service_url = settings['pdf_access_methods']['alternative']['service_url']
    if not service_url:
        raise Exception("Alternative service URL not configured")

    # 3. Construct request URL (service-specific)
    # Example: https://service.example/{doi_or_url}
    request_url = construct_alternative_url(service_url, url)

    # 4. Log usage
    logger.warning(f"Alternative service used: {service_url} for {url}")
    log_alternative_access(url, service_url, timestamp=datetime.now())

    # 5. Download
    response = requests.get(request_url, timeout=60)

    if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
        return {
            'content': response.content,
            'access_method': 'alternative',
            'service': service_url
        }

    raise Exception("Alternative service failed")

def log_alternative_access(url, service, timestamp):
    """Log alternative service usage for accountability"""
    log_entry = {
        'timestamp': timestamp.isoformat(),
        'url': url,
        'service': service,
        'ip_address': get_client_ip()
    }

    # Append to alternative_access.log
    with open('logs/alternative_access.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

---

## Phase 3: Authentication & Session Management

### 3.1 Session-Based Authentication System
**Purpose**: Secure authentication without persistent credential storage

**Features**:
- In-memory session storage only
- No credentials saved to disk
- Automatic session timeout
- Manual logout option
- Clear all sessions on server shutdown
- Support multiple concurrent sessions (different institutions)

**Session Structure**:
```python
{
    'session_id': 'uuid4-string',
    'institution': 'University Name',
    'username': 'user@university.edu',  # For display only
    'created_at': datetime,
    'last_used': datetime,
    'expires_at': datetime,
    'request_session': requests.Session(),  # Actual authenticated session
    'proxy_url': 'https://proxy.university.edu'
}
```

**Implementation**:
```python
class SessionManager:
    def __init__(self, default_timeout_minutes=60):
        self.sessions = {}
        self.default_timeout = default_timeout_minutes
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

    def create_session(self, institution_config, credentials):
        """Create new authenticated session"""
        session_id = str(uuid.uuid4())

        # Authenticate
        request_session = self._authenticate(institution_config, credentials)

        # Create session record
        now = datetime.now()
        self.sessions[session_id] = {
            'session_id': session_id,
            'institution': institution_config['name'],
            'username': credentials['username'],
            'created_at': now,
            'last_used': now,
            'expires_at': now + timedelta(minutes=self.default_timeout),
            'request_session': request_session,
            'proxy_url': institution_config.get('proxy_url', '')
        }

        logger.info(f"Session created: {session_id} for {institution_config['name']}")
        return session_id

    def get_session(self, session_id):
        """Get session if valid, update last_used"""
        if session_id not in self.sessions:
            raise Exception("Session not found")

        session = self.sessions[session_id]

        # Check expiration
        if datetime.now() > session['expires_at']:
            self.destroy_session(session_id)
            raise Exception("Session expired")

        # Update last used
        session['last_used'] = datetime.now()

        return session

    def destroy_session(self, session_id):
        """Destroy session and clear credentials"""
        if session_id in self.sessions:
            logger.info(f"Session destroyed: {session_id}")
            del self.sessions[session_id]

    def destroy_all_sessions(self):
        """Clear all sessions (on shutdown)"""
        logger.info(f"Destroying all {len(self.sessions)} sessions")
        self.sessions.clear()

    def _cleanup_expired(self):
        """Background thread to clean up expired sessions"""
        while True:
            time.sleep(300)  # Check every 5 minutes
            now = datetime.now()
            expired = [
                sid for sid, s in self.sessions.items()
                if now > s['expires_at']
            ]
            for sid in expired:
                self.destroy_session(sid)

    def _authenticate(self, institution_config, credentials):
        """Authenticate with institution and return requests.Session"""
        # Implementation depends on institution type
        # See Phase 2.3 for details
        pass
```

**UI Components**:

1. **Login Modal**:
```
┌─────────────────────────────────┐
│ Login to Institution            │
├─────────────────────────────────┤
│ Institution: [Select...      ▾] │
│                                 │
│ Username: [__________________ ] │
│ Password: [__________________ ] │
│                                 │
│ Session timeout: [60] minutes   │
│ □ Auto-logout on close          │
│                                 │
│        [Cancel]  [Login]        │
└─────────────────────────────────┘
```

2. **Active Sessions Display**:
```
Active Sessions:
┌──────────────────────────────────┐
│ 🟢 MIT Libraries                 │
│    Expires in 45 minutes         │
│    [Logout]                      │
├──────────────────────────────────┤
│ 🟢 University of California      │
│    Expires in 12 minutes         │
│    [Logout]                      │
└──────────────────────────────────┘
```

### 3.2 Cookie Import from Browser
**Purpose**: Import existing authenticated sessions from user's browser

**Features**:
- Import cookies from Chrome, Firefox, Safari, Edge
- Detect active publisher sessions
- Convert browser cookies to requests.Session
- Automatic cookie expiration handling

**Implementation**:
```python
import browser_cookie3

def import_browser_cookies(browser='chrome', domain=None):
    """Import cookies from browser"""

    try:
        if browser == 'chrome':
            cookies = browser_cookie3.chrome(domain_name=domain)
        elif browser == 'firefox':
            cookies = browser_cookie3.firefox(domain_name=domain)
        elif browser == 'safari':
            cookies = browser_cookie3.safari(domain_name=domain)
        elif browser == 'edge':
            cookies = browser_cookie3.edge(domain_name=domain)
        else:
            raise ValueError(f"Unsupported browser: {browser}")

        # Create session with imported cookies
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set_cookie(cookie)

        return session

    except Exception as e:
        logger.error(f"Failed to import cookies from {browser}: {e}")
        raise

def detect_publisher_sessions():
    """Detect active sessions with known publishers"""
    publishers = [
        'ieee.org', 'springer.com', 'sciencedirect.com',
        'acm.org', 'jstor.org', 'wiley.com'
    ]

    active_sessions = []

    for publisher in publishers:
        try:
            cookies = browser_cookie3.chrome(domain_name=publisher)
            if cookies:
                active_sessions.append(publisher)
        except:
            pass

    return active_sessions
```

**UI**:
```
Import Browser Session:
┌─────────────────────────────────┐
│ Detected active sessions:       │
│ ☑ IEEE Xplore (Chrome)          │
│ ☑ SpringerLink (Chrome)         │
│ ☑ JSTOR (Firefox)               │
│                                 │
│ Browser: [Chrome ▾]             │
│                                 │
│ [Import Selected]               │
└─────────────────────────────────┘
```

---

## Phase 4: Integration with Existing Features

### 4.1 Citation Generation Integration
**Purpose**: Extend existing CitationGenerator to support PDFs

**Enhancements to `citation_generator.py`**:

```python
class CitationGenerator:
    # ... existing methods ...

    def generate_pdf_citation(self, pdf_metadata, format='apa'):
        """Generate citation for PDF"""

        if format == 'apa':
            return self._format_apa_pdf(pdf_metadata)
        elif format == 'mla':
            return self._format_mla_pdf(pdf_metadata)
        elif format == 'chicago':
            return self._format_chicago_pdf(pdf_metadata)
        elif format == 'harvard':
            return self._format_harvard_pdf(pdf_metadata)
        elif format == 'ieee':
            return self._format_ieee_pdf(pdf_metadata)
        elif format == 'vancouver':
            return self._format_vancouver_pdf(pdf_metadata)
        elif format == 'bibtex':
            return self._format_bibtex_pdf(pdf_metadata)

    def _format_apa_pdf(self, meta):
        """APA format for journal article"""
        # Authors
        if meta.get('authors'):
            authors = self._format_authors_apa(meta['authors'])
        else:
            authors = "Unknown Author"

        # Year
        year = meta.get('publication_year', 'n.d.')

        # Title
        title = meta.get('title', 'Untitled')

        # Journal info
        journal = meta.get('journal', '')
        volume = meta.get('volume', '')
        issue = meta.get('issue', '')
        pages = meta.get('pages', '')

        # DOI
        doi = meta.get('doi', '')

        # Construct citation
        citation = f"{authors} ({year}). {title}."

        if journal:
            citation += f" {journal}"
            if volume:
                citation += f", {volume}"
            if issue:
                citation += f"({issue})"
            if pages:
                citation += f", {pages}"
            citation += "."

        if doi:
            citation += f" https://doi.org/{doi}"
        elif meta.get('url'):
            citation += f" Retrieved from {meta['url']}"

        return citation

    def _format_bibtex_pdf(self, meta):
        """BibTeX format"""
        # Generate citation key
        first_author = meta['authors'][0].split()[-1] if meta.get('authors') else 'Unknown'
        year = meta.get('publication_year', 'nd')
        key = f"{first_author}{year}"

        # Determine entry type
        if meta.get('journal'):
            entry_type = 'article'
        elif meta.get('conference'):
            entry_type = 'inproceedings'
        else:
            entry_type = 'misc'

        bibtex = f"@{entry_type}{{{key},\n"

        if meta.get('title'):
            bibtex += f"  title = {{{meta['title']}}},\n"

        if meta.get('authors'):
            authors = ' and '.join(meta['authors'])
            bibtex += f"  author = {{{authors}}},\n"

        if meta.get('journal'):
            bibtex += f"  journal = {{{meta['journal']}}},\n"

        if meta.get('volume'):
            bibtex += f"  volume = {{{meta['volume']}}},\n"

        if meta.get('issue'):
            bibtex += f"  number = {{{meta['issue']}}},\n"

        if meta.get('pages'):
            bibtex += f"  pages = {{{meta['pages']}}},\n"

        if meta.get('publication_year'):
            bibtex += f"  year = {{{meta['publication_year']}}},\n"

        if meta.get('doi'):
            bibtex += f"  doi = {{{meta['doi']}}},\n"

        if meta.get('url'):
            bibtex += f"  url = {{{meta['url']}}},\n"

        bibtex += "}"

        return bibtex
```

**Auto-generation on Download**:
```python
def download_pdf_with_citation(url, settings):
    """Download PDF and automatically generate citations"""

    # 1. Download PDF
    pdf_result = download_pdf_with_priority(url, settings)

    # 2. Extract metadata
    metadata = extract_metadata_from_pdf(pdf_result['filepath'])

    # 3. Generate all citation formats
    citation_gen = CitationGenerator()
    citations = {}

    for format in ['apa', 'mla', 'chicago', 'harvard', 'ieee', 'vancouver', 'bibtex']:
        citations[format] = citation_gen.generate_pdf_citation(metadata, format)

    # 4. Save citations
    citation_file = os.path.join(cache_dir, 'citations', f"{metadata['filename']}.json")
    with open(citation_file, 'w') as f:
        json.dump(citations, f, indent=2)

    # 5. Update metadata
    metadata['citations'] = citations

    return metadata
```

### 4.2 Evidence Report Integration
**Purpose**: Extend EvidenceGenerator for legal admissibility of PDFs

**Enhancements to `evidence_generator.py`**:

```python
class EvidenceGenerator:
    # ... existing methods ...

    def generate_pdf_evidence_report(self, pdf_metadata):
        """Generate legal evidence report for PDF"""

        report = {
            'report_type': 'PDF Document Evidence',
            'generated_at': datetime.now().isoformat(),
            'document_info': {
                'title': pdf_metadata.get('title'),
                'authors': pdf_metadata.get('authors'),
                'publication_date': pdf_metadata.get('publication_date'),
                'doi': pdf_metadata.get('doi'),
                'original_url': pdf_metadata.get('url')
            },
            'acquisition': {
                'download_date': pdf_metadata.get('download_date'),
                'access_method': pdf_metadata.get('access_method'),
                'downloaded_by': 'Mucache Player',
                'source_verification': self._verify_source(pdf_metadata)
            },
            'file_integrity': {
                'filename': pdf_metadata.get('filename'),
                'file_size_bytes': pdf_metadata.get('file_size'),
                'md5_hash': pdf_metadata.get('file_hash_md5'),
                'sha1_hash': self._compute_sha1(pdf_metadata['filepath']),
                'sha256_hash': self._compute_sha256(pdf_metadata['filepath'])
            },
            'chain_of_custody': [
                {
                    'timestamp': pdf_metadata.get('download_date'),
                    'action': 'Document downloaded from source',
                    'actor': 'Mucache Player',
                    'location': pdf_metadata.get('url'),
                    'method': pdf_metadata.get('access_method')
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'Evidence report generated',
                    'actor': 'Mucache Evidence Generator',
                    'hash_verification': 'MD5, SHA1, SHA256 computed'
                }
            ],
            'metadata_extraction': {
                'pdf_properties': self._extract_pdf_properties(pdf_metadata['filepath']),
                'external_metadata': {
                    'crossref': pdf_metadata.get('crossref_metadata'),
                    'publisher': pdf_metadata.get('publisher_metadata')
                }
            },
            'authenticity_indicators': {
                'doi_verified': self._verify_doi(pdf_metadata.get('doi')),
                'publisher_verified': self._verify_publisher(pdf_metadata),
                'archive_available': self._check_archive_availability(pdf_metadata.get('url')),
                'citation_count': pdf_metadata.get('citation_count'),
                'peer_reviewed': pdf_metadata.get('peer_reviewed')
            }
        }

        # Generate formatted report
        formatted_report = self._format_evidence_report_pdf(report)

        # Save report
        report_filename = f"{pdf_metadata['filename']}_evidence_report.json"
        report_path = os.path.join(cache_dir, 'evidence_reports', report_filename)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Also save as human-readable PDF
        self._generate_evidence_pdf(report, report_path.replace('.json', '.pdf'))

        return report

    def _verify_source(self, metadata):
        """Verify document source authenticity"""
        verification = {
            'original_url_accessible': False,
            'doi_resolves': False,
            'publisher_match': False,
            'archive_snapshot_exists': False
        }

        # Check original URL
        try:
            response = requests.head(metadata['url'], timeout=10)
            verification['original_url_accessible'] = response.status_code == 200
        except:
            pass

        # Check DOI
        if metadata.get('doi'):
            verification['doi_resolves'] = self._verify_doi(metadata['doi'])

        # Check archive
        verification['archive_snapshot_exists'] = self._check_archive_availability(metadata['url'])

        return verification

    def _extract_pdf_properties(self, pdf_path):
        """Extract PDF document properties"""
        import PyPDF2

        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            info = reader.metadata

            return {
                'title': info.get('/Title', ''),
                'author': info.get('/Author', ''),
                'subject': info.get('/Subject', ''),
                'creator': info.get('/Creator', ''),
                'producer': info.get('/Producer', ''),
                'creation_date': info.get('/CreationDate', ''),
                'modification_date': info.get('/ModDate', ''),
                'page_count': len(reader.pages),
                'encrypted': reader.is_encrypted
            }
```

**Evidence Report Template**:
```
═══════════════════════════════════════════════════════
              PDF DOCUMENT EVIDENCE REPORT
═══════════════════════════════════════════════════════

Generated: [Date and Time]
Report ID: [UUID]

DOCUMENT INFORMATION
───────────────────────────────────────────────────────
Title:      [Document Title]
Authors:    [Author List]
Published:  [Publication Date]
DOI:        [Digital Object Identifier]
Source URL: [Original URL]

ACQUISITION DETAILS
───────────────────────────────────────────────────────
Downloaded:     [Download Date/Time]
Access Method:  [Method Used]
Downloaded By:  Mucache Player v[version]
IP Address:     [IP at download]

FILE INTEGRITY VERIFICATION
───────────────────────────────────────────────────────
Filename:   [Local Filename]
File Size:  [Size in bytes]
MD5:        [MD5 Hash]
SHA-1:      [SHA-1 Hash]
SHA-256:    [SHA-256 Hash]

CHAIN OF CUSTODY
───────────────────────────────────────────────────────
1. [Timestamp] - Document downloaded from [source]
   Method: [access_method]

2. [Timestamp] - File integrity hashes computed
   MD5, SHA-1, SHA-256 generated

3. [Timestamp] - Evidence report generated
   Report created and signed

AUTHENTICITY VERIFICATION
───────────────────────────────────────────────────────
✓ DOI Verified:          [Yes/No]
✓ Publisher Verified:    [Yes/No]
✓ Archive Snapshot:      [Yes/No - with link]
✓ Citation Count:        [Number]
✓ Peer Reviewed:         [Yes/No/Unknown]

METADATA
───────────────────────────────────────────────────────
[Full metadata from PDF properties and external sources]

═══════════════════════════════════════════════════════
This report generated by Mucache Player
For admissibility in legal proceedings
═══════════════════════════════════════════════════════
```

### 4.3 Batch Download from Citation Lists
**Purpose**: Import and download PDFs from BibTeX, RIS, or CSV citation lists

**Supported Formats**:
1. **BibTeX** (`.bib`) - Academic standard
2. **RIS** (`.ris`) - Reference Manager format
3. **CSV** - Custom format with columns: title, authors, doi, url, year
4. **EndNote XML** (`.xml`)

**Implementation**:
```python
import bibtexparser
import rispy

class BatchDownloader:
    def __init__(self, pdf_manager, settings):
        self.pdf_manager = pdf_manager
        self.settings = settings
        self.queue = []
        self.results = {
            'successful': [],
            'failed': [],
            'already_exists': []
        }

    def import_citation_file(self, filepath):
        """Import citations from file"""
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.bib':
            return self._import_bibtex(filepath)
        elif ext == '.ris':
            return self._import_ris(filepath)
        elif ext == '.csv':
            return self._import_csv(filepath)
        elif ext == '.xml':
            return self._import_endnote_xml(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _import_bibtex(self, filepath):
        """Parse BibTeX file"""
        with open(filepath) as f:
            bib_database = bibtexparser.load(f)

        citations = []
        for entry in bib_database.entries:
            citation = {
                'title': entry.get('title', ''),
                'authors': entry.get('author', '').split(' and '),
                'doi': entry.get('doi', ''),
                'url': entry.get('url', ''),
                'year': entry.get('year', ''),
                'journal': entry.get('journal', ''),
                'volume': entry.get('volume', ''),
                'pages': entry.get('pages', '')
            }
            citations.append(citation)

        return citations

    def _import_ris(self, filepath):
        """Parse RIS file"""
        with open(filepath) as f:
            entries = rispy.load(f)

        citations = []
        for entry in entries:
            citation = {
                'title': entry.get('title', ''),
                'authors': entry.get('authors', []),
                'doi': entry.get('doi', ''),
                'url': entry.get('url', ''),
                'year': entry.get('year', ''),
                'journal': entry.get('journal_name', '')
            }
            citations.append(citation)

        return citations

    def _import_csv(self, filepath):
        """Parse CSV file"""
        import csv

        citations = []
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                citation = {
                    'title': row.get('title', ''),
                    'authors': row.get('authors', '').split(';'),
                    'doi': row.get('doi', ''),
                    'url': row.get('url', ''),
                    'year': row.get('year', '')
                }
                citations.append(citation)

        return citations

    def queue_downloads(self, citations):
        """Add citations to download queue"""
        for citation in citations:
            # Determine download URL
            if citation.get('doi'):
                url = f"https://doi.org/{citation['doi']}"
            elif citation.get('url'):
                url = citation['url']
            else:
                logger.warning(f"No URL or DOI for: {citation.get('title')}")
                continue

            # Check if already downloaded
            if self.pdf_manager.get_pdf_by_url(url):
                self.results['already_exists'].append(citation)
                continue

            self.queue.append({
                'url': url,
                'citation': citation
            })

        logger.info(f"Queued {len(self.queue)} PDFs for download")

    def download_all(self, progress_callback=None):
        """Download all queued PDFs"""
        total = len(self.queue)

        for i, item in enumerate(self.queue):
            try:
                # Progress update
                if progress_callback:
                    progress_callback(i + 1, total, item['citation']['title'])

                # Download PDF
                result = download_pdf_with_priority(
                    item['url'],
                    self.settings
                )

                # Add to manager
                self.pdf_manager.add_pdf(result['metadata'])

                self.results['successful'].append(item['citation'])

                logger.info(f"Downloaded: {item['citation']['title']}")

            except Exception as e:
                logger.error(f"Failed to download {item['url']}: {e}")
                self.results['failed'].append({
                    'citation': item['citation'],
                    'error': str(e)
                })

            # Rate limiting
            time.sleep(2)

        return self.results

    def generate_report(self):
        """Generate download report"""
        report = f"""
Batch Download Report
═════════════════════════════════════════════════════

Successful: {len(self.results['successful'])}
Failed:     {len(self.results['failed'])}
Skipped:    {len(self.results['already_exists'])}

FAILED DOWNLOADS:
"""
        for item in self.results['failed']:
            report += f"\n- {item['citation']['title']}\n"
            report += f"  Error: {item['error']}\n"

        return report
```

**UI Flow**:
```
Batch Download:
┌─────────────────────────────────────┐
│ Import Citation List                │
│                                     │
│ [Choose File] bibliography.bib      │
│                                     │
│ Format: [BibTeX ▾]                  │
│                                     │
│ [Parse Citations]                   │
└─────────────────────────────────────┘

After parsing:
┌─────────────────────────────────────┐
│ Found 50 citations                  │
│ Already downloaded: 5               │
│ To download: 45                     │
│                                     │
│ ☑ Skip if already exists            │
│ ☑ Generate citations                │
│ ☑ Generate evidence reports         │
│                                     │
│ Download method priority:           │
│   1. Open Access                    │
│   2. Archive.org                    │
│   3. Institutional                  │
│                                     │
│ [Start Batch Download]              │
└─────────────────────────────────────┘

Progress:
┌─────────────────────────────────────┐
│ Downloading PDFs: 23/45             │
│ ████████████░░░░░░░░░░░░░░░  51%   │
│                                     │
│ Current: "Deep Learning Review"     │
│                                     │
│ Successful: 20                      │
│ Failed: 3                           │
│ Remaining: 22                       │
│                                     │
│ [Pause] [Cancel]                    │
└─────────────────────────────────────┘
```

---

## Phase 5: Legal & Ethical Safeguards

### 5.1 Terms of Use & Disclaimers
**Purpose**: Inform users of legal responsibilities and limitations

**First-Run Disclaimer** (shown once):
```
═══════════════════════════════════════════════════════
   MUCACHE PDF DOWNLOAD - TERMS OF USE
═══════════════════════════════════════════════════════

Welcome to Mucache's PDF download feature!

IMPORTANT LEGAL NOTICE:

This feature is designed to help you:
✓ Access open-access academic papers
✓ Download papers you have legal rights to
✓ Utilize institutional subscriptions you're entitled to
✓ Archive papers for personal research
✓ Verify citations and references

YOU ARE RESPONSIBLE FOR:
⚠ Ensuring your use complies with copyright laws
⚠ Respecting publisher terms of service
⚠ Following institutional access policies
⚠ Using downloaded materials legally

PROHIBITED USES:
✗ Mass downloading for redistribution
✗ Circumventing paywalls you don't have rights to bypass
✗ Sharing copyrighted materials without permission
✗ Commercial use of downloaded materials
✗ Violating institutional policies

Mucache developers:
• Do NOT encourage copyright infringement
• Provide this tool for legitimate research only
• Are NOT liable for your use of this feature
• Log usage for accountability

By clicking "I Understand and Agree", you acknowledge
that you have read and will comply with these terms.

        [I Understand and Agree]  [Cancel]
═══════════════════════════════════════════════════════
```

**Per-Method Warnings**:

1. **Institutional Access Warning**:
```
⚠ INSTITUTIONAL ACCESS

You are about to access content through your
institutional subscription.

• Ensure you are authorized to use this access
• Follow your institution's acceptable use policy
• Do not share institutional credentials
• Respect usage limits and terms

Your institution may monitor this access.

[Continue]  [Cancel]
```

2. **Alternative Service Warning**:
```
⚠⚠⚠ ALTERNATIVE ACCESS SERVICE ⚠⚠⚠

You are enabling access to third-party services
that may operate in legal gray areas.

RISKS:
• May violate publisher terms of service
• Could breach copyright laws in your jurisdiction
• May expose you to legal action
• Usage will be logged

ONLY enable if:
✓ You have exhausted all legal options
✓ You understand the legal risks
✓ You are in a jurisdiction with different copyright laws
✓ You accept full legal responsibility

Type "I ACCEPT ALL RISKS" to continue:
[_________________________________]

[Cancel]
```

**Implementation**:
```python
class DisclaimerManager:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.disclaimer_file = os.path.join(cache_dir, 'disclaimers_accepted.json')
        self.accepted = self._load_accepted()

    def _load_accepted(self):
        """Load previously accepted disclaimers"""
        if os.path.exists(self.disclaimer_file):
            with open(self.disclaimer_file) as f:
                return json.load(f)
        return {}

    def check_disclaimer(self, disclaimer_type):
        """Check if disclaimer has been accepted"""
        return self.accepted.get(disclaimer_type, False)

    def accept_disclaimer(self, disclaimer_type, user_ip=None):
        """Record disclaimer acceptance"""
        self.accepted[disclaimer_type] = {
            'accepted': True,
            'timestamp': datetime.now().isoformat(),
            'ip_address': user_ip
        }

        with open(self.disclaimer_file, 'w') as f:
            json.dump(self.accepted, f, indent=2)

        logger.info(f"Disclaimer accepted: {disclaimer_type}")

    def require_disclaimer(self, disclaimer_type):
        """Decorator to require disclaimer acceptance"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.check_disclaimer(disclaimer_type):
                    raise Exception(f"Must accept {disclaimer_type} disclaimer first")
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

### 5.2 Access Logging & Accountability
**Purpose**: Maintain audit trail of all PDF access attempts

**Logging Structure**:
```python
class PDFAccessLogger:
    def __init__(self, log_dir):
        self.log_file = os.path.join(log_dir, 'pdf_access.log')
        self.detailed_log = os.path.join(log_dir, 'pdf_access_detailed.json')

    def log_access(self, event_type, url, method, success, error=None, metadata=None):
        """Log PDF access event"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,  # 'download', 'access_attempt', 'method_tried'
            'url': url,
            'method': method,  # 'open_access', 'institutional', 'alternative', etc.
            'success': success,
            'error': error,
            'user_ip': self._get_client_ip(),
            'metadata': metadata or {}
        }

        # Append to JSON log
        with open(self.detailed_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Append to human-readable log
        log_line = f"[{log_entry['timestamp']}] {event_type} - {method} - {url} - {'SUCCESS' if success else 'FAILED'}"
        if error:
            log_line += f" - Error: {error}"

        with open(self.log_file, 'a') as f:
            f.write(log_line + '\n')

        # Also log to main logger
        if success:
            logger.info(log_line)
        else:
            logger.warning(log_line)

    def log_download(self, url, method, success, metadata=None):
        """Log successful download"""
        self.log_access('download', url, method, success, metadata=metadata)

    def log_attempt(self, url, method, success, error=None):
        """Log access attempt"""
        self.log_access('access_attempt', url, method, success, error=error)

    def get_access_summary(self, days=30):
        """Get summary of access patterns"""
        cutoff = datetime.now() - timedelta(days=days)

        summary = {
            'total_downloads': 0,
            'by_method': {},
            'failed_attempts': 0,
            'unique_sources': set()
        }

        with open(self.detailed_log) as f:
            for line in f:
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry['timestamp'])

                if entry_time < cutoff:
                    continue

                if entry['event_type'] == 'download' and entry['success']:
                    summary['total_downloads'] += 1
                    summary['by_method'][entry['method']] = summary['by_method'].get(entry['method'], 0) + 1
                    summary['unique_sources'].add(entry['url'])

                if not entry['success']:
                    summary['failed_attempts'] += 1

        summary['unique_sources'] = len(summary['unique_sources'])

        return summary

    def export_logs(self, start_date=None, end_date=None):
        """Export logs for compliance/audit"""
        # Implementation for exporting filtered logs
        pass
```

**Log Format Examples**:
```
# pdf_access.log (human-readable)
[2024-01-15T10:30:45] download - open_access - https://arxiv.org/pdf/2401.00123.pdf - SUCCESS
[2024-01-15T10:31:12] access_attempt - institutional - https://ieeexplore.ieee.org/document/12345 - FAILED - Error: Session expired
[2024-01-15T10:32:01] download - institutional - https://ieeexplore.ieee.org/document/12345 - SUCCESS
[2024-01-15T11:15:33] download - alternative - https://doi.org/10.1234/example - SUCCESS

# pdf_access_detailed.json (machine-readable)
{"timestamp": "2024-01-15T10:30:45", "event_type": "download", "url": "https://arxiv.org/pdf/2401.00123.pdf", "method": "open_access", "success": true, "user_ip": "192.168.1.100", "metadata": {"title": "Example Paper", "doi": "10.48550/arXiv.2401.00123"}}
```

### 5.3 Ethical Boundaries Configuration
**Purpose**: Allow administrators and users to configure ethical limits

**Configuration Options**:
```json
{
  "ethical_settings": {
    "respect_robots_txt": true,
    "respect_publisher_tos": true,
    "rate_limiting": {
      "enabled": true,
      "max_downloads_per_hour": 20,
      "delay_between_downloads_seconds": 3
    },
    "blocked_domains": [
      "example-pirate-site.com"
    ],
    "allowed_methods": {
      "open_access": true,
      "archive_org": true,
      "institutional": true,
      "alternative": false
    },
    "institutional_mode": {
      "enabled": false,
      "require_justification": true,
      "admin_approval_required": false
    },
    "warning_thresholds": {
      "high_volume_downloads": 50,
      "failed_attempts": 10,
      "alternative_service_usage": 1
    }
  }
}
```

**Implementation**:
```python
class EthicalGuard:
    def __init__(self, settings):
        self.settings = settings['ethical_settings']
        self.download_history = []

    def check_robots_txt(self, url):
        """Check if robots.txt allows access"""
        if not self.settings.get('respect_robots_txt', True):
            return True

        from urllib.robotparser import RobotFileParser

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            return rp.can_fetch('*', url)
        except:
            # If can't read robots.txt, allow
            return True

    def check_rate_limit(self):
        """Enforce rate limiting"""
        if not self.settings['rate_limiting']['enabled']:
            return True

        # Count downloads in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_downloads = [
            d for d in self.download_history
            if d['timestamp'] > one_hour_ago
        ]

        max_downloads = self.settings['rate_limiting']['max_downloads_per_hour']

        if len(recent_downloads) >= max_downloads:
            raise Exception(f"Rate limit exceeded: {max_downloads} downloads per hour")

        return True

    def check_domain_blocked(self, url):
        """Check if domain is blocked"""
        parsed = urlparse(url)
        domain = parsed.netloc

        blocked = self.settings.get('blocked_domains', [])

        if domain in blocked:
            raise Exception(f"Domain {domain} is blocked by policy")

        return True

    def check_method_allowed(self, method):
        """Check if download method is allowed"""
        allowed = self.settings['allowed_methods'].get(method, False)

        if not allowed:
            raise Exception(f"Method {method} is not allowed by policy")

        return True

    def record_download(self, url, method):
        """Record download for rate limiting"""
        self.download_history.append({
            'timestamp': datetime.now(),
            'url': url,
            'method': method
        })

        # Clean old history
        one_day_ago = datetime.now() - timedelta(days=1)
        self.download_history = [
            d for d in self.download_history
            if d['timestamp'] > one_day_ago
        ]

    def check_warnings(self):
        """Check if warning thresholds exceeded"""
        warnings = []

        # Check high volume
        if len(self.download_history) > self.settings['warning_thresholds']['high_volume_downloads']:
            warnings.append("High volume of downloads detected")

        # Check alternative service usage
        alt_usage = len([
            d for d in self.download_history
            if d['method'] == 'alternative'
        ])

        if alt_usage >= self.settings['warning_thresholds']['alternative_service_usage']:
            warnings.append(f"Alternative service used {alt_usage} times")

        return warnings
```

**Admin Dashboard** (optional):
```
Ethical Compliance Dashboard
═════════════════════════════════════════════════════

USAGE STATISTICS (Last 30 Days):
─────────────────────────────────────────────────────
Total Downloads:        245
Open Access:            180 (73%)
Archive.org:             45 (18%)
Institutional:           20 (8%)
Alternative:              0 (0%)

WARNINGS:
─────────────────────────────────────────────────────
⚠ High volume day detected: 2024-01-12 (62 downloads)

SETTINGS:
─────────────────────────────────────────────────────
☑ Respect robots.txt
☑ Rate limiting (20/hour)
☐ Require admin approval
☑ Log all access

[Export Logs]  [Update Settings]
```

---

## Phase 6: API & Backend Endpoints

### 6.1 HTTP Endpoints
**Add to `mucache.py` HTTP request handler**:

```python
# GET Endpoints

def handle_get_pdfs(self):
    """GET /pdfs - Return PDF list"""
    pdfs = self.pdf_manager.get_sorted_pdfs()
    self.send_json_response(pdfs)

def handle_get_pdf_file(self, filename):
    """GET /pdf/[filename] - Serve PDF file"""
    pdf_path = os.path.join(self.cache_dir, 'pdfs', filename)

    if not os.path.exists(pdf_path):
        self.send_error(404, "PDF not found")
        return

    self.send_file_response(pdf_path, 'application/pdf')

def handle_get_pdf_settings(self):
    """GET /pdf_settings - Get PDF download settings"""
    settings = self.settings.get('pdf_download_priority', {})
    self.send_json_response(settings)

def handle_get_pdf_sessions(self):
    """GET /pdf_sessions - Get active sessions"""
    sessions = [
        {
            'session_id': sid,
            'institution': s['institution'],
            'expires_at': s['expires_at'].isoformat()
        }
        for sid, s in self.session_manager.sessions.items()
    ]
    self.send_json_response(sessions)

# POST Endpoints

def handle_post_download_pdf(self):
    """POST /download_pdf - Download single PDF"""
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    data = json.loads(body)

    url = data.get('url')
    session_id = data.get('session_id')

    if not url:
        self.send_error(400, "URL required")
        return

    try:
        # Download PDF
        result = download_pdf_with_priority(
            url,
            self.settings,
            session_id=session_id
        )

        # Add to manager
        self.pdf_manager.add_pdf(result['metadata'])

        # Generate citation and evidence report
        if data.get('generate_citation', True):
            generate_citations(result['metadata'])

        if data.get('generate_evidence', True):
            self.evidence_generator.generate_pdf_evidence_report(result['metadata'])

        self.send_json_response({
            'success': True,
            'metadata': result['metadata']
        })

    except Exception as e:
        logger.error(f"PDF download failed: {e}")
        self.send_json_response({
            'success': False,
            'error': str(e)
        })

def handle_post_batch_download_pdfs(self):
    """POST /batch_download_pdfs - Batch download from file"""
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    data = json.loads(body)

    citation_file = data.get('citation_file')

    try:
        # Start batch download in background
        batch_downloader = BatchDownloader(self.pdf_manager, self.settings)
        citations = batch_downloader.import_citation_file(citation_file)
        batch_downloader.queue_downloads(citations)

        # Start background download
        batch_id = str(uuid.uuid4())
        threading.Thread(
            target=batch_downloader.download_all,
            args=(lambda p, t, title: self.broadcast_progress(batch_id, p, t, title),)
        ).start()

        self.send_json_response({
            'success': True,
            'batch_id': batch_id,
            'queued': len(batch_downloader.queue)
        })

    except Exception as e:
        logger.error(f"Batch download failed: {e}")
        self.send_json_response({
            'success': False,
            'error': str(e)
        })

def handle_post_remove_pdf(self):
    """POST /remove_pdf - Remove PDF"""
    url = self.get_query_param('url')

    try:
        self.pdf_manager.remove_pdf(url)

        self.send_json_response({'success': True})

    except Exception as e:
        logger.error(f"Failed to remove PDF: {e}")
        self.send_json_response({
            'success': False,
            'error': str(e)
        })

def handle_post_pdf_settings(self):
    """POST /pdf_settings - Update PDF settings"""
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    data = json.loads(body)

    # Update settings
    self.settings['pdf_download_priority'] = data.get('priority', [])
    self.settings['pdf_access_methods'] = data.get('methods', {})

    # Save settings
    self.save_settings()

    self.send_json_response({'success': True})

def handle_post_pdf_session_login(self):
    """POST /pdf_session_login - Login to institution"""
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    data = json.loads(body)

    institution_config = data.get('institution')
    credentials = data.get('credentials')

    try:
        session_id = self.session_manager.create_session(
            institution_config,
            credentials
        )

        self.send_json_response({
            'success': True,
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Login failed: {e}")
        self.send_json_response({
            'success': False,
            'error': str(e)
        })

def handle_post_pdf_session_logout(self):
    """POST /pdf_session_logout - Logout session"""
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    data = json.loads(body)

    session_id = data.get('session_id')

    try:
        self.session_manager.destroy_session(session_id)

        self.send_json_response({'success': True})

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        self.send_json_response({
            'success': False,
            'error': str(e)
        })

def handle_post_accept_disclaimer(self):
    """POST /accept_disclaimer - Accept disclaimer"""
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    data = json.loads(body)

    disclaimer_type = data.get('type')

    self.disclaimer_manager.accept_disclaimer(
        disclaimer_type,
        user_ip=self.client_address[0]
    )

    self.send_json_response({'success': True})
```

### 6.2 API Documentation
**Endpoint Summary**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pdfs` | List all PDFs with metadata |
| GET | `/pdf/<filename>` | Serve PDF file |
| GET | `/pdf_settings` | Get PDF download settings |
| GET | `/pdf_sessions` | List active sessions |
| POST | `/download_pdf` | Download single PDF by URL |
| POST | `/batch_download_pdfs` | Start batch download from citation file |
| POST | `/remove_pdf?url=...` | Remove PDF from library |
| POST | `/pdf_settings` | Update PDF download settings |
| POST | `/pdf_session_login` | Login to institutional proxy |
| POST | `/pdf_session_logout` | Logout from session |
| POST | `/accept_disclaimer` | Accept legal disclaimer |

**Example API Calls**:

```javascript
// Download single PDF
fetch('/download_pdf', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    url: 'https://arxiv.org/abs/2401.00123',
    generate_citation: true,
    generate_evidence: true
  })
})

// Login to institution
fetch('/pdf_session_login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    institution: {
      name: 'MIT',
      type: 'ezproxy',
      proxy_url: 'https://libraries.mit.edu/ezproxy'
    },
    credentials: {
      username: 'user@mit.edu',
      password: 'password123'
    }
  })
})

// List PDFs
fetch('/pdfs')
  .then(res => res.json())
  .then(pdfs => console.log(pdfs))
```

---

## Phase 7: Testing & Documentation

### 7.1 Testing Strategy

**Unit Tests**:
```python
# test_pdf_manager.py
def test_add_pdf():
    """Test adding PDF to manager"""

def test_remove_pdf():
    """Test removing PDF"""

def test_get_pdf_by_url():
    """Test retrieval by URL"""

# test_download_methods.py
def test_download_arxiv():
    """Test ArXiv download"""

def test_download_open_access():
    """Test open access download via Unpaywall"""

def test_download_archive_org():
    """Test Wayback Machine download"""

def test_priority_fallback():
    """Test method priority and fallback"""

# test_metadata_extraction.py
def test_extract_doi():
    """Test DOI extraction from URL"""

def test_pdf_metadata_extraction():
    """Test extracting metadata from PDF file"""

def test_crossref_api():
    """Test CrossRef API metadata lookup"""

# test_session_management.py
def test_create_session():
    """Test session creation"""

def test_session_expiration():
    """Test session timeout"""

def test_session_cleanup():
    """Test automatic cleanup"""

# test_batch_download.py
def test_import_bibtex():
    """Test BibTeX import"""

def test_batch_queue():
    """Test batch download queue"""

def test_batch_progress():
    """Test progress reporting"""
```

**Integration Tests**:
```python
# test_full_workflow.py
def test_end_to_end_download():
    """Test complete download workflow"""
    # 1. Download PDF
    # 2. Extract metadata
    # 3. Generate citation
    # 4. Generate evidence report
    # 5. Verify file integrity

def test_institutional_access_flow():
    """Test institutional login and download"""
    # 1. Login
    # 2. Download restricted paper
    # 3. Verify session
    # 4. Logout

def test_batch_import_download():
    """Test batch download from BibTeX"""
    # 1. Import BibTeX
    # 2. Parse citations
    # 3. Queue downloads
    # 4. Execute batch
    # 5. Verify results
```

**Manual Test Cases**:

1. **Open Access Test**:
   - Download ArXiv paper: https://arxiv.org/abs/2301.00001
   - Verify metadata extraction
   - Check citation generation
   - Validate evidence report

2. **Archive.org Test**:
   - Search for paywalled paper in Wayback Machine
   - Download archived version
   - Verify archive date recorded

3. **Institutional Access Test**:
   - Configure EZproxy for test institution
   - Login with test credentials
   - Download restricted paper
   - Verify session timeout

4. **Batch Download Test**:
   - Create test BibTeX with 10 citations
   - Import and parse
   - Start batch download
   - Monitor progress
   - Review success/failure report

5. **UI Test**:
   - Navigate to PDFs tab
   - Add PDF via URL
   - View PDF details
   - Generate citation
   - Download PDF file
   - Remove from library

### 7.2 Diagnostic Tool
**Purpose**: Help users troubleshoot PDF download issues

```python
class PDFDiagnostic:
    def __init__(self):
        self.results = {}

    def run_diagnostics(self, url=None):
        """Run comprehensive diagnostics"""
        print("Running PDF Download Diagnostics...")

        # 1. Check dependencies
        self.check_dependencies()

        # 2. Check network
        self.check_network()

        # 3. Test download methods
        self.test_download_methods(url)

        # 4. Check settings
        self.check_settings()

        # 5. Test metadata APIs
        self.test_metadata_apis()

        # 6. Generate report
        return self.generate_diagnostic_report()

    def check_dependencies(self):
        """Check required packages"""
        required = [
            'requests',
            'PyPDF2',
            'bibtexparser',
            'rispy',
            'browser_cookie3'
        ]

        for package in required:
            try:
                __import__(package)
                self.results[f"dependency_{package}"] = "OK"
            except ImportError:
                self.results[f"dependency_{package}"] = "MISSING"

    def check_network(self):
        """Test network connectivity"""
        test_urls = [
            'https://arxiv.org',
            'https://doi.org',
            'https://api.unpaywall.org',
            'https://archive.org'
        ]

        for url in test_urls:
            try:
                response = requests.head(url, timeout=5)
                self.results[f"network_{url}"] = f"OK ({response.status_code})"
            except Exception as e:
                self.results[f"network_{url}"] = f"FAILED: {e}"

    def test_download_methods(self, url):
        """Test each download method"""
        if not url:
            return

        methods = [
            ('open_access', download_from_open_access),
            ('archive_org', download_from_archive_org)
        ]

        for method_name, method_func in methods:
            try:
                result = method_func(url)
                self.results[f"method_{method_name}"] = "SUCCESS"
            except Exception as e:
                self.results[f"method_{method_name}"] = f"FAILED: {e}"

    def check_settings(self):
        """Validate settings"""
        # Check priority order
        # Check enabled methods
        # Check configurations
        pass

    def test_metadata_apis(self):
        """Test metadata API access"""
        # Test CrossRef
        # Test Unpaywall
        # Test Semantic Scholar
        pass

    def generate_diagnostic_report(self):
        """Generate detailed report"""
        report = """
PDF Download Diagnostics Report
═══════════════════════════════════════════════════════

DEPENDENCIES:
"""
        for key, value in self.results.items():
            if key.startswith('dependency_'):
                package = key.replace('dependency_', '')
                status = "✓" if value == "OK" else "✗"
                report += f"  {status} {package}: {value}\n"

        report += "\nNETWORK CONNECTIVITY:\n"
        for key, value in self.results.items():
            if key.startswith('network_'):
                url = key.replace('network_', '')
                status = "✓" if "OK" in value else "✗"
                report += f"  {status} {url}: {value}\n"

        report += "\nDOWNLOAD METHODS:\n"
        for key, value in self.results.items():
            if key.startswith('method_'):
                method = key.replace('method_', '')
                status = "✓" if value == "SUCCESS" else "✗"
                report += f"  {status} {method}: {value}\n"

        return report
```

### 7.3 Documentation

**README.md Updates**:
```markdown
## PDF Download Feature

Mucache now supports downloading PDF documents from academic publishers,
preprint servers, and archives, with intelligent paywall bypass capabilities.

### Features

- ✅ **Multiple Download Methods**:
  - Open access repositories (ArXiv, PubMed Central, Unpaywall)
  - Internet Archive / Wayback Machine
  - Institutional proxy access (EZproxy, Shibboleth)
  - Configurable alternative services

- ✅ **Smart Metadata Extraction**:
  - DOI resolution via CrossRef API
  - PDF file property extraction
  - Publisher metadata scraping
  - Citation count and influence metrics

- ✅ **Automatic Citation Generation**:
  - APA, MLA, Chicago, Harvard, IEEE, Vancouver
  - BibTeX export
  - Batch citation generation

- ✅ **Legal Evidence Documentation**:
  - File integrity hashing (MD5, SHA1, SHA256)
  - Chain of custody tracking
  - Court-admissible evidence reports

- ✅ **Batch Downloads**:
  - Import from BibTeX, RIS, CSV, EndNote XML
  - Progress tracking
  - Success/failure reporting

### Quick Start

1. **Download a PDF from URL**:
   ```
   Navigate to PDFs tab → Enter URL or DOI → Click Download
   ```

2. **Batch Download from Bibliography**:
   ```
   PDFs tab → Import Citation List → Select .bib file → Start Download
   ```

3. **Access via Institution**:
   ```
   Settings → Login to Institution → Enter credentials → Downloads use proxy
   ```

### Supported Sources

**Open Access**:
- ArXiv.org
- PubMed Central
- bioRxiv / medRxiv
- PLOS, DOAJ, CORE
- Unpaywall aggregator

**Archives**:
- Internet Archive / Wayback Machine

**Institutional**:
- EZproxy
- Shibboleth / OpenAthens
- Custom proxy configurations

### Legal & Ethical Use

⚠️ **Important**: This feature is for legitimate research purposes only.

**Allowed Uses**:
- Accessing papers you have rights to
- Using institutional subscriptions you're entitled to
- Downloading open access publications
- Archiving for personal research

**Prohibited**:
- Mass downloading for redistribution
- Bypassing paywalls without authorization
- Violating publisher terms of service
- Commercial use without permission

All PDF access is logged for accountability.

### Configuration

PDF download settings in `settings.json`:

```json
{
  "pdf_download_priority": [
    "open_access",
    "archive_org",
    "institutional"
  ],
  "pdf_access_methods": {
    "institutional": {
      "enabled": true,
      "proxy_url": "https://proxy.university.edu"
    }
  }
}
```

### Troubleshooting

Run diagnostics:
```python
python mucache.py --diagnose-pdf
```

Common issues:
- **"Session expired"**: Re-login to institution
- **"No open access version found"**: Try Archive.org or institutional access
- **"Rate limit exceeded"**: Wait or adjust settings

### API Reference

See [API.md](docs/API.md) for complete endpoint documentation.

```

**User Guide** (`docs/PDF_USER_GUIDE.md`):
```markdown
# PDF Download User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Download Methods](#download-methods)
3. [Basic Usage](#basic-usage)
4. [Institutional Access](#institutional-access)
5. [Batch Downloads](#batch-downloads)
6. [Citations & Evidence](#citations-evidence)
7. [Troubleshooting](#troubleshooting)

## Introduction

The PDF download feature helps researchers access academic papers through
multiple legitimate channels, with automatic fallback when one method fails.

## Download Methods

### Method 1: Open Access
Searches multiple OA repositories for free versions.

**Sources**:
- ArXiv (preprints)
- PubMed Central (medical research)
- Unpaywall (aggregator)
- CORE, DOAJ

**When to use**: Always try first - respects authors' choice to share openly.

### Method 2: Archive.org
Retrieves archived snapshots from Wayback Machine.

**When to use**: When paper was previously public but is now paywalled.

### Method 3: Institutional Access
Uses your university/organization subscription.

**When to use**: When you have institutional affiliation.

**Setup**:
1. Go to Settings → PDF Access
2. Click "Add Institution"
3. Select institution from list (or enter custom)
4. Choose proxy type (EZproxy, Shibboleth)
5. Enter proxy URL
6. Save

**Login**:
1. Click "Login to Institution"
2. Select institution
3. Enter credentials
4. Session lasts 1 hour (configurable)

## Basic Usage

### Download Single PDF

1. **From URL**:
   - Click PDFs tab
   - Paste URL or DOI in input field
   - Click "Download"
   - Wait for automatic method detection and download

2. **Supported URL formats**:
   - Direct PDF: `https://example.com/paper.pdf`
   - DOI: `https://doi.org/10.1234/example`
   - ArXiv: `https://arxiv.org/abs/2401.00123`
   - Publisher pages: IEEE, Springer, Elsevier, etc.

### View Downloaded PDFs

PDFs appear in grid/list with:
- Thumbnail (first page)
- Title, authors, year
- Publisher, journal
- Access method badge
- Actions (open, cite, remove)

### Open PDF

Click PDF card → Opens in browser PDF viewer
Or: Right-click → "Open with..." for external app

## Institutional Access

### Supported Proxy Types

**EZproxy**:
- Most common
- URL format: `https://proxy.university.edu/login?url=...`

**Shibboleth**:
- Federated authentication
- Multi-step SAML flow

**WAYFless**:
- Direct institutional links
- No separate login needed

### Session Management

- Sessions expire after inactivity (default: 60 minutes)
- View active sessions in top-right menu
- Manual logout clears credentials immediately
- All credentials cleared on app shutdown

### Import Browser Cookies

If already logged into publisher in browser:
1. Settings → PDF Access
2. Click "Import Browser Session"
3. Select browser (Chrome, Firefox, Safari, Edge)
4. Check detected sessions
5. Click "Import"

## Batch Downloads

### From BibTeX

1. Export bibliography from reference manager
2. PDFs tab → "Import Citation List"
3. Choose `.bib` file
4. Review parsed citations
5. Configure options:
   - Skip existing
   - Generate citations
   - Generate evidence reports
6. Click "Start Batch Download"
7. Monitor progress

### From RIS / CSV

Same process as BibTeX - format auto-detected.

**CSV format**:
```csv
title,authors,doi,url,year
"Example Paper","Smith, J.; Doe, A.",10.1234/example,https://doi.org/10.1234/example,2024
```

### Progress Monitoring

Batch download shows:
- Progress bar
- Current paper being downloaded
- Success/failure counts
- Estimated time remaining

### Completion Report

After batch completes:
- Summary statistics
- List of failed downloads with errors
- Export detailed report

## Citations & Evidence

### Automatic Citation Generation

Every downloaded PDF gets citations in all formats:
- APA (7th edition)
- MLA (9th edition)
- Chicago (17th edition)
- Harvard
- IEEE
- Vancouver
- BibTeX

**Access citations**:
1. Click PDF card
2. "Citations" tab
3. Copy desired format
4. Or export all to file

### Evidence Reports

For legal proceedings or formal documentation:

1. Click PDF card
2. "Evidence Report" tab
3. View report with:
   - File integrity hashes
   - Chain of custody
   - Source verification
   - Download metadata
4. Export as PDF or JSON

**What's included**:
- MD5, SHA-1, SHA-256 hashes
- Download timestamp and method
- Source URL and accessibility check
- DOI verification
- Publisher verification
- Archive.org snapshot (if available)

## Troubleshooting

### "No PDF found at URL"

**Cause**: URL doesn't lead to PDF
**Solution**:
- Check URL is correct
- Try publisher page URL instead of direct PDF
- Use DOI if available

### "All download methods failed"

**Cause**: Paper not available through any method
**Solution**:
- Verify paper exists (check DOI)
- Try directly on publisher site (may need purchase)
- Request via interlibrary loan
- Contact authors directly

### "Session expired"

**Cause**: Institutional session timed out
**Solution**: Re-login to institution

### "Rate limit exceeded"

**Cause**: Too many downloads in short time
**Solution**:
- Wait for rate limit window to pass
- Adjust settings: increase delay between downloads
- Contact administrator about increasing limits

### "Institutional login failed"

**Cause**: Wrong credentials or proxy configuration
**Solution**:
- Verify credentials with IT department
- Check proxy URL is correct
- Try "Import Browser Session" if logged in via browser
- Contact support with diagnostic log

### Run Diagnostics

For detailed troubleshooting:
```
Settings → Diagnostics → Run PDF Diagnostics
```

Checks:
- Required packages installed
- Network connectivity to services
- Download methods functioning
- API access
- Configuration validity

Export diagnostic report to share with support.

```

---

## Dependencies

**New packages to add**:

```bash
pip install PyPDF2          # PDF file manipulation
pip install pdfplumber      # Alternative PDF parser
pip install bibtexparser    # BibTeX parsing
pip install rispy           # RIS citation parsing
pip install browser-cookie3 # Browser cookie import
pip install scholarly       # Google Scholar metadata (optional)
```

**Already available** (from existing Mucache):
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `playwright` - Browser automation

---

## File Structure

**New directories and files**:

```
mucache/
├── pdf_manager.py                 # NEW: PDF management
├── pdf_download.py                # NEW: Download methods
├── pdf_metadata.py                # NEW: Metadata extraction
├── session_manager.py             # NEW: Authentication sessions
├── batch_downloader.py            # NEW: Batch downloads
├── ethical_guard.py               # NEW: Ethical safeguards
├── disclaimer_manager.py          # NEW: Legal disclaimers
├── pdf_access_logger.py           # NEW: Access logging
├── citation_generator.py          # EXISTING: Extended for PDFs
├── evidence_generator.py          # EXISTING: Extended for PDFs
├── diagnostic.py                  # EXISTING: Extended with PDF diagnostics
├── mucache.py                     # EXISTING: Extended with PDF endpoints
├── player.html                    # EXISTING: Extended with PDF UI
└── ~/Downloads/mucache/data/
    ├── pdfs/
    │   ├── *.pdf                  # Downloaded PDF files
    │   └── pdfs.json              # PDF metadata
    ├── citations/                 # EXISTING: Extended for PDFs
    ├── evidence_reports/          # EXISTING: Extended for PDFs
    ├── logs/
    │   ├── pdf_access.log         # NEW: PDF access log
    │   └── alternative_access.log # NEW: Alternative service log
    ├── settings.json              # EXISTING: Extended with PDF settings
    └── disclaimers_accepted.json  # NEW: Disclaimer acceptance records
```

---

## Implementation Timeline

**Total estimated time**: 15-20 days

### Week 1: Foundation & Core Features
- **Days 1-2**: Phase 1 - Core infrastructure (PDFManager, metadata extraction)
- **Days 3-4**: Phase 2.2 - Archive.org method + Phase 2.4 - Open access
- **Day 5**: Phase 1.3 - Basic UI implementation

### Week 2: Advanced Features
- **Days 6-7**: Phase 3 - Session management & authentication
- **Days 8-9**: Phase 2.3 - Institutional access + Phase 2.1 - Priority system
- **Day 10**: Phase 4.1-4.2 - Citation & evidence integration

### Week 3: Batch, Safety & Polish
- **Days 11-12**: Phase 4.3 - Batch downloads
- **Day 13**: Phase 5 - Legal/ethical safeguards
- **Day 14**: Phase 2.5 - Alternative services (with disclaimers)
- **Days 15-16**: Phase 6 - Complete API endpoints

### Week 4: Testing & Launch
- **Days 17-18**: Phase 7.1 - Testing (unit, integration, manual)
- **Day 19**: Phase 7.2 - Diagnostic tool + Phase 7.3 - Documentation
- **Day 20**: Final testing, bug fixes, polish

---

## Success Metrics

**Functionality**:
- ✅ Can download from at least 3 major publishers via open access
- ✅ Archive.org fallback works for 90%+ of archived papers
- ✅ Institutional access works with at least 2 proxy types
- ✅ Batch download handles 100+ citations without errors
- ✅ Citation generation accuracy >95%

**User Experience**:
- ✅ Average download time <30 seconds
- ✅ UI responsive during batch downloads
- ✅ Clear error messages for failures
- ✅ Session management transparent to user

**Legal/Ethical**:
- ✅ All disclaimers required before restricted features
- ✅ 100% of access attempts logged
- ✅ No credentials stored on disk
- ✅ Rate limiting enforced

**Quality**:
- ✅ Test coverage >80%
- ✅ No critical bugs in production
- ✅ Documentation complete and accurate
- ✅ Diagnostics tool catches common issues

---

## Future Enhancements (Post-Launch)

**Phase 8: Advanced Features** (optional):
1. **Machine Learning**:
   - Predict best download method for given URL
   - Auto-tag papers by topic
   - Recommend related papers

2. **Collaboration**:
   - Shared libraries
   - Team annotations
   - Citation network visualization

3. **Integration**:
   - Zotero/Mendeley sync
   - LaTeX bibliography integration
   - Cloud backup

4. **Enhanced Metadata**:
   - Full-text search within PDFs
   - Figure/table extraction
   - Reference linking

5. **Mobile App**:
   - iOS/Android app
   - Offline reading
   - Sync with desktop

---

## Notes & Considerations

**Security**:
- Never log passwords (only log success/failure of login attempts)
- Use HTTPS for all external requests
- Sanitize all user inputs
- Implement CSRF protection for POST endpoints

**Performance**:
- Async downloads for responsiveness
- Lazy loading for large PDF lists
- Thumbnail caching
- Metadata caching (don't re-fetch from APIs)

**Accessibility**:
- Keyboard navigation for all UI
- Screen reader support
- High contrast mode
- ARIA labels

**Internationalization**:
- Support non-English papers
- Unicode handling for authors/titles
- Multiple date formats
- Citation format localization

**Privacy**:
- Clear privacy policy
- User control over logging
- Option to disable access logs
- GDPR compliance (if applicable)

---

## Questions & Decisions Needed

Before starting implementation, decide:

1. **Unpaywall API**: Requires email address - use developer's email or ask user?
2. **Alternative service**: Which service(s) to support by default? Or leave fully user-configurable?
3. **Storage limits**: Maximum PDFs or total size limits?
4. **Admin features**: Need admin panel for institutional deployments?
5. **Telemetry**: Anonymous usage statistics to improve feature?

---

## Conclusion

This roadmap provides a comprehensive plan for adding PDF download capabilities to Mucache, with:
- Multiple legitimate access methods
- Strong legal and ethical safeguards
- Seamless integration with existing features
- Excellent user experience
- Robust error handling and diagnostics

The phased approach allows for iterative development, testing, and refinement, ensuring a high-quality feature that serves researchers' needs while respecting legal and ethical boundaries.

**Ready to begin implementation!**
