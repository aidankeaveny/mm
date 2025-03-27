import time
import random
import re
import math
import csv
import os
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------------------------
# Slider configuration (IDs from the webpage)
# -----------------------------------------------
SLIDERS = {
    "Seed": "Seed",
    "Win %": "WP",
    "SoS": "SS",
    "Pts / Gm": "PG",
    "Opp Pts / Gm": "OPG",
    "FG %": "FGP",
    "3Pt FG %": "3PFGP",
    "Free Throw %": "FTP",
    "Offense Rating": "OR",
    "Defense Rating": "DR",
    "Adj. Score Margin": "ASM",
    "Rebound %": "RP",
    "Off. Rebound %": "ORP",
    "Effective FG %": "EFGP",
    "True Shooting %": "TSP",
    "Opp. True Shoot %": "OTSP",
    "Pace": "P",
    "Turnover %": "TP",
    "Opp. Turnover %": "OTP",
    "Turnover Margin": "TM",
    "Assist %": "AP",
    "Assists / Turnover": "AT",
    "FT / FGA": "FTFGA",
    "Opp. FT / FGA": "OFTFGA"
}

# -----------------------------------------------
# Configuration parameters
# -----------------------------------------------
CANDIDATE_VALUES = list(range(0, 11))       # Allowed slider values 0 through 10
NUM_SA_ITERATIONS = 100             # SA iterations per run
INITIAL_TEMP = 10.0                 # Starting temperature for SA
COOLING_RATE = 0.95                 # Temperature decay factor
NUM_SA_RUNS_PER_YEAR = 25            # Number of independent SA runs per target year
BIG_JUMP_PROB = 0.2                 # Probability for a big jump
OUTPUT_CSV = "slider_sa_results.csv"      # Log from SA runs
EVAL_CSV = "evaluation_across_years1.csv"    # Evaluation across years output

# Years to test (must match the dropdown text on the site)
YEARS_TO_TEST = ["2024", "2023", "2022", "2021", "2019", "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011", "2010"]

# Generate weights automatically for each year (newer years weighted more)
def generate_year_weights(years, min_weight=0.3, max_weight=1.0):
    years_int = sorted([int(y) for y in years])
    min_year = min(years_int)
    max_year = max(years_int)
    weights = {}
    for y in years_int:
        if max_year == min_year:
            weights[str(y)] = max_weight
        else:
            weight = min_weight + (y - min_year) / (max_year - min_year) * (max_weight - min_weight)
            weights[str(y)] = weight
    return weights

YEAR_WEIGHTS = generate_year_weights(YEARS_TO_TEST, 0.3, 1.0)
print("Year weights:", YEAR_WEIGHTS)

# -----------------------------------------------
# Utility Functions
# -----------------------------------------------
def state_to_tuple(state):
    """Convert a state (dict) to a sorted tuple so it is hashable."""
    return tuple((k, state[k]) for k in sorted(state.keys()))

