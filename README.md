# playwright-doc-fetcher

Scrapes the [Plex Developer API documentation](https://developers.plex.com) and compiles all API endpoints, operations, and parameters into a single `plex_api_docs.json` file.

## Requirements

```bash
pip install playwright tqdm
playwright install
```

## Usage

```bash
# Standard run (progress-bar UI)
python3 main.py

# Verbose output (progress messages)
python3 main.py --verbose
python3 main.py -v

# Debug output (detailed request/parameter and debug logs)
python3 main.py --debug
python3 main.py -d
```

## Output

Produces `plex_api_docs.json` in the project directory with the following shape:

```json
[
  {
    "APIName": "Accounts Payable Invoices API",
    "APIDescription": "...",
    "Operations": [
      {
        "OperationId": "Create AP Invoice",
        "Description": "...",
        "OperationType": "Post",
        "Path": "https://connect.plex.com/accounting/v1/ap-invoices",
        "BaseUrl": "https://connect.plex.com/accounting/v1",
        "URLParameters": [],
        "RequestParameters": []
      }
    ]
  }
]
```
