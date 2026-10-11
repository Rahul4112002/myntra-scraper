# Myntra Style ID Scraper

A small FastAPI web app. Upload an Excel sheet of Myntra Style IDs, watch the
scrape progress live in the browser, and download the results as an Excel file.

> Educational / personal use only. Scraping may violate Myntra's Terms of Service.

## How it works

- **Upload:** an `.xlsx` file with a Style ID column (the first column is used if no column name matches).
- **Scrape:** each product page is fetched with `httpx` (4 at a time) and parsed with BeautifulSoup.
- **Progress:** log lines stream to the page over Server-Sent Events (`/progress`).
- **Result:** an Excel file you download from the page (`/download`).

All progress and results are kept in memory in one process. The app must run as a
**single process with one worker**; with more workers the logs and results get mixed up.

## Run locally

Requires Python 3.12.

```bash
pip install -r requirements.txt
uvicorn app:app --port 8001
```

Open http://localhost:8001.

Run the tests:

```bash
python -m pytest tests
```

## Password protection

The app asks for a username and password (HTTP Basic auth) when the
`APP_PASSWORD` environment variable is set. If it is not set, the app is open to
anyone who has the link.

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `APP_PASSWORD` | No | not set (no login) | Password for the app. Setting it turns the login on. |
| `APP_USERNAME` | No | `admin` | Username for the app. |

To try it locally in PowerShell:

```powershell
$env:APP_PASSWORD = "choose-a-password"
uvicorn app:app --port 8001
```

## Deploy on Render (free)

1. Push this folder to a GitHub repository.
2. On [render.com](https://render.com), choose **New +**, then **Web Service**, and connect the repository.
3. Use these settings:

| Setting | Value |
|---|---|
| Language | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |
| Health Check Path | leave empty |

4. Add these environment variables:

| Variable | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.10` |
| `APP_PASSWORD` | a password of your choice |
| `APP_USERNAME` | a username of your choice (optional, defaults to `admin`) |

5. Choose **Create Web Service**. When the build finishes, Render shows the public link.
6. Test with an Excel file of 3 to 5 Style IDs before running a large batch.

Use the `uvicorn` start command above, not `gunicorn.conf.py`. Leave the Health
Check Path empty: with a password set, every page answers `401` to a request
without a login, and Render would treat that as a failed health check.

## Limits of the Render free tier

- **It sleeps.** After 15 minutes without traffic the service stops, and the next visit takes about a minute to wake it. Keep the browser tab open while a scrape runs.
- **Files are not kept.** Uploads and results are deleted on every restart, redeploy, or sleep. Download the Excel file as soon as the scrape finishes.
- **It is slow.** The free instance has 512 MB of RAM and a fraction of a CPU.
- **Myntra may block it.** Myntra can answer `403` to requests from cloud servers. If every ID shows as failed with `HTTP 403` in the logs, the app is working but Myntra is refusing Render's IP address. Run the app locally instead.
