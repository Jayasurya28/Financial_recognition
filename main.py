from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

def extract_financial_entities(text):
    entities = []
    
    # Enhanced patterns for financial entities
    patterns = {
        'ORG': [
            r'[A-Z][a-zA-Z\s&]+(?:Ltd\.|Limited|Pvt\.|Private|Corporation|Company|Co\.|Group|Holdings|Technologies|Tech|Solutions|Industries|Enterprises)',
            r'(?:BSE|NSE):[A-Z]{1,10}\b',
            r'\b(?:TCS|HDFC|SBI|ICICI|Goldman Sachs|Morgan Stanley|JP Morgan|Bank of America)\b'
        ],
        'MONEY': [
            # Combined pattern for monetary values with context
            r'(?:revenue|profit|loss|earnings|EBITDA|income|debt|assets|liabilities|turnover)\s+of\s+\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b|\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b|\d+(?:,\d{3})*(?:\.\d+)?\s*(?:dollars|USD)\b'
        ],
        'DATE': [
            r'\b(?:19|20)\d{2}\b',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s*(?:19|20)\d{2}',
            r'Q[1-4]\s+(?:19|20)\d{2}'
        ],
        'PERCENT': [
            r'\d+(?:\.\d+)?%',
            r'(?:increase|decrease|growth|decline)\s+(?:of\s+)?\d+(?:\.\d+)?%'
        ],
        'METRIC': [
            r'(?:P/E ratio|EPS|ROI|ROE|ROA|CAGR|margin|PAT|PBT)\s*(?:of)?\s*\d+(?:\.\d+)?',
            r'(?:market cap|market value|valuation)\s+of\s+\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b'
        ]
    }
    
    # Keep track of used spans to avoid overlapping matches
    used_spans = set()
    
    for entity_type, pattern_list in patterns.items():
        for pattern in pattern_list:
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
                    # Extract just the monetary value if it contains "profit of" or similar
                    if 'of $' in matched_text:
                        monetary_value = re.search(r'\$\s*\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?\b', matched_text)
                        if monetary_value:
                            matched_text = monetary_value.group()
                
                if not span_overlaps and not any(e['text'].lower() == matched_text.lower() for e in entities):
                    entities.append({
                        "text": matched_text,
                        "entity": entity_type,
                        "score": 0.95 if entity_type in ['MONEY', 'PERCENT'] else 0.90
                    })
                    used_spans.add((start, end))
    
    return sorted(entities, key=lambda x: x['score'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json.get('text', '')
    results = extract_financial_entities(text)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
