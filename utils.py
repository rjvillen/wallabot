
from transformers import pipeline
import re

pipe = pipeline("zero-shot-classification",
                    model="facebook/bart-large-mnli")

def get_tone_score(message):

    results = pipe(message,
        candidate_labels=["friendly, collaborative", "neutral", "agressive, rude"],
        # candidate_labels=["colaborativo/amable", "neutral", "agresivo/grosero"],
    )

    print(results)

    mappings = {label:score for label,score in zip(results["labels"],results['scores'])}
    tono_score = 0*mappings["friendly, collaborative"] + 5*mappings["neutral"] + 10*mappings["agressive, rude"]
    
    return tono_score,mappings

def extract_price(text):
    """
    Extracts a price from a text.
    
    The regex pattern looks for an optional currency symbol (€, $, £)
    or words (bucks, dollars, euros) that can appear immediately
    before or after the number. It captures a number that might include
    a decimal point (or a comma used as a decimal separator) and returns it as a float.
    
    Parameters:
        text (str): The input text that potentially includes a price.
        
    Returns:
        float or None: The extracted price, or None if no price is found.
    """
    # Regular expression explanation:
    # \b                      : Word boundary to ensure we are matching whole parts.
    # (?:€|\$|£)?            : An optional currency symbol at the start.
    # \s*                     : Optional whitespace.
    # (\d+(?:[,.]\d+)?)       : Capture group for the number (integer or decimal).
    # \s*                     : Optional whitespace.
    # (?:€|\$|£|bucks|dollars|euros)? : An optional currency symbol or currency word after the number.
    pattern = r"\b(?:€|\$|£)?\s*(\d+(?:[,.]\d+)?)(?:\s*(?:€|\$|£|bucks|dollars|euros))?"
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        # replace comma with dot if comma is used for decimals (for example in Spanish text)
        num_str = match.group(1).replace(",", ".")
        try:
            return float(num_str)
        except ValueError:
            return None
    else:
        return None

def map_action(accion):
    if accion <= 20:
        return "Rechazar"
    elif accion <= 50:
        return "Mantener"
    elif accion <= 80:
        return "Contraoferta"
    else:
        return "Aceptar"
    
if __name__ == "__main__":
    number = "Te lo compro por 5 pavos si te parece bien"
    extracted_price = extract_price(number)
    print(f"Extracted price: {extracted_price}") 