from flask import Flask, render_template, request, jsonify
import re  # Using built-in re module instead of regex
import logging
import os
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
from PIL import Image
import pytesseract
import filetype

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    try:
        text = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return ' '.join(text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return ' '.join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return None

def extract_text_from_image(file_path):
    try:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return None

def extract_financial_entities(text):
    try:
        entities = []
        
        # Enhanced patterns for financial entities
        patterns = {
            'ORG': [
                # Major Banks and Financial Institutions
                r'\b(?:Goldman Sachs|JPMorgan Chase|Morgan Stanley|Bank of America|Citigroup|Wells Fargo|HSBC|Deutsche Bank|UBS|Credit Suisse|Barclays|BNP Paribas|Royal Bank of Scotland|Standard Chartered|Santander|BlackRock|Vanguard|State Street|Fidelity|Charles Schwab|Mastercard|Visa|American Express|Capital One)\b',
                
                # Major Tech Companies
                r'\b(?:Apple|Microsoft|Amazon|Alphabet|Google|Meta|Facebook|Netflix|Tesla|NVIDIA|Intel|AMD|Cisco|Oracle|Salesforce|Adobe|IBM|Dell|HP|Lenovo|Samsung|Sony|LG|Huawei|Xiaomi|Twitter|LinkedIn|PayPal|Square|Stripe|Uber|Lyft|Airbnb|DoorDash)\b',
                
                # Major Industrial and Retail
                r'\b(?:General Electric|Boeing|Lockheed Martin|Raytheon|Northrop Grumman|Ford|General Motors|Toyota|Volkswagen|BMW|Mercedes-Benz|Honda|Hyundai|Walmart|Target|Costco|Home Depot|Lowe\'s|CVS|Walgreens|McDonald\'s|Starbucks|Coca-Cola|PepsiCo|Procter & Gamble|Johnson & Johnson|Pfizer|Merck|Nike|Adidas|Disney|AT&T|Verizon|Comcast|ExxonMobil|Chevron|Shell(?!\s*script)|BP)\b',
                
                # Investment firms and Asset Managers
                r'\b(?:Berkshire Hathaway|KKR|Blackstone|Carlyle Group|Apollo Global|TPG|Bain Capital|Wellington Management|PIMCO|Bridgewater Associates|Renaissance Technologies|Two Sigma|Citadel|Point72|AQR Capital|DE Shaw|Tiger Global|Sequoia Capital|Andreessen Horowitz|Accel Partners)\b',
                
                # Major Indian Companies
                r'\b(?:TCS|Infosys|Wipro|HCL|Tech Mahindra|Reliance Industries|HDFC Bank|ICICI Bank|SBI|Axis Bank|Kotak Mahindra|ITC|Hindustan Unilever|Bharti Airtel|Adani Group|Tata Group|Mahindra & Mahindra|Larsen & Toubro|ONGC|NTPC|Bajaj|Maruti Suzuki)\b',
                
                # Insurance Companies
                r'\b(?:AIG|Allianz|Prudential|MetLife|AXA|Zurich Insurance|Munich Re|Swiss Re|Berkshire Hathaway Insurance|Cigna|Anthem|UnitedHealth|Humana|Aetna|New York Life|Northwestern Mutual|Liberty Mutual|Allstate|State Farm|Progressive)\b',
                
                # Consulting Firms
                r'\b(?:McKinsey|Boston Consulting Group|Bain & Company|Deloitte|PwC|EY|KPMG|Accenture|IBM Consulting|Capgemini|Cognizant|Booz Allen Hamilton|Oliver Wyman)\b',
                
                # Stock exchange related
                r'\b(?:NYSE|NASDAQ|BSE|NSE|LSE|TSE|SSE)(?::[A-Z]{1,10})?\b',
                
                # Add case-sensitive matches for potentially ambiguous terms
                r'\b(?:Shell|NSE|BSE|Target)\b(?!\s+(?:script|file|command|variable|path|directory))',
                
                # Specific company names with proper capitalization and suffixes
                r'\b(?<!(?:the|a|an|this|that|our|your|their|its)\s+)[A-Z][a-zA-Z0-9]+(?:[- ][A-Z][a-zA-Z0-9]+)*(?:\s+(?:Inc|Corp|Corporation|Ltd|Limited|LLC|LLP|AG|SA|NV|PLC))(?![\w\s]*(?:Company|Group|Holdings|Technologies|Tech|Solutions|Industries|Enterprises))\b',
                
                # Company names with specific industry identifiers
                r'\b(?<!(?:the|a|an|this|that|our|your|their|its)\s+)[A-Z][a-zA-Z0-9]+(?:[- ][A-Z][a-zA-Z0-9]+)*\s+(?:Bank|Motors|Airlines|Pharmaceuticals|Electronics|Semiconductor|Software|Systems)(?!\s+(?:Company|Group|Corporation))\b'
            ],
            
            # Exclude common false positives
            'EXCLUDE_PATTERNS': [
                r'\b(?:the|a|an|this|that|our|your|their|its)\s+[Cc]ompany\b',
                r'\bCompany(?:\s+(?:believes|reports|states|announced|said|mentioned|indicated|noted|disclosed|confirmed))',
                r'\b(?:significant portion|summary|updates?|value|liquidity|vacancy)\s+(?:of|on|to)\s+the\s+Company\b',
                r'\bthe\s+Company\'s?\b',
                r'\bCompany\s+(?:background|profile)\b',
                r'\b(?:smaller|larger)\s+(?:reporting\s+)?[Cc]ompany\b',
                r'\bstock\s+[Cc]ompany\b'
            ],
            'MONEY': [
                # Currency with optional magnitude
                r'\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b',
                # Numbers followed by currency indicators
                r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:dollars|USD|EUR|GBP|JPY|INR)\b',
                # Numbers with magnitude followed by currency
                r'\b\d+(?:\.\d+)?\s*(?:million|billion|trillion)\s*(?:dollars|USD|EUR|GBP|JPY|INR)\b'
            ],
            'DATE': [
                r'\b(?:19|20)\d{2}\b',
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s*(?:19|20)\d{2}\b',
                r'\bQ[1-4]\s+(?:19|20)\d{2}\b',
                r'\bFY\d{2}(?:-\d{2})?\b'
            ],
            'PERCENT': [
                r'\b\d+(?:\.\d+)?%\b',
                r'\b(?:increase|decrease|growth|decline)\s+(?:of\s+)?\d+(?:\.\d+)?%\b',
                r'\b(?:up|down|gained|lost|rose|fell)\s+\d+(?:\.\d+)?%\b'
            ],
            'FINANCIAL_METRIC': [
                # Financial Ratios
                r'\b(?:P/E ratio|EPS|ROI|ROE|ROA|CAGR|margin|PAT|PBT|EBITDA|NPM|GPM|OPM|D/E ratio|current ratio|quick ratio|asset turnover)\s*(?:of)?\s*\d+(?:\.\d+)?\b',
                # Market Metrics
                r'\b(?:market cap|market value|valuation|mcap)\s+of\s+\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b',
                # Balance Sheet Items
                r'\b(?:assets|liabilities|equity|debt|cash|inventory|receivables|payables)\s+of\s+\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b'
            ],
            'FINANCIAL_TERM': [
                # Financial Statements
                r'\b(?:balance sheet|income statement|cash flow statement|financial statement|annual report|quarterly report|10-K|10-Q|8-K)\b',
                # Financial Concepts
                r'\b(?:dividend|stock split|merger|acquisition|IPO|public offering|debt offering|bond issue|share buyback|restructuring)\b',
                # Trading Terms
                r'\b(?:bull market|bear market|volatility|liquidity|volume|market maker|bid-ask spread|short selling|margin trading)\b'
            ]
        }
        
        # First, identify text to exclude
        exclude_spans = set()
        for pattern in patterns['EXCLUDE_PATTERNS']:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.span()
                exclude_spans.add((start, end))
        
        # Keep track of used spans to avoid overlapping matches
        used_spans = set()
        
        # Process with regex patterns
        for entity_type, pattern_list in patterns.items():
            if entity_type == 'EXCLUDE_PATTERNS':
                continue
                
            for pattern in pattern_list:
                try:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        start, end = match.span()
                        matched_text = match.group().strip()
                        
                        # Skip if this match overlaps with excluded text
                        if any((start >= s and start < e) or (end > s and end <= e) for s, e in exclude_spans):
                            continue
                        
                        # Check if this span overlaps with any existing spans
                        span_overlaps = any(
                            (start >= s and start < e) or (end > s and end <= e)
                            for s, e in used_spans
                        )
                        
                        # Skip common false positives
                        if re.search(r'\b(?:the|a|an|this|that|our|your|their|its)\s+', matched_text, re.IGNORECASE):
                            continue
                            
                        if not span_overlaps and not any(e['text'].lower() == matched_text.lower() for e in entities):
                            # Additional validation for organization names
                            if entity_type == 'ORG':
                                # Skip if it's a generic company reference
                                if re.search(r'\b(?:the|a|an|this|that|our|your|their|its)\s+company\b', matched_text, re.IGNORECASE):
                                    continue
                                # Skip if it's just "Company" with some context
                                if re.match(r'^Company\s+|^the\s+Company\s*$', matched_text, re.IGNORECASE):
                                    continue
                            
                            entities.append({
                                "text": matched_text,
                                "entity": entity_type,
                                "score": 0.95 if entity_type in ['MONEY', 'PERCENT'] else 0.90
                            })
                            used_spans.add((start, end))
                            
                except re.error as e:
                    logger.error(f"Regex error with pattern {pattern}: {str(e)}")
                    continue
        
        return sorted(entities, key=lambda x: (-x['score'], x['text']))
    
    except Exception as e:
        logger.error(f"Error in extract_financial_entities: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        text = request.json.get('text', '')
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        results = extract_financial_entities(text)
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/analyze_file', methods=['POST'])
def analyze_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not supported"}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Detect file type using filetype
            kind = filetype.guess(file_path)
            if kind is None:
                # If filetype can't detect it, try to handle as text file
                if filename.lower().endswith('.txt'):
                    file_type = 'text/plain'
                elif filename.lower().endswith('.docx'):
                    file_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                else:
                    return jsonify({"error": "Unable to determine file type"}), 400
            else:
                file_type = kind.mime
            
            # Extract text based on file type
            if file_type == 'application/pdf':
                text = extract_text_from_pdf(file_path)
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                text = extract_text_from_docx(file_path)
            elif file_type.startswith('image/'):
                text = extract_text_from_image(file_path)
            elif file_type == 'text/plain':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                return jsonify({"error": "Unsupported file type"}), 400
            
            if text is None:
                return jsonify({"error": "Failed to extract text from file"}), 400
            
            # Process the extracted text
            results = extract_financial_entities(text)
            return jsonify(results)
            
        finally:
            # Clean up: remove the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        logger.error(f"Error in analyze_file endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
