# llm_backend.py
from label_studio_ml.model import LabelStudioMLBase

class LLMInteractiveModel(LabelStudioMLBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("LLMInteractiveModel initialized!")

    def predict(self, tasks, **kwargs):
        """This method is called by Label Studio to get predictions."""
        results = []
        for task in tasks:
            input_text = task['data'].get('text', '')

            # Simulate LLM response (replace with real LLM call)
            response = f"LLM response for: {input_text}"

            results.append({
                'result': [{
                    'from_name': 'response',
                    'to_name': 'text',
                    'type': 'textarea',
                    'value': {
                        'text': [response]
                    }
                }]
            })

        return results

    def fit(self, completions, workdir=None, **kwargs):
        # You can implement fine-tuning here if needed
        return {}
