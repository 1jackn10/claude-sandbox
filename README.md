# claude-sandbox

## baby_names.py
Plots US baby-name popularity by year from public SSA data.

    pip install -r requirements.txt
    python baby_names.py Emma Olivia        # compare names
    python baby_names.py Jack --sex M --save jack.png
    python baby_names.py                    # interactive prompt

Downloads https://www.ssa.gov/oact/babynames/names.zip (1880-present); falls back to a GitHub copy of the SSA data (top 1000/yr, 1880-2008).
