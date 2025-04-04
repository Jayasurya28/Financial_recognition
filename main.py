from flask import Flask, render_template, request, jsonify
import re  # Using built-in re module instead of regex
import logging

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
                r'\b(?:General Electric|Boeing|Lockheed Martin|Raytheon|Northrop Grumman|Ford|General Motors|Toyota|Volkswagen|BMW|Mercedes-Benz|Honda|Hyundai|Walmart|Target|Costco|Home Depot|Lowe\'s|CVS|Walgreens|McDonald\'s|Starbucks|Coca-Cola|PepsiCo|Procter & Gamble|Johnson & Johnson|Pfizer|Merck|Nike|Adidas|Disney|AT&T|Verizon|Comcast|ExxonMobil|Chevron|Shell|BP)\b',
                
                # Investment firms and Asset Managers
                r'\b(?:Berkshire Hathaway|KKR|Blackstone|Carlyle Group|Apollo Global|TPG|Bain Capital|Wellington Management|PIMCO|Bridgewater Associates|Renaissance Technologies|Two Sigma|Citadel|Point72|AQR Capital|DE Shaw|Tiger Global|Sequoia Capital|Andreessen Horowitz|Accel Partners)\b',
                
                # Major Indian Companies
                r'\b(?:TCS|Infosys|Wipro|HCL|Tech Mahindra|Reliance Industries|HDFC Bank|ICICI Bank|SBI|Axis Bank|Kotak Mahindra|ITC|Hindustan Unilever|Bharti Airtel|Adani Group|Tata Group|Mahindra & Mahindra|Larsen & Toubro|ONGC|NTPC|Bajaj|Maruti Suzuki)\b',
                
                # Insurance Companies
                r'\b(?:AIG|Allianz|Prudential|MetLife|AXA|Zurich Insurance|Munich Re|Swiss Re|Berkshire Hathaway Insurance|Cigna|Anthem|UnitedHealth|Humana|Aetna|New York Life|Northwestern Mutual|Liberty Mutual|Allstate|State Farm|Progressive)\b',
                
                # Consulting Firms
                r'\b(?:McKinsey|Boston Consulting Group|Bain & Company|Deloitte|PwC|EY|KPMG|Accenture|IBM Consulting|Capgemini|Cognizant|Booz Allen Hamilton|Oliver Wyman)\b',
                
                # Stock exchange related
                r'\b(?:NYSE|NASDAQ|BSE|NSE|LSE|TSE|SSE):[A-Z]{1,10}\b',
                r'\b(?:NYSE|NASDAQ|BSE|NSE|LSE|TSE|SSE)\b',
                
                # General company pattern - with strict rules and common word exclusions
                r'\b(?!(?:The|A|An|This|That|Our|Your|Their|Its)\s+)(?![Cc]ompany\b|[Cc]orporation\b|[Gg]roup\b)[A-Z][a-zA-Z0-9]{2,}(?:[\s-][A-Z][a-zA-Z0-9]{2,})*(?:\s+(?:Ltd|Limited|Pvt|Private|Corporation|Company|Co|Group|Holdings|Technologies|Tech|Solutions|Industries|Enterprises|Inc|Corp|LLC|LLP|AG|SA|NV|PLC)\.?)\b'
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
        
        # Keep track of used spans to avoid overlapping matches
        used_spans = set()
        
        # Process with regex patterns
        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                try:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        start, end = match.span()
                        matched_text = match.group().strip()
                        
                        # Check if this span overlaps with any existing spans
                        span_overlaps = any(
                            (start >= s and start < e) or (end > s and end <= e)
                            for s, e in used_spans
                        )
                        
                        # For MONEY type, clean up the matched text
                        if entity_type == 'MONEY':
                            # Remove any leading text before the actual monetary value
                            if 'of $' in matched_text:
                                monetary_value = re.search(r'\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b', matched_text)
                                if monetary_value:
                                    matched_text = monetary_value.group()
                            # Standardize format
                            matched_text = matched_text.replace(' dollars', ' USD')
                        
                        if not span_overlaps and not any(e['text'].lower() == matched_text.lower() for e in entities):
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

if __name__ == '__main__':
    app.run(debug=True)
