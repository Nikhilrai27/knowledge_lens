import streamlit as st
from knowledge_lens.cli import run_task

st.set_page_config(page_title="Knowledge Lens", page_icon="🔍", layout="centered")

st.title("🔍 Knowledge Lens")
st.markdown("Multi-agent research system — plans, researches, analyzes, writes, and reviews.")

with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("LLM Provider", ["groq", "gemini"], index=0)
    st.markdown("---")
    st.markdown("**How it works**")
    st.markdown("1. Supervisor decomposes your task")
    st.markdown("2. Researcher gathers facts")
    st.markdown("3. Analyst extracts themes")
    st.markdown("4. Writer produces a document")
    st.markdown("5. Reviewer scores the output")
    st.markdown("---")
    st.caption("Knowledge Lens v1.0")

task = st.text_area(
    "What would you like to research?",
    height=150,
    placeholder="e.g. Explain the difference between transformers and LSTMs",
)

col1, col2 = st.columns([1, 5])
with col1:
    run = st.button("Run", type="primary", use_container_width=True)

if run:
    if not task.strip():
        st.error("Please enter a task.")
        st.stop()

    with st.spinner("Running pipeline..."):
        try:
            result = run_task(task, provider=provider, human_gate=False)
        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.stop()

    doc = result.get("document", "")
    score = result.get("review_score", 0)
    feedback = result.get("review_feedback", "")
    iterations = result.get("iterations", 0)

    st.divider()

    score_color = "🟢" if score >= 7 else ("🟡" if score >= 5 else "🔴")
    col1, col2, col3 = st.columns(3)
    col1.metric("Review Score", f"{score}/10", delta=None)
    col2.metric("Iterations", iterations)
    col3.markdown(f"**Status**  \n{score_color} {'Passed' if score >= 7 else 'Needs work'}")

    if feedback:
        st.info(f"**Review Feedback:** {feedback}")

    if doc:
        st.markdown("### Output")
        st.markdown(doc)
    else:
        st.warning("No document was produced.")