# -----------------------------------------------
# Browser & Interaction Helper Functions
# -----------------------------------------------
def init_driver():
    """Initialize a headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def close_popup(driver):
    """Attempt to close the popup (e.g., Mailchimp) if present."""
    selectors = ["button.mc-closeModal"]
    for selector in selectors:
        try:
            popup_close = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            popup_close.click()
            print(f"Popup closed using selector: {selector}")
            return True
        except Exception:
            pass
    print("No popup closed.")
    return False

def set_slider_value(driver, slider_id, value):
    """
    Sets the slider within the div with id=slider_id to the given value.
    Uses an attribute selector to handle IDs that may start with digits.
    """
    try:
        selector = f"div[id='{slider_id}'] input.uk-slider"
        slider = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
            slider, value
        )
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", slider)
        return True
    except Exception as e:
        print(f"Error setting slider {slider_id}: {e}")
        return False

def get_score_num(driver):
    """
    Reads the 'Score' from <h1 id="score"> (displayed like "41/192")
    and returns the numerator (e.g., 41) as an integer.
    Returns None if it cannot be parsed.
    """
    try:
        score_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "score"))
        )
        time.sleep(1.5)  # Allow time for the score to update
        score_text = score_elem.text.strip()
        match = re.match(r"(\d+)\s*/\s*\d+", score_text)
        if match:
            return int(match.group(1))
        try:
            return int(score_text)
        except ValueError:
            return None
    except Exception as e:
        print("Error reading score:", e)
        return None

def click_clear(driver):
    """Clicks the 'Clear' button (id="clear") to reset all sliders."""
    try:
        clear_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "clear"))
        )
        clear_button.click()
        return True
    except Exception as e:
        print("Error clicking clear button:", e)
        return False

def set_year(driver, year):
    """Select the given year from the <select id="year"> dropdown."""
    try:
        year_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "year"))
        )
        select_year = Select(year_dropdown)
        select_year.select_by_visible_text(year)
        time.sleep(1.5)
        print(f"Year {year} selected.")
        return True
    except Exception as e:
        print(f"Error selecting year {year}: {e}")
        return False

def write_results_to_csv(results, output_path):
    """Write results (list of dictionaries) to a CSV file."""
    if not results:
        print("No results to write.")
        return
    fieldnames = list(results[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(results)} rows to {output_path}")

# -----------------------------------------------
# Simulated Annealing Functions
# -----------------------------------------------
def evaluate_state(driver, state):
    """
    Clears sliders, sets them based on the state,
    and returns the score numerator.
    """
    click_clear(driver)
    time.sleep(1)
    for slider_name, value in state.items():
        slider_id = SLIDERS[slider_name]
        set_slider_value(driver, slider_id, value)
    time.sleep(1.5)  # Allow time for recalculation
    return get_score_num(driver)

def random_state():
    """Generate a random state (combination of slider values)."""
    return {slider_name: random.choice(CANDIDATE_VALUES) for slider_name in SLIDERS}

def perturb_state(state, big_jump_prob=None):
    """
    Return a new state by perturbing the current state.
    With probability 'big_jump_prob', perform a big jump by randomly changing two sliders.
    Otherwise, change one slider to a neighboring candidate value.
    """
    if big_jump_prob is None:
        big_jump_prob = BIG_JUMP_PROB
    new_state = state.copy()
    if random.random() < big_jump_prob:
        sliders = list(new_state.keys())
        slider1, slider2 = random.sample(sliders, 2)
        new_state[slider1] = random.choice(CANDIDATE_VALUES)
        new_state[slider2] = random.choice(CANDIDATE_VALUES)
    else:
        slider = random.choice(list(new_state.keys()))
        current_value = new_state[slider]
        possible = sorted(CANDIDATE_VALUES)
        idx = possible.index(current_value)
        if idx == 0:
            new_value = possible[1]
        elif idx == len(possible) - 1:
            new_value = possible[-2]
        else:
            new_value = random.choice([possible[idx - 1], possible[idx + 1]])
        new_state[slider] = new_value
    return new_state

def simulated_annealing(driver, initial_state, initial_temp=INITIAL_TEMP,
                        cooling_rate=COOLING_RATE, num_iterations=NUM_SA_ITERATIONS):
    """
    Runs simulated annealing for a number of iterations.
    Returns the best state, best score, and a log of iterations.
    """
    visited_states = set()
    current_state = initial_state
    visited_states.add(state_to_tuple(current_state))
    current_score = evaluate_state(driver, current_state)
    best_state = current_state
    best_score = current_score
    print(f"Initial state: {current_state}")
    print(f"Initial score: {current_score}")
    sa_log = []
    temp = initial_temp
    for i in range(num_iterations):
        new_state = perturb_state(current_state)
        new_state_tuple = state_to_tuple(new_state)
        while new_state_tuple in visited_states:
            new_state = perturb_state(current_state)
            new_state_tuple = state_to_tuple(new_state)
        visited_states.add(new_state_tuple)
        new_score = evaluate_state(driver, new_state)
        if new_score is None or current_score is None:
            delta = -999
        else:
            delta = new_score - current_score
        if delta > 0 or (temp > 0 and math.exp(delta / temp) > random.random()):
            current_state = new_state
            current_score = new_score
            if new_score is not None and (best_score is None or new_score > best_score):
                best_state = new_state
                best_score = new_score
        sa_log.append({
            "Iteration": i + 1,
            **current_state,
            "Score": current_score,
            "Temperature": temp
        })
        print(f"Iteration {i+1}: current_score = {current_score}, best_score = {best_score}, temp = {temp:.2f}")
        temp *= cooling_rate
    return best_state, best_score, sa_log

# -----------------------------------------------
# Functions for Evaluating States Across Years
# -----------------------------------------------
def evaluate_state_on_year(driver, state, year):
    """
    Applies a given slider state on the specified year.
    Clears sliders, selects the target year, sets sliders, and returns the score numerator.
    """
    set_year(driver, year)
    time.sleep(1)
    click_clear(driver)
    time.sleep(1)
    for slider_name, value in state.items():
        slider_id = SLIDERS[slider_name]
        set_slider_value(driver, slider_id, value)
    time.sleep(1.5)
    return get_score_num(driver)

def evaluate_states_across_years(driver, state, years, year_weights):
    """
    For a given slider state, evaluates the score on each year in 'years'
    and computes a weighted average score (using 'year_weights').
    Returns a dictionary containing the state, the individual year scores, and the weighted score.
    """
    record = state.copy()
    total = 0.0
    total_weight = 0.0
    for year in years:
        score = evaluate_state_on_year(driver, state, year)
        record[f"Score_{year}"] = score
        weight = year_weights.get(year, 1.0)
        total += (score if score is not None else 0) * weight
        total_weight += weight
        print(f"State {state} on year {year} => Score: {score} (Weight: {weight})")
    record["WeightedScore"] = total / total_weight if total_weight else None
    return record

# -----------------------------------------------
# Parallel SA Functions (Per Year)
# -----------------------------------------------
def run_single_sa_for_year(target_year, run_id):
    """
    Runs one simulated annealing process with the target_year set in the driver.
    Returns (target_year, best_state, best_score, sa_log, run_id).
    """
    driver = init_driver()
    driver.get("https://algebracket.com")
    time.sleep(3)
    close_popup(driver)
    if not set_year(driver, target_year):
        print(f"Run {run_id} for year {target_year}: Could not set year.")
    time.sleep(2)
    initial_state = random_state()
    best_state, best_score, sa_log = simulated_annealing(driver, initial_state)
    driver.quit()
    return target_year, best_state, best_score, sa_log, run_id

def run_parallel_sa_for_years(years, runs_per_year):
    """
    For each year in 'years', runs 'runs_per_year' independent SA processes in parallel.
    Returns a list of tuples (target_year, best_state, best_score, sa_log, run_id).
    """
    tasks = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for year in years:
            for run in range(runs_per_year):
                tasks.append(executor.submit(run_single_sa_for_year, year, run))
        results = []
        for future in concurrent.futures.as_completed(tasks):
            results.append(future.result())
    return results

# -----------------------------------------------
# Main Function
# -----------------------------------------------
def main():
    print("Detected CPU cores:", os.cpu_count())
    # Run SA for each target year in parallel
    sa_results = run_parallel_sa_for_years(YEARS_TO_TEST, NUM_SA_RUNS_PER_YEAR)
    combined_log = []
    best_states_by_year = {}
    for target_year, best_state, best_score, sa_log, run_id in sa_results:
        for record in sa_log:
            record["TargetYear"] = target_year
            record["RunID"] = run_id
            combined_log.append(record)
        if target_year not in best_states_by_year or best_score > best_states_by_year[target_year]["Score"]:
            best_states_by_year[target_year] = {"State": best_state, "Score": best_score}
    write_results_to_csv(combined_log, OUTPUT_CSV)
    
    print("\nBest states from SA for each target year:")
    for year, data in best_states_by_year.items():
        print(f"Year {year}: {data['State']} with score {data['Score']}")
    
    # Now evaluate each best state across all years using the weights.
    eval_results = []
    driver = init_driver()
    driver.get("https://algebracket.com")
    time.sleep(3)
    close_popup(driver)
    for target_year, data in best_states_by_year.items():
        state = data["State"]
        print(f"\nEvaluating state from target year {target_year} across all years:")
        eval_record = evaluate_states_across_years(driver, state, YEARS_TO_TEST, YEAR_WEIGHTS)
        eval_record["OptimizedForYear"] = target_year
        eval_results.append(eval_record)
    driver.quit()
    
    write_results_to_csv(eval_results, EVAL_CSV)
    print("\nEvaluation across years completed. Check", EVAL_CSV)

if __name__ == "__main__":
    main()
