import json
import os
from tqdm import tqdm
import numpy as np
import pickle


def populate_skills(file_dir):
    ids, utterances = [], []
    for file in tqdm(os.listdir(file_dir)):
        with open(os.path.join(file_dir, file)) as f:
            data = json.load(f)
            
            # Get utterances and ID information
            skill_id = data["id"]
            utterance = data["sample_utterances"]
            utterances_together = "<###>".join(utterance)
            ids.append(skill_id)
            utterances.append(utterances_together)

    return ids, utterances


def open_csv_skills(file_path):
    ids, utterances = [], []
    with open(file_path) as f:
        for line in f:
            skill_id, utterance_list = line.strip().split(",")
            ids.append(skill_id)
            utterances.append(utterance_list.split("<###>"))
    return ids, utterances


def create_mapping(utterances):
    # Create a mapping from each utterances to skill IDs that have it
    utterance_mapping = {}
    
    for i, utterance in tqdm(enumerate(utterances), total=len(utterances)):
        for u in utterance:
            if u not in utterance_mapping:
                utterance_mapping[u] = []
            utterance_mapping[u].append(i)
    
    # Only care about utterances that appear in more than one skill
    utterance_mapping = {k: v for k, v in utterance_mapping.items() if len(v) > 1}
    
    return utterance_mapping


if __name__ == "__main__":
    # If file exists, read from memory
    if os.path.exists("skills.csv"):
        ids, utterances = open_csv_skills("skills.csv")
    # Otherwise, generate CSV file
    else:
        # Read all files and create one CSV file (for faster i/o)
        ids, utterances = populate_skills("./skill_profiles")

        # Write to CSV file
        with open("skills.csv", "w") as f:
            for id, utterance in zip(ids, utterances):
                f.write(f"{id},{utterance}\n")

    mapping = create_mapping(utterances)

    # Print out utterances and their skill IDs
    for k, v in mapping.items():
        skill_ids = ",".join([ids[x] for x in v])
        print(f"{k} : {skill_ids}")
