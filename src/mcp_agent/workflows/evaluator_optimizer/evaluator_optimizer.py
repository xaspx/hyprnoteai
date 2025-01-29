import contextlib
from enum import Enum
from typing import Callable, List, Optional, Type, TYPE_CHECKING
from pydantic import BaseModel, Field

from mcp_agent.workflows.llm.augmented_llm import (
    AugmentedLLM,
    MessageParamT,
    MessageT,
    ModelT,
    RequestParams,
)
from mcp_agent.agents.agent import Agent
from mcp_agent.logging.logger import get_logger

if TYPE_CHECKING:
    from mcp_agent.context import Context

logger = get_logger(__name__)


class QualityRating(str, Enum):
    """Enum for evaluation quality ratings"""

    POOR = 0  # Major improvements needed
    FAIR = 1  # Several improvements needed
    GOOD = 2  # Minor improvements possible
    EXCELLENT = 3  # No improvements needed


class EvaluationResult(BaseModel):
    """Model representing the evaluation result from the evaluator LLM"""

    rating: QualityRating = Field(description="Quality rating of the response")
    feedback: str = Field(
        description="Specific feedback and suggestions for improvement"
    )
    needs_improvement: bool = Field(
        description="Whether the output needs further improvement"
    )
    focus_areas: List[str] = Field(
        default_factory=list, description="Specific areas to focus on in next iteration"
    )


