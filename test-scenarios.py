#!/usr/bin/env python3
"""
Test script for CircleForge scenarios
Runs different user type scenarios and captures responses
"""
import subprocess
import json
import time
import os

def run_command(cmd):
    """Run a command and return stdout"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="/data/data/com.termux/files/home/.openclaw/workspace/CircleForge")
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return None
    return result.stdout

def parse_json_output(output):
    """Parse JSON from command output"""
    try:
        # Find the JSON object in the output
        for line in output.split('\n'):
            if line.strip().startswith('{'):
                return json.loads(line.strip())
    except:
        pass
    return None

def scenario_student():
    """Student scenario"""
    print("\n" + "="*60)
    print("STUDENT SCENARIO (Python lists)")
    print("="*60)
    
    # Initial exchange
    print("\nStudent: 'Hi CircleForge, I'm struggling with Python lists. Can you explain them simply?'")
    
    # Check if we need to reset for clean state
    # Run a fresh tick with human exchange
    run_command("python3 main.py init --agents 1 --reset")
    time.sleep(1)
    
    # Human exchange
    output = run_command("python3 main.py human-exchange student 'Hi CircleForge, I\\'m struggling with Python lists. Can you explain them simply?' --response 'Sure! A list is like an ordered collection where you can store multiple items. Think of it like a shopping list. In Python, you create a list with square brackets, like this: my_list = [1, 2, 3]. You can add items with append(), remove with remove(), and access items by position. Would you like to try something?'")
    
    # Run a tick to generate response
    output = run_command("python3 main.py tick")
    result = parse_json_output(output)
    
    if result:
        print(f"\nCircleForge response: {result.get('current_intent', 'No intent')}")
        print(f"Active pursuit: {result.get('active_pursuit', 'N/A')}")
    
    # Student asks follow-up
    print("\nStudent: 'So a list is like an array? Can you show me how to add items?'")
    
    # Continue the conversation
    output = run_command("python3 main.py run --ticks 3 --interval 0")
    result = parse_json_output(output)
    
    if result:
        print(f"\nCircleForge response: {result.get('current_intent', 'No intent')}")
    
    print("\n--- Student scenario complete ---")

def scenario_freelancer():
    """Freelancer scenario"""
    print("\n" + "="*60)
    print("FREELANCER SCENARIO (Client prioritization)")
    print("="*60)
    
    run_command("python3 main.py reset")
    time.sleep(1)
    
    print("\nFreelancer: 'I have 5 active clients. How should I prioritize today?'")
    output = run_command("python3 main.py human-exchange freelancer 'I have 5 active clients. How should I prioritize today?' --response 'Let\\'s figure that out together. Could you tell me about each client\\'s deadline and project complexity?'")
    
    output = run_command("python3 main.py tick")
    result = parse_json_output(output)
    
    if result:
        print(f"\nCircleForge response: {result.get('current_intent', 'No intent')}")
    
    print("\n--- Freelancer scenario complete ---")

def scenario_chess():
    """Chess master scenario"""
    print("\n" + "="*60)
    print("CHESS MASTER SCENARIO (Game analysis)")
    print("="*60)
    
    run_command("python3 main.py reset")
    time.sleep(1)
    
    print("\nChess Master: 'I played a game where I blundered in the middlegame. Can we analyze it?'")
    output = run_command("python3 main.py human-exchange chess-master 'I played a game where I blundered in the middlegame. Can we analyze it?' --response 'Absolutely! I\\'d love to help. Could you share the game notation so I can see the position?'")
    
    output = run_command("python3 main.py tick")
    result = parse_json_output(output)
    
    if result:
        print(f"\nCircleForge response: {result.get('current_intent', 'No intent')}")
    
    print("\n--- Chess scenario complete ---")

def scenario_swimmer():
    """Swimmer scenario"""
    print("\n" + "="*60)
    print("SWIMMER SCENARIO (Training optimization)")
    print("="*60)
    
    run_command("python3 main.py reset")
    time.sleep(1)
    
    print("\nSwimmer: 'I'm training for 200m freestyle. My split times are inconsistent.'")
    output = run_command("python3 main.py human-exchange swimmer 'I\\'m training for 200m freestyle. My split times are inconsistent.' --response 'Inconsistent splits are common. To help optimize, could you tell me about your current training volume and recent race times?'")
    
    output = run_command("python3 main.py tick")
    result = parse_json_output(output)
    
    if result:
        print(f"\nCircleForge response: {result.get('current_intent', 'No intent')}")
    
    print("\n--- Swimmer scenario complete ---")

def scenario_babysitter():
    """Babysitter scenario"""
    print("\n" + "="*60)
    print("BABYSITTER SCENARIO (Activity planning)")
    print("="*60)
    
    run_command("python3 main.py reset")
    time.sleep(1)
    
    print("\nBabysitter: 'I\\'m babysitting 3 kids aged 6, 9, and 12. What activities work well?'")
    output = run_command("python3 main.py human-exchange babysitter 'I\\'m babysitting 3 kids aged 6, 9, and 12. What activities work well?' --response 'Great question! With that age range, you want activities that all can enjoy. Some ideas: scavenger hunt, DIY slime station, or a mini Olympics with age-divided events.'")
    
    output = run_command("python3 main.py tick")
    result = parse_json_output(output)
    
    if result:
        print(f"\nCircleForge response: {result.get('current_intent', 'No intent')}")
    
    print("\n--- Babysitter scenario complete ---")

def main():
    """Run all scenarios"""
    print("CircleForge Test Scenarios")
    print("="*60)
    print("Testing different user types and interaction patterns")
    print("="*60)
    
    scenarios = [
        ("Student", scenario_student),
        ("Freelancer", scenario_freelancer),
        ("Chess Master", scenario_chess),
        ("Swimmer", scenario_swimmer),
        ("Babysitter", scenario_babysitter),
    ]
    
    for name, func in scenarios:
        try:
            func()
        except Exception as e:
            print(f"\nERROR in {name} scenario: {e}")
    
    print("\n" + "="*60)
    print("All scenarios complete!")
    print("="*60)

if __name__ == "__main__":
    main()
