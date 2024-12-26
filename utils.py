import random
import secrets


class NameGenerator:
    def __init__(self):
        self.names = []
        self.adverbs = ["accidentally", "always", "angrily", "annually", "anxiously", "awkwardly", "badly", "blindly", "boastfully", "boldly", "bravely", "brightly", "cheerfully", "deftly", "deliberately", "devotedly", "doubtfully",
                "dramatically", "dutifully", "eagerly", "elegantly", "enormously", "enthusiastically", "equally", "eventually", "exactly", "faithfully", "fortunately", "frequently", "generously", "gently", "gladly", "gracefully"]
        self.adjectives = ["adaptable", "adventurous", "affectionate", "ambitious", "amiable", "compassionate", "considerate", "courageous", "courteous", "diligent", "empathetic", "exuberant", "frank", "generous",
                           "gregarious", "impartial", "intuitive", "inventive", "passionate", "persistent", "philosophical", "practical", "rational", "reliable", "resourceful", "sensible", "sincere", "sympathetic", "unassuming", "witty"]

        self.angel_names = ["Michael", "Gabriel", "Raphael", "Uriel", "Castiel","Lucifer", "Raguel", "Sariel", "Remiel", "Jeremiel", "Barachiel", "Kokabiel", "Tzaphqiel", "Haniel", "Azrael", "Metatron",
                            "Sandalphon", "Jophiel", "Zadkiel", "Raziel", "Chamuel", "Zaphkiel", "Zadkiel", "Zerachiel", "Zophiel", "Zuriel", "Zadkiel", "Zaphkiel", "Zerachiel", "Zophiel", "Zuriel"]

        self.possible_names = len(self.adverbs) * len(self.adjectives) * len(self.angel_names)
        print(f"Possible names: {self.possible_names}")

    def generate_name(self):
        original = tries = 3
        while tries > 0:
            name = random.choice(self.adverbs).capitalize() + random.choice(self.adjectives).capitalize() + random.choice(self.angel_names)
            if name not in self.names:
                self.names.append(name)
                return name
            tries -= 1
        raise Exception(f"Could not generate a unique name after {original} tries.")
    
    def generate_name_and_personality(self):
        original = tries = 3
        while tries > 0:
            adverb = random.choice(self.adverbs)
            adjective = random.choice(self.adjectives)
            name = random.choice(self.angel_names)
            full_name = adverb.capitalize() + adjective.capitalize() + name
            if full_name not in self.names:
                self.names.append(full_name)
                return full_name , f"{adverb} {adjective}"
            tries -= 1
        raise Exception(f"Could not generate a unique name after {original} tries.")

def key_by_value(d: dict, value):
    for key, val in d.items():
        if val == value:
            return key
    raise ValueError(f"Value {value} not found in dictionary")

#import time
#ng = NameGenerator()
#while True:
#    try:
#        print(ng.generate_name())
#        time.sleep(0.001)
#    except Exception as e:
#        print(e)
#        break

def get_random_id() -> str:
    return secrets.token_hex(24)