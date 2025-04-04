# Financial Entity Recognition System

A web application that automatically detects and extracts financial information from text, including company names, monetary values, dates, and financial metrics.

## What It Does

✨ Automatically detects:
- 🏢 Organizations (e.g., "Goldman Sachs", "JPMorgan Chase")
- 💰 Money amounts (e.g., "$12.6 billion", "$350")
- 📅 Dates (e.g., "Q3 2023", "FY2022")
- 📊 Percentages (e.g., "15%", "up 12%")
- 📈 Financial Metrics (e.g., "P/E ratio", "EBITDA")
- 📑 Financial Terms (e.g., "balance sheet", "dividend")

## Setup Guide (Windows)

### Step 1: Install Python
1. Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
2. During installation, make sure to check ✅ "Add Python to PATH"

### Step 2: Download the Project
1. Download this project as a ZIP file
2. Extract it to a folder (e.g., `C:\financial_recognition`)
3. Open Command Prompt as administrator

### Step 3: Set Up the Project
Copy and paste these commands into Command Prompt:

```cmd
cd C:\financial_recognition
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## How to Use

1. Start the application:
```cmd
python main.py
```

2. Open your web browser and go to:
```
http://127.0.0.1:5000
```

3. Type or paste your financial text and click "Analyze Text"

## Example Text to Try

Copy and paste this example:
```
In Q1 2024, Morgan Stanley posted a net profit of $11.2 billion with a P/E ratio of 14.8. The firm's market cap rose to $340 billion, marking an 8% year-over-year growth. Their balance sheet recorded total assets of $1.5 trillion, and they declared a quarterly dividend of $2.80 per share while approving a $7 billion stock repurchase plan.
```

## Troubleshooting

### If the application won't start:
1. Check if port 5000 is already in use:
   ```cmd
   netstat -ano | findstr :5000
   ```
   If it shows a process, open Task Manager and end that process

### If you get package errors:
1. Update pip:
   ```cmd
   python -m pip install --upgrade pip
   ```
2. Try installing requirements again:
   ```cmd
   pip install -r requirements.txt
   ```

### If Python is not recognized:
1. Make sure Python is added to PATH
2. Try restarting Command Prompt
3. Use full Python path (typically `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3x\python.exe`)

## Need Help?

If you encounter any issues:
1. Make sure all prerequisites are installed
2. Check if you're using the latest version of Python
3. Try running Command Prompt as administrator
4. Verify all files are in the correct location

## System Requirements

- Windows 10 or 11
- Python 3.8 or higher
- 4GB RAM minimum
- Modern web browser (Chrome, Firefox, Edge)