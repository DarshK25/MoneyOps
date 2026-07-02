class PromptTemplate:
    def __init__(self, template: str):
        self.template = template

    def render(self, **kwargs):
        return self.template.format(**kwargs)


def build_intent_classification_prompt(user_input: str, industry: str = "", has_gst: bool = False) -> str:
    return (
        "Classify this MoneyOps user request. "
        f"Industry: {industry}. GST registered: {has_gst}. "
        f"User input: {user_input}"
    )


ENTITY_EXTRACTION_PROMPT = PromptTemplate(
    "Extract structured entities for intent {intent} from: {user_input}. "
    "Current date: {current_date}. Timezone: {timezone}."
)