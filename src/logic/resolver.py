import os
import json
import numpy as np
import lxml.etree as ET
from openai import OpenAI
import streamlit as st

# 🛡️ CLOUD-RESILIENT PATH ANCHOR
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if "logic" in BASE_DIR:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
else:
    PROJECT_ROOT = BASE_DIR

class AetherEngine:
    def __init__(self):
        # 🛡️ Native Secret Handling (HF Secrets)
        api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Absolute Paths for Cloud Stability
        self.data_processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
        self.metadata_path = os.path.join(self.data_processed_dir, "metadata.json")
        self.vectors_path = os.path.join(self.data_processed_dir, "vectors.npy")
        
        # Load logic fabric
        self._load_fabric()

    def _load_fabric(self):
        """Force load the latest indexed data"""
        if os.path.exists(self.metadata_path) and os.path.exists(self.vectors_path):
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
            self.vectors = np.load(self.vectors_path)
        else:
            self.metadata = []
            self.vectors = np.array([])

    def _get_parent_node(self, parent_name):
        """
        🛡️ SENTINEL SELF-HEALING LOOKUP:
        Finds the parent entity in the Global Layer.
        """
        for entry in self.metadata:
            m = entry['metadata']
            region_check = m.get('region', '').upper()
            if m.get('name') == parent_name and "GLOBAL" in region_check:
                return entry
        return None

    def get_aether_result(self, query, threshold=0.25):
        """
        Retrieval logic with Anti-Hallucination & Sentinel Escalation.
        """
        if not hasattr(self, 'metadata') or len(self.metadata) == 0:
            self._load_fabric()
            
        if len(self.metadata) == 0:
            return "ERROR", 0.0, {"metadata": {"raw_xml": "CRITICAL: Knowledge Fabric missing."}}

        resp = self.client.embeddings.create(input=[query], model="text-embedding-3-small")
        q_vec = np.array(resp.data[0].embedding)
        
        # Calculate Similarity
        sims = np.dot(self.vectors, q_vec) / (np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q_vec))
        
        # 🚀 SENTINEL UPGRADE: Multi-Node Retrieval
        # We take the top 3 nodes instead of just 1 to catch combined factors (e.g. SafeDriver + MultiPolicy)
        top_indices = np.argsort(sims)[-3:][::-1]
        best_score = float(sims[top_indices[0]])

        # 🚨 PROJECT SENTINEL: ESCALATION TRIGGER
        if best_score < threshold:
            return "ESCALATED", best_score, {
                "id": "JIRA-PENDING",
                "metadata": {
                    "name": "GAP_DETECTED", 
                    "raw_xml": f"STATUS: Data Gap Found (Confidence: {best_score:.2f}). Triggering Sentinel Escalation."
                }
            }

        # Collect data from relevant top matches
        combined_context = []
        primary_result = self.metadata[top_indices[0]]
        
        for i in top_indices:
            if sims[i] >= threshold:
                node = self.metadata[i]
                m = node['metadata']
                
                # Check for inheritance
                inherits_from = m.get('inheritsFrom')
                source_label = f"[[ SOURCE: {m.get('region', 'Unknown').upper()} Layer ]]"
                
                content = f"{source_label}\nENTITY: {m.get('name')}\nCONTENT:\n{m.get('raw_xml')}\n"
                
                # Self-Heal: If this node has a parent, fetch it too
                if inherits_from:
                    parent = self._get_parent_node(inherits_from)
                    if parent:
                        content = f"[[ SOURCE: GLOBAL_BASE (Self-Healed) ]]\nENTITY: {inherits_from}\nCONTENT:\n{parent['metadata'].get('raw_xml')}\n\n" + content
                
                combined_context.append(content)

        # Merge all found logic into a single manuscript for the LLM
        final_xml = "### PROJECT SENTINEL DATA LINEAGE ###\n\n" + "\n---\n".join(combined_context) + "\n\n### END LINEAGE ###"
        
        result_payload = {
            "id": primary_result["id"],
            "metadata": primary_result["metadata"].copy()
        }
        result_payload['metadata']['raw_xml'] = final_xml

        return "SUCCESS", best_score, result_payload