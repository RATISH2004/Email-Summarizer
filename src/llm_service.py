import requests
import json

class LLMService:
    def __init__(self):
        self.api_url = "http://127.0.0.1:1234/v1/chat/completions"
        self.model = "deepseek-chat"  # Change to match your loaded LM Studio model
        self.api_key = "dummy-key"    # LM Studio ignores this, but keep for interface compatibility

    def classify_email_importance(self, subject, body):
        prompt = (
    "You are an expert email assistant. For each email, classify its importance as one of:\n"
    "- \"Unimportant\": Social invitations, newsletters, advertisements, or emails that do not require any action or have no significant impact.\n"
    "- \"Important\": Emails that require action soon, involve deadlines, reminders, bills, appointments, or are work-related but not life-changing.\n"
    "- \"Very Important\": Life-changing, urgent, or highly time-sensitive emails such as job offers, university acceptance, legal notices, or critical health/family matters.\n"
    "Return only a JSON object with the field importance_level. Do not explain your answer.\n\n"
    "Example 1:\n"
    "Subject: Distant Friend's Wedding\n"
    "Body: Hey, just letting you know my wedding is next month. Would love to see you there!\n"
    "Output: {\"importance_level\": \"Unimportant\"}\n\n"
    "Example 2:\n"
    "Subject: License Renewal Reminder\n"
    "Body: Your license will expire in 7 days. Please renew to avoid interruption.\n"
    "Output: {\"importance_level\": \"Important\"}\n\n"
    "Example 3:\n"
    "Subject: Congratulations! MIT/NUS Acceptance\n"
    "Body: You have been accepted to MIT/NUS! Please check your portal for next steps.\n"
    "Output: {\"importance_level\": \"Very Important\"}\n\n"
    "Example 4:\n"
    "Subject: Newsletter - Top 10 Travel Destinations\n"
    "Body: Check out our latest list of travel destinations for 2025!\n"
    "Output: {\"importance_level\": \"Unimportant\"}\n\n"
    "Example 5:\n"
    "Subject: Payment Overdue - Immediate Action Required\n"
    "Body: Your electricity bill is overdue. Please pay immediately to avoid disconnection.\n"
    "Output: {\"importance_level\": \"Important\"}\n\n"
    "Example 6:\n"
    "Subject: Job Offer from Google\n"
    "Body: We are pleased to offer you a position at Google. Please review and sign the attached contract.\n"
    "Output: {\"importance_level\": \"Very Important\"}\n\n"
    "Example 7:\n"
    "Subject: Weekly Grocery Deals\n"
    "Body: Save big on your weekly shopping with these deals!\n"
    "Output: {\"importance_level\": \"Unimportant\"}\n\n"
    "Example 8:\n"
    "Subject: Doctor's Appointment Confirmation\n"
    "Body: Your appointment is scheduled for 10:00 AM on July 10th at City Clinic.\n"
    "Output: {\"importance_level\": \"Important\"}\n\n"
    "Example 9:\n"
    "Subject: Family Emergency\n"
    "Body: Please call me as soon as possible. It's urgent.\n"
    "Output: {\"importance_level\": \"Very Important\"}\n\n"
    "Example 10:\n"
    "Subject: Your Amazon Order Has Shipped\n"
    "Body: Your order #12345 has shipped and will arrive soon.\n"
    "Output: {\"importance_level\": \"Unimportant\"}\n\n"
    "Example 11:\n"
    "Subject: Final Notice: Tax Filing Deadline\n"
    "Body: The deadline to file your taxes is tomorrow. Please submit your documents to avoid penalties.\n"
    "Output: {\"importance_level\": \"Important\"}\n\n"
    "Example 12:\n"
    "Subject: Scholarship Awarded\n"
    "Body: Congratulations! You have been awarded a full scholarship for your studies.\n"
    "Output: {\"importance_level\": \"Very Important\"}\n\n"
    "Now classify this email:\n"
    f"Subject: {subject}\n"
    f"Body: {body}\n"
    "Output:"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert email assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 50,
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            answer = result['choices'][0]['message']['content'].strip()
            # Try to parse the JSON from the model's output
            try:
                importance = json.loads(answer)["importance_level"]
                return importance
            except Exception:
                # Fallback: extract label manually
                for label in ["Very Important", "Important", "Unimportant"]:
                    if label in answer:
                        return label
                return "Unimportant"
        except Exception as e:
            print(f"[ERROR] LLM call failed: {e}")
            return "Unimportant"

# Example usage
if __name__ == "__main__":
    llm_service = LLMService()
    emails = [
        {
            "subject": "Distant Friend's Wedding",
            "body": "Hey, just letting you know my wedding is next month. Would love to see you there!"
        },
        {
            "subject": "License Renewal Reminder",
            "body": "Your license will expire in 7 days. Please renew to avoid interruption."
        },
        {
            "subject": "Congratulations! MIT/NUS Acceptance",
            "body": "You have been accepted to MIT/NUS! Please check your portal for next steps."
        }
    ]
    for email in emails:
        importance = llm_service.classify_email_importance(email["subject"], email["body"])
        print(f"Subject: {email['subject']}\nImportance: {importance}\n")
