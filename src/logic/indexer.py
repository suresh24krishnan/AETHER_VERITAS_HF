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

class AetherIndexer:
    def __init__(self):
        # 🛡️ HF Secret Priority
        api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        
        # Absolute paths for data synchronization
        self.data_processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
        self.metadata_path = os.path.join(self.data_processed_dir, "metadata.json")
        self.vectors_path = os.path.join(self.data_processed_dir, "vectors.npy")
        
        # REFINED Semantic Bridge: Strengthening Form & Multi-Factor links
        self.semantic_bridge = {
            "Global_Comprehensive": "Standard Base Policy, Theft, Stolen Vehicle, Fire, Flood, Vandalism, Glass Damage",
            "SafeDriver": "Safe Driver Discount, Clean Record, No Accidents, violation-free multiplier, claimsHistory=0",
            "MultiPolicy": "Multi-policy discount, linking multiple accounts, bundling discount, household bundle, combined insurance, cross-sell credit, multiplier calculation",
            "CA_LIA_Program": "California Low Income Automobile program, state subsidized insurance, LIA Eligibility, Mandatory Forms, Affidavit CA-FRM-LIA, income tiers",
            "CA_FormMasterList": "California mandatory forms, required disclosures, CA-PN-999 Privacy, CA-PROP65 Notice, regional documentation requirements",
            "CA_Comprehensive": "CALIFORNIA ONLY, CA STATE RULES, California Stolen Car, Seismic Surcharge, West Coast Theft",
            "CA_Seismic_Surcharge": "California Earthquake Fee, Seismic Multiplier, Tremor Surcharge, mandatory disaster fee",
            "HighMileage": "15,000 miles, annual mileage limit, driving distance surcharge, high usage penalty, odometer threshold",
            "YouthfulDriver": "under 25, young driver surcharge, teen operator, student driver",
            "Uninsured_Motorist": "protection against drivers without insurance, hit and run liability",
            "Pet_Rider": "domestic animal coverage, dog injury protection, cat rider"
        }

    def chunk_xml(self, file_path, region):
        if not os.path.exists(file_path):
            print(f"❌ Manuscript not found at: {file_path}")
            return []
        
        tree = ET.parse(file_path)
        chunks = []
        
        # 🛠️ FULL SCOPE XPATH: Captures nested RiskFactors and standalone Forms
        query = ".//Coverage | .//Factor | .//RiskFactors/* | .//Governance_Rules | .//FormMasterList | .//Form"
        
        for node in tree.xpath(query):
            # Capture identity: check name, then id, then the tag name itself
            name = node.get('name', node.get('id', node.tag))
            inherits = node.get('inheritsFrom')
            raw_xml = ET.tostring(node, encoding='unicode', pretty_print=True)
            
            # Map technical names to human intent via the bridge
            lookup_key = f"{region}_{name}" if f"{region}_{name}" in self.semantic_bridge else name
            synonyms = self.semantic_bridge.get(lookup_key, "Insurance Logic Component")
            
            # 🛡️ SENTINEL ENHANCEMENT: Explicit meta-tagging for retrieval accuracy
            searchable_text = f"REGION: {region} | ID: {name} | TAG: {node.tag} | INTENT: {synonyms}"
            
            chunks.append({
                "id": f"{region}_{name}_{node.tag}", # Added tag to ID to prevent collisions
                "text": searchable_text, 
                "metadata": {
                    "region": region, 
                    "name": name, 
                    "tag": node.tag,
                    "inheritsFrom": inherits, # Explicitly capture inheritance for Resolver
                    "raw_xml": raw_xml 
                }
            })
        return chunks

    def run_indexing_pipeline(self):
        files_config = {
            "Global": os.path.join(PROJECT_ROOT, "data", "manuscripts", "global_base.xml"), 
            "CA": os.path.join(PROJECT_ROOT, "data", "manuscripts", "ca_overlay.xml")
        }
        
        all_chunks = []
        for region, path in files_config.items():
            print(f"🔎 Ingesting {region} layer...")
            all_chunks.extend(self.chunk_xml(path, region))

        if not all_chunks:
            print("⚠️ No XML logic nodes found. Indexing aborted.")
            return

        # Generate Embeddings
        texts = [c['text'] for c in all_chunks]
        response = self.client.embeddings.create(input=texts, model="text-embedding-3-small")
        vectors = [data.embedding for data in response.data]

        # Save Logic Fabric
        os.makedirs(self.data_processed_dir, exist_ok=True)
        np.save(self.vectors_path, np.array(vectors))
        with open(self.metadata_path, "w") as f:
            json.dump(all_chunks, f, indent=2)
            
        print(f"✅ Indexing Complete. Knowledge Fabric saved to {self.vectors_path}")

if __name__ == "__main__":
    indexer = AetherIndexer()
    indexer.run_indexing_pipeline()