"""Build LangChain agents and report-generation chains."""

from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.tools.web_tools import scrape_url, web_search


def get_llm() -> ChatOpenAI:
    """Create the configured OpenAI chat model after validating credentials."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to backend/.env.")
    # return ChatOpenAI(
    #     model=settings.openai_model,
    #     temperature=0,
    #     api_key=settings.openai_api_key,
    # )

    return ChatOllama(
        model = "qwen2.5:3b",
        temperature = 0,
    )


def build_search_agent():
    """Build an agent that can search the web with Tavily."""
    return create_agent(model=get_llm(), tools=[web_search])


def build_reader_agent():
    """Build an agent that can scrape a selected source URL."""
    return create_agent(model=get_llm(), tools=[scrape_url])


write_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful research writer. Produce clear, structured reports. "
            "Distinguish sourced facts from uncertainty, do not invent citations, and "
            "use only URLs present in the supplied research.",
        ),
        (
            "human",
            """Write a detailed research report on this topic: {topic}

Research gathered:
{research}

Use these sections:
# Introduction
# Key Findings
At least three well-explained findings, where the available evidence permits.
# Limitations and Uncertainties
# Conclusion
# Sources
List the relevant URLs supplied in the research. Do not fabricate URLs.""",
        ),
    ]
)
critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a sharp, constructive research critic. Evaluate evidence, coverage, "
            "source quality, factual caution, and citation traceability. Do not assume "
            "the report is correct just because it sounds confident.",
        ),
        (
            "human",
            """Review this research report strictly:
{report}

Respond in this format:
Score: X/10

Strengths:
- ...

Areas to Improve:
- ...

One line verdict:
...""",
        ),
    ]
)


def build_writer_chain():
    """Create the chain that turns gathered evidence into a Markdown report."""
    return write_prompt | get_llm() | StrOutputParser()


def build_critic_chain():
    """Create the chain that evaluates the generated report."""
    return critic_prompt | get_llm() | StrOutputParser()
