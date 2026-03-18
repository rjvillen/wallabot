# Library that contains all functions related to fuzzy logi such as plotting membership functions and computing fuzzy actions

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from utils import map_action

import matplotlib.pyplot as plt

global tono, diferencia, duracion, acceptance

ACTION_BY_LABEL = {
    'muy_bajo' : "Rechazar",
    'bajo'     : "Mantener",
    'alto'     : "Contraoferta",
    'muy_alto' : "Aceptar"
}

def setup_fuzzy_logic():
    
    print("Setting up fuzzy logic system...")
    
    global tono, diferencia, duracion, acceptance
    
    # Inputs
    tono = ctrl.Antecedent(np.arange(0, 11, 1), 'tono') # user's tone
    diferencia = ctrl.Antecedent(np.arange(0, 101, 1), 'diferencia') # price difference
    duracion = ctrl.Antecedent(np.arange(0, 16, 1), 'duracion') # duration

    tono['amigable'] = fuzz.trimf(tono.universe, [0, 0, 4])
    tono['neutral']   = fuzz.trimf(tono.universe, [2, 5, 8])
    tono['agresivo']  = fuzz.trimf(tono.universe, [6, 10, 10])

    diferencia['baja'] = fuzz.trapmf(diferencia.universe, [0, 0, 5, 10])
    diferencia['media'] = fuzz.trapmf(diferencia.universe, [5, 10, 15, 20])
    diferencia['alta'] = fuzz.trapmf(diferencia.universe, [15, 20, 100, 100])

    duracion['corta'] = fuzz.trapmf(duracion.universe, [0, 0, 2, 4])
    duracion['media'] = fuzz.trapmf(duracion.universe, [3, 4, 6, 7])
    duracion['larga'] = fuzz.trapmf(duracion.universe, [6, 8, 15, 15])

    # Outputs
    acceptance = ctrl.Consequent(np.arange(0, 101, 1), 'acceptance', defuzzify_method='mom')

    acceptance['muy_bajo'] = fuzz.trimf(acceptance.universe, [0, 0, 25]) # -> Rechazar (terminar negociación) / Reject (end negotiation)
    acceptance['bajo'] = fuzz.trimf(acceptance.universe, [15, 35, 55]) # -> Mantener el precio (seguir negociando) / Mantain price (keep negotiating)
    acceptance['alto'] = fuzz.trimf(acceptance.universe, [45, 65, 85]) # -> Ofrecer contraoferta (seguir negociando) / offer counteroffer / (and keep negotiating)
    acceptance['muy_alto'] = fuzz.trimf(acceptance.universe, [75, 100, 100]) # -> Aceptar (cerrar trato) / Accept (close deal)

    # Rules

    # Reglas para tono 'amigable' / rules for friendly tone
    rule_A1 = ctrl.Rule(tono['amigable'] & diferencia['baja'] & (duracion['corta'] | duracion['media']), acceptance['muy_alto'])
    rule_A2 = ctrl.Rule(tono['amigable'] & diferencia['baja'] & duracion['larga'], acceptance['alto'])
    rule_A3 = ctrl.Rule(tono['amigable'] & diferencia['media'] & (duracion['corta'] | duracion['media']), acceptance['alto'])
    rule_A4 = ctrl.Rule(tono['amigable'] & diferencia['media'] & duracion['larga'], acceptance['bajo'])
    rule_A5 = ctrl.Rule(tono['amigable'] & diferencia['alta'] & duracion['corta'], acceptance['alto'])
    rule_A6 = ctrl.Rule(tono['amigable'] & diferencia['alta'] & duracion['media'], acceptance['bajo'])
    rule_A7 = ctrl.Rule(tono['amigable'] & diferencia['alta'] & duracion['larga'], acceptance['muy_bajo'])

    # Reglas para tono 'neutral' / rules for neutral tone
    rule_N1 = ctrl.Rule(tono['neutral'] & diferencia['baja'] & (duracion['corta'] | duracion['media']), acceptance['muy_alto'])
    rule_N2 = ctrl.Rule(tono['neutral'] & diferencia['baja'] & duracion['larga'], acceptance['alto'])
    rule_N3 = ctrl.Rule(tono['neutral'] & diferencia['media'] & duracion['corta'], acceptance['alto'])
    rule_N4 = ctrl.Rule(tono['neutral'] & diferencia['media'] & (duracion['media'] | duracion['larga']), acceptance['bajo'])
    rule_N5 = ctrl.Rule(tono['neutral'] & diferencia['alta'], acceptance['bajo']) 

    # Reglas para tono 'agresivo' / rules for agressive tone
    rule_AG1 = ctrl.Rule(tono['agresivo'] & diferencia['baja'] & (duracion['corta'] | duracion['media']), acceptance['bajo'])
    rule_AG2 = ctrl.Rule(tono['agresivo'] & diferencia['baja'] & duracion['larga'], acceptance['muy_bajo'])
    rule_AG3 = ctrl.Rule(tono['agresivo'] & diferencia['media'] & (duracion['corta'] | duracion['media']), acceptance['bajo'])
    rule_AG4 = ctrl.Rule(tono['agresivo'] & diferencia['media'] & duracion['larga'], acceptance['muy_bajo'])
    rule_AG5 = ctrl.Rule(tono['agresivo'] & diferencia['alta'], acceptance['muy_bajo'])

    # (there are 17 rules in total)
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

    crisp = simulation.output['acceptance']
    idx   = int(round(crisp))

    best_label = max(
    acceptance.terms,
    key=lambda lab: acceptance.terms[lab].mf[idx])
    
    best_action = ACTION_BY_LABEL[best_label]

    print(f"Crisp value: {crisp:.2f} → index {idx}")
    print("Pertenencias en ese punto:",{lab: acceptance.terms[lab].mf[idx] for lab in acceptance.terms})
    print(f"Ganador: {best_label} → {best_action}")

    return best_action, crisp

def get_membership_plot(var,simulation):
    if var not in ['tono', 'diferencia', 'duracion', 'acceptance']:
        raise ValueError("Variable must be one of: 'tono', 'diferencia', 'duracion', 'acceptance'")
    elif var == "acceptance":
        fig = acceptance.view(sim=simulation) 
    elif var == "tono":
        fig = tono.view(sim=simulation)
    elif var == "diferencia":
        fig = diferencia.view(sim=simulation)
    elif var == "duracion":
        fig = duracion.view(sim=simulation)
    
    fig = plt.gcf()
    return fig
