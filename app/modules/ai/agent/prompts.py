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


PLAN_EDIT_CLASSIFICATION_PROMPT = """
You are given a trip plan and a user's edit request chat history.

Classify the user's **final instruction** as:
- "simple": minor edits like adding/removing/reordering steps within one city, or small updates like title/meta changes.
- "complex": structural changes like modifying cities, transport routes, or too many edits needing reasoning.
- "unrelated": if the final request is not related to the trip plan at all.

## Plan:
{plan}

## Chat History:
{chat_history}

Respond in JSON format:
```json
{
  "type": "simple" | "complex" | "unrelated",
  "response": "string"  // 
    - If unrelated: write a direct reply to the user.
    - If simple or complex: rewrite the final user instruction into a clear, standalone form that doesn't rely on prior messages.
}
````
"""

PLAN_SIMPLE_EDIT_PROMPT = """
The user made a simple edit request to the trip plan.
Given the trip plan with indexed days and steps, and user request, extract the changes in this format:

```json
{
  "to_remove": [int], // index of steps to remove
  "to_reorder": [(int, int)], // index of steps to reorder (1st index is old index, 2nd index is new index)
  "to_add": [{ "day_index": int, "steps_description": "str" }], // Simple description of step to add to day
  "day_title_change": [{ "day_index": int, "new_title": "str" }], // New title for day
  "meta_change": {
    "new_title": "str", // New title to replace old title
    "new_description": "str", // New description to replace old description
    "new_no_of_people": int, // New number of people
    "new_start_city": "str" // New start city
  }
}
```

** IF ANY PARTICULAR FIELD DO NOT NEED TO BE CHANGED, JUST LEAVE IT null **

## Plan:
{plan}

## User Request:
{prompt}
"""



PLAN_COMPLEX_EDIT_PROMPT = """
You are an agent responsible for refining user's edit request into structured and more detailed response to regerate tne entire trip again with requested changes.

For example you're given
# Plan: Advanture to pokhara

day 1: 
step 1: visit place 1
step 2: visit place 2
step 3: travel to city 2

day 2:
step 5: visit place 3
step 6: visit place 4
step 7: travel to city 1 

# User Request:
Innstead of city 1, lets start and end with city 2

## Your Response
```json
{
  "refined_prompt": "Generate a 2 days trip plan starting and ending with city 2. In city 2, visit place 3 and 4, and visit place 1 and 2 in city 1, .....", // Detailed prompt on how to regenrate trip with requested changes
  "start_city": "city 2"  // or null if not changed
  "no_of_people": null // Include this if mentioned on request, keep it null otherwise
}
```
Respond in this strict JSON format:
```json
{
  "refined_prompt": "str",
  "start_city": "str" | null,
  "no_of_people": int | null
}
```

## Refined Prompt Guidelines:
- Describe what types of places, activities, and cities to include
- Mention a logical route or direction if applicable
- Respect user preferences, but enrich or expand if vague
- Reuse parts of the current plan unless clearly rejected
- Do not describe how to format the plan, only what to include

Plan:
{plan}

User Request:
{prompt}
"""

DAY_ADDITION_PROMPT = """
You are an agent responsible for editing a **single day** of a trip plan by **adding new steps** based on the user's request.

You will be provided:
- A list of **available places and activities** that can be added.
- The **user’s prompt** describing what they want to add to the day.

---

# Your Responsibilities
- Generate a list of new steps to **add** to the given day based on the user’s request.
- Only use **places, cities, and activities from the provided context**.
- Each step must fall into one of the following categories:
  - `"visit"`: Visiting a specific place.
  - `"activity"`: Performing a specific activity at a place (only if the place explicitly supports that activity, otherwise default to `"visit"`).
  - `"transport"`: Traveling from one city to another.

---

# Output Format
Respond in a **strict JSON array**, where each element is a single step in the following format:

```json
{
  "index": int, // Index to add it on, if you wanna add between step_10 and step_11, it should be 11, if multiple steps are to be added you can use the same index
  "category": "visit" | "activity" | "transport",  // All lowercase
  "place": "str" | null,                       // Required for 'visit'
  "city": "str" | null,                    // City to transport to. Required for 'transport'
  "place_activity": ["str", "str"] | null      // Required for 'activity' as [place, activity]
}
```

- Do not include any step that refers to a place, activity, or city not listed in the available context.
- You are only responsible for adding steps—do not remove or reorder existing ones

# Context

## Available Places and activities
{places}

## Existing Steps
{steps}

## User's Request
{prompt}
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