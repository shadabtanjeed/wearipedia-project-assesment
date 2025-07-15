# wearipedia-project-assesment

This repository contains solutions to seven tasks related to the Wearipedia project assessment. Each task resides in its own directory, accompanied by a README file explaining the task and its solution. For further details, refer to the respective branches.

- **Tasks 0a to 3** were completed by **15th July 2025, 12 PM PST** and are available in the `main` branch.
- **Tasks 4 to 6** are being developed in their respective branches and will not be merged into `main` since they were done outside the designated timeframe (This README will be updated once those tasks are finished.)

## Getting Started

1. **Clone the repository:**
    ```sh
    git clone https://github.com/shadabtanjeed/wearipedia-project-assesment
    cd wearipedia-project-assesment
    ```

2. **Ensure data files are present in `Data/Modified Data`.**

    The following files are **not tracked by git** and must be downloaded manually:

    - `Data/Raw Data/complete_user1_raw.json`
    - `Data/Raw Data/hr_user1_raw.json`
    - `Data/Raw Data/complete_user2_raw.json`
    - `Data/Raw Data/hr_user2_raw.json`

## Downloading the Data Files

You can obtain the required data files using the instructions below, depending on your operating system.

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

Alternatively, you can download the files manually from the following Google Drive folder:  
[Data/Raw Data Folder](https://drive.google.com/drive/folders/1883VBRmFepECPhCCWwYBObX7BW7li8VK?usp=drive_link)

---

For running a specific task, refer to the detailed solution in the corresponding directory's README.
