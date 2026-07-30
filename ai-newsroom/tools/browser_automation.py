"""સામાન્ય બ્રાઉઝર ટેબ ઓટોમેશન — Playwright થી.

ઘણી ટેબ ખોલે, વચ્ચે સ્વિચ કરે, દરેકમાં સ્ક્રોલ/ક્લિક/ફોર્મ-ફિલ કરે.
તમારી પોતાની સાઈટ, ટેસ્ટિંગ કે પ્રોડક્ટિવિટી માટે વાપરો.

ઈન્સ્ટોલ:
    pip install playwright
    playwright install chromium

ચલાવો:
    python browser_automation.py
"""
import logging
import sys

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("browser-bot")


# દરેક ટેબ માટે શું કરવું એની યાદી. તમારી જરૂર મુજબ બદલો.
TASKS = [
    {
        "url": "https://example.com",
        "scroll": True,
        "click": "a",                       # CSS selector (ન હોય તો None)
        "fill": None,                        # (selector, text)
    },
    {
        "url": "https://www.wikipedia.org",
        "scroll": True,
        "click": None,
        "fill": ("input#searchInput", "Gujarat"),
    },
    {
        "url": "https://httpbin.org/forms/post",
        "scroll": False,
        "click": None,
        "fill": ('input[name="custname"]', "Public Daily India"),
    },
]


def do_actions(page, task, idx):
    """એક ટેબમાં ક્રિયાઓ કરે — દરેક ક્રિયા સ્વતંત્ર try માં, એક ફેલ થાય
    તો બાકીની ચાલુ રહે."""
    if task.get("scroll"):
        try:
            page.mouse.wheel(0, 2000)
            log.info("ટેબ %d: સ્ક્રોલ થયું", idx)
        except Exception as e:
            log.warning("ટેબ %d: સ્ક્રોલ ફેલ — %s", idx, e)

    sel = task.get("click")
    if sel:
        try:
            page.click(sel, timeout=5000)
            log.info("ટેબ %d: '%s' પર ક્લિક થયું", idx, sel)
        except PWTimeout:
            log.warning("ટેબ %d: '%s' મળ્યું નહીં (ક્લિક છોડ્યું)", idx, sel)
        except Exception as e:
            log.warning("ટેબ %d: ક્લિક ફેલ — %s", idx, e)

    fill = task.get("fill")
    if fill:
        selector, text = fill
        try:
            page.fill(selector, text, timeout=5000)
            log.info("ટેબ %d: '%s' માં લખ્યું: %s", idx, selector, text)
        except PWTimeout:
            log.warning("ટેબ %d: ફોર્મ ફીલ્ડ '%s' મળ્યું નહીં", idx, selector)
        except Exception as e:
            log.warning("ટેબ %d: ફોર્મ ફિલ ફેલ — %s", idx, e)


def run(tasks, headless=False):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        pages = []

        # 1. દરેક ટાસ્ક માટે નવી ટેબ ખોલો
        for idx, task in enumerate(tasks, 1):
            try:
                page = context.new_page()
                page.goto(task["url"], timeout=30000)
                log.info("ટેબ %d ખૂલી: %s", idx, task["url"])
                pages.append((page, task, idx))
            except Exception as e:
                log.error("ટેબ %d ખોલવામાં ભૂલ (%s): %s",
                          idx, task.get("url"), e)

        # 2. દરેક ટેબ પર સ્વિચ કરી ક્રિયાઓ કરો
        for page, task, idx in pages:
            try:
                page.bring_to_front()          # આ ટેબ પર સ્વિચ
                log.info("── ટેબ %d પર સ્વિચ થયું ──", idx)
                do_actions(page, task, idx)
                page.wait_for_timeout(1000)
            except Exception as e:
                log.error("ટેબ %d પર કામ કરતાં ભૂલ: %s", idx, e)

        log.info("બધી %d ટેબનું કામ પૂરું ✅", len(pages))
        if not headless:
            input("બ્રાઉઝર જોવા માટે ખુલ્લું છે — Enter દબાવો બંધ કરવા... ")
        context.close()
        browser.close()


if __name__ == "__main__":
    headless = "--headless" in sys.argv
    try:
        run(TASKS, headless=headless)
    except KeyboardInterrupt:
        log.info("વપરાશકર્તાએ રોક્યું")
    except Exception as e:
        log.error("ગંભીર ભૂલ: %s", e)
        sys.exit(1)
