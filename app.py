import json

import streamlit as st

from config import get_groq_api_key
from prompts import generate_action_items, retrieve_context


def main() -> None:
    st.set_page_config(
        page_title="Meeting Notes → Action Items Assistant",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.title("Meeting Notes → Action Items Assistant")
        st.write(
            "Paste raw meeting notes, then generate a structured list of action items "
            "(task, assignee, deadline, priority)."
        )
        if not get_groq_api_key():
            st.warning("GROQ_API_KEY is not set. Add it to a local `.env` file to enable generation.")
        st.divider()
        st.caption("Governance")
        low_conf_threshold = st.slider(
            "Low-confidence threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.05,
        )
        st.divider()
        st.caption("RAG")
        show_context = st.checkbox(
            "Show retrieved context after generation",
            value=False,
            help="Displays TF–IDF chunks from knowledge_base/ used to steer the model.",
        )

    st.title("Meeting Notes → Action Items Assistant")
    st.caption(
        "Generate structured action items, then review, edit, and finalize before use. "
        "See GOVERNANCE.md for when human judgment is required."
    )

    st.subheader("Paste meeting notes")
    notes = st.text_area(
        "Meeting notes",
        placeholder="Paste your notes here (bullets, transcript snippets, Zoom summary, etc.)",
        height=280,
        label_visibility="collapsed",
    )

    generate = st.button("Generate Action Items", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Action Items (results)")

    if not generate:
        st.info("Click **Generate Action Items** to see results here.")
        st.stop()

    if not notes.strip():
        st.warning("Please paste meeting notes first.")
        st.stop()

    with st.spinner("Generating action items..."):
        try:
            result = generate_action_items(notes)
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
            st.stop()

    action_items = result.get("action_items", [])
    if not isinstance(action_items, list):
        st.error("Model output missing `action_items` list. Please try again.")
        st.stop()

    if not action_items:
        st.info("No action items detected.")
        st.stop()

    if show_context:
        ctx = retrieve_context(notes)
        with st.expander("Retrieved context (RAG)", expanded=bool(ctx.strip())):
            if ctx.strip():
                st.code(ctx, language="markdown")
            else:
                st.caption("No chunks scored above the minimum similarity threshold.")

    edited_items: list[dict] = []
    low_conf_count = 0

    st.subheader("Review & edit")
    st.caption(
        "Adjust fields as needed. Check **Reviewed** for every row before finalizing—especially items flagged as low confidence."
    )
    for i, item in enumerate(action_items, start=1):
        conf = float(item.get("confidence", 0.0) or 0.0)
        is_low = conf < low_conf_threshold
        if is_low:
            low_conf_count += 1

        with st.container(border=True):
            cols = st.columns([2, 1, 1, 1])
            cols[0].markdown(f"**Item {i}**")
            cols[1].markdown(f"**Confidence:** {conf:.2f}")
            cols[2].markdown(f"**Priority:** {item.get('priority', '')}")
            if is_low:
                cols[3].warning("Low confidence")
            else:
                cols[3].success("OK")

            task = st.text_input("Task", value=str(item.get("task", "")), key=f"task_{i}")
            assignee = st.text_input(
                "Assignee", value=str(item.get("assignee", "")), key=f"assignee_{i}"
            )
            deadline = st.text_input(
                "Deadline (YYYY-MM-DD or None)",
                value=str(item.get("deadline", "")),
                key=f"deadline_{i}",
            )
            pr = str(item.get("priority", "Medium"))
            if pr not in ["High", "Medium", "Low"]:
                pr = "Medium"
            priority = st.selectbox(
                "Priority",
                options=["High", "Medium", "Low"],
                index=["High", "Medium", "Low"].index(pr),
                key=f"priority_{i}",
            )
            reviewed = st.checkbox(
                "Reviewed",
                value=not is_low,
                key=f"reviewed_{i}",
                help="Low-confidence items must be reviewed before finalizing.",
            )

        edited_items.append(
            {
                "task": task.strip(),
                "assignee": assignee.strip() or "Unassigned",
                "deadline": deadline.strip() or "None",
                "priority": priority,
                "confidence": conf,
                "reviewed": reviewed,
            }
        )

    st.divider()
    st.subheader("Finalize")
    reviewed_ok = all(bool(x.get("reviewed")) for x in edited_items)
    if low_conf_count:
        st.info(f"{low_conf_count} item(s) are below the confidence threshold and require review.")

    acknowledge = st.checkbox("I confirm I manually reviewed the action items.")
    if not (reviewed_ok and acknowledge):
        st.warning("Please review flagged items and confirm manual review to finalize.")
        st.stop()

    final_payload = {
        "action_items": [{k: v for k, v in it.items() if k != "reviewed"} for it in edited_items]
    }
    st.success("Ready to export — copy JSON below or download the file.")
    st.json(final_payload)
    st.download_button(
        label="Download action_items.json",
        data=json.dumps(final_payload, ensure_ascii=False, indent=2),
        file_name="action_items.json",
        mime="application/json",
        type="primary",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
