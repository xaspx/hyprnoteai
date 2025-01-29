from typing import List, Optional, TYPE_CHECKING

from mcp_agent.workflows.embedding.embedding_cohere import CohereEmbeddingModel
from mcp_agent.workflows.intent_classifier.intent_classifier_base import Intent
from mcp_agent.workflows.intent_classifier.intent_classifier_embedding import (
    EmbeddingIntentClassifier,
)

if TYPE_CHECKING:
    from mcp_agent.context import Context


class CohereEmbeddingIntentClassifier(EmbeddingIntentClassifier):
    """
    An intent classifier that uses Cohere's embedding models for computing semantic simiarity based classifications.
    """

    def __init__(
        self,
        intents: List[Intent],
        embedding_model: CohereEmbeddingModel | None = None,
        context: Optional["Context"] = None,
        **kwargs,
    ):
        embedding_model = embedding_model or CohereEmbeddingModel()
        super().__init__(
            embedding_model=embedding_model, intents=intents, context=context, **kwargs
        )

    @classmethod
    async def create(
        cls,
        intents: List[Intent],
        embedding_model: CohereEmbeddingModel | None = None,
        context: Optional["Context"] = None,
    ) -> "CohereEmbeddingIntentClassifier":
        """
        Factory method to create and initialize a classifier.
        Use this instead of constructor since we need async initialization.
        """
        instance = cls(
            intents=intents, embedding_model=embedding_model, context=context
        )
        await instance.initialize()
        return instance
