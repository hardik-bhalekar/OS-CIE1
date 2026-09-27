# OS-CIE1 — System Detective

CIE-1 activity for Computer Organisation & Operating Systems (CO1).

This repository contains the Streamlit dashboard, locality benchmark, captured command output, report, and AI interaction log used for the submission.

## Structure

```text
OS-CIE1/
├── Report.pdf
├── ai_log.pdf
├── README.md
├── dashboard/
│   ├── app.py
│   └── requirements.txt
├── command_outputs/
│   └── README.md
├── locality/
│   ├── locality.c
│   ├── locality_results.csv
│   └── locality_run.txt
└── screenshots/
    └── README.md
```

## Dashboard

The dashboard is a Streamlit application. CPU information is read from `lscpu`, memory from `free -h`, process data from `ps`, a batch `top` snapshot is used in place of interactive `htop`, and `strace -c` is executed for the system-call summary. Locality timings are read from the saved benchmark result so that refreshing the dashboard does not rerun the expensive benchmark.

### Run

```bash
cd dashboard
python3 -m pip install -r requirements.txt
streamlit run app.py
```

The dashboard expects to be run from the repository checkout. It resolves the repository root from the location of `dashboard/app.py`.

## Locality experiment

The benchmark compares row-major and column-major traversal of an 8192 × 8192 two-dimensional array and records three runs.

Compile and run:

```bash
gcc -O2 -o locality locality.c
./locality | tee locality_run.txt
```

The CSV file is the saved measurement used by the dashboard.

## Data policy

Machine-dependent values are measurements from the Linux/WSL environment used for this CIE-1 activity. They are not meant to be treated as generic hardware specifications. Run the commands again during the viva to reproduce live values.
