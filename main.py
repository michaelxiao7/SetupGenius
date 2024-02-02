import ast
from collections import defaultdict
from itertools import combinations
from credit_card_info.credit_card import CreditCard
import os

# Setup files
def load_data(file_name):
    with open(file_name, "r") as f:
        return ast.literal_eval(f.read())

# Global constants
user_info = load_data("user_info.txt")
card_metadata = load_data("credit_card_info/credit_card_metadata.txt")
team_miles = user_info["Modifiers"]["Team Travel"]
redemption_value = user_info["Modifiers"]["Miles CPP redemption value"]
must_have_priority_pass = user_info["Modifiers"]["Setup must have Priority Pass"]
chase_cards = {"cff", "cfu", "csp", "csr"}
catch_all_cards = {"vx", "2x", "cfu", "bbp", "cdc"}
priority_pass_cards = {"csr", "plat", "usbar", "vx", }


"""
Main function to calculate the best credit card setup based on user input.
"""
def main():
    # User input for number of cards in setup
    num_cards = user_info["Modifiers"]["Number of cards in setup"]
    if not (isinstance(num_cards, int) and 1 <= num_cards <= 5):
        print("Number of cards in setup must be an integer between 1 and 5")
        return

    if user_info["Modifiers"]["Use mobile wallet for all purchases"]:
        catch_all_cards.add("usbar")
        card_metadata["usbar"]["catch_all"] = 3

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Calculating best setup...\n")

    all_cards = list(card_metadata.keys())
    best_setup = {"cards": {}, "total_rewards": 0}

    for card_combination in combinations(all_cards, num_cards):
        current_setup = list(card_combination)

        # Skips infeasible setups
        if (invalidSetup(current_setup) or (must_have_priority_pass and not hasPriorityPass(current_setup))):
            continue

        setup_metadata, total_rewards = calculateSetupValue(current_setup)

        # Stores best setup
        if total_rewards > best_setup["total_rewards"]:
            best_setup["cards"] = setup_metadata
            best_setup["total_rewards"] = total_rewards

    os.system('cls' if os.name == 'nt' else 'clear')
    print_best_setup(best_setup)   
    return best_setup


"""
Prints the details of the best credit card setup.
Args:
    best_setup (dict): Dictionary containing information about the best credit card setup.
"""
def print_best_setup(best_setup):
    annual_fee = sum(card_metadata[card]["annual_fee"] for card in best_setup["cards"])
    total_rewards = round(best_setup['total_rewards'], 2)
    total_spend = sum(user_info["Spending"][category] for category in user_info["Spending"])
    best_setup["cards"] = dict(sorted(best_setup["cards"].items(), key=lambda x: x[1][0], reverse=True))
    
    if total_spend == 0:
        print("No spending data provided.\n")
        return

    for card in best_setup["cards"]:
        print(f"Credit Card: {card_metadata[card]['name']}\n" \
            f"Annual Rewards Value: ${round(best_setup['cards'][card][0], 2)}\n" \
            f"Categories: {', '.join([category[0] for category in best_setup['cards'][card][1]])}\n\n")

    print(f"Total Rewards: ${total_rewards}\n"\
        f"Total Annual Fee: ${annual_fee}\n"\
        f"Total Return on Spend: {int(100 * total_rewards / total_spend )}%\n")
    
    return


"""
Calculates the value of the current credit card setup.
Args:
    current_setup (list): List of credit cards in the setup.
Returns:
    tuple: Table with metadata and total value of the setup.
"""
def calculateSetupValue(current_setup):
    table = defaultdict(list)
    rewards = defaultdict(dict)
    spending_info = dict(user_info["Spending"])
    credit_info = dict(user_info["Credits"])
    possible_trifectas = possibleTrifectas(current_setup)
    chase_mult = chaseMultiplier(current_setup)
    max_chase_redemption = max(chase_mult, redemption_value)
    credit_cards = {card: CreditCard(card_metadata[card]) for card in current_setup}
    catch_all_card, catch_all_id = credit_cards[current_setup[0]], current_setup[0]
    total_value = 0

    # Sets up the card metadata table and also processes credits and annual fee
    for card, cc in credit_cards.items():
        card_credit_value = cc.calculateTotalCredits(credit_info)
        table[card] = [card_credit_value - cc.af, []]
        total_value += card_credit_value - cc.af
        card_rewards = card_metadata[card].get("rewards")
        if card_rewards:
            for categories in card_rewards:
                rewards[categories][card] = card_rewards[categories]

    sorted_data = [(category, sorted(items.items(), key=lambda x: x[1], reverse=True)) \
                 for category, items in rewards.items()]

    # Processes the category spend rewards
    for category, all_metadata in sorted_data:
        for card, reward in all_metadata:
            cc = credit_cards[card]

            # Decides which card is the catch-all in the setup
            if cc.catchall > catch_all_card.catchall:
                catch_all_card = cc
                catch_all_id = card

            # Figures out how much how much value is returned from category spend
            if spending_info[category] == 0:
                continue

            total_spent = cc.totalSpent(category, spending_info)
            is_chase = "Chase" in cc.name
            category_reward = cc.rewardsValue(category, total_spent, team_miles, possible_trifectas,
                                              max_chase_redemption if is_chase else redemption_value)
            total_value += category_reward
            table[card][0] += category_reward
            table[card][1].append([category, category_reward])

    # Processes the catch all rewards
    is_chase = "Chase" in catch_all_card.name
    catch_all_rewards = catch_all_card.catchAllReward(spending_info, team_miles, possible_trifectas, max_chase_redemption if is_chase else redemption_value)
    total_value += catch_all_rewards
    table[catch_all_id][0] += catch_all_rewards
    table[catch_all_id][1].append(["Catch All", catch_all_rewards])

    return table, total_value


"""
Checks if the current credit card setup is invalid.
Args:
    current_setup (list): List of credit cards in the setup.
Returns:
    bool: True if the setup is invalid, False otherwise.
"""
def invalidSetup(current_setup):
    counts = {'ccc': 0, 'usbc': 0, 'csr_csp': 0}
    for card in current_setup:
        if 'ccc' in card: counts['ccc'] += 1; 
        if counts['ccc'] >= 2: return True
        if 'usbc' in card: counts['usbc'] += 1; 
        if counts['usbc'] >= 2: return True
        if card in {'csr', 'csp'}: counts['csr_csp'] += 1; 
        if counts['csr_csp'] >= 2: return True
    return False


"""
Calculates the multiplier for Chase cards in the setup.
Args:
    current_setup (list): List of credit cards in the setup.
Returns:
    float: Chase multiplier.
"""
def chaseMultiplier(current_setup):
    multipliers = {"csr": 1.5, "csp": 1.25}
    for card in current_setup:
        if card in multipliers:
            return multipliers[card]
    return 1


"""
Identifies possible trifectas in the credit card setup.
Args:
    current_setup (list): List of credit cards in the setup.
Returns:
    set: Set of possible trifectas.
"""
def possibleTrifectas(current_setup):
    possible_trifectas = { "csp" : "Chase", "csr" : "Chase", "vx" : "Capital One", "cpc" : "Citi" }
    return {possible_trifectas[card] for card in current_setup if card in possible_trifectas}


"""
Checks if the credit card setup has a Priority Pass card.
Args:
    current_setup (list): List of credit cards in the setup.
Returns:
    bool: True if the setup has a Priority Pass card, False otherwise.
"""
def hasPriorityPass(current_setup):
    for card in current_setup:
        if card in priority_pass_cards:
            return True
    return False


if __name__ == "__main__":
    main()