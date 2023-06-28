import json
import logging
import os
from typing import Optional, Union

import openai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


class Message(BaseModel):
    content: str
    role: str


class Choice(BaseModel):
    finish_reason: Optional[str]  # Sometimes this is null in the response??
    index: int
    message: Message


class Usage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class Completion(BaseModel):
    choices: list[Choice]
    created: int
    id: str
    model: str
    object: str
    usage: Usage

    def get_content(self) -> str:
        return self.choices[0].message.content


class Categories(BaseModel):
    hate: bool
    hate_threatening: bool = Field(..., alias="hate/threatening")
    self_harm: bool = Field(..., alias="self-harm")
    sexual: bool
    sexual_minors: bool = Field(..., alias="sexual/minors")
    violence: bool
    violence_graphic: bool = Field(..., alias="violence/graphic")


class CategoryScores(BaseModel):
    hate: float
    hate_threatening: float = Field(..., alias="hate/threatening")
    self_harm: float = Field(..., alias="self-harm")
    sexual: float
    sexual_minors: float = Field(..., alias="sexual/minors")
    violence: float
    violence_graphic: float = Field(..., alias="violence/graphic")


class ModerationResult(BaseModel):
    categories: Categories
    category_scores: CategoryScores
    flagged: bool


class ModerationResults(BaseModel):
    results: list[ModerationResult]


class DalleData(BaseModel):
    url: str


class DalleResp(BaseModel):
    created: int
    data: list[DalleData]

    def get_urls(self) -> list[str]:
        return [d.url for d in self.data]


class OpenAIChatFormattingError(Exception):
    """
    OpenAI did not return the chat in the desired format.
    For example we asked it to return a response as json but it didn't.

    Sometimes we want openai responses in a certain format, such as json.
    The best we can do is to ask it politely to return the response in json.
    If it doesn't return it in our specified format, raise this message.
    """


class OpenAIConfig(BaseModel):
    api_key: str


class OpenAI:
    """
    Openai client.
    """

    api_key: str

    def __init__(self, api_key=OPENAI_API_KEY):
        openai.api_key = api_key

    def chat(self, prompt: str) -> str:
        completion: dict = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        logger.debug("Getting content of openai Completion", content_dict=completion)
        c = Completion(**completion)
        return OpenAI._parse_message(c.get_content())

    def chat_list_resp(self, prompt: str, *, n=5) -> list[str]:
        prompt = (
            f"For the following prompt, return {n} examples fitting the prompt in a json array literal, "
            f'ie ["answer 1", "answer 2", "answer 3"]. '
            f"If you are unable to reply in a json array literal, do not respond to the prompt."
            f"If you cannot reply, do not respond to the prompt instead of apologizing or saying 'I'm sorry'."
            f"\n\n```{prompt}```"
        )
        string = self.chat(prompt)
        if string.startswith("I'm sorry") or string.startswith("Unfortunately"):
            return []
        try:
            print(string)
            return json.loads(string)
        except json.decoder.JSONDecodeError:
            logger.error(
                "Could not decode openai response as json",
                openai_response=string,
            )
            raise OpenAIChatFormattingError

    def generate_images(
        self, prompt: str, *, n: int = 1, size: tuple[int, int] = (512, 512)
    ) -> list[str]:
        """
        Returns list of urls of generated images.
        """
        resp = openai.Image.create(
            prompt=prompt,
            n=n,
            size=f"{size[0]}x{size[1]}",
        )
        return DalleResp(**resp).get_urls()

    def moderate(
        self, content: Union[str, list[str]]
    ) -> Union[ModerationResult, list[ModerationResult]]:
        """
        Given content, return a moderation result.

        The intended purpose of this is *not* to moderate user-created content on our plaform. From the docs:
        > The moderation endpoint is free to use when monitoring the inputs and outputs of OpenAI APIs.
        > We currently do not support monitoring of third-party traffic.

        https://platform.openai.com/docs/guides/moderation/overview
        """
        resp = openai.Moderation.create(input=content)
        results = ModerationResults(**resp)
        if isinstance(content, list):
            print(results)
            return results.results
        else:
            print(results)
            return results.results[0]

    @staticmethod
    def _parse_message(msg: str):
        return msg.strip("\n")

    def get_intent(self, text: str, max_words: int = 7) -> str:
        """
        Returns the intent of the text.

        Example:
            text:
                "Tell Bob to healthcare is a basic right! Please, let’s support our
                community and stand up. We will not quit we will protest in the streets,
                at the capital, or online!"
            responses:
                max_words = 1: 'Advocacy'
                max_words = 2: 'Healthcare advocacy.'
                max_words = 5: 'Demand for healthcare rights.'
                max_words = 7: 'Advocate for healthcare as a right.'
                max_words = 9: 'Advocacy for healthcare as a right, urging action.'
                max_words = 19: 'To demand healthcare as a right and encourage support
                                for protests in various forms (street, capital, online).'
        """
        prompt = f"What is the intent of this message. Reply in {max_words} words. \n\n```{text}```"
        return self.chat(prompt=prompt)
