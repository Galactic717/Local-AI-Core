"""
Brain Router - Intelligent Model Selection System
Automatically selects the best Ollama model based on query type, language, and complexity
"""
import re
from typing import Dict, List, Optional
from enum import Enum

class QueryType(Enum):
    """Types of queries for model selection"""
    GENERAL = "general"
    CODING = "coding"
    MATH = "math"
    REASONING = "reasoning"
    MULTILINGUAL = "multilingual"
    SIMPLE = "simple"

class BrainRouter:
    """
    Intelligent router that selects the best LLM model based on query characteristics
    """

    def __init__(self):
        # Model capabilities mapping
        self.models = {
            "qwen3.5:9b": {
                "size_gb": 6.6,
                "strengths": ["general", "reasoning", "knowledge"],
                "languages": ["en", "uk", "ru", "zh"],
                "speed": "medium",
                "quality": "high",
                "description": "Найрозумніша універсальна. Найкращий баланс логіки, знань та швидкості."
            },
            "falcon3:10b": {
                "size_gb": 6.3,
                "strengths": ["math", "science", "reasoning"],
                "languages": ["en"],
                "speed": "medium",
                "quality": "high",
                "description": "Наука та математика. Найпотужніша у своєму класі для складних обчислень."
            },
            "granite3-dense:8b": {
                "size_gb": 4.9,
                "strengths": ["tools", "rag", "agents"],
                "languages": ["en"],
                "speed": "fast",
                "quality": "high",
                "description": "Агентські функції. Ідеально працює з інструментами (Tool-calling) та MCP."
            },
            "deepseek-r1:8b": {
                "size_gb": 5.2,
                "strengths": ["reasoning", "planning", "cot"],
                "languages": ["en", "zh"],
                "speed": "slow",
                "quality": "very_high",
                "description": "Reasoning (CoT). Найкраща для складного покрокового планування."
            },
            "aya-expanse:8b": {
                "size_gb": 5.1,
                "strengths": ["multilingual", "translation"],
                "languages": ["en", "uk", "pl", "ru", "ar", "hi", "zh", "es", "fr", "de"],
                "speed": "medium",
                "quality": "high",
                "description": "Мультимовність. Якщо потрібна ідеальна українська/польська/інші."
            },
            "llama3.2:latest": {
                "size_gb": 2.0,
                "strengths": ["general", "fast"],
                "languages": ["en"],
                "speed": "very_fast",
                "quality": "medium",
                "description": "Швидкі відповіді. Найменша та найшвидша модель."
            },
            "qwen2.5-coder:32b": {
                "size_gb": 19.9,
                "strengths": ["coding", "debugging", "refactoring"],
                "languages": ["en", "zh"],
                "speed": "slow",
                "quality": "very_high",
                "description": "Coding спеціаліст. Найкраща для програмування."
            }
        }

        # Keyword patterns for query type detection
        self.patterns = {
            QueryType.CODING: [
                r'\b(code|coding|program|function|class|debug|error|bug|refactor|api|algorithm)\b',
                r'\b(python|javascript|java|c\+\+|rust|go|typescript|sql)\b',
                r'```',  # Code blocks
            ],
            QueryType.MATH: [
                r'\b(calculate|compute|solve|equation|formula|math|integral|derivative|probability)\b',
                r'\b(sum|average|mean|median|variance|statistics)\b',
                r'[\d\+\-\*/\=\(\)]+',  # Math expressions
            ],
            QueryType.REASONING: [
                r'\b(why|how|explain|analyze|compare|evaluate|reason|logic|think|plan)\b',
                r'\b(step by step|let\'s think|break down|consider)\b',
            ],
            QueryType.MULTILINGUAL: [
                r'[а-яА-ЯіІїЇєЄґҐ]+',  # Ukrainian/Russian
                r'[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+',  # Polish
                r'[äöüßÄÖÜ]+',  # German
                r'[àâäæçéèêëïîôùûüÿœ]+',  # French
            ],
            QueryType.SIMPLE: [
                r'^\w{1,20}$',  # Single word
                r'^.{1,50}$',  # Very short query
            ]
        }

    def detect_language(self, query: str) -> str:
        """Detect query language"""
        # Ukrainian/Russian
        if re.search(r'[а-яА-ЯіІїЇєЄґҐ]', query):
            # Distinguish Ukrainian from Russian
            if re.search(r'[іІїЇєЄґҐ]', query):
                return "uk"
            return "ru"

        # Polish
        if re.search(r'[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', query):
            return "pl"

        # German
        if re.search(r'[äöüßÄÖÜ]', query):
            return "de"

        # French
        if re.search(r'[àâäæçéèêëïîôùûüÿœ]', query):
            return "fr"

        # Chinese
        if re.search(r'[\u4e00-\u9fff]', query):
            return "zh"

        # Default to English
        return "en"

    def detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query"""
        query_lower = query.lower()

        # Check each pattern type
        for query_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return query_type

        # Default to general
        return QueryType.GENERAL

    def estimate_complexity(self, query: str) -> str:
        """Estimate query complexity: simple, medium, complex"""
        # Simple: short queries, single questions
        if len(query) < 50:
            return "simple"

        # Complex: multiple questions, detailed requests
        if len(query) > 200 or query.count('?') > 2 or query.count('\n') > 3:
            return "complex"

        # Medium: everything else
        return "medium"

    def select_model(self, query: str, available_ram_gb: float = 12.0) -> Dict:
        """
        Select the best model for the given query

        Args:
            query: User query text
            available_ram_gb: Available RAM in GB (for model size filtering)

        Returns:
            Dict with selected model info and reasoning
        """
        # Detect query characteristics
        language = self.detect_language(query)
        query_type = self.detect_query_type(query)
        complexity = self.estimate_complexity(query)

        # Score each model
        scores = {}
        for model_name, model_info in self.models.items():
            score = 0
            reasons = []

            # Check if model fits in RAM
            if model_info["size_gb"] > available_ram_gb:
                continue  # Skip models that don't fit

            # Language match (high priority)
            if language in model_info["languages"]:
                score += 30
                reasons.append(f"Підтримує {language}")

            # Query type match
            if query_type == QueryType.CODING and "coding" in model_info["strengths"]:
                score += 40
                reasons.append("Спеціалізація на coding")
            elif query_type == QueryType.MATH and "math" in model_info["strengths"]:
                score += 40
                reasons.append("Спеціалізація на математиці")
            elif query_type == QueryType.REASONING and "reasoning" in model_info["strengths"]:
                score += 35
                reasons.append("Сильний reasoning")
            elif query_type == QueryType.MULTILINGUAL and "multilingual" in model_info["strengths"]:
                score += 40
                reasons.append("Мультимовна модель")
            elif query_type == QueryType.SIMPLE and model_info["speed"] == "very_fast":
                score += 30
                reasons.append("Швидка відповідь")
            elif query_type == QueryType.GENERAL and "general" in model_info["strengths"]:
                score += 25
                reasons.append("Універсальна модель")

            # Complexity match
            if complexity == "simple" and model_info["speed"] in ["fast", "very_fast"]:
                score += 15
                reasons.append("Швидка для простих запитів")
            elif complexity == "complex" and model_info["quality"] in ["high", "very_high"]:
                score += 20
                reasons.append("Висока якість для складних запитів")

            # Quality bonus
            if model_info["quality"] == "very_high":
                score += 10
            elif model_info["quality"] == "high":
                score += 5

            # Speed bonus for simple queries
            if complexity == "simple":
                if model_info["speed"] == "very_fast":
                    score += 10
                elif model_info["speed"] == "fast":
                    score += 5

            scores[model_name] = {
                "score": score,
                "reasons": reasons,
                "info": model_info
            }

        # Select best model
        if not scores:
            # Fallback to smallest model if nothing fits
            return {
                "model": "llama3.2:latest",
                "score": 0,
                "reasons": ["Fallback: найменша модель"],
                "query_analysis": {
                    "language": language,
                    "type": query_type.value,
                    "complexity": complexity
                }
            }

        best_model = max(scores.items(), key=lambda x: x[1]["score"])

        return {
            "model": best_model[0],
            "score": best_model[1]["score"],
            "reasons": best_model[1]["reasons"],
            "description": best_model[1]["info"]["description"],
            "query_analysis": {
                "language": language,
                "type": query_type.value,
                "complexity": complexity
            }
        }

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model"""
        return self.models.get(model_name)

    def list_models(self) -> Dict[str, Dict]:
        """List all available models with their info"""
        return self.models


# Example usage
if __name__ == "__main__":
    router = BrainRouter()

    # Test queries
    test_queries = [
        "Привіт, як справи?",
        "Write a Python function to calculate fibonacci numbers",
        "Solve this equation: 2x + 5 = 15",
        "Explain quantum entanglement step by step",
        "Translate this to Polish: Hello world",
        "Hi",
        "Напиши функцію на Python для сортування масиву",
    ]

    print("Brain Router - Model Selection Examples\n")

    for query in test_queries:
        result = router.select_model(query)
        print(f"Query: {query[:50]}...")
        print(f"Selected: {result['model']}")
        print(f"Score: {result['score']}")
        print(f"Analysis: {result['query_analysis']}")
        print(f"Reasons: {', '.join(result['reasons'])}")
        print(f"Description: {result['description']}")
        print("-" * 80)
