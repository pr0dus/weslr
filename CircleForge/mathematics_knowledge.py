# mathematics_knowledge.py - Mathematics foundation for CircleForge
"""
Mathematics concepts that CircleForge should understand to model relationships,
patterns, and quantitative reasoning.
"""
from __future__ import annotations

# ============================================================================
# MATHEMATICS FOUNDATION
# ============================================================================

MATHEMATICS_FOUNDATIONS = {
    # Numbers and Operations
    "number_systems": {
        "natural": {"description": "counting numbers", "examples": ["1", "2", "3", "..."]},
        "integers": {"description": "whole numbers", "examples": ["-2", "-1", "0", "1", "2", "..."]},
        "rationals": {"description": "fractions", "examples": ["p/q where p, q are integers"]},
        "reals": {"description": "all points on number line", "examples": ["includes irrationals like pi, sqrt(2)"]},
        "complex": {"description": "a + bi", "examples": ["i = sqrt(-1)"]},
    },
    
    # Algebra
    "algebra": {
        "equations": {
            "linear": "ax + b = 0",
            "quadratic": "ax^2 + bx + c = 0",
            "polynomial": "a_n*x^n + ... + a_1*x + a_0 = 0",
        },
        "functions": {
            "linear": "f(x) = mx + b",
            "quadratic": "f(x) = ax^2 + bx + c",
            "exponential": "f(x) = ab^x",
            "logarithmic": "f(x) = log_b(x)",
        },
        "relationships": {
            "proportionality": "y = kx",
            "inverse": "y = k/x",
            "direct": "y = kx",
        },
    },
    
    # Geometry
    "geometry": {
        "shapes": {
            "triangle": {"sides": 3, "angles": 180},
            "rectangle": {"sides": 4, "angles": 90},
            "circle": {"radius": "r", "area": "pi*r^2", "circumference": "2*pi*r"},
            "sphere": {"radius": "r", "volume": "4/3*pi*r^3", "surface": "4*pi*r^2"},
        },
        "properties": {
            "symmetry": "balance across axis",
            "similarity": "same shape, different size",
            "congruence": "same shape and size",
        },
    },
    
    # Calculus
    "calculus": {
        "derivatives": {
            "definition": "rate of change",
            "notation": "f'(x), dy/dx",
            "meaning": "instantaneous slope",
        },
        "integrals": {
            "definition": "accumulation",
            "notation": "integral f(x)dx",
            "meaning": "area under curve",
        },
        "fundamental_theorem": "differentiation and integration are inverses",
    },
    
    # Probability and Statistics
    "probability": {
        "basic": {
            "probability": "P(A) = favorable/outcomes",
            "range": "0 <= P(A) <= 1",
            "complement": "P(not A) = 1 - P(A)",
        },
        "independence": "P(A and B) = P(A) * P(B)",
        "conditional": "P(A|B) = P(A and B) / P(B)",
    },
    "statistics": {
        "measures": {
            "mean": "average",
            "median": "middle value",
            "mode": "most frequent",
            "standard_deviation": "spread around mean",
        },
        "distributions": {
            "normal": "bell curve",
            "binomial": "success/failure trials",
            "poisson": "rare events",
        },
    },
    
    # Logic and Set Theory
    "logic": {
        "propositions": {
            "and": "and",
            "or": "or",
            "not": "not",
            "implies": "implies",
        },
        "quantifiers": {
            "for_all": "for_all",
            "there_exists": "there_exists",
        },
        "truth_tables": "systematic evaluation of logical expressions",
    },
    "set_theory": {
        "operations": {
            "union": "A union B",
            "intersection": "A intersection B",
            "complement": "A complement",
        },
        "relationships": {
            "subset": "A subset B",
            "proper_subset": "A proper_subset B",
            "element": "x in A",
        },
    },
    
    # Linear Algebra
    "linear_algebra": {
        "vectors": {
            "components": "[x, y, z]",
            "magnitude": "||v|| = sqrt(x^2 + y^2 + z^2)",
            "operations": "addition, scalar multiplication, dot product",
        },
        "matrices": {
            "notation": "A = [a_ij]",
            "operations": "multiplication, transpose, determinant",
        },
        "transformations": {
            "rotation": "change direction",
            "scaling": "change size",
            "projection": "shadow onto subspace",
        },
    },
    
    # Differential Equations
    "differential_equations": {
        "first_order": "dy/dx = f(x, y)",
        "second_order": "d^2y/dx^2 = f(x, y, dy/dx)",
        "systems": "multiple coupled equations",
        "applications": ["physics", "engineering", "biology", "economics"],
    },
    
    # Graph Theory
    "graph_theory": {
        "components": {
            "vertices": "nodes",
            "edges": "connections",
            "degree": "edges per vertex",
        },
        "paths": {
            "walk": "sequence of edges",
            "path": "no repeated vertices",
            "cycle": "starts and ends at same vertex",
        },
        "applications": ["networks", "algorithms", "social connections"],
    },
}

# ============================================================================
# MATHEMATICS TEACHING STRATEGY
# ============================================================================

MATHEMATICS_TEACHING_STRATEGY = {
    "approach": "abstraction_then_application",
    "methods": [
        "pattern_recognition",    # Find regularities
        "abstraction",            # Generalize patterns
        "formalization",          # Write rules precisely
        "application",            # Use in real problems
    ],
}