class EvaluatorOptimizerLLM(AugmentedLLM[MessageParamT, MessageT]):
    """
    Implementation of the evaluator-optimizer workflow where one LLM generates responses
    while another provides evaluation and feedback in a refinement loop.

    This can be used either:
    1. As a standalone workflow with its own optimizer agent
    2. As a wrapper around another workflow (Orchestrator, Router, ParallelLLM) to add
       evaluation and refinement capabilities

    When to use this workflow:
    - When you have clear evaluation criteria and iterative refinement provides value
    - When LLM responses improve with articulated feedback
    - When the task benefits from focused iteration on specific aspects

    Examples:
    - Literary translation with "expert" refinement
    - Complex search tasks needing multiple rounds
    - Document writing requiring multiple revisions
    """

    def __init__(
        self,
        optimizer: Agent | AugmentedLLM,
        evaluator: str | Agent | AugmentedLLM,
        min_rating: QualityRating = QualityRating.GOOD,
        max_refinements: int = 3,
        llm_factory: Callable[[Agent], AugmentedLLM] | None = None,
        context: Optional["Context"] = None,
    ):
        """
        Initialize the evaluator-optimizer workflow.

        Args:
            optimizer: The agent/LLM/workflow that generates responses. Can be:
                     - An Agent that will be converted to an AugmentedLLM
                     - An AugmentedLLM instance
                     - An Orchestrator/Router/ParallelLLM workflow
            evaluator_agent: The agent/LLM that evaluates responses
            evaluation_criteria: Criteria for the evaluator to assess responses
            min_rating: Minimum acceptable quality rating
            max_refinements: Maximum refinement iterations
            llm_factory: Optional factory to create LLMs from agents
        """
        super().__init__(context=context)

        # Set up the optimizer
        self.name = optimizer.name
        self.llm_factory = llm_factory
        self.optimizer = optimizer
        self.evaluator = evaluator

        if isinstance(optimizer, Agent):
            if not llm_factory:
                raise ValueError("llm_factory is required when using an Agent")

            self.optimizer_llm = llm_factory(agent=optimizer)
            self.aggregator = optimizer
            self.instruction = (
                optimizer.instruction
                if isinstance(optimizer.instruction, str)
                else None
            )

        elif isinstance(optimizer, AugmentedLLM):
            self.optimizer_llm = optimizer
            self.aggregator = optimizer.aggregator
            self.instruction = optimizer.instruction

        else:
            raise ValueError(f"Unsupported optimizer type: {type(optimizer)}")

        self.history = self.optimizer_llm.history

        # Set up the evaluator
        if isinstance(evaluator, AugmentedLLM):
            self.evaluator_llm = evaluator
        elif isinstance(evaluator, Agent):
            if not llm_factory:
                raise ValueError(
                    "llm_factory is required when using an Agent evaluator"
                )

            self.evaluator_llm = llm_factory(agent=evaluator)
        elif isinstance(evaluator, str):
            # If a string is passed as the evaluator, we use it as the evaluation criteria
            # and create an evaluator agent with that instruction
            if not llm_factory:
                raise ValueError(
                    "llm_factory is required when using a string evaluator"
                )

            self.evaluator_llm = llm_factory(
                agent=Agent(name="Evaluator", instruction=evaluator)
            )
        else:
            raise ValueError(f"Unsupported evaluator type: {type(evaluator)}")

        self.min_rating = min_rating
        self.max_refinements = max_refinements

        # Track iteration history
        self.refinement_history = []

    async def generate(
        self,
        message: str | MessageParamT | List[MessageParamT],
        request_params: RequestParams | None = None,
    ) -> List[MessageT]:
        """Generate an optimized response through evaluation-guided refinement"""
        refinement_count = 0
        response = None
        best_response = None
        best_rating = QualityRating.POOR
        self.refinement_history = []

        # Initial generation
        async with contextlib.AsyncExitStack() as stack:
            if isinstance(self.optimizer, Agent):
                await stack.enter_async_context(self.optimizer)
            response = await self.optimizer_llm.generate(
                message=message,
                request_params=request_params,
            )

        best_response = response

        while refinement_count < self.max_refinements:
            logger.debug("Optimizer result:", data=response)

            # Evaluate current response
            eval_prompt = self._build_eval_prompt(
                original_request=str(message),
                current_response="\n".join(str(r) for r in response)
                if isinstance(response, list)
                else str(response),
                iteration=refinement_count,
            )

            evaluation_result = None
            async with contextlib.AsyncExitStack() as stack:
                if isinstance(self.evaluator, Agent):
                    await stack.enter_async_context(self.evaluator)

                evaluation_result = await self.evaluator_llm.generate_structured(
                    message=eval_prompt,
                    response_model=EvaluationResult,
                    request_params=request_params,
                )

            # Track iteration
            self.refinement_history.append(
                {
                    "attempt": refinement_count + 1,
                    "response": response,
                    "evaluation_result": evaluation_result,
                }
            )

            logger.debug("Evaluator result:", data=evaluation_result)

            # Track best response (using enum ordering)
            if evaluation_result.rating.value > best_rating.value:
                best_rating = evaluation_result.rating
                best_response = response
                logger.debug(
                    "New best response:",
                    data={"rating": best_rating, "response": best_response},
                )

            # Check if we've reached acceptable quality
            if (
                evaluation_result.rating.value >= self.min_rating.value
                or not evaluation_result.needs_improvement
            ):
                logger.debug(
                    f"Acceptable quality {evaluation_result.rating.value} reached",
                    data={
                        "rating": evaluation_result.rating.value,
                        "needs_improvement": evaluation_result.needs_improvement,
                        "min_rating": self.min_rating.value,
                    },
                )
                break

            # Generate refined response
            refinement_prompt = self._build_refinement_prompt(
                original_request=str(message),
                current_response="\n".join(str(r) for r in response)
                if isinstance(response, list)
                else str(response),
                feedback=evaluation_result,
                iteration=refinement_count,
            )

            async with contextlib.AsyncExitStack() as stack:
                if isinstance(self.optimizer, Agent):
                    await stack.enter_async_context(self.optimizer)

                response = await self.optimizer_llm.generate(
                    message=refinement_prompt,
                    request_params=request_params,
                )

            refinement_count += 1

        return best_response

    async def generate_str(
        self,
        message: str | MessageParamT | List[MessageParamT],
        request_params: RequestParams | None = None,
    ) -> str:
        """Generate an optimized response and return it as a string"""
        response = await self.generate(
            message=message,
            request_params=request_params,
        )

        return "\n".join(self.optimizer_llm.message_str(r) for r in response)

    async def generate_structured(
        self,
        message: str | MessageParamT | List[MessageParamT],
        response_model: Type[ModelT],
        request_params: RequestParams | None = None,
    ) -> ModelT:
        """Generate an optimized structured response"""
        response_str = await self.generate_str(
            message=message, request_params=request_params
        )

        return await self.optimizer.generate_structured(
            message=response_str,
            response_model=response_model,
            request_params=request_params,
        )

    def _build_eval_prompt(
        self, original_request: str, current_response: str, iteration: int
    ) -> str:
        """Build the evaluation prompt for the evaluator"""
        return f"""
        Evaluate the following response based on these criteria:
        {self.evaluator.instruction}

        Original Request: {original_request}
        Current Response (Iteration {iteration + 1}): {current_response}

        Provide your evaluation as a structured response with:
        1. A quality rating (EXCELLENT, GOOD, FAIR, or POOR)
        2. Specific feedback and suggestions
        3. Whether improvement is needed (true/false)
        4. Focus areas for improvement

        Rate as EXCELLENT only if no improvements are needed.
        Rate as GOOD if only minor improvements are possible.
        Rate as FAIR if several improvements are needed.
        Rate as POOR if major improvements are needed.
        """

    def _build_refinement_prompt(
        self,
        original_request: str,
        current_response: str,
        feedback: EvaluationResult,
        iteration: int,
    ) -> str:
        """Build the refinement prompt for the optimizer"""
        return f"""
        Improve your previous response based on the evaluation feedback.
        
        Original Request: {original_request}
        
        Previous Response (Iteration {iteration + 1}): 
        {current_response}
        
        Quality Rating: {feedback.rating}
        Feedback: {feedback.feedback}
        Areas to Focus On: {", ".join(feedback.focus_areas)}
        
        Generate an improved version addressing the feedback while maintaining accuracy and relevance.
        """
