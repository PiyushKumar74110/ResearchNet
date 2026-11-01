
"""Test the local Ollama model and its LangChain integration."""

from langchain_ollama import ChatOllama


def test_ollama_connection():
    """Check whether the configured Ollama model responds successfully."""

    model = ChatOllama(
        model="qwen2.5:3b",
        base_url="http://localhost:11434",
        temperature=0,
    )

    response = model.invoke(
        "Explain what a multi-agent AI research system is in three sentences."
    )

    print("\nOllama connection successful!")
    print(f"Model response:\n{response.content}")


if __name__ == "__main__":
    """Run the Ollama connection test."""

    try:
        test_ollama_connection()
    except Exception as error:
        print("\nOllama connection failed.")
        print(f"Error: {error}")
