import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

import openai

from dotenv import load_dotenv
import os
from utils import *
import time

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def setup_fuzzy_logic():
    
    print("Setting up fuzzy logic system...")
    
    # Inputs
    tono = ctrl.Antecedent(np.arange(0, 11, 1), 'tono')
    diferencia = ctrl.Antecedent(np.arange(0, 101, 1), 'diferencia')
    duracion = ctrl.Antecedent(np.arange(0, 16, 1), 'duracion')

    tono['amigable'] = fuzz.trimf(tono.universe, [0, 0, 4])
    tono['neutral']   = fuzz.trimf(tono.universe, [2, 5, 8])
    tono['agresivo']  = fuzz.trimf(tono.universe, [6, 10, 10])

    diferencia['baja'] = fuzz.trapmf(diferencia.universe, [0, 0, 5, 10])
    diferencia['media'] = fuzz.trapmf(diferencia.universe, [5, 10, 15, 20])
    diferencia['alta'] = fuzz.trapmf(diferencia.universe, [15, 20, 100, 100])

    duracion['corta'] = fuzz.trapmf(duracion.universe, [0, 2, 3, 4])
    duracion['media'] = fuzz.trapmf(duracion.universe, [3, 4, 6, 7])
    duracion['larga'] = fuzz.trapmf(duracion.universe, [6, 8, 15, 15])

    # Outputs
    acceptance = ctrl.Consequent(np.arange(0, 101, 1), 'acceptance')

    acceptance['muy_bajo'] = fuzz.trimf(acceptance.universe, [0, 0, 25]) # -> Rechazar (terminar negociación)
    acceptance['bajo'] = fuzz.trimf(acceptance.universe, [15, 40, 55]) # -> Mantener el precio (seguir negociando)
    acceptance['alto'] = fuzz.trimf(acceptance.universe, [45, 65, 85]) # -> Ofrecer contraoferta (seguir negociando)
    acceptance['muy_alto'] = fuzz.trimf(acceptance.universe, [75, 100, 100]) # -> Aceptar (cerrar trato)

    # Rules

    # Reglas para tono 'amigable'
    rule_A1 = ctrl.Rule(tono['amigable'] & diferencia['baja'] & (duracion['corta'] | duracion['media']), acceptance['muy_alto'])
    rule_A2 = ctrl.Rule(tono['amigable'] & diferencia['baja'] & duracion['larga'], acceptance['alto'])
    rule_A3 = ctrl.Rule(tono['amigable'] & diferencia['media'] & (duracion['corta'] | duracion['media']), acceptance['alto'])
    rule_A4 = ctrl.Rule(tono['amigable'] & diferencia['media'] & duracion['larga'], acceptance['bajo'])
    rule_A5 = ctrl.Rule(tono['amigable'] & diferencia['alta'] & duracion['corta'], acceptance['alto'])
    rule_A6 = ctrl.Rule(tono['amigable'] & diferencia['alta'] & duracion['media'], acceptance['bajo'])
    rule_A7 = ctrl.Rule(tono['amigable'] & diferencia['alta'] & duracion['larga'], acceptance['muy_bajo'])

    # Reglas para tono 'neutral'
    rule_N1 = ctrl.Rule(tono['neutral'] & diferencia['baja'] & (duracion['corta'] | duracion['media']), acceptance['muy_alto'])
    rule_N2 = ctrl.Rule(tono['neutral'] & diferencia['baja'] & duracion['larga'], acceptance['alto'])
    rule_N3 = ctrl.Rule(tono['neutral'] & diferencia['media'] & duracion['corta'], acceptance['alto'])
    rule_N4 = ctrl.Rule(tono['neutral'] & diferencia['media'] & (duracion['media'] | duracion['larga']), acceptance['bajo'])
    rule_N5 = ctrl.Rule(tono['neutral'] & diferencia['alta'], acceptance['bajo'])  # Aplica para cualquier duración

    # Reglas para tono 'agresivo'
    rule_AG1 = ctrl.Rule(tono['agresivo'] & diferencia['baja'] & (duracion['corta'] | duracion['media']), acceptance['bajo'])
    rule_AG2 = ctrl.Rule(tono['agresivo'] & diferencia['baja'] & duracion['larga'], acceptance['muy_bajo'])
    rule_AG3 = ctrl.Rule(tono['agresivo'] & diferencia['media'] & (duracion['corta'] | duracion['media']), acceptance['bajo'])
    rule_AG4 = ctrl.Rule(tono['agresivo'] & diferencia['media'] & duracion['larga'], acceptance['muy_bajo'])
    rule_AG5 = ctrl.Rule(tono['agresivo'] & diferencia['alta'], acceptance['muy_bajo'])  # Aplica para cualquier duración

    # (17 reglas en total)
    rules = [rule_A1, rule_A2, rule_A3, rule_A4, rule_A5, rule_A6, rule_A7,
            rule_N1, rule_N2, rule_N3, rule_N4, rule_N5,
            rule_AG1, rule_AG2, rule_AG3, rule_AG4, rule_AG5]

    negotiation_ctrl = ctrl.ControlSystem(rules)
    simulation = ctrl.ControlSystemSimulation(negotiation_ctrl)
    
    print("Fuzzy logic system setup complete.")
    
    return negotiation_ctrl, simulation
    
def compute_fuzzy_action(simulation, tono_score, price_difference, n_interactions):
    
    print(f"\nComputing fuzzy action with tono_score: {tono_score}, price_difference: {price_difference}, n_interactions: {n_interactions}")
    
    # fuzzification
    simulation.input['tono'] = tono_score
    simulation.input['diferencia'] = price_difference
    simulation.input['duracion'] = n_interactions

    simulation.compute()

    fuzzy_action = simulation.output['acceptance']
    print(f"\nFuzzy action computed: {fuzzy_action}")
    fuzzy_action = map_action(fuzzy_action)
    print(f"Mapped to: {fuzzy_action}")
    
    return fuzzy_action
    
