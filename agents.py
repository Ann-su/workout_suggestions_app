import google.generativeai as genai
from Models.models import Workout, User
import json
import os
from dotenv import load_dotenv

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

PROCESSOR_PROMPT = f'''
You are a text processing agent working with a description of a workout.


Extract specified values from the source text.
Return answer as a JSON format summary of the exercises in the workout structured as follows:
-"exercise_name" <string>
-"weight_kilograms" <number>
-"repetitions" <number>
-"sets" <number>
-"distance_kilometers" <number>
-"duration_minutes" <number>
-"kilocalories_burned" <number>

Even when there is only 1 exercise, make sure to include an "exercises" field.
Exercise names should be translated to polish and CamelCase.
Make sure the exercise names are standarised.
Calculate any missing values based on the source text.
Do any necessary conversions to metric units.
For kilocalories_burned, use the average kilocalories burned per minute / repetition / distance depending on which data is available for a given exercise.
In the output do not include any calculations, conversions or any text besides the result JSON.
Do not infer any data based on previous training, strictly use only source text given below as input.

=====
'''


TRAINER_PROMPT = f'''
You are a personal trainer working with a client. You are provided with a list of the client's previous workouts in JSON format, as well as their height, weight, and age.
Based on this data, generate a suggestion for the client's next workout. The workout should be challenging but not too difficult. The data is formatted as follows:
-"exercise_name" <string>
-"weight_kilograms" <number>
-"repetitions" <number>
-"sets" <number>
-"distance_kilometers" <number>
-"duration_minutes" <number>
-"kilocalories_burned" <number>

Generate the workout suggestion in Polish.
Do not add any additional questions, only generate the workout based on the provided data.
=====
'''

class PersonalTrainer:
    def __init__(self):
        self.client = genai.GenerativeModel("gemini-2.0-flash")

    def workout_to_json(self, text):
        prompt = PROCESSOR_PROMPT + text
        completion = self.client.generate_content(
            prompt,
            generation_config={"temperature": 0, "response_mime_type": "application/json"}
        )
        return completion.text

    def suggest_workout(self, current_user_id):
        workouts = Workout.query.filter_by(user_id=current_user_id).all()
        current_user = User.query.filter_by(id=current_user_id).first()
        user_info = f"The client is {current_user.age} years old, weighs {current_user.weight_kilograms} kilograms and is {current_user.height_centimeters} centimeters tall."
        workouts_json = json.dumps([workout.to_dict() for workout in workouts])
        prompt = TRAINER_PROMPT + user_info + workouts_json
        completion = self.client.generate_content(
            prompt, generation_config={"temperature": 0}
        )
        return completion.text