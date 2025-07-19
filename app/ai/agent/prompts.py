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
You are an agent responsible for refining user prompt, you'll be provided with user prompt as well as user prefrenced obtained in long run.
Give more weight to user prompt, but keep some elements from user's past prefrences since future agents wont have this preference.

you will generate structured response in the following format
```json
{
    "refined_prompt": "str", # new refined prompt for plan generation agent
    "start_city": "str, # name of the start city
    "no_of_people": "int" # No of people if mentioned in prompt, else 1
}
```
The refined prompt should mention what types of places to look into, what should be general route that can be followed, what types of activity user
prefers, menntion if any place or activity user wants explecitely, from where plan should start and end. The prompt should give enough context for next agent that it can generate plan overview kust with
your refined prompt.
start and end your plan in {start_end_city} if not provided in prompt.

# Note: DO NOT MENTION HOW TO STRUCTURE PLAN, BUT WHAT TO INCLUDE 

USER_PREFERENCE : 
{user_pref}
USER_PROMPT: {user_prompt}
"""


OVERALL_PLAN_GENERATION_PROMPT = """
You are an intermediate planning agent responsible for designing a high-level **ground-based trip plan** within Nepal.

You'll be given:
- A **refined user prompt** expressing user preferences and intent.
- A **list of possible cities**, extracted based on relevance. These are suggestions, not mandatory destinations.

---

# Instructions

Your goal is to generate a clear **daily plan structure** that aligns closely with the user's prompt. This includes:
- Divide the trip into meaningful daily themes (e.g., culture, nature, adventure, local life, travel).
- Use 10–12 hours of time per day efficiently, balancing activities, travel, meals, and rest.
- Avoid frequent city hopping; only include intercity travel when necessary or logical.
- Prioritize geographic flow — minimize backtracking and long detours between cities.
- Use only cities from the provided `AVAILABLE_CITIES` list for planning.
- Assign 1–3 cities per day: If traveling between cities, include multiple; if staying, include just one.
- Travel-heavy days should have fewer activities, while stay days can have 3–4 planned visits or experiences.
- Tailor each day to the user’s preferences from the prompt (e.g., nature, adventure, spiritual sites).
- Keep daily descriptions short but vivid, and give each day a creative and thematic title.
- Ensure realism: consider actual travel durations and typical tourist flow when sequencing cities and activities.


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
AVAILABLE_CITIES:
{cities}
PROMPT :
{prompt}
"""


SINGLE_DAY_EXPANDING_PROMPT = """
You are an agent responsible for expanding the details of a specific day in the user's trip plan.

You will be provided:
- A **description of what the user should do on this particular day**.
- A list of **available places and activities**, specific to the context.
- A list of **activities and places already visited**, so you don't repeat them.
- A list of **descriptions for upcoming days**, so you don't suggest things planned for the future.

---

# Your Responsibilities
- Generate a step-by-step plan to fulfill the day's goal, using **only the provided context**.
- Each step must fall into one of the following categories:
  - `"visit"`: Going to a specific place.
  - `"activity"`: Performing a specific activity at a place if that place explicitly mentions it, otherwise just keep in visit category.
  - `"travel"`: Moving from one city to another.

- Do **not** repeat anything from `already_done_tasks`.
- Do **not** include any place, activity, or city that is **not mentioned in the provided context**.
- Ensure you **respect the description of upcoming days** and avoid visiting those locations or doing those activities prematurely.

---

# Output Format
Respond in a **strict JSON array**, where each element is a single step of the day in the following format:

```json
{
  "category": "visit" | "activity" | "travel",  // All lowercase
  "place": "str" | null,                       // Required for 'visit'
  "end_city": "str" | null,                    // Required for 'travel'
  "place_activity": ["str", "str"] | null            // Required for 'activity' as [place, activity]
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

Expand the plan for **Day {day_index}**, based on the following description:
"{day_description}"
"""