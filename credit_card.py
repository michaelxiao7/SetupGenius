class CreditCard:

  def __init__(self, card):
    self.name = card["name"]
    self.rewards = card["rewards"]
    self.credits = card["credits"] if "credits" in card else {}
    self.af = card["annual_fee"]
    self.cb = card["cb_convert"]
    self.pp = "priority_pass" in card
    self.limits = card["limits"] if "limits" in card else {}
    self.catchall = card["catch_all"]
    self.miles = "miles" in card
    self.trifecta = card["trifecta"] if "trifecta" in card else ""

  
  # Calculates the total value of credits
  # Modifying credit info in-place
  def calculateTotalCredits(self, credit_info):
    total_return = 0
    for credit in self.credits:
      value = min(self.credits[credit], credit_info[credit])
      credit_info[credit] -= value
      total_return += value
    return total_return

  
  # Calculates the total value of spending in a single category
  # Modifies spending info in-place  
  def totalSpent(self, category, spend_info):
    value = min(
        spend_info[category],
        self.limits[category] if category in self.limits else float("inf"))
    spend_info[category] -= value
    return value

  
  # Calculates the redemption value of a card's total rewards
  def rewardsValue(self, category, total_spent, team_miles, possible_trifectas, redemption_value):
    value = (self.rewards[category] * total_spent) / 100

    if not team_miles:
      value *= self.cb

    elif self.miles or (self.trifecta in possible_trifectas and team_miles):
      value *= redemption_value

    return value

  
  # Calculates the value a card generates as a catch-all card
  def catchAllReward(self, spend_info, team_miles, possible_trifectas, redemption_value):
    total_return = 0

    for category in spend_info:
      if (spend_info[category] == 0) or \
          (self.name != "Bilt Mastercard" and category == "Rent"):
        continue
      value = spend_info[category]
      spend_info[category] = 0
      total_return += self.catchall * value / 100

    if self.name == "Capital One Venture X":
      total_return += 100

    if not team_miles:
      total_return *= self.cb

    elif self.miles or (self.trifecta in possible_trifectas and team_miles):
      total_return *= redemption_value

    return total_return
