class CreditCard:

    """
    Initializes a CreditCard instance with the provided card data.
    Args:
        card (dict): Dictionary containing information about the credit card.
    """
    def __init__(self, card):
        get = card.get
        self.af = card["annual_fee"]
        self.cb = card["cb_convert"]
        self.catchall = card["catch_all"]
        self.credits = get("credits", {})
        self.limits = get("limits", {})
        self.miles = "miles" in card
        self.name = card["name"]
        self.pp = "priority_pass" in card
        self.rewards = card["rewards"]
        self.trifecta = get("trifecta", "")

    
    """
    Calculates the total value of credits and modifies credit info in-place.
    Args:
        credit_info (dict): Dictionary containing user's credit information.
    Returns:
        float: Total value of credits.
    """
    # Calculates the total value of credits
    # Modifying credit info in-place
    def calculateTotalCredits(self, credit_info):
        total_credits = 0
        for credit, value in self.credits.items():
            val = min(value, credit_info.get(credit, 0))
            credit_info[credit] -= val
            total_credits += val
        return total_credits

    
    """
    Calculates the total value of spending in a single category and modifies spending info in-place.
    Args:
        category (str): Category for which spending is calculated.
        spend_info (dict): Dictionary containing user's spending information.
    Returns:
        float: Total value of spending in the specified category.
    """
    def totalSpent(self, category, spend_info):
        value = min(spend_info[category], self.limits.get(category, float("inf")))
        spend_info[category] -= value
        return value


    """
    Calculates the redemption value of a card's total rewards.
    Args:
        category (str): Category for which rewards are calculated.
        total_spent (float): Total spending in the specified category.
        team_miles (bool): Indicates if team miles are used.
        possible_trifectas (set): Set of possible trifectas in the current setup.
        redemption_value (float): Redemption value for miles.
    Returns:
        float: Redemption value of the card's total rewards.
    """
    # Calculates the redemption value of a card's total rewards
    def rewardsValue(self, category, total_spent, team_miles, possible_trifectas, redemption_value):
        value = (self.rewards[category] * total_spent) / 100
        value *= self.cb if not team_miles else redemption_value if self.miles or \
            (self.trifecta in possible_trifectas and team_miles) else 1
        return value

    
    """
    Calculates the value a card generates as a catch-all card.
    Args:
        spend_info (dict): Dictionary containing user's spending information.
        team_miles (bool): Indicates if team miles are used.
        possible_trifectas (set): Set of possible trifectas in the current setup.
        redemption_value (float): Redemption value for miles.
    Returns:
        float: Total value generated as a catch-all card.
    """
    def catchAllReward(self, spend_info, team_miles, possible_trifectas, redemption_value):
        multiplier = self.miles or (self.trifecta in possible_trifectas and team_miles)
        total_return = sum(self.catchall * value / 100 for category, value in spend_info.items() if value != 0 and \
            (self.name == "Bilt Mastercard" or category != "Rent"))
        total_return += 100 if self.name == "Capital One Venture X" else 0
        total_return *= self.cb if not team_miles else redemption_value if multiplier else 1
        return total_return