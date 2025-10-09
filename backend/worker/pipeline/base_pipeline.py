"""
Base Pipeline Classes

This module defines the abstract base classes for the pipeline pattern
used in data processing workflows.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..strategies.base_strategy import MarketData, Signal


@dataclass
class ProcessingResult:
    """Container for pipeline processing results"""
    
    success: bool
    data: Optional[MarketData] = None
    signals: Optional[List[Signal]] = None
    error: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PipelineContext:
    """Context object passed through pipeline steps"""
    
    market_data: MarketData
    signals: List[Signal] = None
    indicators: dict = None
    errors: List[str] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.signals is None:
            self.signals = []
        if self.indicators is None:
            self.indicators = {}
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class ProcessingStep(ABC):
    """
    Abstract base class for all processing steps in a pipeline.
    
    Each step represents a single operation in the data processing workflow,
    such as data validation, indicator calculation, or signal evaluation.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the processing step.
        
        Args:
            name: Optional name for the step. If not provided, 
                  will use the class name.
        """
        self.name = name or self.__class__.__name__
        self._parameters: dict = {}
    
    @abstractmethod
    def process(self, data: MarketData) -> MarketData:
        """
        Process the input data and return modified data.
        
        Args:
            data: Input market data
            
        Returns:
            Processed market data
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If processing fails
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of this processing step.
        
        Returns:
            Step name string
        """
        pass
    
    def get_parameters(self) -> dict:
        """
        Get step parameters.
        
        Returns:
            Dictionary of step parameters
        """
        return self._parameters.copy()
    
    def set_parameter(self, key: str, value: Any) -> None:
        """
        Set a step parameter.
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        self._parameters[key] = value
    
    def validate_input(self, data: MarketData) -> bool:
        """
        Validate input data for this step.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if data is None:
                return False
            
            if not isinstance(data, MarketData):
                return False
            
            return True
        except Exception:
            return False
    
    def __str__(self) -> str:
        """String representation of the step"""
        return f"{self.get_name()}({self._parameters})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the step"""
        return f"{self.__class__.__name__}(name='{self.get_name()}', parameters={self._parameters})"


class ProcessingPipeline:
    """
    Main processing pipeline that executes a sequence of processing steps.
    
    This class implements the pipeline pattern, allowing for flexible
    composition of data processing workflows.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize the processing pipeline.
        
        Args:
            name: Optional name for the pipeline
        """
        self.name = name or self.__class__.__name__
        self.steps: List[ProcessingStep] = []
        self._parameters: dict = {}
    
    def add_step(self, step: ProcessingStep) -> 'ProcessingPipeline':
        """
        Add a processing step to the pipeline.
        
        Args:
            step: Processing step to add
            
        Returns:
            Self for method chaining
        """
        if not isinstance(step, ProcessingStep):
            raise ValueError(f"Step must be an instance of ProcessingStep, got {type(step)}")
        
        self.steps.append(step)
        return self
    
    def remove_step(self, step_name: str) -> bool:
        """
        Remove a processing step by name.
        
        Args:
            step_name: Name of the step to remove
            
        Returns:
            True if step was removed, False if not found
        """
        for i, step in enumerate(self.steps):
            if step.get_name() == step_name:
                del self.steps[i]
                return True
        return False
    
    def execute(self, data: MarketData) -> ProcessingResult:
        """
        Execute all steps in the pipeline.
        
        Args:
            data: Input market data
            
        Returns:
            ProcessingResult with success status and results
        """
        try:
            if not data:
                return ProcessingResult(
                    success=False,
                    error="No input data provided"
                )
            
            # Execute each step in sequence
            current_data = data
            signals = []
            
            for i, step in enumerate(self.steps):
                try:
                    # Validate input for this step
                    if not step.validate_input(current_data):
                        return ProcessingResult(
                            success=False,
                            error=f"Input validation failed for step {step.get_name()}"
                        )
                    
                    # Process the data
                    current_data = step.process(current_data)
                    
                    # Check if step generated signals
                    if hasattr(current_data, 'signals') and current_data.signals:
                        signals.extend(current_data.signals)
                    
                except Exception as e:
                    return ProcessingResult(
                        success=False,
                        error=f"Error in step {step.get_name()}: {str(e)}"
                    )
            
            # Return successful result
            return ProcessingResult(
                success=True,
                data=current_data,
                signals=signals if signals else None,
                metadata={
                    'pipeline_name': self.name,
                    'steps_executed': len(self.steps),
                    'step_names': [step.get_name() for step in self.steps]
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error=f"Pipeline execution failed: {str(e)}"
            )
    
    def get_steps(self) -> List[ProcessingStep]:
        """
        Get list of processing steps.
        
        Returns:
            List of processing steps
        """
        return self.steps.copy()
    
    def get_step_count(self) -> int:
        """
        Get number of processing steps.
        
        Returns:
            Number of steps in the pipeline
        """
        return len(self.steps)
    
    def get_parameters(self) -> dict:
        """
        Get pipeline parameters.
        
        Returns:
            Dictionary of pipeline parameters
        """
        return self._parameters.copy()
    
    def set_parameter(self, key: str, value: Any) -> None:
        """
        Set a pipeline parameter.
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        self._parameters[key] = value
    
    def clear_steps(self) -> None:
        """Clear all processing steps from the pipeline."""
        self.steps.clear()
    
    def __str__(self) -> str:
        """String representation of the pipeline"""
        step_names = [step.get_name() for step in self.steps]
        return f"{self.name}({len(self.steps)} steps: {', '.join(step_names)})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the pipeline"""
        return f"{self.__class__.__name__}(name='{self.name}', steps={len(self.steps)})"
