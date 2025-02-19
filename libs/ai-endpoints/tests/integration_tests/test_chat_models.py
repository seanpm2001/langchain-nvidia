"""Test ChatNVIDIA chat model."""

from typing import List

import pytest
from langchain_core.load.dump import dumps
from langchain_core.load.load import loads
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from langchain_nvidia_ai_endpoints.chat_models import ChatNVIDIA

#
# we setup an --all-models flag in conftest.py, when passed it configures chat_model
# and image_in_model to be all available models of type chat or image_in
#
# note: currently --all-models only works with the default mode because different
#       modes may have different available models
#


def test_chat_ai_endpoints(chat_model: str, mode: dict) -> None:
    """Test ChatNVIDIA wrapper."""
    chat = ChatNVIDIA(model=chat_model, temperature=0.7, **mode)
    message = HumanMessage(content="Hello")
    response = chat.invoke([message])
    assert isinstance(response, BaseMessage)
    assert isinstance(response.content, str)


def test_unknown_model() -> None:
    with pytest.raises(ValueError):
        ChatNVIDIA(model="unknown_model")


def test_base_url_unknown_model() -> None:
    llm = ChatNVIDIA(model="unknown_model", base_url="http://localhost:88888/v1")
    assert llm.model == "unknown_model"


def test_chat_ai_endpoints_system_message(chat_model: str, mode: dict) -> None:
    """Test wrapper with system message."""
    # mamba_chat only supports 'user' or 'assistant' messages -
    #  Exception: [422] Unprocessable Entity
    #  body -> messages -> 0 -> role
    #    Input should be 'user' or 'assistant'
    #     (type=literal_error; expected='user' or 'assistant')
    if chat_model == "mamba_chat":
        pytest.skip(f"{chat_model} does not support system messages")

    chat = ChatNVIDIA(model=chat_model, max_tokens=36, **mode)
    system_message = SystemMessage(content="You are to chat with the user.")
    human_message = HumanMessage(content="Hello")
    response = chat.invoke([system_message, human_message])
    assert isinstance(response, BaseMessage)
    assert isinstance(response.content, str)


@pytest.mark.parametrize(
    "exchange",
    [
        pytest.param([], id="no_message"),
        pytest.param([HumanMessage(content="Hello")], id="single_human_message"),
        pytest.param([AIMessage(content="Hi")], id="single_ai_message"),
        pytest.param(
            [HumanMessage(content="Hello"), HumanMessage(content="Hello")],
            id="double_human_message",
            marks=pytest.mark.xfail(
                reason="Known issue, messages types must alternate"
            ),
        ),
        pytest.param(
            [AIMessage(content="Hi"), AIMessage(content="Hi")],
            id="double_ai_message",
            marks=pytest.mark.xfail(reason="Known issue, message types must alternate"),
        ),
        pytest.param(
            [HumanMessage(content="Hello"), AIMessage(content="Hi")],
            id="human_ai_message",
        ),
        pytest.param(
            [AIMessage(content="Hi"), HumanMessage(content="Hello")],
            id="ai_human_message",
        ),
        pytest.param(
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi"),
                HumanMessage(content="There"),
            ],
            id="human_ai_human_message",
        ),
        pytest.param(
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi"),
                HumanMessage(content="There"),
                AIMessage(content="Ok"),
            ],
            id="human_ai_human_ai_message",
        ),
        pytest.param(
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi"),
                HumanMessage(content="There"),
                AIMessage(content="Ok"),
                HumanMessage(content="Now what?"),
            ],
            id="human_ai_human_ai_human_message",
        ),
    ],
)
@pytest.mark.parametrize(
    "system",
    [
        pytest.param([], id="no_system_message"),  # no system message
        pytest.param(
            [SystemMessage(content="You are to chat with the user.")],
            id="single_system_message",
        ),
    ],
)
def test_messages(
    chat_model: str, mode: dict, system: List, exchange: List[BaseMessage]
) -> None:
    if not system and not exchange:
        pytest.skip("No messages to test")
    chat = ChatNVIDIA(model=chat_model, max_tokens=36, **mode)
    response = chat.invoke(system + exchange)
    assert isinstance(response, BaseMessage)
    assert response.response_metadata["role"] == "assistant"
    assert isinstance(response.content, str)


## TODO: Not sure if we want to support the n syntax. Trash or keep test


