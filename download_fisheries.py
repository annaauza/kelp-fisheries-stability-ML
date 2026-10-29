from pathlib import Path
import re
from playwright.sync_api import sync_playwright

years = range(1980, 2026)

areas = [
    "Eureka Area",
    "Fort Bragg Area",
    "Inland Waters Area",
    "Los Angeles Area",
    "Monterey Area",
    "Morro Bay Area",
    "Sacramento Delta Area",
    "San Diego Area",
    "San Francisco Area",
    "Santa Barbara Area",
]

# Files will be saved in the project's downloads folder
download_folder = Path(__file__).resolve().parent / "downloads"
download_folder.mkdir(exist_ok=True)

url = (
    "https://mfde.wildlife.ca.gov/summarize/"
    "CaliforniaCommercialLandings/"
)


def safe_name(name):
    """Make an area name suitable for a Windows filename."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main():
    failed = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        for area in areas:
            for year in years:
                area_name = safe_name(area)
                filename_start = f"landings_{year}_{area_name}"

                # Skip an existing file for this area and year
                if list(download_folder.glob(f"{filename_start}.*")):
                    print(f"Already exists; skipped: {year}, {area}")
                    continue

                print(f"\nDownloading {year}, {area}...", flush=True)

                try:
                    # Open a fresh form
                    page.goto(url, wait_until="domcontentloaded")

                    # Select year
                    page.locator("svg").first.click()
                    page.get_by_text(str(year), exact=True).click()

                    # Select report type
                    page.get_by_text("Select...", exact=True).click()
                    page.locator("#react-select-3-option-2").click()

                    # Open the location dropdown and select the area
                    page.get_by_text("Select...", exact=True).click()
                    area_option = page.locator(
                        '[id^="react-select-4-option-"]'
                    ).filter(
                        has_text=re.compile(
                            "^" + re.escape(area) + "$"
                        )
                    )
                    area_option.click()

                    # Generate report
                    page.get_by_role(
                        "button", name="Generate Report"
                    ).click()

                    # Download the Excel file
                    with page.expect_download(
                        timeout=120_000
                    ) as download_info:
                        page.get_by_role(
                            "button", name="Excel"
                        ).click(timeout=120_000)

                    download = download_info.value
                    extension = Path(download.suggested_filename).suffix
                    file_path = download_folder / (
                        filename_start + extension
                    )

                    download.save_as(file_path)
                    print(f"Saved: {file_path.name}", flush=True)

                except Exception as error:
                    print(f"Problem with {year}, {area}: {error}")
                    failed.append((year, area))

        context.close()
        browser.close()

    print(f"\nFiles are in: {download_folder}")

    if failed:
        print("\nPlease check or retry these downloads:")
        for year, area in failed:
            print(f"  {year}: {area}")
    else:
        print("\nFinished!")


if __name__ == "__main__":
    main()