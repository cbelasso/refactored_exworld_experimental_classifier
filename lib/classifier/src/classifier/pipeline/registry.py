"""
Stage Registry

Manages stage registration and dependency resolution.
This is where stages are discovered and their execution order is determined.

Design Philosophy:
- Explicit registration (no magic auto-discovery)
- Topological sort for dependency resolution
- Clear error messages for missing dependencies or cycles
"""

from typing import Dict, List, Optional, Set

from .interfaces import Stage


class StageRegistry:
    """
    Registry for pipeline stages.

    Handles:
    - Stage registration
    - Dependency resolution via topological sort
    - Validation of dependency graph

    Usage:
        registry = StageRegistry()
        registry.register(stage1)
        registry.register(stage2)

        # Get execution order
        order = registry.resolve_order()  # ["stage1", "stage2"]

        # Or run specific stages (dependencies auto-included)
        order = registry.resolve_order(["stage2"])  # ["stage1", "stage2"]
    """

    def __init__(self):
        self._stages: Dict[str, Stage] = {}

    def register(self, stage: Stage) -> "StageRegistry":
        """
        Register a stage.

        Returns self for chaining:
            registry.register(s1).register(s2).register(s3)
        """
        name = stage.name

        if name in self._stages:
            raise ValueError(f"Stage '{name}' is already registered")

        self._stages[name] = stage
        return self

    def get(self, name: str) -> Stage:
        """Get a stage by name."""
        if name not in self._stages:
            available = list(self._stages.keys())
            raise ValueError(f"Unknown stage: '{name}'. Available stages: {available}")
        return self._stages[name]

    def list_stages(self) -> List[str]:
        """List all registered stage names."""
        return list(self._stages.keys())

    def resolve_order(
        self,
        stage_names: Optional[List[str]] = None,
        include_dependencies: bool = True,
    ) -> List[str]:
        """
        Resolve execution order via topological sort.

        Args:
            stage_names: Stages to run (None = all registered stages)
            include_dependencies: If True, automatically include dependencies
                                  even if not in stage_names

        Returns:
            List of stage names in execution order

        Raises:
            ValueError: If circular dependency detected or missing dependency
        """
        if stage_names is None:
            stage_names = list(self._stages.keys())

        # Validate all requested stages exist
        for name in stage_names:
            if name not in self._stages:
                raise ValueError(f"Unknown stage: '{name}'")

        # Build the set of stages to include
        to_include = set(stage_names)

        if include_dependencies:
            # Recursively add dependencies
            to_process = list(to_include)
            while to_process:
                name = to_process.pop()
                stage = self._stages[name]

                for dep in stage.dependencies:
                    if dep not in self._stages:
                        raise ValueError(
                            f"Stage '{name}' depends on '{dep}', but '{dep}' is not registered"
                        )
                    if dep not in to_include:
                        to_include.add(dep)
                        to_process.append(dep)

        # Build dependency graph for included stages
        graph: Dict[str, Set[str]] = {}
        for name in to_include:
            stage = self._stages[name]
            # Only include dependencies that are in our set
            deps = set(stage.dependencies) & to_include
            graph[name] = deps

        # Topological sort (Kahn's algorithm)
        return self._topological_sort(graph)

    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """
        Perform topological sort on the dependency graph.

        Uses Kahn's algorithm.
        """
        # Calculate in-degrees
        in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            for dep in deps:
                # dep points to node (dep must run before node)
                pass

        # Actually, we need reverse: count how many depend ON each node
        # In our graph, deps are what a node depends ON
        # So we need: for each node, count nodes that have it in their deps
        reverse_in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            for dep in deps:
                pass  # node depends on dep

        # Let's use standard approach: in_degree = number of deps
        in_degree = {node: len(deps) for node, deps in graph.items()}

        # Queue of nodes with no dependencies (in_degree = 0)
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Take any node with no remaining dependencies
            current = queue.pop(0)
            result.append(current)

            # Remove this node from other nodes' dependencies
            for node, deps in graph.items():
                if current in deps:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)

        # Check for cycles
        if len(result) != len(graph):
            # Find the cycle
            remaining = set(graph.keys()) - set(result)
            raise ValueError(f"Circular dependency detected among stages: {remaining}")

        return result

    def validate(self) -> List[str]:
        """
        Validate the registry.

        Returns list of warnings/issues (empty if valid).
        Raises ValueError for critical issues.
        """
        issues = []

        # Check all dependencies exist
        for name, stage in self._stages.items():
            for dep in stage.dependencies:
                if dep not in self._stages:
                    raise ValueError(f"Stage '{name}' depends on unregistered stage '{dep}'")

        # Check for cycles (will raise if found)
        try:
            self.resolve_order()
        except ValueError as e:
            raise

        # Check for orphan stages (no dependents and not terminal)
        # This is just a warning, not an error
        has_dependents = set()
        for name, stage in self._stages.items():
            has_dependents.update(stage.dependencies)

        roots = set(self._stages.keys()) - has_dependents
        if len(roots) > 1:
            issues.append(
                f"Multiple root stages (no dependencies): {roots}. This is fine if intentional."
            )

        return issues


def create_default_registry(
    content,
    schema_factory,
) -> StageRegistry:
    """
    Create a registry with all default stages.

    This is the standard 3-stage pipeline:
    1. Category Detection
    2. Element Extraction
    3. Attribute Extraction

    Args:
        content: ContentProvider instance
        schema_factory: SchemaFactory instance

    Returns:
        Configured StageRegistry
    """
    from ..stages import (
        AttributeExtractionStage,
        CategoryDetectionStage,
        ElementExtractionStage,
    )

    registry = StageRegistry()

    registry.register(CategoryDetectionStage(content, schema_factory))
    registry.register(ElementExtractionStage(content, schema_factory))
    registry.register(AttributeExtractionStage(content, schema_factory))

    return registry
