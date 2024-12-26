import functions_framework
from googleapiclient.discovery import build
from google.oauth2 import service_account
from flask import jsonify
import json

@functions_framework.http
def hello_http(request):

    # Parse the request to get the form ID
    request_json = request.get_json(silent=True)
    if request_json and "form_id" in request_json:
        form_id = request_json["form_id"]
    else:
        form_id = request.args.get("form_id", None)
    if not form_id:
        return jsonify({"error": "Form ID not provided"}), 400

    try:
        creds = service_account.Credentials.from_service_account_file('service_account.json')
        service = build("forms", "v1", credentials=creds)

        # Fetch form metadata to get question details
        form_metadata = service.forms().get(formId=form_id).execute()
        question_items = form_metadata.get("items", [])

        # Create a mapping of questionId to question title
        question_map = {}
        for item in question_items:
            if "questionItem" in item:  
                question_id = item["questionItem"]["question"]["questionId"]
                question_title = item["title"]
                question_map[question_id] = question_title

        # Fetch responses from the Google Form
        responses = service.forms().responses().list(formId=form_id).execute()
        response_items = responses.get("responses", [])
        if not response_items:
            return jsonify({"message": "No responses found for this form"}), 200

        # Format responses for better readability
        formatted_responses = []
        for response in response_items:
            formatted_response = {"responseId": response["responseId"]}
            answers = response.get("answers", {})
            for question_id, answer_data in answers.items():
                question_title = question_map.get(question_id, "Unknown Question")
                text_answers = answer_data.get("textAnswers", {}).get("answers", [])
                formatted_response[question_title] = [answer["value"] for answer in text_answers]
            formatted_responses.append(formatted_response)

        # Return the formatted responses with non-ASCII characters rendered
        return json.dumps(formatted_responses, ensure_ascii=False), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500