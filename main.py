import streamlit as st
import numpy as np
from fuzzy_utils import *
import openai
import os
from dotenv import load_dotenv

from utils import *
# from chatbot import *

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


### Streamlit App Initialization ###
# tab1, tab2 = st.tabs(["🤖 Chatbot", "📊 Panel de Control"])

#st.set_page_config(page_title="Wallabot - Chat de Negociación", layout="centered")

# Initialize session state variables on first load.
if "CONVERSATION" not in st.session_state:
    
    # Define product information.
    product_info = {
        'nombre_producto': 'Patinete Eléctrico',
        'precio_original': 250,
        'imagen': 'https://images.unsplash.com/photo-1614226170075-d338afcd9c53?q=80&w=2080&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
    }
    
    st.session_state.product_name = product_info['nombre_producto']
    st.session_state.product_price = product_info['precio_original']
    st.session_state.product_image = product_info['imagen']
    
    # Initialize conversation history with system prompt
    st.session_state.CONVERSATION = build_system_prompt(product_info)
    
    # Set up fuzzy logic.
    negotiation_ctrl, simulation = setup_fuzzy_logic()
    st.session_state.negotiation_ctrl = negotiation_ctrl
    st.session_state.simulation = simulation
    
    # Context stores negotiation info.
    st.session_state.context = {'precio_original': product_info['precio_original'],
                                'ultima_oferta': product_info['precio_original']}
    st.session_state.n_interactions = 1



### Streamlit Control Panel ###
# with tab2:
#     st.title("📊 Panel de Control")
#     st.markdown("Aquí puedes ver los resultados de la negociación y ajustar los parámetros del sistema difuso.")
    
    # Display the fuzzy logic parameters.
    # st.subheader("Parámetros del Sistema Difuso")
    # st.write(f"**Tono del Comprador:** {st.session_state.context['tono_score']}")
    # st.write(f"**Diferencia de Precio:** {st.session_state.context['precio_ofertado']}")



### Streamlit Chat Interface ###

selected_view = st.radio("Ver:", ["🤖 Chat", "📊 Panel de control"], horizontal=True)

if selected_view == "🤖 Chat":
    # Aquí va el chat, con st.chat_input() al final (funcionará bien)
elif selected_view == "📊 Panel de control":
    # Mostrar métricas, gráficas, etc.

st.title("🛍️ Wallabot: Chat de Negociación Inteligente")
st.markdown(f"**Producto:** {st.session_state.product_name} - 💶 {st.session_state.product_price}€")
st.image(image=st.session_state.product_image,
        width=300)

user_message = st.chat_input("Haz tu oferta o pregúntame algo...")

if user_message:
    
    st.session_state.CONVERSATION.append({"role": "user", "content": user_message})
    
    # Check if the message includes a price offer.
    offered_price = extract_price(user_message)
    
    if offered_price is None:
        # No price found; generate a normal response.
        response = generate_seller_response(user_message, conversation=st.session_state.CONVERSATION)
    else:
        print(st.session_state.context)
        # Calculate fuzzy parameters.
        price_difference = (st.session_state.context['precio_original'] - offered_price) / st.session_state.context['precio_original'] * 100
        tono_score = get_tone_score(user_message)
        fuzzy_action = compute_fuzzy_action(st.session_state.simulation, tono_score, price_difference, st.session_state.n_interactions)
        
        st.session_state.context.update({'precio_ofertado': offered_price})
        
        if fuzzy_action == "Contraoferta":
            st.session_state.context['contraoferta'] = round(min(
                                                            max(st.session_state.context['precio_original'] * 0.9, (offered_price + st.session_state.context['precio_original']) / 2),
                                                            st.session_state.context["ultima_oferta"]))
            
        response = generate_seller_response(user_message, st.session_state.context, fuzzy_action,
                                            conversation=st.session_state.CONVERSATION)
        if fuzzy_action == "Contraoferta":
            st.session_state.context['ultima_oferta'] = st.session_state.context['contraoferta']
        
        st.session_state.n_interactions += 1
        
        print(st.session_state.context)
        
    st.session_state.CONVERSATION.append({"role": "assistant", "content": response})
    
    for msg in st.session_state.CONVERSATION:
        if msg["role"] == "system":
            continue 
        elif msg["role"] == "user":
            st.chat_message(name="Comprador", avatar="👤").markdown(msg["content"])
        elif msg["role"] == "assistant":
            st.chat_message(name="Vendedor", avatar="🤖").markdown(msg["content"])