# Task 2
______

This task involves the creation of synthetic data using the provided notebook.

## **Missing Data Patterns for Testing Interpolation and Imputation**  
Structured missing data patterns were implemented to mimic real-world scenarios, rather than simply introducing random missing values.

### Missing Data Modifications
- **Random Missing Values**: Random points are set to `None` (10% by default).
- **Time-of-Day Missing Data**: Data is systematically removed during specific times (e.g., sleeping hours 12am–5am) to simulate device removal during sleep.
- **Consecutive Blocks**: Continuous chunks of missing data (e.g., 1–4 hour blocks) are created to simulate device charging or non-compliance periods.
- **Mixed Patterns**: These patterns are combined to create realistic adherence scenarios.

Such structured patterns provide more meaningful challenges for imputation algorithms than purely random missing values, as they better represent actual usage patterns with temporal structure.

## **Outliers for Testing Detection Algorithms**  
Physiologically plausible outliers were introduced instead of arbitrary extreme values.

### Outlier Modifications
- **Extreme but Plausible Values**: Occasional high heart rate spikes (175–195 bpm) are added, simulating intense exercise or stress.
- **Implausible Values**: Rare sensor errors (30–35 bpm or 250+ bpm) are introduced to represent technical failures.
- **Rapid Change Sequences**: Physiologically unlikely patterns, such as dramatic heart rate changes over short periods (zigzag patterns), are created.
- **SpO2 Outliers**: Occasional low oxygen saturation values (88–92%) are added to indicate possible breathing issues.

These realistic outliers enable detection algorithms to be tested against patterns that may occur in real monitoring scenarios, distinguishing between true physiological events and measurement errors.

## **Health Condition Simulations for Testing Specialized Analytics**  
Specific health conditions were simulated across multiple physiological parameters.

### Health Condition Simulations
- **Sleep Apnea Episodes**: Correlated patterns across multiple sensors were created:
    - Heart rate patterns show characteristic drops followed by compensatory spikes.
    - SpO2 data exhibits periodic desaturations during sleep hours.
    - Breathing rate variations are synchronized with SpO2 drops.
- **Multi-parameter Correlation**: Abnormalities appear consistently across related measurements.
- **Temporal Consistency**: Patterns are placed during physiologically appropriate times (e.g., sleep apnea during night hours).

This multi-parameter simulation allows for the testing of sophisticated analytics that detect clinically meaningful patterns across different physiological signals, providing realistic test cases for condition-specific detection algorithms.

## **Time-based Patterns to Test Circadian Rhythm Detection**  
Realistic daily patterns following natural physiological rhythms were incorporated.

### Circadian Rhythm Patterns
- **Daily Heart Rate Variations**: Patterns follow expected circadian changes:
    - Lower heart rates during deep sleep (0–4am, ~15% below baseline).
    - Gradual increase during morning hours (4–7am).
    - Elevated rates during morning activity (7–10am, ~10% above baseline).
    - Midday stable period (10am–2pm).
    - Afternoon dip (2–5pm, ~5% below baseline).
    - Evening activity period (5–8pm, ~5% above baseline).
    - Evening wind-down (8pm–midnight, gradually decreasing).
- **Activity Correlation**: Realistic variations based on typical daily activities are added.

These circadian patterns allow for the testing of algorithms designed to detect normal physiological rhythms and identify deviations that may indicate health issues or lifestyle factors affecting well-being.

## **Autocorrelated Data for Testing Time-Series Models**  
Time-series dependencies were enhanced to create more realistic physiological signals.

### Time-Series Dependencies
- **Temporal Smoothing**: Smoothing filters are applied to add autocorrelation to heart rate and other metrics.
- **Physiological Constraints**: Changes between consecutive measurements follow physiologically possible rates of change.
- **Random Variation**: Small amounts of Gaussian noise are added to simulate natural variability while maintaining overall patterns.
- **Window-based Processing**: Moving averages with small random deviations are used to create natural-looking time series.

