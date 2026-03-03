import streamlit as st
import pandas as pd
from randomizer import parse_labels, validate, build_sequence

# --- configuration ---
RUNS = [
    {"id": "op1day1", "label": "Operator 1 — Day 1"},
    {"id": "op1day2", "label": "Operator 1 — Day 2"},
    {"id": "op2day1", "label": "Operator 2 — Day 1"},
]

METHOD_DESCRIPTIONS = {
    "Option 1 — Poopy Samples": "One NC/PC set → 3 independently randomized sequences",
    "Option 2 — Separate Samples": "Enter a distinct NC/PC set for each run",
    "Option 3 — Single List": "One NC/PC set → one randomized sequence",
}
st.set_page_config(
    page_title="Validation Randomizer",
    page_icon="🧪",
    layout="centered"
)
st.title("Validation Randomized Sequence Generator")
st.write("Evenly spaces positive controls between ordered negative controls")

# --- dropdown ---
method = st.selectbox("Test Method", list(METHOD_DESCRIPTIONS.keys()))
st.caption(METHOD_DESCRIPTIONS[method])  # shows the description below the dropdown

# --- session state setup ---
if "results" not in st.session_state:
    st.session_state.results = None

# --- inputs ---
if method == "Option 2 — Separate Samples":
    # show three separate input cards, one per run
    sets = []
    for run in RUNS:
        st.subheader(run["label"])
        col1, col2 = st.columns(2)
        with col1:
            nc = st.text_area(f"NC labels", height=150, key=f"nc_{run['id']}")
        with col2:
            pc = st.text_area(f"PC labels", height=150, key=f"pc_{run['id']}")
        sets.append({"nc": nc, "pc": pc})

else:
    # options 1 and 3 share a single input
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Negative Controls")
        shared_nc = st.text_area("Paste NC labels", height=200, 
                                  placeholder="NC-1\nNC-2\nNC-3")
    with col2:
        st.subheader("Positive Controls")
        shared_pc = st.text_area("Paste PC labels", height=200, 
                                  placeholder="PC-A\nPC-B\nPC-C")
        
# --- generate button ---
button_labels = {
    "Option 1 — Shared Samples": "Generate 3 Sequences",
    "Option 2 — Separate Samples": "Generate All Sequences",
    "Option 3 — Single List": "Generate Sequence",
}

if st.button(button_labels[method], type="primary"):
    st.session_state.results = None

    if method == "Option 2 — Separate Samples":
        all_results = []
        error_found = False

        for i, run in enumerate(RUNS):
            ncs = parse_labels(sets[i]["nc"])
            pcs = parse_labels(sets[i]["pc"])
            error = validate(ncs, pcs)

            if error:
                st.error(f"{run['label']}: {error}")
                error_found = True
                break

            all_results.append({
                "label": run["label"],
                "items": build_sequence(ncs, pcs)
            })

        if not error_found:
            st.session_state.results = all_results

    elif method == "Option 3 — Single List":
        ncs = parse_labels(shared_nc)
        pcs = parse_labels(shared_pc)
        error = validate(ncs, pcs)

        if error:
            st.error(error)
        else:
            st.session_state.results = [{"label": "Randomized Sequence", 
                                          "items": build_sequence(ncs, pcs)}]

    else:  # Option 1
        ncs = parse_labels(shared_nc)
        pcs = parse_labels(shared_pc)
        error = validate(ncs, pcs)

        if error:
            st.error(error)
        else:
            # same NCs, PCs reshuffled independently for each run
            st.session_state.results = [
                {"label": run["label"], "items": build_sequence(list(ncs), pcs)}
                for run in RUNS
            ]

# --- results ---
if st.session_state.results:
    st.subheader(f"Results — {len(st.session_state.results)} sequence(s)")

    # build one combined dataframe for CSV download
    all_dfs = []

    for result in st.session_state.results:
        st.markdown(f"**{result['label']}**")

        df = pd.DataFrame(result["items"])
        df.index = df.index + 1
        df.columns = ["Label", "Type"]

        # count NCs and PCs for the stats summary
        nc_count = df[df["Type"] == "NC"].shape[0]
        pc_count = df[df["Type"] == "PC"].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df))
        col2.metric("NCs", nc_count)
        col3.metric("PCs", pc_count)

        st.dataframe(df, use_container_width=True)
        all_dfs.append(df.add_prefix(f"{result['label']} — "))

    # single CSV download covering all sequences
    combined = pd.concat(all_dfs, axis=1)
    csv = combined.to_csv().encode("utf-8")
    st.download_button("Download CSV", csv, "controls.csv", "text/csv")
