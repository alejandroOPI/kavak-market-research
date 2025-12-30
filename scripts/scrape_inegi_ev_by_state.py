#!/usr/bin/env python3
"""
Scrape INEGI EV/Hybrid sales by state from interactive tabulado
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_FILE = Path("data/processed/inegi_ev_sales_by_state.json")


def scrape_ev_sales_by_state():
    """Scrape EV/Hybrid sales by state from INEGI interactive tabulado"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to INEGI tabulado...")
        page.goto("https://www.inegi.org.mx/app/tabulados/interactivos/?px=RAIAVL_11&bd=RAIAVL")
        page.wait_for_load_state("networkidle")
        time.sleep(5)

        # Find and click all "Todo" checkboxes by their label text
        print("Selecting all options...")

        # Get all checkbox containers
        # The structure seems to be: checkbox followed by label with "Todo" text
        page.evaluate("""
            () => {
                // Find all labels containing "Todo" and click their associated checkboxes
                const labels = document.querySelectorAll('label');
                labels.forEach(label => {
                    if (label.innerText.trim() === 'Todo') {
                        const checkbox = label.previousElementSibling ||
                                         label.querySelector('input[type="checkbox"]') ||
                                         label.parentElement.querySelector('input[type="checkbox"]');
                        if (checkbox && !checkbox.checked) {
                            checkbox.click();
                        }
                    }
                });
            }
        """)
        time.sleep(2)

        # Alternative: Click by finding checkboxes near "Todo" text
        page.evaluate("""
            () => {
                // Find all elements containing "Todo" text
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                const todoElements = [];
                while (walker.nextNode()) {
                    if (walker.currentNode.textContent.trim() === 'Todo') {
                        todoElements.push(walker.currentNode.parentElement);
                    }
                }

                todoElements.forEach(el => {
                    // Try to find checkbox near this element
                    const parent = el.parentElement;
                    const checkbox = parent.querySelector('input[type="checkbox"]');
                    if (checkbox && !checkbox.checked) {
                        checkbox.click();
                    }
                });
            }
        """)
        time.sleep(2)

        # Take screenshot
        page.screenshot(path="data/outputs/inegi_ev_screenshot_2.png")
        print("Screenshot saved to data/outputs/inegi_ev_screenshot_2.png")

        # Now scroll down to find "Unidades vehiculares" and select its Todo
        page.evaluate("""
            () => {
                window.scrollBy(0, 300);
            }
        """)
        time.sleep(1)

        # Click any remaining Todo checkboxes
        page.evaluate("""
            () => {
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach((cb, idx) => {
                    // Get the label text
                    const label = cb.nextElementSibling || cb.parentElement;
                    if (label && label.innerText && label.innerText.includes('Todo') && !cb.checked) {
                        cb.click();
                    }
                });
            }
        """)
        time.sleep(2)

        # Take another screenshot
        page.screenshot(path="data/outputs/inegi_ev_screenshot_3.png")

        # Try to find and click a generate/consultar button or scroll to see table
        print("Looking for table or download button...")

        # Check if there's a download dropdown
        download_btn = page.locator("button:has-text('Descargar'), [class*='download'], svg[class*='download']").first
        if download_btn:
            try:
                download_btn.click(timeout=5000)
                time.sleep(2)
                page.screenshot(path="data/outputs/inegi_ev_screenshot_download.png")
            except:
                print("Download button not clickable")

        # Try clicking on the download icon area
        page.evaluate("""
            () => {
                // Look for download/export buttons
                const buttons = document.querySelectorAll('button, [role="button"], .btn');
                buttons.forEach(btn => {
                    const text = btn.innerText.toLowerCase();
                    const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                    if (text.includes('descargar') || text.includes('exportar') ||
                        text.includes('csv') || text.includes('excel') ||
                        ariaLabel.includes('download') || ariaLabel.includes('export')) {
                        console.log('Found download button:', btn);
                        btn.click();
                    }
                });
            }
        """)
        time.sleep(2)

        # Scroll down to see if there's a table
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        page.screenshot(path="data/outputs/inegi_ev_screenshot_bottom.png")

        # Try to extract any visible data
        print("Extracting available data...")

        page_data = page.evaluate("""
            () => {
                const result = {
                    selectedYears: [],
                    selectedMonths: [],
                    selectedStates: [],
                    tables: [],
                    divData: []
                };

                // Get selected checkboxes info
                const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
                checkboxes.forEach(cb => {
                    const label = cb.nextElementSibling || cb.parentElement;
                    if (label) {
                        const text = label.innerText.trim();
                        if (text.match(/^20\\d{2}$/)) {
                            result.selectedYears.push(text);
                        } else if (['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'].includes(text)) {
                            result.selectedMonths.push(text);
                        }
                    }
                });

                // Get any table data
                const tables = document.querySelectorAll('table');
                tables.forEach((table, idx) => {
                    const rows = [];
                    table.querySelectorAll('tr').forEach(row => {
                        const cells = [];
                        row.querySelectorAll('td, th').forEach(cell => {
                            cells.push(cell.innerText.trim());
                        });
                        if (cells.length > 0) rows.push(cells);
                    });
                    if (rows.length > 0) result.tables.push(rows);
                });

                // Get any data divs
                const dataDivs = document.querySelectorAll('[class*="data"], [class*="result"], [class*="table"]');
                dataDivs.forEach(div => {
                    if (div.innerText.length > 10 && div.innerText.length < 10000) {
                        result.divData.push({
                            class: div.className,
                            text: div.innerText.substring(0, 1000)
                        });
                    }
                });

                return result;
            }
        """)

        browser.close()

        # Save results
        result = {
            "source": "INEGI RAIAVL",
            "description": "Venta de vehículos híbridos y eléctricos por entidad federativa",
            "url": "https://www.inegi.org.mx/app/tabulados/interactivos/?px=RAIAVL_11&bd=RAIAVL",
            "scraped_data": page_data,
            "note": "Interactive tabulado requires JavaScript. Manual download may be needed."
        }

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {OUTPUT_FILE}")
        print(f"Selected years: {page_data.get('selectedYears', [])}")
        print(f"Selected months: {page_data.get('selectedMonths', [])}")
        print(f"Tables found: {len(page_data.get('tables', []))}")

        return result


if __name__ == "__main__":
    result = scrape_ev_sales_by_state()