def test_ai_endpoints_streaming(chat_model: str, mode: dict) -> None:
    """Test streaming tokens from ai endpoints."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=36, **mode)

    cnt = 0
    for token in llm.stream("I'm Pickle Rick"):
        assert isinstance(token.content, str)
        cnt += 1
    assert cnt > 1


async def test_ai_endpoints_astream(chat_model: str, mode: dict) -> None:
    """Test streaming tokens from ai endpoints."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=35, **mode)

    cnt = 0
    async for token in llm.astream("I'm Pickle Rick"):
        assert isinstance(token.content, str)
        cnt += 1
    assert cnt > 1


async def test_ai_endpoints_abatch(chat_model: str, mode: dict) -> None:
    """Test streaming tokens."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=36, **mode)

    result = await llm.abatch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


async def test_ai_endpoints_abatch_tags(chat_model: str, mode: dict) -> None:
    """Test batch tokens."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=55, **mode)

    result = await llm.abatch(
        ["I'm Pickle Rick", "I'm not Pickle Rick"], config={"tags": ["foo"]}
    )
    for token in result:
        assert isinstance(token.content, str)


def test_ai_endpoints_batch(chat_model: str, mode: dict) -> None:
    """Test batch tokens."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=60, **mode)

    result = llm.batch(["I'm Pickle Rick", "I'm not Pickle Rick"])
    for token in result:
        assert isinstance(token.content, str)


async def test_ai_endpoints_ainvoke(chat_model: str, mode: dict) -> None:
    """Test invoke tokens."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=60, **mode)

    result = await llm.ainvoke("I'm Pickle Rick", config={"tags": ["foo"]})
    assert isinstance(result.content, str)


def test_ai_endpoints_invoke(chat_model: str, mode: dict) -> None:
    """Test invoke tokens."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=60, **mode)

    result = llm.invoke("I'm Pickle Rick", config=dict(tags=["foo"]))
    assert isinstance(result.content, str)


# todo: tests for parameters -
#        bad: str - Bad words to avoid (cased)
#        stop: str - Stop words (cased)


# todo: max_tokens test for ainvoke, batch, abatch, stream, astream


@pytest.mark.parametrize("max_tokens", [-100, 0])
def test_ai_endpoints_invoke_max_tokens_negative_a(
    chat_model: str,
    mode: dict,
    max_tokens: int,
) -> None:
    """Test invoke's max_tokens' negative bounds."""
    with pytest.raises(Exception):
        llm = ChatNVIDIA(model=chat_model, max_tokens=max_tokens, **mode)
        llm.invoke("Show me the tokens")
    assert llm._client.client.last_response.status_code in [400, 422]
    assert "max_tokens" in str(llm._client.client.last_response.content)


@pytest.mark.parametrize("max_tokens", [2**31 - 1])
def test_ai_endpoints_invoke_max_tokens_negative_b(
    chat_model: str,
    mode: dict,
    max_tokens: int,
) -> None:
    """Test invoke's max_tokens' positive bounds."""
    with pytest.raises(Exception):
        llm = ChatNVIDIA(model=chat_model, max_tokens=max_tokens, **mode)
        llm.invoke("Show me the tokens")
    assert llm._client.client.last_response.status_code in [400, 422]
    # custom error string -
    #    model inference failed -- ValueError: A requested length of the model output
    #    is too big. Maximum allowed output length is X, whereas requested output
    #    length is Y.
    assert "length" in str(llm._client.client.last_response.content)


def test_ai_endpoints_invoke_max_tokens_positive(
    chat_model: str, mode: dict, max_tokens: int = 21
) -> None:
    """Test invoke's max_tokens."""
    llm = ChatNVIDIA(model=chat_model, max_tokens=max_tokens, **mode)
    result = llm.invoke("Show me the tokens")
    assert isinstance(result.content, str)
    assert "token_usage" in result.response_metadata
    assert "completion_tokens" in result.response_metadata["token_usage"]
    assert result.response_metadata["token_usage"]["completion_tokens"] <= max_tokens


# todo: seed test for ainvoke, batch, abatch, stream, astream


