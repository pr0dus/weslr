# Weslr Test Scenarios

## Student (15 years old, learning programming)

**Scenario:** Student wants to learn Python basics and get help with homework.

**Turn 1:**
> "Hi Weslr, I'm struggling with Python lists. Can you explain them simply?"

**Expected response:** Clear, patient explanation with examples, no jargon overload.

**Turn 2:**
> "So a list is like an array? Can you show me how to add items?"

**Expected response:** Shows code examples, asks if they want to try something.

**Turn 3:**
> "What if I have a list and want to remove duplicates?"

**Expected response:** Explains `set()` approach, mentions trade-offs.

---

## Babysitter (22 years old, organizing activities)

**Scenario:** Babysitter needs fun, safe activities for kids of different ages.

**Turn 1:**
> "I'm babysitting 3 kids aged 6, 9, and 12. What activities work well?"

**Expected response:** Age-appropriate suggestions, safety considerations, materials needed.

**Turn 2:**
> "They've done arts and crafts. What's something active we can do?"

**Expected response:** Indoor/outdoor options, considers space constraints.

**Turn 3:**
> "The 12-year-old is getting bored. Any ideas that challenge them?"

**Expected response:** More complex challenges, learning opportunities.

---

## Freelancer (30 years old, managing multiple clients)

**Scenario:** Freelancer wants to track projects and manage time efficiently.

**Turn 1:**
> "I have 5 active clients. How should I prioritize today?"

**Expected response:** Asks clarifying questions about deadlines, complexity, urgency.

**Turn 2:**
> "Client A needs a quick fix, Client B has a deadline tomorrow, Client C is ongoing."

**Expected response:** Suggests time-blocking strategy, mentions communication needs.

**Turn 3:**
> "What's a good end-of-day routine to track progress?"

**Expected response:** Template for daily review, tracking metrics, planning next day.

---

## Chess Master (45 years old, teaching/playing)

**Scenario:** Chess master wants to analyze games and teach students.

**Turn 1:**
> "I played a game where I blundered in the middlegame. Can we analyze it?"

**Expected response:** Asks for game notation, suggests analysis approach.

**Turn 2:**
> "Here's the position after move 15. Black just played Rfd8."

**Expected response:** Evaluates the move, suggests alternatives, explains reasoning.

**Turn 3:**
> "How should I explain this to my beginner student?"

**Expected response:** Simplified explanation, teaches calculation method, not just result.

---

## Professional Swimmer (28 years old, training for competition)

**Scenario:** Swimmer wants to optimize training and track progress.

**Turn 1:**
> "I'm training for 200m freestyle. My split times are inconsistent."

**Expected response:** Asks about training schedule, recovery, technique focus.

**Turn 2:**
> "I swim 5 days/week, include strength 2x/week, and have race in 6 weeks."

**Expected response:** Suggests periodization, key workouts, race strategy.

**Turn 3:**
> "My turn at the wall feels slow. Any technique tips?"

**Expected response:** Breakdown of wall approach, push-off mechanics, drill suggestions.

---

## Test Framework

Run these scenarios with:
```bash
# Student
python3 main.py human-exchange student "Hi Weslr, I'm struggling with Python lists. Can you explain them simply?" --response "Sure! A list is like an ordered collection where you can store multiple items. Think of it like a shopping list..."

# Freelancer
python3 main.py human-exchange freelancer "I have 5 active clients. How should I prioritize today?" --response "Let's figure that out together. Could you tell me about each client's deadline and project complexity?"

# Chess Master
python3 main.py human-exchange chess-master "I played a game where I blundered in the middlegame. Can we analyze it?" --response "Absolutely! I'd love to help. Could you share the game notation so I can see the position?"

# Swimmer
python3 main.py human-exchange swimmer "I'm training for 200m freestyle. My split times are inconsistent." --response "Inconsistent splits are common. To help optimize, could you tell me about your current training volume and recent race times?"

# Babysitter
python3 main.py human-exchange babysitter "I'm babysitting 3 kids aged 6, 9, and 12. What activities work well?" --response "Great question! With that age range, you want activities that all can enjoy. Some ideas..."
```