# ============================================================================
# MATHEMATICS SELF-TEST QUESTIONS
# ============================================================================

MATHEMATICS_SELF_TEST_QUESTIONS = [
    {
        "question": "What's the derivative of x^2?",
        "mechanism": "power_rule",
        "mathematics_concept": "calculus derivatives",
    },
    {
        "question": "Probability of 3 heads in 5 coin flips?",
        "mechanism": "binomial_probability",
        "mathematics_concept": "probability binomial distribution",
    },
    {
        "question": "Area of circle with radius 5?",
        "mechanism": "circle_area",
        "mathematics_concept": "geometry circle area",
    },
    {
        "question": "Solve 2x + 5 = 15?",
        "mechanism": "linear_equation",
        "mathematics_concept": "algebra linear equations",
    },
]

# ============================================================================
# MATHEMATICS KNOWLEDGE ACCESS
# ============================================================================

def get_mathematics_concept(concept_name: str) -> dict:
    """Get a specific mathematics concept."""
    return MATHEMATICS_FOUNDATIONS.get(concept_name, {})


def get_all_mathematics_concepts() -> list:
    """Get all available mathematics concepts."""
    return list(MATHEMATICS_FOUNDATIONS.keys())


def calculate_derivative(formula: str, variable: str = "x") -> dict:
    """
    Calculate derivative of a basic function.
    """
    # Simple power rule: d/dx(x^n) = nx^(n-1)
    if "x^" in formula:
        parts = formula.split("x^")
        if len(parts) == 2:
            try:
                coefficient = float(parts[0]) if parts[0] else 1.0
                exponent = float(parts[1])
                new_coefficient = coefficient * exponent
                new_exponent = exponent - 1
                return {
                    "original": formula,
                    "derivative": f"{new_coefficient}x^{new_exponent}",
                    "rule": "power_rule",
                }
            except:
                pass
    
    # Linear function: ax + b -> a
    if "+" in formula or "-" in formula:
        return {
            "original": formula,
            "derivative": "constant (slope)",
            "rule": "linear_approximation",
        }
    
    return {"original": formula, "derivative": "unknown", "info": "Complex function requires symbolic math"}


def calculate_area(shape: str, dimensions: dict) -> dict:
    """
    Calculate area of common shapes.
    """
    shapes = {
        "circle": "pi*r^2",
        "rectangle": "width * height",
        "triangle": "0.5 * base * height",
        "sphere_surface": "4*pi*r^2",
        "cylinder_surface": "2*pi*r^2 + 2*pi*r*h",
    }
    
    formula = shapes.get(shape, "unknown")
    
    # Substitute dimensions
    result = {
        "shape": shape,
        "formula": formula,
        "dimensions": dimensions,
    }
    
    if shape == "circle" and "radius" in dimensions:
        import math
        r = dimensions["radius"]
        result["calculation"] = f"pi * {r}^2 = {math.pi * r**2:.2f}"
    elif shape == "rectangle" and "width" in dimensions and "height" in dimensions:
        result["calculation"] = f"{dimensions['width']} * {dimensions['height']} = {dimensions['width'] * dimensions['height']}"
    elif shape == "triangle" and "base" in dimensions and "height" in dimensions:
        result["calculation"] = f"0.5 * {dimensions['base']} * {dimensions['height']} = {0.5 * dimensions['base'] * dimensions['height']}"
    
    return result


def solve_linear_equation(a: float, b: float, c: float) -> dict:
    """
    Solve ax + b = c for x.
    """
    if a == 0:
        return {
            "equation": f"{a}x + {b} = {c}",
            "solution": "no_unique_solution" if b != c else "infinite_solutions",
        }
    
    x = (c - b) / a
    
    return {
        "equation": f"{a}x + {b} = {c}",
        "solution": x,
        "verification": f"{a} * {x} + {b} = {a * x + b}",
    }


def calculate_probability(event: str, total: int, favorable: int) -> dict:
    """
    Calculate simple probability.
    """
    if total == 0:
        return {"error": "total cannot be zero"}
    
    probability = favorable / total
    percentage = probability * 100
    
    return {
        "event": event,
        "favorable": favorable,
        "total": total,
        "probability": probability,
        "percentage": f"{percentage:.1f}%",
    }


def calculate_growth(rate: float, initial: float, periods: int) -> dict:
    """
    Calculate exponential growth: A = P(1 + r)^t
    """
    import math
    final = initial * (1 + rate) ** periods
    
    return {
        "initial": initial,
        "rate": f"{rate * 100}%",
        "periods": periods,
        "formula": "A = P(1 + r)^t",
        "final": round(final, 2),
    }


def analyze_relationship(variables: list, relationship_type: str) -> dict:
    """
    Analyze mathematical relationship between variables.
    """
    relationships = {
        "linear": "y = mx + b",
        "quadratic": "y = ax^2 + bx + c",
        "exponential": "y = ab^x",
        "inverse": "y = k/x",
        "direct": "y = kx",
    }
    
    formula = relationships.get(relationship_type, "unknown")
    
    return {
        "variables": variables,
        "relationship_type": relationship_type,
        "formula": formula,
        "characteristics": {
            "linear": "constant rate of change, straight line graph",
            "quadratic": "changing rate, parabolic graph",
            "exponential": "proportional growth/decay",
            "inverse": "one increases, other decreases",
            "direct": "both increase or decrease together",
        }.get(relationship_type, "unknown characteristics"),
    }
