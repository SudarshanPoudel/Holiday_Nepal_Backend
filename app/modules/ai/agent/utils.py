

def combine_user_pref_and_prompt_json(user_json, prompt_json, include_empty=True, only_pref=False):
    # Base output dict
    output = {
        "no_of_days": prompt_json.get("no_of_days", None),
        "no_of_people": prompt_json.get("no_of_people", 1),
        "estimated_budget_per_day": 0,
        "start_city": prompt_json.get("start_city", prompt_json.get("end_city", user_json.get("city", ""))),
        "end_city": prompt_json.get("end_city", prompt_json.get("start_city", user_json.get("city", ""))),
        "distance_range": "medium",
        "cities": {
            "preferred_type": "",
            "avoid_type": "",
            "must_visit": prompt_json.get("cities", {}).get("must_visit", [])
        },
        "places": {
            "preferred_type": "",
            "avoid_type": "",
            "must_visit": prompt_json.get("places", {}).get("must_visit", [])
        },
        "activities": {
            "preferred_type": "",
            "avoid_type": "",
            "must_do": []
        }
    }

    # Derived values
    budget_per_person = user_json.get("estimated_budget_per_day_per_person", 0)
    output["estimated_budget_per_day"] = budget_per_person * output["no_of_people"]

    if user_json.get("places"):
        output["places"]["preferred_type"] = ", ".join(user_json["places"])
    elif prompt_json.get("places", {}).get("preferred_type"):
        output["places"]["preferred_type"] = prompt_json["places"]["preferred_type"]

    if user_json.get("activties"):
        output["activities"]["preferred_type"] = ", ".join(user_json["activties"])

    if user_json.get("distance"):
        distance_map = {"short": "short", "mid": "medium", "long": "long"}
        output["distance_range"] = distance_map.get(user_json["distance"], "medium")

    if user_json.get("city"):
        output["start_city"] = user_json["city"]
        output["end_city"] = user_json["city"]

    # Handle include_empty flag
    def clean_dict(d):
        cleaned = {}
        for k, v in d.items():
            if isinstance(v, dict):
                nested = clean_dict(v)
                if nested:
                    cleaned[k] = nested
            elif v not in (None, "", [], {}):
                cleaned[k] = v
        return cleaned

    if not include_empty:
        output = clean_dict(output)

    # Handle only_pref flag
    if only_pref:
        # Keys considered "directly from prompt" that should be dropped
        prompt_only_keys = {"no_of_days", "no_of_people"}
        prompt_nested_keys = {
            ("cities", "must_visit"),
            ("places", "must_visit"),
        }

        def remove_prompt_keys(d, path=()):
            filtered = {}
            for k, v in d.items():
                current_path = path + (k,)
                if isinstance(v, dict):
                    nested = remove_prompt_keys(v, current_path)
                    if nested:
                        filtered[k] = nested
                else:
                    if k in prompt_only_keys and len(path) == 0:
                        continue
                    if current_path in prompt_nested_keys:
                        continue
                    filtered[k] = v
            return filtered

        output = remove_prompt_keys(output)

        if not include_empty:
            output = clean_dict(output)

    return output
