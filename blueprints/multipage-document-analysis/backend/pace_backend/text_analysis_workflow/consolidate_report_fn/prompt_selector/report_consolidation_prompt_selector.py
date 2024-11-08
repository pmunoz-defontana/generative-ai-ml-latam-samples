# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from langchain.chains.prompt_selector import ConditionalPromptSelector

from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, \
    AIMessagePromptTemplate

from .prompts import CLAUDE_SYSTEM_PROMPT_EN, CLAUDE_USER_PROMPT_EN, CLAUDE_SYSTEM_PROMPT_ES, CLAUDE_USER_PROMPT_ES

from typing import Callable


def is_es(language: str) -> bool:
    return "es" == language


def is_en(language: str) -> bool:
    return "en" == language


def is_claude(model_id: str) -> bool:
    return "claude" in model_id


def is_titan(model_id: str) -> bool:
    return "titan" in model_id


def is_es_claude(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_es(language) and is_claude(model_id)


def is_en_claude(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_claude(model_id)


def is_es_titan(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_es(language) and is_titan(model_id)


def is_en_titan(language: str) -> Callable[[str], bool]:
    return lambda model_id: is_en(language) and is_titan(model_id)


def get_information_consolidation_prompt_selector(lang: str) -> ConditionalPromptSelector:

    # Prompts by language
    CLAUDE_INFORMATION_CONSOLIDATION_PROMPT_TEMPLATE_EN = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(CLAUDE_SYSTEM_PROMPT_EN, validate_template=True),
        HumanMessagePromptTemplate.from_template(CLAUDE_USER_PROMPT_EN,
                                                 input_variables=["information"],
                                                 validate_template=True),
    ])

    CLAUDE_INFORMATION_CONSOLIDATION_PROMPT_TEMPLATE_ES = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(CLAUDE_SYSTEM_PROMPT_ES, validate_template=True),
        HumanMessagePromptTemplate.from_template(CLAUDE_USER_PROMPT_ES,
                                                 input_variables=["information"],
                                                 validate_template=True),
    ])

    return ConditionalPromptSelector(
        default_prompt=CLAUDE_INFORMATION_CONSOLIDATION_PROMPT_TEMPLATE_EN,
        conditionals=[
            (is_es_claude(lang), CLAUDE_INFORMATION_CONSOLIDATION_PROMPT_TEMPLATE_ES),
            (is_en_titan(lang), CLAUDE_INFORMATION_CONSOLIDATION_PROMPT_TEMPLATE_EN),
            (is_es_titan(lang), CLAUDE_INFORMATION_CONSOLIDATION_PROMPT_TEMPLATE_ES),
        ]
    )

