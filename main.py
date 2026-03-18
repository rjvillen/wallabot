import streamlit as st
import numpy as np
from fuzzy_utils import *
import openai
import os
from dotenv import load_dotenv

import matplotlib

from utils import *

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


### CHATBOT FUNCTIONS ###
def build_system_prompt(product_info):
    system_prompt = f"""Eres un vendedor amable experto en negociaciones por chat. Estás vendiendo productos de segunda mano. Eres conciso y profesional.
    
    El producto que estás viniendo ahora mismo es un {product_info['nombre_producto']} y su precio original es {product_info['precio_original']} euros.

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
        
    return [{"role": "system", "content": system_prompt}]
    
def generate_seller_response(message, context={}, fuzzy_action=None, conversation=None):
    """Generate a response from the seller using OpenAI's API, using the provided conversation history."""
    
    # Build the user prompt based on the context and fuzzy action.
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
        Mensaje del comprador: {message}
        Acción que debes tomar: {fuzzy_action}
        Precio ofertado por el comprador: {context['precio_ofertado']}
        '''
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation+[{'role': 'user', 'content': user_prompt}],
            temperature=0.7
        )
    except Exception as e:
        print(e)
        st.error("Lo siento, no puedo responder en este momento.")
        return "Lo siento, no puedo responder en este momento."
    
    response_content = response.choices[0].message.content
    
    return response_content


# Streamlit App Initialization

if "CONVERSATION" not in st.session_state:
    
    # just some random product for testing
    product_info = {
        'nombre_producto': 'Patinete Eléctrico',
        'precio_original': 250,
        'imagen': 'https://images.unsplash.com/photo-1614226170075-d338afcd9c53?q=80&w=2080&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
    }
    
    # product_info = {
    #     'nombre_producto': 'Juego de Nintendo',
    #     'precio_original': 70,
    #     'imagen': 'https://www.mujeresaseguir.com/siteresources/files/847/86.webp',
    # }
    
    st.session_state.product_name = product_info['nombre_producto']
    st.session_state.product_price = product_info['precio_original']
    st.session_state.product_image = product_info['imagen']
    
    st.session_state.last_tono_score = 0
    st.session_state.last_price_diff = 0
    st.session_state.last_fuzzy_action = 0
    
    st.session_state.CONVERSATION = build_system_prompt(product_info)
    
    # Set up fuzzy logic
    negotiation_ctrl, simulation = setup_fuzzy_logic()
    st.session_state.negotiation_ctrl = negotiation_ctrl
    st.session_state.simulation = simulation # ControlSystemSimulation instance from skfuzzy library
    
    # Context stores negotiation info
    st.session_state.context = {'precio_original': product_info['precio_original'],
                                'ultima_oferta': product_info['precio_original']}
    st.session_state.n_interactions = 1

# saves history of fuzzy actions
if "history" not in st.session_state:
    st.session_state.history = []



### Interface ###

selected_view = st.radio("Vista:", ["🤖 Chat", "📊 Panel de control"], horizontal=True)

if selected_view == "🤖 Chat":
    
    st.title("🛍️ Wallabot: Chat de Negociación Inteligente")
    st.markdown(f"**Producto:** {st.session_state.product_name} - 💶 {st.session_state.product_price}€")
    st.image(image=st.session_state.product_image,
            width=300)
    
    for msg in st.session_state.CONVERSATION:
            if msg["role"] == "system":
                continue 
            elif msg["role"] == "user":
                st.chat_message(name="Comprador", avatar="🥸").markdown(msg["content"])
            elif msg["role"] == "assistant":
                st.chat_message(name="Vendedor", avatar="🤖").markdown(msg["content"])

    user_message = st.chat_input("Haz tu oferta o pregúntame algo...")

    if user_message:
        
        st.session_state.CONVERSATION.append({"role": "user", "content": user_message})
        
        # Check if the message includes a price offer
        offered_price = extract_price(user_message)
        
        if offered_price is None:
            # No price found; generate a normal response.
            response = generate_seller_response(user_message, conversation=st.session_state.CONVERSATION)
        else:
            print(st.session_state.context)
            # fuzzy parameters.
            price_difference = (st.session_state.context['precio_original'] - offered_price) / st.session_state.context['precio_original'] * 100
            tono_score,tono_mappings = get_tone_score(user_message)
            fuzzy_action,fuzzy_action_value = compute_fuzzy_action(st.session_state.simulation, tono_score, price_difference, st.session_state.n_interactions)
            
            # save state for the control panel view
            st.session_state.last_tono_score = tono_score
            st.session_state.last_price_diff = price_difference
            st.session_state.last_fuzzy_action = fuzzy_action
            st.session_state.tono_mappings = tono_mappings
            
            st.session_state.context.update({'precio_ofertado': offered_price})
            
            if fuzzy_action == "Contraoferta":
                st.session_state.context['contraoferta'] = round(min(
                                                                max(st.session_state.context['precio_original'] * 0.93, (offered_price + st.session_state.context['precio_original']) / 2),
                                                                st.session_state.context["ultima_oferta"]))
                
            response = generate_seller_response(user_message, st.session_state.context, fuzzy_action,
                                                conversation=st.session_state.CONVERSATION)
            if fuzzy_action == "Contraoferta":
                st.session_state.context['ultima_oferta'] = st.session_state.context['contraoferta']
            
            st.session_state.history.append({
                "user_input": user_message,
                "tone": tono_score,
                "price_diff": price_difference,
                "action": fuzzy_action
            })
            
            st.session_state.n_interactions += 1
            
            print(st.session_state.context)
            
            
            
        st.session_state.CONVERSATION.append({"role": "assistant", "content": response})
        
        st.rerun()      

elif selected_view == "📊 Panel de control":
    st.empty()
    st.title("📊 Panel de Control")
    
    # METRICS
    st.subheader("Variables de entrada")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Tono del mensaje (0 friendly - 10 agressive)", f"{st.session_state.last_tono_score:.2f}")
       
        st.metric("Diferencia de precio (%)", f"{st.session_state.last_price_diff:.2f}%")
        st.metric("Duración (Interacciones)", st.session_state.n_interactions)

    with col2:
        if "tono_mappings" in st.session_state:
            st.markdown("**Desglose del tono**")

            for label, value in st.session_state.tono_mappings.items():
                st.markdown(f"- `{label.capitalize()}` → **{value:.2f}**")
        st.metric("Acción difusa", st.session_state.last_fuzzy_action or "No calculada")

    st.divider()

    # DISPLAY MEMBERSHIP FUNCTIONS
    st.subheader("Funciones de pertenencia")

    input_figs = [get_membership_plot(var,st.session_state.simulation) for var in ["tono", "diferencia", "duracion"]]
    
    for title,fig in zip(["Tono del mensaje", "Diferencia relativa de precio", "Duración de la negociación"],input_figs):
        st.markdown(f"**{title}**")
        st.pyplot(fig)

    st.markdown("**Resultado del sistema**")
    output_fig = get_membership_plot("acceptance",st.session_state.simulation)
    st.pyplot(output_fig)

    st.divider()

    # DECISION HISTORY
    st.subheader("Histórico de interacciones")

    if "history" in st.session_state and st.session_state.history:
        for item in reversed(st.session_state.history[-10:]):
            st.markdown(f"""
            <div style="padding:8px;border-left:3px solid #2c6e49;margin-bottom:12px;">
            🧍‍♀️ <strong>Usuario:</strong> {item['user_input']}<br>
            🎙️ <strong>Tono:</strong> {item['tone']:.2f} — 💸 <strong>Diferencia:</strong> {item['price_diff']:.1f}%<br>
            🧠 <strong>Acción fuzzy:</strong> <span style="color:#2c6e49;font-weight:bold;">{item['action']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay interacciones previas registradas.")