### CHAT FUNCTIONS ###

def build_system_prompt(product_info):
    global SYSTEM_PROMPT
    global CONVERSATION
    SYSTEM_PROMPT = f"""Eres un vendedor amable experto en negociaciones por chat. Estás vendiendo productos de segunda mano. Eres conciso y profesional.
    
    El producto que estás veniendo ahora mismo es un {product_info['nombre_producto']} y su precio original es {product_info['precio_original']} euros.
    
    Recibirás una conversación completa con mensajes con esta estructura:
    
    - Mensaje del comprador: [mensaje]
    - Acción que debes tomar: [acción]
    - Precio ofertado por el comprador: [precio ofertado]
    Cuando la acción que debes tomar sea "Contraoferta", además recibirás otro parámetro que te indica la contraoferta que tienes que hacerle:
    - Contraoferta del vendedor: [precio ofertado por el vendedor]
    
    La acción está determinada por un sistema difuso que tiene en cuenta el tono del comprador, la diferencia relativa entre el ofertado 
    por el vendedor y el precio ofertado por el comprador.
    
    Las acciones que se te manden pueden ser únicamente una de estas:
    - Aceptar: En ese caso, debes aceptar la oferta del comprador y cerrar el trato.
    - Contraoferta: En este caso, debes ofrecer una contraoferta al comprador. Puedes ofrecer un precio ligeramente más bajo con un descuento de máximo 15% del precio original.
    - Mantener: En este caso, debes mantenerte firme con el precio original e indicarle amablemente que en principio no tienes pensado bajar el precio. La conversación puede continuar.
    - Rechazar: En este caso, debes rechazar la oferta del comprador e indicar educamente que no estás dispuesto a negociar más porque no llegaréis
    a un acuerdo beneficioso para ambos. Cierra la conversación.
    
    Tu tarea consiste en generar el siguiente mensaje de la conversación que sirva como respuesta para el comprador, utilizando obligatoriamente la acción que se te indica en el último mensaje.
    
    Si recibes un mensaje del usuario que no es una oferta, simplemente responde a la pregunta o comentario del usuario, sin tomar ninguna decisión y trata de proceder con la negociación."""

    CONVERSATION = [{"role": "system", "content": SYSTEM_PROMPT}]
    
def generate_seller_response(message,context={},fuzzy_action=None):
    '''Generate a response from the seller using OpenAI's API.'''
    
    print(f"\nContext: {context}")
    
    if not fuzzy_action and not context:
        user_prompt = message
    elif fuzzy_action == "Contraoferta":
        user_prompt = f'''
        Mensaje del comprador: {message}
        Acción que debes tomar: {fuzzy_action}
        Precio ofertado por el comprador: {context['precio_ofertado']}
        Contraoferta del vendedor: {context['contraoferta']}
        '''
    else:
        user_prompt = f'''
        Mensaje del comprador: {message}'
        Acción que debes tomar: {fuzzy_action}
        Precio ofertado por el comprador: {context['precio_ofertado']}
        '''
        
    CONVERSATION.append({"role": "user", "content": user_prompt})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=CONVERSATION,
            temperature=0.7
        )
    
    except Exception as e:
        print("Error:", e)
        return "Lo siento, no puedo responder en este momento."
    
    CONVERSATION.append({"role":"assistant","content":response.choices[0].message.content})
    
    return response.choices[0].message.content
    


def chat(context, simulation):
    '''Run the chat simulation with the user.
    product_info: dict with product information (name and price).'''
    
    n_interactions = 1 # initialize conversation duration to 1
    
    context["ultima_oferta"] = context['precio_original']
    
    while True:
        # get users' message
        user_message = input("User: ")
        
        if user_message.lower() in ["salir", "adiós", "adios","hasta luego"]:
            print("Ending conversation...")
            break
        
        # get context information from users' message
        offered_price = extract_price(user_message)
        
        if offered_price is None:
            # offer a normal response
            response = generate_seller_response(user_message)
        else:   
            price_difference = (context['precio_original'] - offered_price)/context['precio_original'] * 100 # percentage difference
            tono_score = get_tone_score(user_message)
            fuzzy_action = compute_fuzzy_action(simulation, tono_score,price_difference,n_interactions)        
            
            context.update({
                'precio_ofertado': offered_price
            })
            
            if fuzzy_action == "Contraoferta":
                context['contraoferta'] = round(min(
                                                    max(context['precio_original'] * 0.9,
                                                    (offered_price+context['precio_original'])/2),
                                                context["ultima_oferta"]))
                    
            response = generate_seller_response(user_message,context,fuzzy_action)
            context['ultima_oferta'] = context['contraoferta'] if fuzzy_action == "Contraoferta" else context['ultima_oferta']
                        
            n_interactions += 1 # increment conversation duration only if the user made an offer
        
        print(f"Seller: {response}")
        
        if fuzzy_action in ["Rechazar","Aceptar"]:
            print("Ending conversation...")
            break
        
        


if __name__ == "__main__":

    product_info = {
        'nombre_producto': 'Patinete Eléctrico',
        'precio_original': 250
    }

    ### FUZZY LOGIC SYSTEM SETUP ###
    negotiation_ctrl, simulation = setup_fuzzy_logic()
    
    build_system_prompt(product_info)
    
    ### CHAT SIMULATION ###
    chat(product_info, simulation)
    
    
