# Algebracket SA Slider Optimizer

This repository contains a Python script (`alge2.py`) that uses **Simulated Annealing** (SA) to optimize slider configurations on the [AlgeBracket](https://algebracket.com) website. The goal is to automatically adjust various slider inputs to maximize a score displayed on the site.

## Features

- **Simulated Annealing:** Automatically searches for optimal slider configurations by iteratively adjusting values.
- **Browser Automation:** Uses Selenium with a headless Chrome browser to interact with the webpage.
- **Multi-Year Evaluation:** Evaluates slider configurations across multiple target years with weighted scores, prioritizing newer years.
- **Parallel Processing:** Runs independent SA processes in parallel for faster computation.
- **Logging:** Outputs detailed logs of SA iterations to `slider_sa_results.csv` and evaluation results across years to `evaluation_across_years1.csv`.

## Prerequisites

- **Python 3.x**
- **Conda** (recommended for managing environments)
- **Google Chrome/Chromium**
- **ChromeDriver:** A version compatible with your Chrome browser must be installed and available in your PATH.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/algebracket-sa-optimizer.git
cd algebracket-sa-optimizer
```

### 2. Set Up the Environment

#### Using Conda (Recommended)
##### Create and activate the environment with:
```bash
conda env create -f environment.yml
conda activate mm_env
```
#### Using requirements.txt with Virtualenv
##### Alternatively, create a virtual environment and install the dependencies:
```bash
python -m venv venv
source venv/bin/activate    # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure ChromeDriver
#### Ensure that ChromeDriver is installed and matches your installed version of Chrome.
#### Verify ChromeDriver Installation
To verify that ChromeDriver is correctly installed, run the following command:

```bash
chromedriver --version
```

Ensure the version matches your installed Chrome browser. If not, download the correct version from [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/).

### 4. Run the Script
Once the environment is set up and ChromeDriver is configured, you can run the script:

```bash
python alge2.py
```

### 5. Output Files
The script generates the following output files:
- `slider_sa_results.csv`: Logs of the Simulated Annealing iterations.
- `evaluation_across_years1.csv`: Evaluation results of slider configurations across multiple years.

## Usage Notes
- **Adjusting Parameters:** You can modify the parameters for Simulated Annealing (e.g., temperature, cooling rate) in the script to fine-tune the optimization process.
- **Headless Mode:** The script uses a headless Chrome browser by default. To disable headless mode for debugging, update the Selenium WebDriver options in the script.

## Troubleshooting
- **ChromeDriver Errors:** Ensure that ChromeDriver is in your PATH and matches your Chrome version.
- **Dependency Issues:** If you encounter issues with dependencies, try recreating the environment using the provided `environment.yml` or `requirements.txt`.
