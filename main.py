import ast
from collections import defaultdict
from itertools import combinations
import os

from credit_card import CreditCard

# Handles all the main logic
def main():
  all_cards = list(card_data.keys())
  best_setup = {"cards": {}, "total_rewards": 0}

  for card_combination in combinations(all_cards, num_cards):
    total_rewards = 0
    current_setup = list(card_combination)

    # Skips infeasible setups
    if (invalidSetup(current_setup) or (must_have_priority_pass and not hasPriorityPass(current_setup))):
      continue

    setup_metadata, total_rewards = calculateSetupValue(current_setup)

    # Stores best setup
    if total_rewards > best_setup["total_rewards"]:
      best_setup["cards"] = setup_metadata
      best_setup["total_rewards"] = total_rewards

  af, text = 0, ""
  total_rewards = round(best_setup['total_rewards'], 2)
  best_setup["cards"] = dict(sorted(best_setup["cards"].items(), key=lambda x: x[1][0], reverse=True))
  for card in best_setup["cards"]:
    text += f"Credit Card: {card_data[card]['name']}\n" \
        f"Annual Rewards Value: ${round(best_setup['cards'][card][0], 2)}\n" \
        f"Categories: {', '.join([category[0] for category in best_setup['cards'][card][1]])}\n\n"
    af += card_data[card]['annual_fee']


  text += f"Total Rewards: ${total_rewards}\n"\
          f"Total Annual Fee: ${af}\n"\
          f"Total Return on Spend: {int(100 * total_rewards / sum(user_info["Spending"][category] for category in user_info["Spending"]))}%\n"
  
  os.system('cls' if os.name == 'nt' else 'clear')
  print(text)
  return best_setup


# Calculate the value of the current setup
def calculateSetupValue(current_setup):
  table = defaultdict(list)
  rewards = defaultdict(list)
  spending_info = user_info["Spending"].copy()
  credit_info = user_info["Credits"].copy()
  possible_trifectas = possibleTrifectas(current_setup)
  chase_mult = chaseMultiplier(current_setup)
  catch_all_card, catch_all_id = CreditCard(card_data[current_setup[0]]), current_setup[0]
  total_value = 0

  # Sets up the card metadata table and also processes credits and annual fee
  for card in current_setup:
    cc = CreditCard(card_data[card])
    card_credit_value = cc.calculateTotalCredits(credit_info)
    table[card] = [card_credit_value - cc.af, []]
    total_value += card_credit_value - cc.af
    if "rewards" in card_data[card]:
      for categories in card_data[card]["rewards"]:
        rewards[categories] += [[card, card_data[card]["rewards"][categories]]]

  sorted_data = sorted([(category, sorted(items, key=lambda x: x[1], reverse=True)) \
                 for category, items in rewards.items()], key= lambda x: x[0])

  # Processes the category spend rewards
  for category, all_metadata in sorted_data:
    for card_metadata in all_metadata:
      id = card_metadata[0]
      card = CreditCard(card_data[id])

      # Decides which card is the catch-all in the setup
      if card.catchall > catch_all_card.catchall:
        catch_all_card = card
        catch_all_id = id

      # Figures out how much how much value is returned from category spend
      if spending_info[category] == 0:
        continue

      total_spent = card.totalSpent(category, spending_info)
      category_reward = card.rewardsValue(category, total_spent, team_miles, possible_trifectas,
                                          max(chase_mult, redemption_value) if "Chase" in card.name else redemption_value)
      total_value += category_reward
      table[id][0] += category_reward
      table[id][1].append([category, category_reward])

  # Processes the catch all rewards
  if "Chase" in catch_all_card.name:
    catch_all_rewards = catch_all_card.catchAllReward(spending_info, team_miles, possible_trifectas,
                                                      max(chase_mult, redemption_value) if "Chase" in card.name else redemption_value)
  else:
    catch_all_rewards = catch_all_card.catchAllReward(spending_info, team_miles, possible_trifectas, redemption_value)
  total_value += catch_all_rewards
  table[catch_all_id][0] += catch_all_rewards
  table[catch_all_id][1].append(["Catch All", catch_all_rewards])

  return table, total_value


# Removes duplicate Custom Cashes and USBank Cash+ from the list
def invalidSetup(current_setup):
  return (sum(1 for card in current_setup if card.startswith("ccc")) >= 2 or
          (sum(1 for card in current_setup if card.startswith("usbc")) >= 2) or
          all(card in set(current_setup) for card in {"csr", "csp"}))

# Tacks on the 1.5/1.25X multiplier for Chase cards
def chaseMultiplier(current_setup):
  current_setup = set(current_setup)
  if "csr" in current_setup:
    return 1.5
  elif "csp" in current_setup:
    return 1.25
  return 1

# Tacks on the 1.5/1.25X multiplier for Chase cards
def possibleTrifectas(current_setup):
  possible_trifectas = { "csp" : "Chase", "csr" : "Chase", "vx" : "Capital One", "cpc" : "Citi" }
  setup_trifectas = set()
  for card in current_setup:
    if card in possible_trifectas:
      setup_trifectas.add(possible_trifectas[card])
  return setup_trifectas


# Checks if the current setup has a Priority Pass card
def hasPriorityPass(current_setup):
  return (sum(1 for card in current_setup if card in priority_pass_cards) >= 1)


if __name__ == "__main__":
  # Open files
  with open("user_info.txt", "r") as s:
    user_info = ast.literal_eval(s.read())
  with open("credit_card_data.txt", "r") as c:
    card_data = ast.literal_eval(c.read())

  # User input for number of cards in setup
  num_cards = user_info["Modifiers"]["Number of cards in setup"]

  if (not isinstance(num_cards, int) or num_cards < 1 or num_cards > 5):
    print("Number of cards in setup must be an integer between 1 and 5")
  else:
    # init variables
    team_miles = user_info["Modifiers"]["Team Travel"]
    redemption_value = user_info["Modifiers"]["Miles CPP redemption value"]
    must_have_priority_pass = user_info["Modifiers"]["Setup must have Priority Pass"]
    chase_cards = {"cff", "cfu", "csp", "csr"}
    catch_all_cards = {"vx", "2x", "cfu", "bbp", "cdc"}
    priority_pass_cards = {"csr", "plat", "usbar", "vx", }

    if user_info["Modifiers"]["Use mobile wallet for all purchases"]:
      catch_all_cards.add("usbar")
      card_data["usbar"]["catch_all"] = 3

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Calculating...")
    main()