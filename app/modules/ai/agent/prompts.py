import json
import re

def get_prompt(template: str, **kwargs) -> str:
    def replace_match(match):
        key = match.group(1)
        value = kwargs.get(key)
        if value is None:
            return match.group(0)  # leave unchanged if not found
        if isinstance(value, dict):
            return "```json\n" + json.dumps(value, indent=4) + "\n```"
        return str(value)

    # Match only single-word placeholders like {user_pref}, not { something }
    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replace_match, template)


PROMPT_IMPROVEMENT_PROMPT = """
You are an agent responsible for refining user prompt for plan generation.

based on provided chat history you will generate structured response in the following format
```json
{
    "refined_prompt": "str", # new refined prompt for plan generation agent
    "start_city": "str, # name of the start city
    "no_of_people": "int" # No of people if mentioned in prompt, else 1
}
```
The refined prompt should describe what types of places to explore, what the general route or direction should look like, what kinds of activities the user prefers, and if any specific places or experiences are explicitly requested. It should clearly mention the starting and ending point of the trip. The refined prompt must provide enough guidance for the next agent to generate a high-level plan using only this refined input

# Notes
- DO NOT MENTION HOW TO STRUCTURE PLAN, BUT WHAT TO INCLUDE 
- Unless the original prompt specifically restricts it, feel free to expand or enrich the plan with nearby relevant cities or activities to make the trip more complete and realistic
- If the prompt lacks detail (e.g., long duration but limited area), suggest additional nearby places to better utilize the time.
- start and end your plan in {start_city} if not provided in prompt.

CHAT HISTORY:
{chat_history}
"""


OVERALL_PLAN_GENERATION_PROMPT = """
You are an intermediate planning agent responsible for designing a high-level {no_of_days} days **ground-based trip plan** starting from city of {start_city} within Nepal.

You'll be given:
- A **refined user prompt** expressing user preferences and intent.
- A **list of possible cities**, extracted based on relevance. These are suggestions, not mandatory destinations.

---

# Instructions

Your goal is to generate a clear **daily plan structure** that aligns closely with the user's prompt. This includes:
- Use 12-15 hours of time per day efficiently, travelling between cities, visiting touristic destinations and experiencing activities.
- Prioritize geographic flow — minimize backtracking and long detours between cities.
- Use only cities from the provided `AVAILABLE_CITIES` list for planning.
- Assign 1–3 cities per day: If transporting between cities, include multiple; if staying, include just one.
- Travel-heavy days should have fewer activities and visits, while stay days can have 4-5 planned visits or experiences.
- Keep daily descriptions detailed, and give each day a creative and thematic title.
- Ensure realism: consider actual travel durations and typical tourist flow when sequencing cities and activities.

# Special Note
**FOCUS ON WHAT TYPES OF TOURIST PLACES OR ACTIVITIES TO INCLUDE, BUT FEEL FREE TO MENTION SPECIFIC NAMES IF THE PROMPT SUGGESTS THEM. AVOID DETAILS ABOUT FOOD, ACCOMMODATION, OR TRANSPORT MODE.**

---

# Output Format

Respond strictly in the following JSON format:

```json
{
    "title": "str",                  // A creative, descriptive title for the overall trip
    "description": "str",            // Summary of what the user will experience across the trip
    "days": [
        {
            "title": "str",         // Title for the day's theme or focus
            "description": "str",   // Overview of places, activities, or travel for the day
            "cities": ["str"]       // 1–3 cities relevant for this day (based on actual travel), is user is travelling from one city to another inlude multiple, if visiting places in same city keep only one
        }
        // Repeat for each day
    ]
}
---

# Provided Context
## AVAILABLE_CITIES:
{cities}

## PROMPT :
{prompt}
"""

SINGLE_DAY_EXPANDING_PROMPT = """
You are an agent responsible for expanding the details of a specific day in the user's trip plan.

You will be provided:
- A **general description** of what the user should do on this day. Use it as **guidance**, not strict instruction — it may have been generated automatically and might not fully capture the intent or opportunities.
- A list of **available places and their activities**, carefully selected and specific to this day’s context.
- A list of **activities and places already completed**, which must not be repeated.
- A list of **future plans**, so you can avoid suggesting anything scheduled for later.

---

# Your Role

- Create a thoughtful, step-by-step plan for the day based on the above inputs.
- You are allowed to reason creatively, but must stay within the **provided context** — no outside places, cities, or activities.
- Interpret the day's description flexibly and prioritize **meaningful exploration** of tourist places and **structured activities** where appropriate.

---

# Guidelines

- Each step must fall into one of the following categories:
  - `"visit"`: Going to a tourist attraction, landmark, or location of interest.
  - `"activity"`: Doing a specific structured or recreational activity **at a valid place that explicitly supports it**. Do **not** suggest vague actions like "eating", "resting", or "strolling".
  - `"transport"`: Moving from one city to another.

- For this plan:
  - **Places** refer to notable **tourist destinations or attractions** (e.g., lakes, temples, viewpoints — not hotels or restaurants).
  - **Activities** refer to actual **adventure or recreational experiences** (e.g., boating, paragliding — not passive things like walking or relaxing).

- **Do NOT repeat**:
    - Any previously visited place.
    - Any previously done activity (at the same place).
  
- **Do NOT invent**:
    - New cities, places, or activities not present in the provided context.

- **Do respect**:
    - The future day's descriptions — avoid visiting places or doing activities scheduled for upcoming days.

---

# Output Format

Respond in a **strict JSON array**, where each element represents one step of the day:

```json
{
  "category": "visit" | "activity" | "transport",  
  "place": "str" | null,                          // Required for 'visit'
  "city": "str" | null,                           // Required for 'transport'
  "place_activity": ["str", "str"] | null         // Required for 'activity': [place, activity], avoid having activity without place
}
```

# Input Context

## Available Places and activities
{places}


## Already Done Tasks

{already_done_tasks}

## Description of Upcoming Days

{upcoming_days}

## Your Job

Expand the plan for single day, based on the following description:
"{day_description}"
"""



RESPONSE_GENERATOR_AGENT_PROMPT = """
You are an agent responsible for generating natural language response to user's response. You'll be given user's request
for plan generation or plan modification, alongside the events that happened after the request. You should answer
what happed to their request in natural language without telling too much technical details.
You should answer in strict json format as
```json
{
  "response": "str"
}
```

# Events:
{events}

# Prompt:
{prompt}
"""