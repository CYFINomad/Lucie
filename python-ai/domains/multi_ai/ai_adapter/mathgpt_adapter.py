from typing import Dict, List, Optional, Union
import requests
import json
from abc import ABC, abstractmethod


class MathGPTModel:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category


class MathGPTAdapter:
    """
    Adapter for MathGPT, a specialized LLM for mathematical problem-solving.
    This adapter provides access to models optimized for mathematical reasoning,
    equation solving, and computational tasks.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.mathgpt.example"):
        """
        Initialize the MathGPT adapter.

        Args:
            api_key (str): API key for authenticating with the MathGPT service
            base_url (str): Base URL for the MathGPT API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.available_models = self._initialize_models()

    def _initialize_models(self) -> Dict[str, MathGPTModel]:
        """Initialize the available MathGPT models with their metadata."""
        return {
            "mathgpt-v1": MathGPTModel(
                "mathgpt-v1", "General-purpose mathematical problem solver", "general"
            ),
            "mathgpt-v1-pro": MathGPTModel(
                "mathgpt-v1-pro",
                "Advanced model for complex mathematical reasoning",
                "advanced",
            ),
            "mathgpt-calculus": MathGPTModel(
                "mathgpt-calculus",
                "Specialized for calculus and analysis problems",
                "specialized",
            ),
            "mathgpt-algebra": MathGPTModel(
                "mathgpt-algebra",
                "Optimized for algebraic problems and equation solving",
                "specialized",
            ),
            "mathgpt-stats": MathGPTModel(
                "mathgpt-stats",
                "Specialized for statistics and probability problems",
                "specialized",
            ),
            "mathgpt-geometry": MathGPTModel(
                "mathgpt-geometry",
                "Optimized for geometric reasoning and visualization",
                "specialized",
            ),
            "mathgpt-latex": MathGPTModel(
                "mathgpt-latex",
                "Focused on converting math problems to LaTeX format",
                "specialized",
            ),
        }

    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models with their metadata."""
        return [
            {
                "name": model.name,
                "description": model.description,
                "category": model.category,
            }
            for model in self.available_models.values()
        ]

    def generate_response(
        self,
        prompt: str,
        model_name: str = "mathgpt-v1",
        temperature: float = 0.3,  # Lower default temperature for math precision
        max_tokens: Optional[int] = 1024,
        system_prompt: Optional[str] = None,
        show_work: bool = True,  # Option to show intermediate steps
        format_as_latex: bool = False,  # Option to format response as LaTeX
        verify_solution: bool = True,  # Option to verify the solution
    ) -> Dict[str, Union[str, Dict]]:
        """
        Generate a mathematical solution using the specified MathGPT model.

        Args:
            prompt (str): The mathematical problem to solve
            model_name (str): Which MathGPT model to use
            temperature (float): Sampling temperature (lower is more deterministic)
            max_tokens (Optional[int]): Maximum tokens to generate
            system_prompt (Optional[str]): System instruction
            show_work (bool): Whether to show intermediate steps in the solution
            format_as_latex (bool): Whether to format the response as LaTeX
            verify_solution (bool): Whether to verify the solution

        Returns:
            Dict[str, Union[str, Dict]]: The solution and metadata
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "options": {
                    "show_work": show_work,
                    "format_as_latex": format_as_latex,
                    "verify_solution": verify_solution,
                },
            }

            if system_prompt:
                payload["system_prompt"] = system_prompt

            response = requests.post(
                f"{self.base_url}/v1/generate", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()

                # Extract the different parts of the response
                solution = result.get("solution", "")
                working_steps = result.get("working_steps", [])
                latex_solution = result.get("latex_solution", "")

                # Determine the text to return
                if format_as_latex:
                    text = latex_solution or solution
                elif show_work and working_steps:
                    text = "\n".join(working_steps) + "\n\nFinal answer: " + solution
                else:
                    text = solution

                return {
                    "text": text,
                    "metadata": {
                        "model": model_name,
                        "tokens": result.get("tokens_used", 0),
                        "calculation_time": result.get("calculation_time_ms", 0),
                        "confidence": result.get("confidence", 0.0),
                        "is_verified": result.get("is_verified", False),
                        "has_working_steps": bool(working_steps),
                        "has_latex": bool(latex_solution),
                    },
                    "solution_data": {
                        "solution": solution,
                        "working_steps": working_steps,
                        "latex_solution": latex_solution,
                    },
                }
            else:
                return {
                    "text": f"Error: {response.status_code} - {response.text}",
                    "metadata": {"error": True},
                }

        except Exception as e:
            return {
                "text": f"Error generating solution: {str(e)}",
                "metadata": {"error": True},
            }

    def verify_solution(
        self, problem: str, solution: str, model_name: str = "mathgpt-v1"
    ) -> Dict[str, Union[bool, Dict]]:
        """
        Verify if a given solution to a mathematical problem is correct.

        Args:
            problem (str): The original mathematical problem
            solution (str): The proposed solution to verify
            model_name (str): Which MathGPT model to use for verification

        Returns:
            Dict[str, Union[bool, Dict]]: Verification results
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": model_name,
                "problem": problem,
                "proposed_solution": solution,
            }

            response = requests.post(
                f"{self.base_url}/v1/verify", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()

                return {
                    "is_correct": result.get("is_correct", False),
                    "confidence": result.get("confidence", 0.0),
                    "explanation": result.get("explanation", ""),
                    "metadata": {
                        "model": model_name,
                        "verification_method": result.get(
                            "verification_method", "unknown"
                        ),
                    },
                }
            else:
                return {
                    "is_correct": False,
                    "metadata": {
                        "error": True,
                        "message": f"Error: {response.status_code} - {response.text}",
                    },
                }

        except Exception as e:
            return {
                "is_correct": False,
                "metadata": {
                    "error": True,
                    "message": f"Error verifying solution: {str(e)}",
                },
            }

    def generate_practice_problems(
        self,
        topic: str,
        difficulty: str = "medium",  # "easy", "medium", "hard", or "expert"
        count: int = 3,
        model_name: str = "mathgpt-v1",
        with_solutions: bool = True,
    ) -> Dict[str, Union[List[Dict], Dict]]:
        """
        Generate practice problems on a specific mathematical topic.

        Args:
            topic (str): Mathematical topic for problems (e.g., "integration", "systems of equations")
            difficulty (str): Difficulty level of problems
            count (int): Number of problems to generate
            model_name (str): Which MathGPT model to use
            with_solutions (bool): Whether to include solutions

        Returns:
            Dict[str, Union[List[Dict], Dict]]: Generated problems and metadata
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": model_name,
                "topic": topic,
                "difficulty": difficulty,
                "count": count,
                "with_solutions": with_solutions,
            }

            response = requests.post(
                f"{self.base_url}/v1/generate_problems", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()

                return {
                    "problems": result.get("problems", []),
                    "metadata": {
                        "model": model_name,
                        "topic": topic,
                        "difficulty": difficulty,
                        "count": len(result.get("problems", [])),
                    },
                }
            else:
                return {
                    "problems": [],
                    "metadata": {
                        "error": True,
                        "message": f"Error: {response.status_code} - {response.text}",
                    },
                }

        except Exception as e:
            return {
                "problems": [],
                "metadata": {
                    "error": True,
                    "message": f"Error generating problems: {str(e)}",
                },
            }

    def convert_to_latex(
        self,
        math_text: str,
        model_name: str = "mathgpt-latex",
    ) -> Dict[str, Union[str, Dict]]:
        """
        Convert a mathematical expression or solution to LaTeX format.

        Args:
            math_text (str): Mathematical expression to convert
            model_name (str): Which MathGPT model to use

        Returns:
            Dict[str, Union[str, Dict]]: LaTeX output and metadata
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": model_name,
                "math_text": math_text,
            }

            response = requests.post(
                f"{self.base_url}/v1/to_latex", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()

                return {
                    "latex": result.get("latex", ""),
                    "display_latex": result.get(
                        "display_latex", ""
                    ),  # For display math mode
                    "inline_latex": result.get(
                        "inline_latex", ""
                    ),  # For inline math mode
                    "metadata": {
                        "model": model_name,
                        "tokens": result.get("tokens_used", 0),
                    },
                }
            else:
                return {
                    "latex": "",
                    "metadata": {
                        "error": True,
                        "message": f"Error: {response.status_code} - {response.text}",
                    },
                }

        except Exception as e:
            return {
                "latex": "",
                "metadata": {
                    "error": True,
                    "message": f"Error converting to LaTeX: {str(e)}",
                },
            }

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model."""
        if model_name in self.available_models:
            model = self.available_models[model_name]
            return {
                "name": model.name,
                "description": model.description,
                "category": model.category,
            }
        return None
