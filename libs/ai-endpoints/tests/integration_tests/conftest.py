import inspect
from typing import List

import pytest

import langchain_nvidia_ai_endpoints
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank
from langchain_nvidia_ai_endpoints._statics import MODEL_TABLE, Model


def get_mode(config: pytest.Config) -> dict:
    nim_endpoint = config.getoption("--nim-endpoint")
    if nim_endpoint:
        return dict(base_url=nim_endpoint)
    return {}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--chat-model-id",
        action="store",
        nargs="+",
        help="Run tests for a specific chat model or list of models",
    )
    parser.addoption(
        "--embedding-model-id",
        action="store",
        help="Run tests for a specific embedding model",
    )
    parser.addoption(
        "--rerank-model-id",
        action="store",
        help="Run tests for a specific rerank model",
    )
    parser.addoption(
        "--vlm-model-id",
        action="store",
        help="Run tests for a specific vlm model",
    )
    parser.addoption(
        "--all-models",
        action="store_true",
        help="Run tests across all models",
    )
    parser.addoption(
        "--nim-endpoint",
        type=str,
        help="Run tests using NIM mode",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    mode = get_mode(metafunc.config)

    def get_all_known_models() -> List[Model]:
        return list(MODEL_TABLE.values())

    if "chat_model" in metafunc.fixturenames:
        models = [ChatNVIDIA._default_model]
        if model_list := metafunc.config.getoption("chat_model_id"):
            models = model_list
        if metafunc.config.getoption("all_models"):
            models = [
                model.id
                for model in ChatNVIDIA(**mode).available_models
                if model.model_type == "chat"
            ]
        metafunc.parametrize("chat_model", models, ids=models)

    if "rerank_model" in metafunc.fixturenames:
        models = ["nv-rerank-qa-mistral-4b:1"]
        if model := metafunc.config.getoption("rerank_model_id"):
            models = [model]
        # nim-mode reranking does not support model listing via /v1/models endpoint
        if metafunc.config.getoption("all_models"):
            if mode.get("mode", None) == "nim":
                models = [model.id for model in NVIDIARerank(**mode).available_models]
            else:
                models = [
                    model.id
                    for model in get_all_known_models()
                    if model.model_type == "ranking"
                ]
        metafunc.parametrize("rerank_model", models, ids=models)

    if "vlm_model" in metafunc.fixturenames:
        models = ["nvidia/neva-22b"]
        if model := metafunc.config.getoption("vlm_model_id"):
            models = [model]
        if metafunc.config.getoption("all_models"):
            models = [
                model.id
                for model in get_all_known_models()
                if model.model_type == "vlm"
            ]
        metafunc.parametrize("vlm_model", models, ids=models)

    if "qa_model" in metafunc.fixturenames:
        models = []
        if metafunc.config.getoption("all_models"):
            models = [
                model.id for model in get_all_known_models() if model.model_type == "qa"
            ]
        metafunc.parametrize("qa_model", models, ids=models)

    if "embedding_model" in metafunc.fixturenames:
        models = [NVIDIAEmbeddings._default_model]
        if metafunc.config.getoption("embedding_model_id"):
            models = [metafunc.config.getoption("embedding_model_id")]
        if metafunc.config.getoption("all_models"):
            models = [model.id for model in NVIDIAEmbeddings(**mode).available_models]
        metafunc.parametrize("embedding_model", models, ids=models)


@pytest.fixture
def mode(request: pytest.FixtureRequest) -> dict:
    return get_mode(request.config)


@pytest.fixture(
    params=[
        member[1]
        for member in inspect.getmembers(langchain_nvidia_ai_endpoints, inspect.isclass)
    ]
)
def public_class(request: pytest.FixtureRequest) -> type:
    return request.param
