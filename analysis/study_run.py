"""Plan a sealed study and do not fit an adapter."""

from __future__ import annotations

from pathlib import Path

from analysis.equal_compute import (
    FrozenTrainingRecipe,
    RecipeNotFrozen,
    TrainingNotRun,
    TargetTokenCount,
    plan_equal_compute,
)


class StudyRunPlan:
    """Plan every sealed prefix under a frozen recipe. Do not fit an adapter."""

    def __init__(
        self,
        recipe: FrozenTrainingRecipe,
        seal_dir: Path,
        count_target_tokens: TargetTokenCount,
        sequence_length: int = 8192,
    ) -> None:
        self.recipe = recipe
        self.seal_dir = seal_dir
        self.count_target_tokens = count_target_tokens
        self.sequence_length = sequence_length

    def plan(self) -> dict[str, object]:
        """Raise RecipeNotFrozen before the seal is read, then return the plan."""
        try:
            self.recipe.require_ready()
        except RecipeNotFrozen:
            raise
        return plan_equal_compute(
            self.seal_dir,
            self.count_target_tokens,
            self.sequence_length,
        )

    def train(self) -> None:
        self.plan()
        raise TrainingNotRun("the schedule is planned and no adapter was fit")