@pytest.mark.xfail(reason="seed does not consistently control determinism")
def test_ai_endpoints_invoke_seed_default(chat_model: str, mode: dict) -> None:
    """Test invoke's seed (default)."""
    llm0 = ChatNVIDIA(model=chat_model, **mode)  # default seed should not repeat
    result0 = llm0.invoke("What's in a seed?")
    assert isinstance(result0.content, str)
    llm1 = ChatNVIDIA(model=chat_model, **mode)  # default seed should not repeat
    result1 = llm1.invoke("What's in a seed?")
    assert isinstance(result1.content, str)
    # if this fails, consider setting a high temperature to avoid deterministic results
    assert result0.content != result1.content


@pytest.mark.parametrize(
    "seed",
    [
        pytest.param(
            -1000,
            marks=pytest.mark.xfail(reason="Known issue, negative seed not supported"),
        ),
        0,
        1000,
    ],
)
def test_ai_endpoints_invoke_seed_range(chat_model: str, mode: dict, seed: int) -> None:
    llm = ChatNVIDIA(model=chat_model, seed=seed, **mode)
    llm.invoke("What's in a seed?")
    assert llm._client.client.last_response.status_code == 200


@pytest.mark.xfail(reason="seed does not consistently control determinism")
def test_ai_endpoints_invoke_seed_functional(
    chat_model: str, mode: dict, seed: int = 413
) -> None:
    llm = ChatNVIDIA(model=chat_model, seed=seed, **mode)
    result0 = llm.invoke("What's in a seed?")
    assert isinstance(result0.content, str)
    result1 = llm.invoke("What's in a seed?")
    assert isinstance(result1.content, str)
    assert result0.content == result1.content


# todo: temperature test for ainvoke, batch, abatch, stream, astream


@pytest.mark.parametrize("temperature", [-0.1, 2.1])
def test_ai_endpoints_invoke_temperature_negative(
    chat_model: str, mode: dict, temperature: int
) -> None:
    """Test invoke's temperature (negative)."""
    with pytest.raises(Exception):
        llm = ChatNVIDIA(model=chat_model, temperature=temperature, **mode)
        llm.invoke("What's in a temperature?")
    assert llm._client.client.last_response.status_code in [400, 422]
    assert "temperature" in str(llm._client.client.last_response.content)


@pytest.mark.xfail(reason="temperature not consistently implemented")
def test_ai_endpoints_invoke_temperature_positive(chat_model: str, mode: dict) -> None:
    """Test invoke's temperature (positive)."""
    # idea is to have a fixed seed and vary temperature to get different results
    llm0 = ChatNVIDIA(model=chat_model, seed=608, templerature=0, **mode)
    result0 = llm0.invoke("What's in a temperature?")
    assert isinstance(result0.content, str)
    llm1 = ChatNVIDIA(model=chat_model, seed=608, templerature=1, **mode)
    result1 = llm1.invoke("What's in a temperature?")
    assert isinstance(result1.content, str)
    assert result0.content != result1.content


# todo: top_p test for ainvoke, batch, abatch, stream, astream


@pytest.mark.parametrize("top_p", [-10, 10])
def test_ai_endpoints_invoke_top_p_negative(
    chat_model: str, mode: dict, top_p: int
) -> None:
    """Test invoke's top_p (negative)."""
    with pytest.raises(Exception):
        llm = ChatNVIDIA(model=chat_model, top_p=top_p, **mode)
        llm.invoke("What's in a top_p?")
    assert llm._client.client.last_response.status_code in [400, 422]
    assert "top_p" in str(llm._client.client.last_response.content)


@pytest.mark.xfail(reason="seed does not consistently control determinism")
def test_ai_endpoints_invoke_top_p_positive(chat_model: str, mode: dict) -> None:
    """Test invoke's top_p (positive)."""
    # idea is to have a fixed seed and vary top_p to get different results
    llm0 = ChatNVIDIA(model=chat_model, seed=608, top_p=0.1, **mode)
    result0 = llm0.invoke("What's in a top_p?")
    assert isinstance(result0.content, str)
    llm1 = ChatNVIDIA(model=chat_model, seed=608, top_p=1, **mode)
    result1 = llm1.invoke("What's in a top_p?")
    assert isinstance(result1.content, str)
    assert result0.content != result1.content


@pytest.mark.skip("serialization support is broken, needs attention")
def test_serialize_chatnvidia(chat_model: str, mode: dict) -> None:
    llm = ChatNVIDIA(model=chat_model, **mode)
    model = loads(dumps(llm), valid_namespaces=["langchain_nvidia_ai_endpoints"])
    result = model.invoke("What is there if there is nothing?")
    assert isinstance(result.content, str)