These modifications result in data that better represents the continuous nature of physiological signals, where each measurement is related to previous ones. This provides a more realistic challenge for time-series analysis methods compared to completely independent data points.

Both the original and modified versions of the data are saved in the directories `/Data/Raw Data` and `/Data/Modified Data`.

These modifications were performed to mimic real-world scenarios, enabling visualization of outliers and missing data in subsequent tasks.

A `user_id` field is added to each metric's generated data. Currently, data has been generated for two users.

**Note:**  
The following files are not tracked by git:

- Data/Raw Data/complete_user1_raw.json
- Data/Raw Data/hr_user1_raw.json
- Data/Raw Data/complete_user2_raw.json
- Data/Raw Data/hr_user2_raw.json

## Downloading the Data Files

You can obtain the required data files using the following instructions, depending on your operating system.

### Windows

```powershell
# Create the directory if it doesn't exist
New-Item -Path "Data/Raw Data" -ItemType Directory -Force

# Download the files
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=17JDEIkw29NgXiyFmowiQv9E68_pKWwGc" -OutFile "Data/Raw Data/complete_user1_raw.json"
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1uDgV2LYx8UNOCq-JtgbFg-PYQgUaLde2" -OutFile "Data/Raw Data/hr_user1_raw.json"
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=13VVG80CODeIiH02Mw2ihuFmQWLvHeJ2h" -OutFile "Data/Raw Data/complete_user2_raw.json"
Invoke-WebRequest -Uri "https://drive.google.com/uc?export=download&id=1eFTYoqBpcV1T_4cie8qTZ-LgIsjPpLjd" -OutFile "Data/Raw Data/hr_user2_raw.json"

Write-Host "All data files downloaded successfully!" -ForegroundColor Green
```

### Linux / macOS

```bash
# Create the directory if it doesn't exist
mkdir -p "Data/Raw Data"

# Download the files
curl -L "https://drive.google.com/uc?export=download&id=17JDEIkw29NgXiyFmowiQv9E68_pKWwGc" -o "Data/Raw Data/complete_user1_raw.json"
curl -L "https://drive.google.com/uc?export=download&id=1uDgV2LYx8UNOCq-JtgbFg-PYQgUaLde2" -o "Data/Raw Data/hr_user1_raw.json"
curl -L "https://drive.google.com/uc?export=download&id=13VVG80CODeIiH02Mw2ihuFmQWLvHeJ2h" -o "Data/Raw Data/complete_user2_raw.json"
curl -L "https://drive.google.com/uc?export=download&id=1eFTYoqBpcV1T_4cie8qTZ-LgIsjPpLjd" -o "Data/Raw Data/hr_user2_raw.json"

echo "All data files downloaded successfully!"
```

### Using wget

```bash
# Create the directory if it doesn't exist
mkdir -p "Data/Raw Data"

# Download the files
wget -O "Data/Raw Data/complete_user1_raw.json" "https://drive.google.com/uc?export=download&id=17JDEIkw29NgXiyFmowiQv9E68_pKWwGc"
wget -O "Data/Raw Data/hr_user1_raw.json" "https://drive.google.com/uc?export=download&id=1uDgV2LYx8UNOCq-JtgbFg-PYQgUaLde2"
wget -O "Data/Raw Data/complete_user2_raw.json" "https://drive.google.com/uc?export=download&id=13VVG80CODeIiH02Mw2ihuFmQWLvHeJ2h"
wget -O "Data/Raw Data/hr_user2_raw.json" "https://drive.google.com/uc?export=download&id=1eFTYoqBpcV1T_4cie8qTZ-LgIsjPpLjd"

echo "All data files downloaded successfully!"
```
You can also download the files manually from the links provided in the `Data/Raw Data` directory: https://drive.google.com/drive/folders/1883VBRmFepECPhCCWwYBObX7BW7li8VK?usp=drive_link