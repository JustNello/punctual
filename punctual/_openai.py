from json import loads
from datetime import timedelta

from openai import OpenAI


def guess_duration(entry: str, token: str) -> timedelta:
    client = OpenAI(api_key=token)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are provided with a sample database containing activities and their respective durations in minutes. For example, \"Having lunch, 20\". Your task is to estimate the duration in minutes for any given entry that is not listed in the sample database and output the result in a JSON file. Avoid any discussion, suggestions, or comments\n\nInput Example:\n\"Having lunch\"\n\nOutput Example:\n{ \"duration\": 20 }\n\nSample database\nGrocery: 25 minutes\nParking: 15 minutes\nCooking: 12 minutes\nMeal: 12 minutes\nClean: 10 minutes\nBreakfast: 10 minutes\nLunch: 10 minutes\nDinner: 10 minutes\nShower: 20 minutes\nShaving: 15 minutes\nGet dressed: 15 minutes"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Cleaning the kitchen"
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "```json\n{\n  \"duration\": 10\n}\n```"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": entry
                    }
                ]
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        response_format={"type": "json_object"},
        frequency_penalty=0,
        presence_penalty=0
    )

    return timedelta(minutes=(loads(response.choices[0].message.content)['duration']))
