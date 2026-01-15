import os
import sys
import streamlit as st
import pandas as pd
from openai import OpenAI
import re
from datetime import datetime

# 🛡️ FIX 1: ABSOLUTE PATH LOGIC
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DATA_PATH = os.path.join(BASE_DIR, "data", "processed")
V_PATH = os.path.join(DATA_PATH, "vectors.npy")
M_PATH = os.path.join(DATA_PATH, "metadata.json")

def ensure_logic_fabric():
    if not os.path.exists(V_PATH) or not os.path.exists(M_PATH):
        with st.spinner("🛡️ AETHER_VERITAS: Reconstructing Knowledge Fabric..."):
            try:
                from logic.indexer import AetherIndexer
                os.makedirs(DATA_PATH, exist_ok=True)
                indexer = AetherIndexer()
                indexer.run_indexing_pipeline() 
            except Exception as e:
                st.error(f"Provisioning failed: {e}")

ensure_logic_fabric()

try:
    from logic.resolver import AetherEngine 
except ImportError as e:
    st.error(f"Critical Error: Could not find AetherEngine. {e}")
    st.stop()

api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="AETHER_VERITAS Command", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .audit-card { background: #161B22; border: 1px solid #30363D; border-radius: 12px; padding: 25px; margin-top: 20px; }
    .governed-header { color: #3fb950; font-size: 1.5rem; font-weight: bold; display: flex; align-items: center; gap: 10px; }
    .escalated-header { color: #f85149; font-size: 1.5rem; font-weight: bold; display: flex; align-items: center; gap: 10px; }
    .self-heal-badge { background-color: #1f6feb; color: white; border-radius: 4px; padding: 4px 12px; font-size: 0.85rem; font-weight: bold; margin-bottom: 15px; display: inline-block; }
    .anti-hal-badge { color: #f85149; font-weight: bold; margin-bottom: 10px; border: 1px solid #f85149; padding: 5px; border-radius: 4px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_engine(): return AetherEngine()
engine = load_engine()

if "audit_log" not in st.session_state: st.session_state.audit_log = []

with st.sidebar:
    st.title("⚖️ VERITAS Hub")
    
    # --- ADDED: DOWNLOAD AUDIT LOG FUNCTIONALITY ---
    if st.session_state.audit_log:
        export_df = pd.DataFrame(st.session_state.audit_log)
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Audit Log (CSV)",
            data=csv_data,
            file_name=f"AETHER_VERITAS_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Export audit history for Jira escalation or reporting."
        )

    if st.button("🔄 Force Cloud Resync", use_container_width=True):
        if os.path.exists(V_PATH): os.remove(V_PATH)
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    st.subheader("📈 Governance Metrics")
    escalated = sum(1 for l in st.session_state.audit_log if l['status'] == "ESCALATED")
    governed = sum(1 for l in st.session_state.audit_log if l['status'] == "GOVERNED")
    healed_count = sum(1 for l in st.session_state.audit_log if l.get('healed'))
    
    m1, m2 = st.columns(2)
    m1.metric("Governed", governed)
    m2.metric("Escalated", escalated)
    st.metric("Self-Healed (Global)", healed_count)
    
    st.divider()
    if st.button("Reset Session History", use_container_width=True):
        st.session_state.audit_log = []
        st.rerun()

st.header("🛡️ AETHER_VERITAS: Manuscript Command Center")
tab1, tab2, tab3 = st.tabs(["🚀 Audit Portal", "📖 VERITAS FAQ", "📋 Prompt Library"])

with tab1:
    query = st.text_input("Consulting AETHER layers...", placeholder="Enter query (e.g., 'Safe Driver discount')")
    
    if st.button("Execute Governance Audit", type="primary"):
        with st.spinner("Reconciling XML Layers..."):
            status_code, score, result_payload = engine.get_aether_result(query)
            _, _, global_context = engine.get_aether_result("Global Base Layer Master")
            
            combined_xml = f"PRIMARY_MATCH (Regional): {result_payload['metadata'].get('raw_xml', '')}\n\nGLOBAL_MASTER: {global_context['metadata'].get('raw_xml', '')}"
            ticket_id = f"VRTS-{len(st.session_state.audit_log)+101}"

            # 🛡️ THE IDEAL RESPONSE SYSTEM INSTRUCTIONS
            system_instructions = """
            You are the AETHER_VERITAS Thought Partner. 

            ### THE IDEAL RESPONSE PROTOCOL:
            1. CATEGORY LOCK: If the query is about 'Deductibles', stay strictly in that node. Do NOT mention Seismic, Environmental, or Mileage data.
            2. SIBLING RULE: If a requested value (like 1000) is missing, find the values that DO exist in that same category. Tell me: "I don't see 1000, but I do see the 250 and 500 options available."
            3. TRACEABILITY: If you pull from Global because Regional is blank, you MUST explicitly state you 'self-healed' the audit.
            4. TONE: Professional but natural peer-to-peer conversation. "I've reviewed the manuscripts..." or "I noticed a gap..."
            5. ESCALATION: If missing everywhere, state: "I am escalating a ticket for this data gap."

            End with exactly 'RESULT: GOVERNED' or 'RESULT: DATA GAP DETECTED'.
            """
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_instructions}, 
                          {"role": "user", "content": f"### MANUSCRIPT CONTEXT ###\n{combined_xml}\n\nQuery: {query}"}],
                temperature=0.0
            )
            answer = res.choices[0].message.content
            
            is_gap = "DATA GAP" in answer.upper()
            status = "ESCALATED" if is_gap else "GOVERNED"
            is_healed = "SELF-HEAL" in answer.upper() or "GLOBAL" in answer.upper()

            st.session_state.audit_log.insert(0, {
                "id": ticket_id, "query": query, "status": status, 
                "healed": is_healed, "response": answer
            })
            st.rerun()

    if st.session_state.audit_log:
        log = st.session_state.audit_log[0]
        st.markdown('<div class="audit-card">', unsafe_allow_html=True)
        if log['status'] == "GOVERNED":
            st.markdown(f'<div class="governed-header">✅ GOVERNED | {log["id"]}</div>', unsafe_allow_html=True)
            if log['healed']: st.markdown('<div class="self-heal-badge">🛡️ AETHER: SELF-HEALED</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="escalated-header">🚨 ESCALATED | {log["id"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="anti-hal-badge">🛡️ ANTI-HALLUCINATION: SOURCE DATA ABSENT</div>', unsafe_allow_html=True)
        st.write(log['response'])
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("📖 Understanding AETHER_VERITAS")
    
    st.subheader("🏛️ Architectural Nomenclature")
    st.markdown("""
    * **🛡️ AETHER** (The Scales)
        * *Automated Evidence-based Truth & Holistic Evidence Reconciliation*
        * A specialized **Zero-Trust layer** designed to reconcile local variations against global standards, ensuring mathematical and legal defensibility.
    * **⚖️ VERITAS** (The Truth)
        * *Validated Evidence-based Rating Integrity & Technical Audit System*
        * The **Forensic Audit Engine** that transforms raw XML into a certified, ticket-indexed reality where every insight is an evidence-backed fact.
    """)

    st.divider()

    st.subheader("⚙️ Governance Protocols")
    st.markdown("""
    How the system maintains the integrity of the logic fabric:

    * **🛡️ Self-Healing**: If a regional manuscript is silent, the system inherits logic from the **Global Base Layer**. These tickets are tagged as **Auto-Resolved**.
    * **✅ Governed**: Confirms the audit was resolved using explicit, localized data. No further action is required.
    * **🚨 Escalated**: Triggered when data is absent from all layers. This generates an **Open Jira Ticket** for manual intervention.
    * **🧠 Anti-Hallucination**: A zero-trust protocol ensuring the AI never "guesses"—it is strictly forbidden from using industry knowledge not present in your XML.
    """)

with tab3:
    st.subheader("📋 AETHER_VERITAS Prompt Library")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ✅ Governed & Self-Healing (10)")
        governed_prompts = [
            
            "What is the discount for a safe driver?",
            "How much is the seismic surcharge in California?",
            "What is the liability limit for Uninsured Motorist coverage?",
            "Check for 'Multi-Policy' discount rules.",
            "What is the surcharge for high annual mileage?",
            "What is the deductible for the base policy?",
            "Is there a surcharge for environmental factors?",
            "What are the mandatory forms for CA Low Income Automobile (LIA)?",
            "Calculate the total multiplier for Safe Driver + Multi-Policy.",
            "List all mandatory forms for the California region.",
            "Does the multi-policy factor apply if I have 2 or more links?",
            "What happens if I drive more than 15,000 miles per year?"
        ]
        for p in governed_prompts: st.code(p, language=None)
    with c2:
        st.markdown("#### 🛡️ Anti-Hallucination / Escalation (10)")
        gap_prompts = [
            "What is the surcharge for a 1000 deductible?",
            "Does the policy offer a 'Good Student Discount'?",
            "Check for 'Electric Vehicle' (EV) incentives in the XML.",
            "What is the rate for a 'Ride-Share' endorsement?",
            "Is there a discount for 'Low Income' drivers?",
            "What is the default coverage for personal injury protection?",
            "Does the XML define a 'Solar Panel Damage' rider?",
            "Verify 'Telematics' monitoring discount values.",
            "What is the deductible for 'Classic Car' valuation?",
            "Look for 'Pet Injury Coverage' in the base layer.",
            "Verify the 'Defensive Driving' course discount.",
            "What is the surcharge for 'Salvage Title' vehicles?"
        ]
        for p in gap_prompts: st.code(p, language=None)

if st.session_state.audit_log:
    st.divider()
    st.subheader("📜 Audit History")
    for log in st.session_state.audit_log:
        status_icon = "🟢" if log['status'] == "GOVERNED" else "🔴"
        heal_icon = " 🛡️" if log['healed'] else ""
        with st.expander(f"{status_icon}{heal_icon} {log['id']} | {log['query']}"):
            st.write(log['response'])