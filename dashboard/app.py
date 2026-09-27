from pathlib import Path
import io
import re
import subprocess

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent.parent
LOCALITY_FILE = ROOT / "locality_run.txt"
LOCALITY_CSV = ROOT / "locality.csv"


st.set_page_config(
    page_title="System Detective",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .stApp {
            background: #0b1220;
            color: #e5e7eb;
        }

        [data-testid="stHeader"] {
            background: #0b1220;
        }

        [data-testid="stSidebar"] {
            background: #101827;
        }

        h1, h2, h3 {
            color: #67e8f9 !important;
        }

        .section-title {
            border-left: 3px solid #22d3ee;
            padding-left: 10px;
            margin-top: 20px;
            margin-bottom: 12px;
            font-weight: 650;
        }

        div[data-testid="stMetric"] {
            background: #111c2f;
            border: 1px solid #24344d;
            border-radius: 10px;
            padding: 10px;
        }

        .stButton > button {
            background: #123047;
            color: #e5e7eb;
            border: 1px solid #22d3ee;
            border-radius: 7px;
        }

        .stButton > button:hover {
            background: #16435e;
            color: white;
            border-color: #67e8f9;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_command(command: str, timeout: int = 20) -> str:
    """Run a Linux command and return its output without inventing fallback data."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"Command failed: {exc}"


def parse_key_value_output(text: str) -> dict:
    values = {}

    for line in text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()

    return values


def read_locality_results() -> pd.DataFrame:
    """
    Read the user's previously measured locality result.
    The benchmark is not rerun on every dashboard refresh.
    """
    for path in (LOCALITY_CSV, LOCALITY_FILE):
        if not path.exists():
            continue

        text = path.read_text(errors="replace").strip()

        if not text:
            continue

        # CSV format:
        # run,row_major_s,col_major_s,ratio
        try:
            df = pd.read_csv(io.StringIO(text))

            normalized = {str(c).strip().lower(): c for c in df.columns}

            run_col = normalized.get("run")
            row_col = next(
                (
                    normalized[c]
                    for c in normalized
                    if "row" in c and "major" in c
                ),
                None,
            )
            col_col = next(
                (
                    normalized[c]
                    for c in normalized
                    if "column" in c and "major" in c
                ),
                None,
            )

            if run_col and row_col and col_col:
                result = pd.DataFrame(
                    {
                        "Run": pd.to_numeric(df[run_col], errors="coerce"),
                        "Row-major (s)": pd.to_numeric(
                            df[row_col], errors="coerce"
                        ),
                        "Column-major (s)": pd.to_numeric(
                            df[col_col], errors="coerce"
                        ),
                    }
                ).dropna()

                if not result.empty:
                    result["Ratio"] = (
                        result["Column-major (s)"]
                        / result["Row-major (s)"]
                    )
                    return result

        except Exception:
            pass

        # Plain-text fallback for locality_run.txt.
        rows = []

        for line in text.splitlines():
            match = re.search(
                r"(?i)"
                r"(?:run\s*)?(\d+)"
                r"\s*[,:\s]+\s*"
                r"([0-9]+\.[0-9]+)"
                r"\s*[,:\s]+\s*"
                r"([0-9]+\.[0-9]+)"
                r"(?:\s*[,:\s]+\s*([0-9]+\.[0-9]+))?",
                line.strip(),
            )

            if not match:
                continue

            run_no = int(match.group(1))
            row_time = float(match.group(2))
            col_time = float(match.group(3))

            rows.append(
                {
                    "Run": run_no,
                    "Row-major (s)": row_time,
                    "Column-major (s)": col_time,
                    "Ratio": col_time / row_time if row_time else None,
                }
            )

        if rows:
            return pd.DataFrame(rows)

        # Single-result fallback.
        match = re.search(
            r"(?is)"
            r"row[- ]major.*?([0-9]+\.[0-9]+).*?"
            r"column[- ]major.*?([0-9]+\.[0-9]+)",
            text,
        )

        if match:
            row_time = float(match.group(1))
            col_time = float(match.group(2))

            return pd.DataFrame(
                [
                    {
                        "Run": 1,
                        "Row-major (s)": row_time,
                        "Column-major (s)": col_time,
                        "Ratio": col_time / row_time if row_time else None,
                    }
                ]
            )

    return pd.DataFrame()


def get_live_data():
    lscpu = run_command("lscpu")
    free = run_command("free -h")

    # Live process table used by the dashboard.
    processes = run_command(
        "ps -eo pid,ppid,stat,%cpu,%mem,etime,comm --sort=-%cpu | head -n 6"
    )

    # Batch mode is used because interactive htop cannot be captured reliably
    # without a terminal. This provides a reproducible top snapshot.
    top = run_command("top -b -n 1 -H | head -n 20")

    # System-call summary.
    strace = run_command(
        "strace -c ls /tmp 2>&1",
        timeout=30,
    )

    locality = read_locality()

    return lscpu, free, processes, top, strace, locality


st.title("System Detective")
st.caption("Computer Organisation & Operating Systems — CIE-1")


if st.button("Refresh system data"):
    st.rerun()


lscpu_text, free_text, process_text, top_text, strace_text, locality = (
    get_live_data()
)


# ---------------------------------------------------------------------
# CPU / ISA
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">CPU and ISA</div>',
    unsafe_allow_html=True,
)

cpu = parse_key_value_output(lscpu_text)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Architecture", cpu.get("Architecture", "N/A"))
c2.metric("Logical CPUs", cpu.get("CPU(s)", "N/A"))
c3.metric("Cores / Socket", cpu.get("Core(s) per socket", "N/A"))
c4.metric("Threads / Core", cpu.get("Thread(s) per core", "N/A"))

c1, c2, c3 = st.columns(3)

c1.metric("CPU model", cpu.get("Model name", "N/A"))
c2.metric("Virtualization", cpu.get("Virtualization", "N/A"))
c3.metric("Address sizes", cpu.get("Address sizes", "N/A"))

with st.expander("Full lscpu output"):
    st.code(lscpu_text, language="text")


# ---------------------------------------------------------------------
# MEMORY
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Memory</div>',
    unsafe_allow_html=True,
)

memory_rows = {}

for line in free_text.splitlines():
    parts = line.split()

    if not parts:
        continue

    if parts[0] == "Mem:" and len(parts) >= 7:
        memory_rows["Mem"] = parts[1:]

    elif parts[0] == "Swap:" and len(parts) >= 4:
        memory_rows["Swap"] = parts[1:]


if "Mem" in memory_rows:
    values = memory_rows["Mem"]

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total", values[0])
    c2.metric("Used", values[1])
    c3.metric("Free", values[2])
    c4.metric("Buff/Cache", values[4])
    c5.metric("Available", values[5])


if "Swap" in memory_rows:
    values = memory_rows["Swap"]

    st.metric(
        "Swap",
        f"{values[0]} total | {values[1]} used | {values[2]} free",
    )


with st.expander("Full free -h output"):
    st.code(free_text, language="text")


# ---------------------------------------------------------------------
# PROCESSES
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Top processes</div>',
    unsafe_allow_html=True,
)

try:
    process_df = pd.read_csv(
        io.StringIO(process_text),
        sep=r"\s+",
        engine="python",
    )

    st.dataframe(
        process_df,
        use_container_width=True,
        hide_index=True,
    )

except Exception:
    st.code(process_text, language="text")


with st.expander("top snapshot"):
    st.code(top_text, language="text")


# ---------------------------------------------------------------------
# STRACE
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">System calls</div>',
    unsafe_allow_html=True,
)

with st.expander("strace -c output", expanded=True):
    st.code(strace_text, language="text")


# ---------------------------------------------------------------------
# LOCALITY
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Locality of reference</div>',
    unsafe_allow_html=True,
)

if locality.empty:
    st.warning(
        "No locality result was found. Run the locality experiment and "
        "save its output in the project root."
    )

else:
    display_df = locality.copy()

    display_df["Ratio"] = display_df["Ratio"].map(
        lambda value: f"{value:.2f}x"
        if pd.notna(value)
        else ""
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    row_mean = locality["Row-major (s)"].mean()
    column_mean = locality["Column-major (s)"].mean()

    ratio = column_mean / row_mean if row_mean else 0

    c1, c2, c3 = st.columns(3)

    c1.metric("Mean row-major", f"{row_mean:.6f} s")
    c2.metric("Mean column-major", f"{column_mean:.6f} s")
    c3.metric("Mean slowdown", f"{ratio:.2f}x")

    chart_df = locality.set_index("Run")[
        ["Row-major (s)", "Column-major (s)"]
    ]

    st.line_chart(chart_df)


# ---------------------------------------------------------------------
# REQUIRED COMMAND OUTPUTS
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Required command outputs</div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "lscpu",
        "free -h",
        "top",
        "ps -eLf",
        "strace -c",
    ]
)

required_outputs = [
    lscpu_text,
    free_text,
    top_text,
    run_command("ps -eLf | head -n 30"),
    strace_text,
]

for tab, output in zip(tabs, required_outputs):
    with tab:
        st.code(output, language="text")
