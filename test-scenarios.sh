#!/bin/bash
# Test scenarios for CircleForge
# Run: bash test-scenarios.sh

set -e

cd /data/data/com.termux/files/home/.openclaw/workspace/CircleForge

echo "========================================"
echo "CircleForge Test Scenarios"
echo "========================================"

# Scenario 1: Student (Python)
echo ""
echo "SCENARIO 1: Student learning Python lists"
echo "----------------------------------------"
python3 main.py init --agents 1 --reset
python3 main.py human-exchange student "Hi CircleForge, I'm struggling with Python lists. Can you explain them simply?" --response "Sure! A list is like an ordered collection where you can store multiple items. Think of it like a shopping list. In Python, you create a list with square brackets. Would you like to try something?"
python3 main.py tick | grep -A 5 '"current_intent"\|"active_pursuit"\|"unresolved_question"' | head -15

# Scenario 2: Freelancer
echo ""
echo "SCENARIO 2: Freelancer client prioritization"
echo "----------------------------------------"
python3 main.py reset
python3 main.py human-exchange freelancer "I have 5 active clients. How should I prioritize today?" --response "Let's figure that out together. Could you tell me about each client's deadline and project complexity?"
python3 main.py tick | grep -A 5 '"current_intent"\|"active_pursuit"\|"unresolved_question"' | head -15

# Scenario 3: Chess Master
echo ""
echo "SCENARIO 3: Chess Master game analysis"
echo "----------------------------------------"
python3 main.py reset
python3 main.py human-exchange chess-master "I played a game where I blundered in the middlegame. Can we analyze it?" --response "Absolutely! I'd love to help. Could you share the game notation so I can see the position?"
python3 main.py tick | grep -A 5 '"current_intent"\|"active_pursuit"\|"unresolved_question"' | head -15

# Scenario 4: Swimmer
echo ""
echo "SCENARIO 4: Swimmer training optimization"
echo "----------------------------------------"
python3 main.py reset
python3 main.py human-exchange swimmer "I'm training for 200m freestyle. My split times are inconsistent." --response "Inconsistent splits are common. To help optimize, could you tell me about your current training volume and recent race times?"
python3 main.py tick | grep -A 5 '"current_intent"\|"active_pursuit"\|"unresolved_question"' | head -15

# Scenario 5: Babysitter
echo ""
echo "SCENARIO 5: Babysitter activity planning"
echo "----------------------------------------"
python3 main.py reset
python3 main.py human-exchange babysitter "I'm babysitting 3 kids aged 6, 9, and 12. What activities work well?" --response "Great question! With that age range, activities that all can enjoy. Some ideas: scavenger hunt, DIY slime, or mini Olympics with age-divided events."
python3 main.py tick | grep -A 5 '"current_intent"\|"active_pursuit"\|"unresolved_question"' | head -15

echo ""
echo "========================================"
echo "All scenarios complete!"
echo "========================================"
