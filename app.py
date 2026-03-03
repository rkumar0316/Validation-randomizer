import streamlit as st
import pandas as pd
from randomizer import parse_labels, validate, build_sequence

OPT1 = "Option 1 — 1 Set 3 Lists"
OPT2 = "Option 2 — 3 Sets 3 Lists"
OPT3 = "Option 3 — 1 List"

# --- configuration ---
RUNS = [
    {"id": "OpAD1", "label": "Operator A — Day 1"},
    {"id": "OpAD2", "label": "Operator A — Day 2"},
    {"id": "OpBD1", "label": "Operator B — Day 1"},
]

METHOD_DESCRIPTIONS = {
    OPT1: "One set of NC/PCs → 3 randomized lists (HVLD/VD)",
    OPT2: "Three separate NC/PC sets → three separate randomized lists (HeLD)",
    OPT3: "One NC/PC set → one randomized list (other use cases)",
}
st.set_page_config(
    page_title="Validation Randomized List maker",
    page_icon="🧪",
    layout="centered"
)
st.title("Validation Randomized List Generator")
st.write("Evenly spaces positive controls while keeping negative controls. You can just paste your labels and press the button to have the list generated for you.")

# --- dropdown ---
method = st.selectbox("Test Method", list(METHOD_DESCRIPTIONS.keys()))
st.caption(METHOD_DESCRIPTIONS[method])  # shows the description below the dropdown

# --- session state setup ---
if "results" not in st.session_state:
    st.session_state.results = None

# --- inputs ---
if method == OPT2:
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
    OPT1: "Generate 3 Sequences",
    OPT2: "Generate All Sequences",
    OPT3: "Generate Sequence",
}

if st.button(button_labels[method], type="primary"):
    st.session_state.results = None

    if method == OPT2:
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

    elif method == OPT3:
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
