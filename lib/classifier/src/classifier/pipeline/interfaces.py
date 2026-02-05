"""Pipeline interfaces - Stage and PipelineContext."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..infrastructure.llm.interfaces import LLMClient


class PipelineContext:
    """Carries data between pipeline stages."""

    def __init__(self):
        self._results: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Any] = {}

    def get_stage_result(self, stage_name: str, text: str) -> Optional[Any]:
        return self._results.get(stage_name, {}).get(text)

    def set_stage_result(self, stage_name: str, text: str, result: Any) -> None:
        if stage_name not in self._results:
            self._results[stage_name] = {}
        self._results[stage_name][text] = result

    def set_stage_results(self, stage_name: str, results: Dict[str, Any]) -> None:
        self._results[stage_name] = results

    def get_all_stage_results(self, stage_name: str) -> Dict[str, Any]:
        return self._results.get(stage_name, {})

    def get_merged_results(self) -> Dict[str, Dict[str, Any]]:
        merged = {}
        for stage_name, stage_results in self._results.items():
            for text, result in stage_results.items():
                if text not in merged:
                    merged[text] = {"_text": text}
                merged[text][stage_name] = result
        return merged

    def set_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        return self._metadata.get(key)


class Stage(ABC):
    """A self-contained processing unit in the classification pipeline."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def dependencies(self) -> List[str]:
        return []

    @abstractmethod
    def process(
        self, texts: List[str], context: PipelineContext, llm: "LLMClient"
    ) -> Dict[str, Any]:
        pass

    def get_prompt_for_export(self, text: str, context: PipelineContext) -> Optional[str]:
        return None
