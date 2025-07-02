# Selenium Captcha Solving Integration

This project integrates two Selenium scripts to handle captcha solving:

- `main.py`: Your main automation script using local Chrome
- `main2.py`: Bright Data script that solves captchas

## How It Works

### 1. Main Script (main.py)

- Runs your main automation tasks using local Chrome
- Detects captchas on the page
- When captcha is found, it:
  - Saves current session state to `session_state.json`
  - Calls `main2.py` to solve the captcha
  - Reads the solution from `captcha_solution.json`
  - Applies the solution and continues

### 2. Bright Data Script (main2.py)

- Uses Bright Data's residential proxies and captcha solving
- Reads session state from `session_state.json`
- Solves captcha automatically
- Saves solution data to `captcha_solution.json`

## Files Created During Process

- `session_state.json`: Current URL and cookies from main.py
- `captcha_solution.json`: Solved captcha data (cookies, final URL)
- `page.png`: Screenshot of the solved page
- `page_source.html`: HTML source for debugging

## Usage

### Normal Operation

```bash
python main.py
```

The script will automatically call main2.py if a captcha is detected.

### Standalone Bright Data Testing

```bash
python main2.py
```

Runs the Bright Data script independently for testing.

### Test Integration

```bash
python test_integration.py
```

Creates test files to simulate the integration.

## Captcha Detection

The system detects captchas by looking for:

- reCAPTCHA elements (`iframe[src*='recaptcha']`)
- Captcha divs (`div[id*='captcha']`)
- Text indicators ("unusual traffic", "verify you're not a robot")

## Solution Transfer

When main2.py solves a captcha, it saves:

- **Cookies**: Session cookies from the solved page
- **Final URL**: The URL after captcha solving
- **User Agent**: Browser user agent string
- **Status**: Success/failure indicator

## Error Handling

- If captcha solving fails, main.py continues anyway
- All errors are logged with descriptive messages
- Debug files are saved for troubleshooting

## Requirements

- Selenium WebDriver
- Chrome/ChromeDriver for main.py
- Bright Data account and credentials for main2.py
- Python 3.7+
