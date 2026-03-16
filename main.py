import re
import argparse
from playwright.sync_api import Playwright, sync_playwright, expect
from tqdm import tqdm

parser = argparse.ArgumentParser(description="Scrape Plex API documentation into JSON.")
parser.add_argument("-v", "--verbose", action="store_true", help="Show processing progress messages")
parser.add_argument("-d", "--debug", action="store_true", help="Show all debug output")
args = parser.parse_args()

LOG_LEVEL = 2 if args.debug else (1 if args.verbose else 0)

def verbose(*msg):
    if LOG_LEVEL >= 1:
        print(*msg)

def debug(*msg):
    if LOG_LEVEL >= 2:
        print("[DEBUG]", *msg)


def run(playwright: Playwright) -> None:  # noqa
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://developers.plex.com/docs/accounts-payable-invoices-api")
    page.wait_for_load_state("domcontentloaded")

    # Select iframe and wait for its content to load
    api_selector = "div.list-group > a.list-group-item"
    sidebar_frame = page.frame(url=re.compile(r"https://developers\.plex\.com|docs|accounts-payable-invoices-api"))
    sidebar_frame.locator(api_selector).first.wait_for()
    
    # Extract API link elements from the sidebar
    sidebar_links = sidebar_frame.locator(api_selector)

    api_count = sidebar_links.count()
    verbose(f"Found {api_count} APIs")
    for i in range(api_count):
        debug(f"API {i + 1}: {sidebar_links.nth(i).inner_text().strip()}")

    results = []
    api_bar = tqdm(
        total=api_count - 1,
        desc="APIs Processed",
        unit="api",
        position=0,
        leave=True,
        disable=LOG_LEVEL > 0,
    )

    # Iterate through the API links
    for i in range(api_count - 1): # Last link is Getting Started, which we can skip
        current_api = sidebar_links.nth(i)
        api_name = current_api.inner_text().strip()
        verbose("-" * 75)
        verbose(f"Processing API: {api_name}")

        # Navigate to API page and assert new header matches expected API name
        current_api.click()
        expect(page.locator("div.header").first).to_contain_text(api_name, timeout=5000)

        # Extract API description
        api_description = " ".join(page.locator("div.subHeader p").all_inner_texts()).strip()

        # Extract operation buttons for the current API
        api_operation_buttons = sidebar_frame.locator("div.selected-api-operations-section > a:not(.section-link)")
        op_count = api_operation_buttons.count()
        verbose(f"Found {op_count} operations for API: {api_name}")
        op_bar = tqdm(
            total=op_count,
            desc="API Ops Processed",
            unit="op",
            position=1,
            leave=False,
            disable=LOG_LEVEL > 0,
        )

        api_result = {
            "APIName": api_name,
            "APIDescription": api_description,
            "Operations": []
        }

        # Iterate through API operations
        for j in range(op_count):
            current_operation = api_operation_buttons.nth(j)
            operation_name = current_operation.inner_text().split('\n')[1].strip()
            verbose("-" * 25)
            verbose(f"Processing operation: {operation_name}")
            
            # Navigate to operation page and assert header matches expected operation name
            current_operation.click()
            expect(page.locator("div.header").first).to_contain_text(operation_name, timeout=5000)

            # Extract Method, Description, and URL
            request_details = page.locator("div.api-info-value").all_inner_texts() # First value is method, second is description
            request_method = request_details[0] if len(request_details) > 0 else ""
            request_description = request_details[1] if len(request_details) > 1 else ""
            request_url = page.locator("div.api-info-url").inner_text().strip()
            debug(f"Request method for {operation_name}: {request_method}")
            debug(f"Request description for {operation_name}: {request_description[:40]}...")
            debug(f"Request URL for {operation_name}: {request_url}")

            # Extract URL parameters, if present
            url_parameters_result = []
            url_parameter_rows = page.locator("div.url-params-container tbody tr")
            debug(f"Found {url_parameter_rows.count()} URL parameters for operation: {operation_name}")
            for k in range(url_parameter_rows.count()):
                cells = url_parameter_rows.nth(k).locator("td")
                if cells.count() < 6:
                    continue
                param_name = url_parameter_rows.nth(k).locator("div.name-column").inner_text().split('*')[0].strip()
                param_type = url_parameter_rows.nth(k).locator("div.type-column").inner_text().strip()
                param_format = cells.nth(2).inner_text().strip()
                param_description = url_parameter_rows.nth(k).locator("div.description-column").inner_text().strip()
                param_default = cells.nth(4).inner_text().strip()
                param_required = cells.nth(5).inner_text().strip()

                url_parameters_result.append({
                    "name": param_name,
                    "type": param_type,
                    "format": param_format,
                    "description": param_description,
                    "default": param_default,
                    "required": param_required
                })

            # Extract request parameters, if present
            request_parameters_result = []
            parameter_rows = page.locator("div.request-body-container tbody tr")
            is_request_body = parameter_rows.count() > 0
            if not is_request_body:
                parameter_rows = page.locator("div.query-params-container tbody tr")
            debug(f"Found {parameter_rows.count()} parameters for operation: {operation_name}")
            for k in range(parameter_rows.count()):
                cells = parameter_rows.nth(k).locator("td")

                if is_request_body:
                    param_key = parameter_rows.nth(k).locator("div.key-column").inner_text().split('*')[0].strip()
                    param_type = parameter_rows.nth(k).locator("div.type-column").inner_text().strip()
                    param_format = cells.nth(2).inner_text().strip()
                    param_description = parameter_rows.nth(k).locator("div.description-column").inner_text().strip()
                    param_required = cells.nth(4).inner_text().strip()
                    request_parameters_result.append({
                        "key": param_key,
                        "type": param_type,
                        "format": param_format,
                        "description": param_description,
                        "required": param_required
                    })
                else:
                    param_name = parameter_rows.nth(k).locator("div.name-column").inner_text().split('*')[0].strip()
                    param_type = parameter_rows.nth(k).locator("div.type-column").inner_text().strip()
                    param_format = cells.nth(2).inner_text().strip()
                    param_description = parameter_rows.nth(k).locator("div.description-column").inner_text().strip()
                    param_default = cells.nth(4).inner_text().strip()
                    param_required = cells.nth(5).inner_text().strip()
                    request_parameters_result.append({
                    "name": param_name,
                    "type": param_type,
                    "format": param_format,
                    "description": param_description,
                    "default": param_default,
                    "required": param_required
                })


            # Insert operation details into the result
            api_result["Operations"].append({
                "OperationId": operation_name,
                "Description": request_description,
                "OperationType": request_method,
                "Path": request_url,
                "BaseUrl": request_url.split("/v1", 1)[0] + "/v1" if "/v1" in request_url else request_url,
                "URLParameters": url_parameters_result,
                "RequestParameters": request_parameters_result
            })
            op_bar.update(1)

        op_bar.close()
        api_bar.update(1)

        # Append the API result to the overall results list
        results.append(api_result)

    api_bar.close()

    # Write results to a JSON file
    import json
    with open("plex_api_docs.json", "w") as f:
        json.dump(results, f, indent=4)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)  # LOG_LEVEL is module-level